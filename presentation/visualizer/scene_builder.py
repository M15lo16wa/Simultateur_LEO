import math

import numpy as np
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (requis pour projection="3d")

from domain.entities.orbital_position import OrbitalPosition
from domain.entities.station import Station
from domain.entities.visibility import Visibility

EARTH_RADIUS_KM = 6371.0
_CURVE_COLORS = ["#2980b9", "#c0392b", "#27ae60", "#8e44ad", "#d35400"]


def _lat_lon_alt_to_xyz(
    lat_deg: float, lon_deg: float, alt_km: float, earth_radius_km: float = EARTH_RADIUS_KM
) -> tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    r = earth_radius_km + alt_km

    x = r * math.cos(lat) * math.cos(lon)
    y = r * math.cos(lat) * math.sin(lon)
    z = r * math.sin(lat)
    return x, y, z


def _coverage_circle_xyz(
    station: Station, altitude_km: float, min_elevation_deg: float, n_points: int = 72
) -> tuple[list[float], list[float], list[float]]:
    """Cercle au sol délimitant la zone de couverture (satellites au-dessus de l'élévation minimale)."""
    e = math.radians(min_elevation_deg)
    gamma = math.acos((EARTH_RADIUS_KM * math.cos(e)) / (EARTH_RADIUS_KM + altitude_km)) - e

    lat1 = math.radians(station.latitude_deg)
    lon1 = math.radians(station.longitude_deg)

    xs, ys, zs = [], [], []
    for i in range(n_points + 1):
        bearing = 2 * math.pi * i / n_points
        lat2 = math.asin(
            math.sin(lat1) * math.cos(gamma) + math.cos(lat1) * math.sin(gamma) * math.cos(bearing)
        )
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(gamma) * math.cos(lat1),
            math.cos(gamma) - math.sin(lat1) * math.sin(lat2),
        )
        x, y, z = _lat_lon_alt_to_xyz(math.degrees(lat2), math.degrees(lon2), 0.0)
        xs.append(x)
        ys.append(y)
        zs.append(z)
    return xs, ys, zs


def _draw_earth_sphere(ax, n: int = 30) -> None:
    u = np.linspace(0, 2 * math.pi, n)
    v = np.linspace(0, math.pi, n)

    x = EARTH_RADIUS_KM * np.outer(np.cos(u), np.sin(v))
    y = EARTH_RADIUS_KM * np.outer(np.sin(u), np.sin(v))
    z = EARTH_RADIUS_KM * np.outer(np.ones_like(u), np.cos(v))

    ax.plot_surface(x, y, z, color="#1b3a5c", alpha=0.35, linewidth=0, antialiased=True, shade=True)


def _draw_orbital_panel(
    ax,
    positions_snapshot: list[OrbitalPosition],
    visibilities_snapshot: dict[str, Visibility],
    station: Station,
    min_elevation_deg: float,
) -> None:
    _draw_earth_sphere(ax)

    visible_xyz: list[tuple[float, float, float]] = []
    hidden_xyz: list[tuple[float, float, float]] = []
    altitudes: list[float] = []

    for position in positions_snapshot:
        xyz = _lat_lon_alt_to_xyz(position.latitude_deg, position.longitude_deg, position.altitude_km)
        altitudes.append(position.altitude_km)
        visibility = visibilities_snapshot.get(position.satellite_id)
        if visibility is not None and visibility.is_visible:
            visible_xyz.append(xyz)
        else:
            hidden_xyz.append(xyz)

    if hidden_xyz:
        hx, hy, hz = zip(*hidden_xyz)
        ax.scatter(hx, hy, hz, s=10, color="#8a97a8", label="Non visibles")
    if visible_xyz:
        vx, vy, vz = zip(*visible_xyz)
        ax.scatter(vx, vy, vz, s=35, color="#2ecc71", label="Visibles")

    station_xyz = _lat_lon_alt_to_xyz(
        station.latitude_deg, station.longitude_deg, station.altitude_m / 1000.0
    )
    ax.scatter(*station_xyz, s=90, color="#e74c3c", marker="D", label=station.name)

    if altitudes:
        mean_altitude_km = sum(altitudes) / len(altitudes)
        cx, cy, cz = _coverage_circle_xyz(station, mean_altitude_km, min_elevation_deg)
        ax.plot(cx, cy, cz, color="#f1c40f", linewidth=2, label="Zone de couverture")

    limit = EARTH_RADIUS_KM + 1500
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    ax.set_box_aspect((1, 1, 1))
    ax.set_title(f"Plan orbital & couverture ({len(positions_snapshot)} satellites)")
    ax.legend(loc="upper left", fontsize=7)


def _annotate_extremum(
    ax, x: list[float], y: list[float], color: str, fmt: str, kind: str, dx: float = 5
) -> None:
    """Marque le point maximal ou minimal d'une courbe, s'il s'agit d'un vrai pic/creux interne
    (pas juste le début ou la fin de la fenêtre observée, qui n'apporte pas d'information)."""
    if len(y) < 3:
        return

    index = (max if kind == "max" else min)(range(len(y)), key=lambda i: y[i])
    if index == 0 or index == len(y) - 1:
        return

    xi, yi = x[index], y[index]
    marker = "^" if kind == "max" else "v"

    ax.scatter([xi], [yi], color=color, s=45, marker=marker, zorder=5, edgecolors="black", linewidths=0.6)
    ax.annotate(
        fmt.format(yi),
        xy=(xi, yi),
        xytext=(dx, 7 if kind == "max" else -11),
        textcoords="offset points",
        fontsize=7,
        color=color,
        fontweight="bold",
    )


def _draw_distance_rtt_panel(ax, series: dict[str, dict[str, list]]) -> None:
    ax_rtt = ax.twinx()

    for i, (satellite_id, data) in enumerate(series.items()):
        color = _CURVE_COLORS[i % len(_CURVE_COLORS)]
        minutes = data["minutes"]
        ax.plot(minutes, data["distance_km"], color=color, label=f"{satellite_id}")
        ax_rtt.plot(minutes, data["rtt_ms"], color=color, linestyle="--", alpha=0.6)

        # RTT dérive directement de la distance : ses extrema tombent au même instant,
        # inutile de dupliquer l'annotation (juste la distance, plus parlante, est marquée).
        _annotate_extremum(ax, minutes, data["distance_km"], color, "{:.0f} km", kind="min")
        _annotate_extremum(ax, minutes, data["distance_km"], color, "{:.0f} km", kind="max")

    ax.set_xlabel("Temps (minutes)")
    ax.set_ylabel("Distance (km) — trait plein")
    ax_rtt.set_ylabel("RTT (ms) — pointillés")
    ax.set_title("Distance & RTT dans le temps (▲ max  ▼ min)")
    ax.legend(loc="upper right", fontsize=7, title="Satellite")
    ax.grid(alpha=0.3)


def _draw_doppler_throughput_panel(ax, series: dict[str, dict[str, list]]) -> None:
    ax_throughput = ax.twinx()

    for i, (satellite_id, data) in enumerate(series.items()):
        color = _CURVE_COLORS[i % len(_CURVE_COLORS)]
        minutes = data["minutes"]
        ax.plot(minutes, data["doppler_hz"], color=color, label=f"{satellite_id}")
        ax_throughput.plot(minutes, data["throughput_mbps"], color=color, linestyle="--", alpha=0.6)

        _annotate_extremum(ax, minutes, data["doppler_hz"], color, "{:+.0f} Hz", kind="max", dx=5)
        _annotate_extremum(ax, minutes, data["doppler_hz"], color, "{:+.0f} Hz", kind="min", dx=5)
        _annotate_extremum(ax_throughput, minutes, data["throughput_mbps"], color, "{:.0f} Mbps", kind="max", dx=-45)
        _annotate_extremum(ax_throughput, minutes, data["throughput_mbps"], color, "{:.0f} Mbps", kind="min", dx=-45)

    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Temps (minutes)")
    ax.set_ylabel("Décalage Doppler (Hz) — trait plein")
    ax_throughput.set_ylabel("Débit estimé (Mbps) — pointillés")
    ax.set_title("Doppler & débit estimé dans le temps (▲ max  ▼ min)")
    ax.legend(loc="upper right", fontsize=7, title="Satellite")
    ax.grid(alpha=0.3)


def build_figure(
    positions_snapshot: list[OrbitalPosition],
    visibilities_snapshot: dict[str, Visibility],
    station: Station,
    min_elevation_deg: float,
    series: dict[str, dict[str, list]],
) -> Figure:
    fig = Figure(figsize=(14, 8), layout="constrained")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.2, 1])

    ax_3d = fig.add_subplot(gs[:, 0], projection="3d")
    _draw_orbital_panel(ax_3d, positions_snapshot, visibilities_snapshot, station, min_elevation_deg)

    if series:
        ax_distance = fig.add_subplot(gs[0, 1])
        _draw_distance_rtt_panel(ax_distance, series)

        ax_doppler = fig.add_subplot(gs[1, 1])
        _draw_doppler_throughput_panel(ax_doppler, series)
    else:
        ax_empty = fig.add_subplot(gs[:, 1])
        ax_empty.axis("off")
        ax_empty.text(0.5, 0.5, "Aucun satellite suivi pour les courbes", ha="center", va="center")

    fig.suptitle(f"Simulateur LEO — {station.name}, seuil élévation {min_elevation_deg}°", fontsize=13)
    return fig
