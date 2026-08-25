from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HandoverEvent:
    station_name: str
    timestamp: datetime

    previous_satellite_id: str | None
    new_satellite_id: str
    reason: str
