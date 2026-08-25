from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DopplerResult:
    satellite_id: str
    station_name: str
    timestamp: datetime

    relative_velocity_km_s: float
    downlink_frequency_hz: float
    frequency_shift_hz: float
