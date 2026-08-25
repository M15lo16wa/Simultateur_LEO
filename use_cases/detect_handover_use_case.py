from domain.entities.handover_event import HandoverEvent
from domain.entities.visibility import Visibility


class DetectHandoverUseCase:
    def __init__(self) -> None:
        self._current_satellite_by_station: dict[str, str] = {}

    def execute(self, visibilities: list[Visibility], station_name: str) -> HandoverEvent | None:
        visible = [v for v in visibilities if v.is_visible]
        if not visible:
            return None

        nearest = min(visible, key=lambda v: v.distance_km)
        previous_satellite_id = self._current_satellite_by_station.get(station_name)

        if previous_satellite_id == nearest.satellite_id:
            return None

        self._current_satellite_by_station[station_name] = nearest.satellite_id

        return HandoverEvent(
            station_name=station_name,
            timestamp=nearest.timestamp,
            previous_satellite_id=previous_satellite_id,
            new_satellite_id=nearest.satellite_id,
            reason="acquisition_initiale" if previous_satellite_id is None else "satellite_plus_proche_change",
        )
