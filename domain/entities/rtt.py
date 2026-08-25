from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RTTResult:
    satellite_id: str
    station_name: str
    timestamp: datetime

    distance_km: float
    propagation_delay_ms: float
    processing_delay_ms: float
    rtt_ms: float
