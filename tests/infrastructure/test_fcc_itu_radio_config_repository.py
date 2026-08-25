from infrastructure.radio.fcc_itu_radio_config_repository import FCCITURadioConfigRepository


def test_loads_ku_band_config_from_reference_file() -> None:
    repository = FCCITURadioConfigRepository(reference_dir="data/radio_reference")

    config = repository.get_config("ku_band")

    assert config.downlink_frequency_hz == 12_000_000_000.0
    assert config.bandwidth_hz > 0
