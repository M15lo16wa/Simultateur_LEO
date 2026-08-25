from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Satellite:
    norad_id: str
    name: str
    tle_line1: str
    tle_line2: str
    epoch: datetime
