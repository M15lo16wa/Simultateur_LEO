import math

from domain.entities.orbital_position import OrbitalPosition
from domain.entities.station import Station
from domain.entities.visibility import Visibility

# Ellipsoïde WGS84 (km)
_WGS84_A_KM = 6378.137
_WGS84_F = 1 / 298.257223563
_WGS84_E2 = _WGS84_F * (2 - _WGS84_F)


def _geodetic_to_ecef_km(lat_deg: float, lon_deg: float, alt_km: float) -> tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)

    n = _WGS84_A_KM / math.sqrt(1 - _WGS84_E2 * sin_lat**2)

    x = (n + alt_km) * cos_lat * math.cos(lon)
    y = (n + alt_km) * cos_lat * math.sin(lon)
    z = (n * (1 - _WGS84_E2) + alt_km) * sin_lat
    return x, y, z


def _ecef_delta_to_enu(dx: float, dy: float, dz: float, lat_deg: float, lon_deg: float) -> tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    sin_lon, cos_lon = math.sin(lon), math.cos(lon)

    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return east, north, up


class ComputeVisibilityUseCase:
    def __init__(self, min_elevation_deg: float) -> None:
        self._min_elevation_deg = min_elevation_deg

    def execute(self, position: OrbitalPosition, station: Station) -> Visibility:
        station_xyz = _geodetic_to_ecef_km(
            station.latitude_deg, station.longitude_deg, station.altitude_m / 1000.0
        )
        satellite_xyz = _geodetic_to_ecef_km(
            position.latitude_deg, position.longitude_deg, position.altitude_km
        )

        dx = satellite_xyz[0] - station_xyz[0]
        dy = satellite_xyz[1] - station_xyz[1]
        dz = satellite_xyz[2] - station_xyz[2]

        east, north, up = _ecef_delta_to_enu(dx, dy, dz, station.latitude_deg, station.longitude_deg)

        distance_km = math.sqrt(east**2 + north**2 + up**2)
        elevation_deg = math.degrees(math.atan2(up, math.sqrt(east**2 + north**2)))
        azimuth_deg = math.degrees(math.atan2(east, north)) % 360.0

        return Visibility(
            satellite_id=position.satellite_id,
            station_name=station.name,
            timestamp=position.timestamp,
            elevation_deg=elevation_deg,
            azimuth_deg=azimuth_deg,
            distance_km=distance_km,
            is_visible=elevation_deg >= self._min_elevation_deg,
        )

    def execute_many(self, positions: list[OrbitalPosition], station: Station) -> list[Visibility]:
        return [self.execute(position, station) for position in positions]
