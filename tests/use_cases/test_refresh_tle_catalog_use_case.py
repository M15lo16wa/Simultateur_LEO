from datetime import datetime, timezone

from domain.entities.satellite import Satellite
from infrastructure.tle.in_memory_tle_catalog import InMemoryTLECatalog
from interfaces.tle_repository_port import TLERepositoryPort
from use_cases.refresh_tle_catalog_use_case import RefreshTLECatalogUseCase


class FakeTLERepository(TLERepositoryPort):
    def __init__(self, satellites: list[Satellite]) -> None:
        self._satellites = satellites

    def fetch_catalog(self, group: str) -> list[Satellite]:
        return self._satellites


def _make_satellite(norad_id: str) -> Satellite:
    return Satellite(
        norad_id=norad_id,
        name=f"STARLINK-{norad_id}",
        tle_line1="1 44713U 19074A   24001.00000000  .00000000  00000-0  00000-0 0  9990",
        tle_line2="2 44713  53.0000   0.0000 0001000   0.0000   0.0000 15.00000000    01",
        epoch=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def test_refresh_populates_catalog() -> None:
    satellites = [_make_satellite("44713"), _make_satellite("44714")]
    catalog = InMemoryTLECatalog()
    use_case = RefreshTLECatalogUseCase(FakeTLERepository(satellites), catalog)

    count = use_case.execute(group="starlink")

    assert count == 2
    assert len(catalog) == 2
    assert catalog.get("44713") is satellites[0]


def test_refresh_replaces_previous_content() -> None:
    catalog = InMemoryTLECatalog()
    catalog.replace_all([_make_satellite("00001")])

    use_case = RefreshTLECatalogUseCase(FakeTLERepository([_make_satellite("44713")]), catalog)
    use_case.execute(group="starlink")

    assert catalog.get("00001") is None
    assert catalog.get("44713") is not None
