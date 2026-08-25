from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LinkBudgetResult:
    satellite_id: str
    station_name: str
    timestamp: datetime

    distance_km: float
    free_space_path_loss_db: float
    received_power_dbm: float
    snr_db: float
    estimated_throughput_mbps: float
