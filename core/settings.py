from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    celestrak_group: str = "starlink"
    tle_refresh_interval_hours: int = 6

    min_elevation_deg: float = 25.0
    speed_of_light_km_s: float = 299_792.458

    default_station_name: str = "Dakar Ground Station"
    default_station_latitude_deg: float = 14.6928
    default_station_longitude_deg: float = -17.4467
    default_station_altitude_m: float = 24.0

    processing_delay_ms: float = 5.0
    radio_band: str = "ku_band"

    radio_reference_dir: str = "data/radio_reference"
    measurements_dir: str = "data/measurements"


settings = Settings()
