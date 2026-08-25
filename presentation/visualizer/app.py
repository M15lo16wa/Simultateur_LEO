import tkinter as tk
from datetime import datetime, timedelta, timezone

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from core.settings import settings
from domain.entities.satellite import Satellite
from domain.entities.station import Station
from infrastructure.propagation.sgp4_propagator import SGP4Propagator
from infrastructure.radio.fcc_itu_radio_config_repository import FCCITURadioConfigRepository
from infrastructure.tle.celestrak_tle_repository import CelestrakTLERepository, TLEDataNotYetAvailable
from presentation.visualizer.scene_builder import build_figure
from use_cases.compute_doppler_use_case import ComputeDopplerUseCase
from use_cases.compute_link_budget_use_case import ComputeLinkBudgetUseCase
from use_cases.compute_rtt_use_case import ComputeRTTUseCase
from use_cases.compute_visibility_use_case import ComputeVisibilityUseCase
from use_cases.propagate_positions_use_case import PropagatePositionsUseCase

MAX_SATELLITES = 300
TRACKED_SATELLITES_COUNT = 3
TIME_WINDOW_MINUTES = 20
TIME_STEP_SECONDS = 30
REFRESH_INTERVAL_MS = 30_000


def fetch_satellites(max_satellites: int = MAX_SATELLITES) -> list[Satellite]:
    repository = CelestrakTLERepository()
    try:
        satellites = repository.fetch_catalog(settings.celestrak_group)[:max_satellites]
        print(f"{len(satellites)} satellites chargés depuis CelesTrak (groupe: {settings.celestrak_group})")
    except TLEDataNotYetAvailable:
        print("Groupe complet pas encore rafraîchi (limite ~2h), repli sur la requête NAME= (catalogue complet).")
        satellites = repository.fetch_by_name("STARLINK")[:max_satellites]
        print(f"{len(satellites)} satellites chargés via NAME=STARLINK")
    return satellites


def default_station() -> Station:
    return Station(
        name=settings.default_station_name,
        latitude_deg=settings.default_station_latitude_deg,
        longitude_deg=settings.default_station_longitude_deg,
        altitude_m=settings.default_station_altitude_m,
    )


def _compute_snapshot_and_series(satellites: list[Satellite], station: Station, now: datetime):
    propagate_use_case = PropagatePositionsUseCase(SGP4Propagator())
    visibility_use_case = ComputeVisibilityUseCase(min_elevation_deg=settings.min_elevation_deg)
    rtt_use_case = ComputeRTTUseCase(settings.speed_of_light_km_s, settings.processing_delay_ms)
    doppler_use_case = ComputeDopplerUseCase(SGP4Propagator(), visibility_use_case, settings.speed_of_light_km_s)

    radio_config = FCCITURadioConfigRepository(settings.radio_reference_dir).get_config(settings.radio_band)
    link_budget_use_case = ComputeLinkBudgetUseCase(radio_config)

    positions_snapshot = propagate_use_case.execute(satellites, at=now)
    visibilities_snapshot = {
        v.satellite_id: v for v in visibility_use_case.execute_many(positions_snapshot, station)
    }

    tracked_positions = sorted(
        positions_snapshot, key=lambda p: visibilities_snapshot[p.satellite_id].distance_km
    )[:TRACKED_SATELLITES_COUNT]
    satellites_by_id = {sat.norad_id: sat for sat in satellites}

    step = timedelta(seconds=TIME_STEP_SECONDS)
    sample_count = int(TIME_WINDOW_MINUTES * 60 / TIME_STEP_SECONDS) + 1

    series: dict[str, dict[str, list]] = {}
    for position in tracked_positions:
        satellite = satellites_by_id[position.satellite_id]
        minutes, distance_km, rtt_ms, doppler_hz, throughput_mbps = [], [], [], [], []

        for i in range(sample_count):
            t = now + step * i
            pos = propagate_use_case.execute([satellite], at=t)[0]
            visibility = visibility_use_case.execute(pos, station)
            rtt = rtt_use_case.execute(visibility)
            doppler = doppler_use_case.execute(satellite, station, t, radio_config.downlink_frequency_hz)
            link_budget = link_budget_use_case.execute(visibility)

            minutes.append(i * TIME_STEP_SECONDS / 60)
            distance_km.append(visibility.distance_km)
            rtt_ms.append(rtt.rtt_ms)
            doppler_hz.append(doppler.frequency_shift_hz)
            throughput_mbps.append(max(link_budget.estimated_throughput_mbps, 0.0))

        series[satellite.norad_id] = {
            "minutes": minutes,
            "distance_km": distance_km,
            "rtt_ms": rtt_ms,
            "doppler_hz": doppler_hz,
            "throughput_mbps": throughput_mbps,
        }

    visible_count = sum(1 for v in visibilities_snapshot.values() if v.is_visible)
    return positions_snapshot, visibilities_snapshot, series, visible_count


class VisualizerWindow:
    """Fenêtre Tkinter embarquant le rendu matplotlib (3D interactif + courbes), avec rafraîchissement périodique."""

    def __init__(self, satellites: list[Satellite], station: Station) -> None:
        self._satellites = satellites
        self._station = station

        self._root = tk.Tk()
        self._root.title("Simulateur LEO — rendu interactif")
        self._root.geometry("1500x950")
        self._root.minsize(1100, 700)
        try:
            self._root.state("zoomed")  # démarre maximisée : le contenu (graphique + barre d'état) tient toujours
        except tk.TclError:
            pass

        self._status = tk.StringVar(value="Initialisation…")
        tk.Label(
            self._root,
            textvariable=self._status,
            anchor="w",
            padx=8,
            pady=5,
            font=("Segoe UI", 10),
            background="#2c3e50",
            foreground="white",
        ).pack(fill="x", side="bottom")

        self._canvas_widget: tk.Widget | None = None
        self._toolbar: NavigationToolbar2Tk | None = None

        self._redraw()
        self._root.after(REFRESH_INTERVAL_MS, self._periodic_refresh)

    def _redraw(self) -> None:
        now = datetime.now(timezone.utc)
        positions, visibilities, series, visible_count = _compute_snapshot_and_series(
            self._satellites, self._station, now
        )
        figure = build_figure(positions, visibilities, self._station, settings.min_elevation_deg, series)

        if self._canvas_widget is not None:
            self._canvas_widget.destroy()
        if self._toolbar is not None:
            self._toolbar.destroy()

        canvas = FigureCanvasTkAgg(figure, master=self._root)
        canvas.draw()

        self._toolbar = NavigationToolbar2Tk(canvas, self._root, pack_toolbar=False)
        self._toolbar.update()
        self._toolbar.pack(fill="x", side="top")

        self._canvas_widget = canvas.get_tk_widget()
        self._canvas_widget.pack(fill="both", expand=True, side="top")

        self._status.set(
            f"Mise à jour {now.strftime('%H:%M:%S')} UTC — {len(positions)} satellites, "
            f"{visible_count} visibles depuis {self._station.name}"
        )

    def _periodic_refresh(self) -> None:
        self._redraw()
        self._root.after(REFRESH_INTERVAL_MS, self._periodic_refresh)

    def run(self) -> None:
        self._root.mainloop()


def launch(satellites: list[Satellite], station: Station) -> None:
    VisualizerWindow(satellites, station).run()


def run(max_satellites: int = MAX_SATELLITES) -> None:
    satellites = fetch_satellites(max_satellites)
    station = default_station()
    launch(satellites, station)


if __name__ == "__main__":
    run()
