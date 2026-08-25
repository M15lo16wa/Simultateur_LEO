import httpx
from skyfield.api import EarthSatellite

from domain.entities.satellite import Satellite
from infrastructure.propagation.sgp4_propagator import get_shared_timescale
from interfaces.tle_repository_port import TLERepositoryPort

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php"


class TLEDataNotYetAvailable(Exception):
    """CelesTrak n'a pas encore de nouvelles données (rafraîchies environ toutes les 2h par groupe)."""


class CelestrakTLERepository(TLERepositoryPort):
    def __init__(self, timeout_s: float = 15.0) -> None:
        self._timeout_s = timeout_s
        self._timescale = get_shared_timescale()

    def fetch_catalog(self, group: str) -> list[Satellite]:
        response = httpx.get(
            CELESTRAK_URL,
            params={"GROUP": group, "FORMAT": "tle"},
            timeout=self._timeout_s,
        )
        if response.status_code == 403 and "has not updated" in response.text:
            raise TLEDataNotYetAvailable(response.text.strip())
        response.raise_for_status()
        return self._parse_tle_text(response.text)

    def fetch_by_name(self, name: str) -> list[Satellite]:
        """Requête alternative (NAME=) : utile quand fetch_catalog est bloqué par la limite ~2h de CelesTrak,
        car soumise à un compteur de fraîcheur différent de GROUP=."""
        response = httpx.get(
            CELESTRAK_URL,
            params={"NAME": name, "FORMAT": "tle"},
            timeout=self._timeout_s,
        )
        if response.status_code == 403 and "has not updated" in response.text:
            raise TLEDataNotYetAvailable(response.text.strip())
        response.raise_for_status()
        return self._parse_tle_text(response.text)

    def fetch_single(self, norad_id: str) -> Satellite:
        response = httpx.get(
            CELESTRAK_URL,
            params={"CATNR": norad_id, "FORMAT": "tle"},
            timeout=self._timeout_s,
        )
        if response.status_code == 403 and "has not updated" in response.text:
            raise TLEDataNotYetAvailable(response.text.strip())
        response.raise_for_status()
        return self._parse_tle_text(response.text)[0]

    def _parse_tle_text(self, text: str) -> list[Satellite]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        satellites: list[Satellite] = []
        for i in range(0, len(lines) - 2, 3):
            name, line1, line2 = lines[i], lines[i + 1], lines[i + 2]
            earth_satellite = EarthSatellite(line1, line2, name, self._timescale)
            satellites.append(
                Satellite(
                    norad_id=str(earth_satellite.model.satnum),
                    name=name,
                    tle_line1=line1,
                    tle_line2=line2,
                    epoch=earth_satellite.epoch.utc_datetime(),
                )
            )
        return satellites
