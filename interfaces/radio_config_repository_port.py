from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RadioConfig:
    downlink_frequency_hz: float
    bandwidth_hz: float
    satellite_eirp_dbw: float
    user_terminal_gain_dbi: float
    system_noise_temperature_k: float
    other_losses_db: float


class RadioConfigRepositoryPort(ABC):
    @abstractmethod
    def get_config(self, band: str) -> RadioConfig:
        """Retourne les paramètres radio de référence pour une bande donnée."""
