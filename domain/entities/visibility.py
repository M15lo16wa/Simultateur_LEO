from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Visibility:
    satellite_id: str
    station_name: str
    timestamp: datetime

    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    is_visible: bool
