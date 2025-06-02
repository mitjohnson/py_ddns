import pytest
from pyddns.config import Config


def test_config_singleton():
    config1 = Config(config_file="py_ddns.ini")
    config2 = Config(config_file="py_ddns.ini")
    assert config1 is config2, "Config is not a singleton!"


def test_config_get():
    config = Config(config_file="py_ddns.ini")
    value = config.get("Client_settings", "logging_level")
    assert value == "info", "Config did not return the correct value!"


def test_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        Config(config_file="non_existent.ini")
