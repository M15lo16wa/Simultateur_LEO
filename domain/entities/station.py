from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    name: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
