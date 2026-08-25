from datetime import datetime, timezone

from domain.entities.visibility import Visibility
from interfaces.radio_config_repository_port import RadioConfig
from use_cases.compute_link_budget_use_case import ComputeLinkBudgetUseCase

RADIO_CONFIG = RadioConfig(
    downlink_frequency_hz=12_000_000_000.0,
    bandwidth_hz=240_000_000.0,
    satellite_eirp_dbw=34.0,
    user_terminal_gain_dbi=34.0,
    system_noise_temperature_k=200.0,
    other_losses_db=2.0,
)


def _visibility(distance_km: float) -> Visibility:
    return Visibility(
        satellite_id="44714",
        station_name="Test Station",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        elevation_deg=45.0,
        azimuth_deg=0.0,
        distance_km=distance_km,
        is_visible=True,
    )


def test_throughput_decreases_with_distance() -> None:
    use_case = ComputeLinkBudgetUseCase(RADIO_CONFIG)

    near = use_case.execute(_visibility(550.0))
    far = use_case.execute(_visibility(1500.0))

    assert near.free_space_path_loss_db < far.free_space_path_loss_db
    assert near.received_power_dbm > far.received_power_dbm
    assert near.estimated_throughput_mbps > far.estimated_throughput_mbps


def test_throughput_is_positive_and_plausible_for_typical_leo_link() -> None:
    use_case = ComputeLinkBudgetUseCase(RADIO_CONFIG)

    result = use_case.execute(_visibility(600.0))

    assert result.estimated_throughput_mbps > 0
    assert result.estimated_throughput_mbps < 10_000
