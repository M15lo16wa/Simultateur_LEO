from datetime import datetime, timezone

from domain.entities.orbital_position import OrbitalPosition
from domain.entities.satellite import Satellite
from infrastructure.propagation.sgp4_propagator import SGP4Propagator
from interfaces.orbital_propagator_port import OrbitalPropagatorPort
from use_cases.propagate_positions_use_case import PropagatePositionsUseCase

# TLE réel (ISS ZARYA, capturé le 2026-08-15) : sert de fixture stable, sans appel réseau.
ISS_SATELLITE = Satellite(
    norad_id="25544",
    name="ISS (ZARYA)",
    tle_line1="1 25544U 98067A   26227.08368476  .00005059  00000+0  98393-4 0  9995",
    tle_line2="2 25544  51.6330   8.6029 0007564  47.5489 312.6138 15.49446478580889",
    epoch=datetime(2026, 8, 15, tzinfo=timezone.utc),
)


class FakePropagator(OrbitalPropagatorPort):
    def __init__(self, position: OrbitalPosition) -> None:
        self._position = position

    def propagate(self, satellite: Satellite, at: datetime) -> OrbitalPosition:
        return self._position


def test_propagate_positions_calls_propagator_for_each_satellite() -> None:
    expected_position = OrbitalPosition(
        satellite_id="25544",
        timestamp=datetime(2026, 8, 15, 12, tzinfo=timezone.utc),
        latitude_deg=0.0,
        longitude_deg=0.0,
        altitude_km=420.0,
        velocity_km_s=(7.5, 0.0, 0.0),
    )
    use_case = PropagatePositionsUseCase(FakePropagator(expected_position))

    positions = use_case.execute([ISS_SATELLITE], at=expected_position.timestamp)

    assert positions == [expected_position]


def test_sgp4_propagator_gives_a_plausible_leo_position() -> None:
    use_case = PropagatePositionsUseCase(SGP4Propagator())

    positions = use_case.execute(
        [ISS_SATELLITE], at=datetime(2026, 8, 16, 12, tzinfo=timezone.utc)
    )

    assert len(positions) == 1
    position = positions[0]
    assert position.satellite_id == "25544"
    assert -90.0 <= position.latitude_deg <= 90.0
    assert -180.0 <= position.longitude_deg <= 180.0
    # L'ISS orbite entre ~400 et ~430 km d'altitude.
    assert 350.0 <= position.altitude_km <= 450.0
