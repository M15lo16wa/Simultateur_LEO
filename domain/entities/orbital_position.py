from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OrbitalPosition:
    satellite_id: str
    timestamp: datetime

    latitude_deg: float
    longitude_deg: float
    altitude_km: float

    velocity_km_s: tuple[float, float, float]
