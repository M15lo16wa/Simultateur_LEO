from infrastructure.tle.in_memory_tle_catalog import InMemoryTLECatalog
from interfaces.tle_repository_port import TLERepositoryPort


class RefreshTLECatalogUseCase:
    def __init__(self, tle_repository: TLERepositoryPort, catalog: InMemoryTLECatalog) -> None:
        self._tle_repository = tle_repository
        self._catalog = catalog

    def execute(self, group: str) -> int:
        satellites = self._tle_repository.fetch_catalog(group)
        self._catalog.replace_all(satellites)
        return len(satellites)
