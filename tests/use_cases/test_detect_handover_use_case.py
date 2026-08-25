from datetime import datetime, timezone

from domain.entities.visibility import Visibility
from use_cases.detect_handover_use_case import DetectHandoverUseCase


def _visibility(satellite_id: str, distance_km: float, is_visible: bool = True) -> Visibility:
    return Visibility(
        satellite_id=satellite_id,
        station_name="Test Station",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        elevation_deg=45.0,
        azimuth_deg=0.0,
        distance_km=distance_km,
        is_visible=is_visible,
    )


def test_first_call_emits_initial_acquisition() -> None:
    use_case = DetectHandoverUseCase()
    event = use_case.execute([_visibility("A", 600.0)], "Test Station")

    assert event is not None
    assert event.previous_satellite_id is None
    assert event.new_satellite_id == "A"
    assert event.reason == "acquisition_initiale"


def test_no_event_when_nearest_satellite_is_unchanged() -> None:
    use_case = DetectHandoverUseCase()
    use_case.execute([_visibility("A", 600.0)], "Test Station")

    event = use_case.execute([_visibility("A", 610.0), _visibility("B", 900.0)], "Test Station")

    assert event is None


def test_event_when_a_closer_satellite_appears() -> None:
    use_case = DetectHandoverUseCase()
    use_case.execute([_visibility("A", 600.0)], "Test Station")

    event = use_case.execute([_visibility("A", 900.0), _visibility("B", 550.0)], "Test Station")

    assert event is not None
    assert event.previous_satellite_id == "A"
    assert event.new_satellite_id == "B"
    assert event.reason == "satellite_plus_proche_change"


def test_no_visible_satellite_returns_none() -> None:
    use_case = DetectHandoverUseCase()
    event = use_case.execute([_visibility("A", 600.0, is_visible=False)], "Test Station")

    assert event is None
