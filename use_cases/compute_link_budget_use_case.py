import math

from domain.entities.link_budget_result import LinkBudgetResult
from domain.entities.visibility import Visibility
from interfaces.radio_config_repository_port import RadioConfig

_BOLTZMANN_CONSTANT_J_PER_K = 1.380649e-23


class ComputeLinkBudgetUseCase:
    def __init__(self, radio_config: RadioConfig) -> None:
        self._radio_config = radio_config

    def execute(self, visibility: Visibility) -> LinkBudgetResult:
        freq_mhz = self._radio_config.downlink_frequency_hz / 1e6

        free_space_path_loss_db = (
            20 * math.log10(visibility.distance_km) + 20 * math.log10(freq_mhz) + 32.44
        )

        received_power_dbm = (
            self._radio_config.satellite_eirp_dbw
            + 30  # dBW -> dBm
            + self._radio_config.user_terminal_gain_dbi
            - free_space_path_loss_db
            - self._radio_config.other_losses_db
        )

        noise_power_dbm = (
            10
            * math.log10(
                _BOLTZMANN_CONSTANT_J_PER_K
                * self._radio_config.system_noise_temperature_k
                * self._radio_config.bandwidth_hz
            )
            + 30
        )
        snr_db = received_power_dbm - noise_power_dbm
        snr_linear = 10 ** (snr_db / 10)

        estimated_throughput_mbps = (
            self._radio_config.bandwidth_hz * math.log2(1 + snr_linear) / 1e6
        )

        return LinkBudgetResult(
            satellite_id=visibility.satellite_id,
            station_name=visibility.station_name,
            timestamp=visibility.timestamp,
            distance_km=visibility.distance_km,
            free_space_path_loss_db=free_space_path_loss_db,
            received_power_dbm=received_power_dbm,
            snr_db=snr_db,
            estimated_throughput_mbps=estimated_throughput_mbps,
        )
