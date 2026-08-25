from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.orbital_position import OrbitalPosition
from domain.entities.satellite import Satellite


class OrbitalPropagatorPort(ABC):
    @abstractmethod
    def propagate(self, satellite: Satellite, at: datetime) -> OrbitalPosition:
        """Calcule la position réelle d'un satellite à un instant donné."""
