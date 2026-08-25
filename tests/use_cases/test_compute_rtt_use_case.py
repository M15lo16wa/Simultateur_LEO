from datetime import datetime, timezone

from domain.entities.visibility import Visibility
from use_cases.compute_rtt_use_case import ComputeRTTUseCase

SPEED_OF_LIGHT_KM_S = 299_792.458


def test_rtt_matches_speed_of_light_round_trip() -> None:
    use_case = ComputeRTTUseCase(speed_of_light_km_s=SPEED_OF_LIGHT_KM_S, processing_delay_ms=5.0)
    visibility = Visibility(
        satellite_id="44714",
        station_name="Test Station",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        elevation_deg=45.0,
        azimuth_deg=180.0,
        distance_km=1000.0,
        is_visible=True,
    )

    result = use_case.execute(visibility)

    expected_propagation_ms = 2 * 1000.0 / SPEED_OF_LIGHT_KM_S * 1000
    assert result.propagation_delay_ms == expected_propagation_ms
    assert result.processing_delay_ms == 5.0
    assert result.rtt_ms == expected_propagation_ms + 5.0


def test_rtt_increases_with_distance() -> None:
    use_case = ComputeRTTUseCase(speed_of_light_km_s=SPEED_OF_LIGHT_KM_S, processing_delay_ms=5.0)
    near = Visibility(
        satellite_id="1", station_name="S", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        elevation_deg=80.0, azimuth_deg=0.0, distance_km=550.0, is_visible=True,
    )
    far = Visibility(
        satellite_id="2", station_name="S", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        elevation_deg=25.0, azimuth_deg=0.0, distance_km=1500.0, is_visible=True,
    )

    assert use_case.execute(near).rtt_ms < use_case.execute(far).rtt_ms
