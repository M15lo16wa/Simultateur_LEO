from datetime import datetime, timedelta

from domain.entities.doppler_result import DopplerResult
from domain.entities.satellite import Satellite
from domain.entities.station import Station
from interfaces.orbital_propagator_port import OrbitalPropagatorPort
from use_cases.compute_visibility_use_case import ComputeVisibilityUseCase


class ComputeDopplerUseCase:
    def __init__(
        self,
        propagator: OrbitalPropagatorPort,
        visibility_use_case: ComputeVisibilityUseCase,
        speed_of_light_km_s: float,
        sampling_interval_s: float = 1.0,
    ) -> None:
        self._propagator = propagator
        self._visibility_use_case = visibility_use_case
        self._speed_of_light_km_s = speed_of_light_km_s
        self._sampling_interval_s = sampling_interval_s

    def execute(
        self, satellite: Satellite, station: Station, at: datetime, downlink_frequency_hz: float
    ) -> DopplerResult:
        position_t0 = self._propagator.propagate(satellite, at)
        position_t1 = self._propagator.propagate(
            satellite, at + timedelta(seconds=self._sampling_interval_s)
        )

        distance_t0_km = self._visibility_use_case.execute(position_t0, station).distance_km
        distance_t1_km = self._visibility_use_case.execute(position_t1, station).distance_km

        radial_velocity_km_s = (distance_t1_km - distance_t0_km) / self._sampling_interval_s
        # Rapproche (distance décroissante) -> décalage positif (blueshift).
        frequency_shift_hz = -downlink_frequency_hz * (radial_velocity_km_s / self._speed_of_light_km_s)

        return DopplerResult(
            satellite_id=satellite.norad_id,
            station_name=station.name,
            timestamp=at,
            relative_velocity_km_s=radial_velocity_km_s,
            downlink_frequency_hz=downlink_frequency_hz,
            frequency_shift_hz=frequency_shift_hz,
        )
