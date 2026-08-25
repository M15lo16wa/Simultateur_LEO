from datetime import datetime

from domain.entities.orbital_position import OrbitalPosition
from domain.entities.satellite import Satellite
from interfaces.orbital_propagator_port import OrbitalPropagatorPort


class PropagatePositionsUseCase:
    def __init__(self, propagator: OrbitalPropagatorPort) -> None:
        self._propagator = propagator

    def execute(self, satellites: list[Satellite], at: datetime) -> list[OrbitalPosition]:
        return [self._propagator.propagate(satellite, at) for satellite in satellites]
