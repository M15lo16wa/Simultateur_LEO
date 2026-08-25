from abc import ABC, abstractmethod

from domain.entities.satellite import Satellite


class TLERepositoryPort(ABC):
    @abstractmethod
    def fetch_catalog(self, group: str) -> list[Satellite]:
        """Récupère l'ensemble des satellites (avec leurs TLE) d'un groupe donné."""
