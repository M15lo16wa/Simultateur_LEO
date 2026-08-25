from datetime import datetime, timezone

from domain.entities.orbital_position import OrbitalPosition
from domain.entities.station import Station
from use_cases.compute_visibility_use_case import ComputeVisibilityUseCase

STATION = Station(name="Test Station", latitude_deg=48.8566, longitude_deg=2.3522, altitude_m=35.0)


def test_satellite_directly_overhead_is_visible_near_zenith() -> None:
    use_case = ComputeVisibilityUseCase(min_elevation_deg=25.0)
    position = OrbitalPosition(
        satellite_id="1",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        latitude_deg=STATION.latitude_deg,
        longitude_deg=STATION.longitude_deg,
        altitude_km=550.0,
        velocity_km_s=(0.0, 0.0, 0.0),
    )

    visibility = use_case.execute(position, STATION)

    assert visibility.is_visible
    assert visibility.elevation_deg > 89.0
    assert 545.0 <= visibility.distance_km <= 555.0


def test_satellite_on_opposite_side_of_earth_is_not_visible() -> None:
    use_case = ComputeVisibilityUseCase(min_elevation_deg=25.0)
    position = OrbitalPosition(
        satellite_id="2",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        latitude_deg=-STATION.latitude_deg,
        longitude_deg=STATION.longitude_deg + 180.0,
        altitude_km=550.0,
        velocity_km_s=(0.0, 0.0, 0.0),
    )

    visibility = use_case.execute(position, STATION)

    assert not visibility.is_visible
    assert visibility.elevation_deg < 0.0


def test_execute_many_processes_every_position() -> None:
    use_case = ComputeVisibilityUseCase(min_elevation_deg=25.0)
    positions = [
        OrbitalPosition(
            satellite_id=str(i),
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            latitude_deg=STATION.latitude_deg,
            longitude_deg=STATION.longitude_deg,
            altitude_km=550.0,
            velocity_km_s=(0.0, 0.0, 0.0),
        )
        for i in range(3)
    ]

    visibilities = use_case.execute_many(positions, STATION)

    assert len(visibilities) == 3
    assert all(v.is_visible for v in visibilities)
