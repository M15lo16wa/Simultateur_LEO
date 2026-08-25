from datetime import datetime, timezone
from functools import lru_cache

from skyfield.api import EarthSatellite, load
from skyfield.timelib import Timescale

from domain.entities.orbital_position import OrbitalPosition
from domain.entities.satellite import Satellite
from interfaces.orbital_propagator_port import OrbitalPropagatorPort


@lru_cache(maxsize=1)
def get_shared_timescale() -> Timescale:
    """Charge l'échelle de temps Skyfield une seule fois (chaque appel est coûteux)."""
    return load.timescale()


class SGP4Propagator(OrbitalPropagatorPort):
    def __init__(self) -> None:
        self._timescale = get_shared_timescale()

    def propagate(self, satellite: Satellite, at: datetime) -> OrbitalPosition:
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)

        earth_satellite = EarthSatellite(
            satellite.tle_line1, satellite.tle_line2, satellite.name, self._timescale
        )
        time = self._timescale.from_datetime(at)

        geocentric = earth_satellite.at(time)
        subpoint = geocentric.subpoint()
        velocity_km_s = geocentric.velocity.km_per_s

        return OrbitalPosition(
            satellite_id=satellite.norad_id,
            timestamp=at,
            latitude_deg=subpoint.latitude.degrees,
            longitude_deg=subpoint.longitude.degrees,
            altitude_km=subpoint.elevation.km,
            velocity_km_s=(velocity_km_s[0], velocity_km_s[1], velocity_km_s[2]),
        )
