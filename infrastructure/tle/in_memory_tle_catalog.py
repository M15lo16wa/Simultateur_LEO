from domain.entities.satellite import Satellite


class InMemoryTLECatalog:
    def __init__(self) -> None:
        self._satellites: dict[str, Satellite] = {}

    def replace_all(self, satellites: list[Satellite]) -> None:
        self._satellites = {sat.norad_id: sat for sat in satellites}

    def get(self, norad_id: str) -> Satellite | None:
        return self._satellites.get(norad_id)

    def all(self) -> list[Satellite]:
        return list(self._satellites.values())

    def __len__(self) -> int:
        return len(self._satellites)
