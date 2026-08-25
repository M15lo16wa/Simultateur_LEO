from domain.entities.rtt import RTTResult
from domain.entities.visibility import Visibility


class ComputeRTTUseCase:
    def __init__(self, speed_of_light_km_s: float, processing_delay_ms: float) -> None:
        self._speed_of_light_km_s = speed_of_light_km_s
        self._processing_delay_ms = processing_delay_ms

    def execute(self, visibility: Visibility) -> RTTResult:
        propagation_delay_ms = 2 * visibility.distance_km / self._speed_of_light_km_s * 1000

        return RTTResult(
            satellite_id=visibility.satellite_id,
            station_name=visibility.station_name,
            timestamp=visibility.timestamp,
            distance_km=visibility.distance_km,
            propagation_delay_ms=propagation_delay_ms,
            processing_delay_ms=self._processing_delay_ms,
            rtt_ms=propagation_delay_ms + self._processing_delay_ms,
        )
