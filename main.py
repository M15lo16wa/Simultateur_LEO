import sys
from datetime import datetime, timedelta, timezone

# La console Windows utilise un encodage (cp1252) qui ne représente pas tous les
# caractères Unicode : sans ceci, un simple print() avec le mauvais caractère peut
# lever une UnicodeEncodeError et tuer le process (vu avec "≈", probablement aussi
# via des avertissements internes de matplotlib).
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.settings import settings
from domain.entities.station import Station
from infrastructure.propagation.sgp4_propagator import SGP4Propagator
from infrastructure.radio.fcc_itu_radio_config_repository import FCCITURadioConfigRepository
from infrastructure.tle.celestrak_tle_repository import CelestrakTLERepository, TLEDataNotYetAvailable
from presentation.visualizer.app import launch as launch_visualizer
from use_cases.compute_doppler_use_case import ComputeDopplerUseCase
from use_cases.compute_link_budget_use_case import ComputeLinkBudgetUseCase
from use_cases.compute_rtt_use_case import ComputeRTTUseCase
from use_cases.compute_visibility_use_case import ComputeVisibilityUseCase
from use_cases.detect_handover_use_case import DetectHandoverUseCase
from use_cases.propagate_positions_use_case import PropagatePositionsUseCase

MAX_SATELLITES = 300
PASS_SEARCH_HORIZON_HOURS = 24.0
PASS_SEARCH_STEP_MINUTES = 2.0
HANDOVER_WINDOW_MINUTES = 30.0
HANDOVER_STEP_MINUTES = 1.0


def _default_station() -> Station:
    return Station(
        name=settings.default_station_name,
        latitude_deg=settings.default_station_latitude_deg,
        longitude_deg=settings.default_station_longitude_deg,
        altitude_m=settings.default_station_altitude_m,
    )


def _fetch_satellites(repository: CelestrakTLERepository, max_satellites: int) -> list:
    try:
        satellites = repository.fetch_catalog(settings.celestrak_group)[:max_satellites]
        print(f"{len(satellites)} satellites chargés depuis CelesTrak (groupe: {settings.celestrak_group})")
    except TLEDataNotYetAvailable:
        print("Groupe complet pas encore rafraîchi (limite ~2h), repli sur la requête NAME= (catalogue complet).")
        satellites = repository.fetch_by_name("STARLINK")[:max_satellites]
        print(f"{len(satellites)} satellites chargés via NAME=STARLINK")
    return satellites


def _find_next_visible_pass(
    satellites: list,
    station: Station,
    start: datetime,
    horizon_hours: float = PASS_SEARCH_HORIZON_HOURS,
    step_minutes: float = PASS_SEARCH_STEP_MINUTES,
):
    """Balaie le temps jusqu'à trouver le premier instant où au moins un satellite dépasse le seuil d'élévation."""
    propagate_use_case = PropagatePositionsUseCase(SGP4Propagator())
    visibility_use_case = ComputeVisibilityUseCase(min_elevation_deg=settings.min_elevation_deg)

    steps = int(horizon_hours * 60 / step_minutes)
    for i in range(steps):
        t = start + timedelta(minutes=i * step_minutes)
        positions = propagate_use_case.execute(satellites, at=t)
        visibilities = visibility_use_case.execute_many(positions, station)
        visible = [v for v in visibilities if v.is_visible]
        if visible:
            best = max(visible, key=lambda v: v.elevation_deg)
            return t, best
    return None, None


def _run_handover_timeline(
    satellites: list,
    station: Station,
    start: datetime,
    window_minutes: float = HANDOVER_WINDOW_MINUTES,
    step_minutes: float = HANDOVER_STEP_MINUTES,
) -> list:
    """Suit le satellite servant (le plus proche visible) minute par minute et retourne chaque
    changement détecté — la seule façon de voir un vrai handover, par opposition à un instant unique
    où il n'existe encore aucun 'précédent' à comparer."""
    propagate_use_case = PropagatePositionsUseCase(SGP4Propagator())
    visibility_use_case = ComputeVisibilityUseCase(min_elevation_deg=settings.min_elevation_deg)
    handover_use_case = DetectHandoverUseCase()

    steps = int(window_minutes / step_minutes) + 1
    events = []
    for i in range(steps):
        t = start + timedelta(minutes=i * step_minutes)
        positions = propagate_use_case.execute(satellites, at=t)
        visibilities = visibility_use_case.execute_many(positions, station)
        event = handover_use_case.execute(visibilities, station.name)
        if event:
            events.append((i * step_minutes, event))
    return events


def _run_analysis(satellites: list, station: Station, at: datetime) -> list:
    """Exécute visibilité -> RTT -> handover -> Doppler -> bilan de liaison à l'instant `at`, imprime les résultats."""
    satellites_by_id = {sat.norad_id: sat for sat in satellites}

    print(f"\n=== Visibilité à {at.isoformat()} ===")
    visibility_use_case = ComputeVisibilityUseCase(min_elevation_deg=settings.min_elevation_deg)
    positions = PropagatePositionsUseCase(SGP4Propagator()).execute(satellites, at=at)
    visibilities = visibility_use_case.execute_many(positions, station)
    visible = sorted((v for v in visibilities if v.is_visible), key=lambda v: v.distance_km)
    print(f"{len(visible)} satellites visibles depuis {station.name} (seuil {settings.min_elevation_deg}°)")

    print("\n=== RTT (5 plus proches) ===")
    rtt_use_case = ComputeRTTUseCase(settings.speed_of_light_km_s, settings.processing_delay_ms)
    for v in visible[:5]:
        rtt = rtt_use_case.execute(v)
        print(f"  {rtt.satellite_id:>8}  distance={rtt.distance_km:7.1f} km  RTT={rtt.rtt_ms:6.2f} ms")

    print(f"\n=== Handover (suivi sur {HANDOVER_WINDOW_MINUTES:.0f} min à partir de {at.isoformat()}) ===")
    handover_events = _run_handover_timeline(satellites, station, at)
    if handover_events:
        for minute, event in handover_events:
            print(f"  t+{minute:4.0f} min  {event.reason} : {event.previous_satellite_id} -> {event.new_satellite_id}")
    else:
        print("  Aucun satellite visible sur toute la fenêtre : pas de satellite servant à sélectionner.")

    radio_repository = FCCITURadioConfigRepository(settings.radio_reference_dir)
    radio_config = radio_repository.get_config(settings.radio_band)

    print("\n=== Doppler (3 plus proches) ===")
    doppler_use_case = ComputeDopplerUseCase(SGP4Propagator(), visibility_use_case, settings.speed_of_light_km_s)
    for v in visible[:3]:
        doppler = doppler_use_case.execute(
            satellites_by_id[v.satellite_id], station, at, radio_config.downlink_frequency_hz
        )
        print(f"  {doppler.satellite_id:>8}  décalage={doppler.frequency_shift_hz:9.1f} Hz")

    print("\n=== Bilan de liaison (3 plus proches) ===")
    link_budget_use_case = ComputeLinkBudgetUseCase(radio_config)
    for v in visible[:3]:
        link_budget = link_budget_use_case.execute(v)
        print(
            f"  {link_budget.satellite_id:>8}  SNR={link_budget.snr_db:6.1f} dB  "
            f"débit~{link_budget.estimated_throughput_mbps:7.1f} Mbps"
        )

    return visible


def main() -> None:
    station = _default_station()

    print("=== Chargement des satellites ===")
    tle_repository = CelestrakTLERepository()
    satellites = _fetch_satellites(tle_repository, MAX_SATELLITES)

    now = datetime.now(timezone.utc)
    at = now

    print(f"\n=== Vérification de l'instant présent ({now.isoformat()}) ===")
    positions_now = PropagatePositionsUseCase(SGP4Propagator()).execute(satellites, at=now)
    visibility_use_case = ComputeVisibilityUseCase(min_elevation_deg=settings.min_elevation_deg)
    visible_now = [v for v in visibility_use_case.execute_many(positions_now, station) if v.is_visible]

    if visible_now:
        print(f"{len(visible_now)} satellite(s) déjà visible(s) maintenant, pas besoin de chercher plus loin.")
    else:
        print("Aucun satellite visible maintenant, recherche du prochain passage (jusqu'à 24h)...")
        pass_time, best = _find_next_visible_pass(satellites, station, now)
        if pass_time is None:
            print("Aucun passage visible trouvé dans les prochaines 24h avec ce jeu de satellites.")
            print("(Le groupe complet CelesTrak est peut-être encore limité ~2h ; réessaie plus tard.)")
            at = now
        else:
            delay_min = (pass_time - now).total_seconds() / 60
            print(
                f"Passage trouvé : satellite {best.satellite_id} dans {delay_min:.1f} min "
                f"(élévation {best.elevation_deg:.1f}°)"
            )
            at = pass_time

    _run_analysis(satellites, station, at)

    print("\n=== Rendu visuel (fenêtre interactive, live à partir de maintenant) ===")
    launch_visualizer(satellites, station)


if __name__ == "__main__":
    main()
