import json
from pathlib import Path

from interfaces.radio_config_repository_port import RadioConfig, RadioConfigRepositoryPort


class FCCITURadioConfigRepository(RadioConfigRepositoryPort):
    """Lit les paramètres radio depuis data/radio_reference/radio_config.json.

    Les valeurs par défaut fournies sont des estimations publiques approximatives
    (littérature Starlink bande Ku), pas des extraits officiels de dossiers FCC/ITU.
    À remplacer par des données de référence réelles quand elles seront disponibles.
    """

    def __init__(self, reference_dir: str) -> None:
        self._file_path = Path(reference_dir) / "radio_config.json"

    def get_config(self, band: str) -> RadioConfig:
        data = json.loads(self._file_path.read_text())
        return RadioConfig(**data[band])
