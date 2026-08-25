from datetime import datetime, timedelta, timezone

from domain.entities.satellite import Satellite
from domain.entities.station import Station
from infrastructure.propagation.sgp4_propagator import SGP4Propagator
from use_cases.compute_doppler_use_case import ComputeDopplerUseCase
from use_cases.compute_visibility_use_case import ComputeVisibilityUseCase

ISS_SATELLITE = Satellite(
    norad_id="25544",
    name="ISS (ZARYA)",
    tle_line1="1 25544U 98067A   26227.08368476  .00005059  00000+0  98393-4 0  9995",
    tle_line2="2 25544  51.6330   8.6029 0007564  47.5489 312.6138 15.49446478580889",
    epoch=datetime(2026, 8, 15, tzinfo=timezone.utc),
)
STATION = Station(name="Test Station", latitude_deg=48.8566, longitude_deg=2.3522, altitude_m=35.0)
DOWNLINK_FREQUENCY_HZ = 12_000_000_000.0


def test_doppler_shift_is_within_physical_bounds() -> None:
    use_case = ComputeDopplerUseCase(
        propagator=SGP4Propagator(),
        visibility_use_case=ComputeVisibilityUseCase(min_elevation_deg=-90.0),
        speed_of_light_km_s=299_792.458,
    )

    result = use_case.execute(
        ISS_SATELLITE,
        STATION,
        at=datetime(2026, 8, 16, 12, tzinfo=timezone.utc),
        downlink_frequency_hz=DOWNLINK_FREQUENCY_HZ,
    )

    # Vitesse orbitale LEO < 10 km/s -> le décalage Doppler en bande Ku reste sous ~500 kHz.
    assert abs(result.relative_velocity_km_s) < 10.0
    assert abs(result.frequency_shift_hz) < 500_000.0


def test_doppler_radial_velocity_matches_manual_distance_derivative() -> None:
    propagator = SGP4Propagator()
    visibility_use_case = ComputeVisibilityUseCase(min_elevation_deg=-90.0)
    at = datetime(2026, 8, 16, 12, tzinfo=timezone.utc)

    position_t0 = propagator.propagate(ISS_SATELLITE, at)
    position_t1 = propagator.propagate(ISS_SATELLITE, at + timedelta(seconds=1))
    distance_t0 = visibility_use_case.execute(position_t0, STATION).distance_km
    distance_t1 = visibility_use_case.execute(position_t1, STATION).distance_km
    expected_radial_velocity_km_s = distance_t1 - distance_t0

    use_case = ComputeDopplerUseCase(propagator, visibility_use_case, speed_of_light_km_s=299_792.458)
    result = use_case.execute(
        ISS_SATELLITE, STATION, at=at, downlink_frequency_hz=DOWNLINK_FREQUENCY_HZ
    )

    assert result.relative_velocity_km_s == expected_radial_velocity_km_s
