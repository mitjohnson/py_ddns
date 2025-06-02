import pytest
from unittest.mock import MagicMock
from pyddns.services.duckdns_service import DuckDNS


def test_duckdns_initialization():
    with pytest.raises(KeyError):
        DuckDNS(token=None)

    client = DuckDNS(token="test_token")
    assert client is not None, "Failed to initialize DuckDNS!"


def test_duckdns_update():
    client = DuckDNS(token="test_token")
    client.storage = MagicMock()
    client.storage.update_ip = MagicMock()

    client._parse_api_response = MagicMock(
        return_value=("OK", "127.0.0.1", None, "UPDATED")
    )

    try:
        client.update_dns("127.0.0.1", "test.example.com")
    except Exception as e:
        pytest.fail(f"update_dns raised an exception: {e}")

    client.storage.update_ip.assert_called_once()


def test_duckdns_obtain_record():
    client = DuckDNS(token="test_token")
    client.storage = MagicMock()
    client.storage.retrieve_record = MagicMock(return_value="test")

    record = client._obtain_record("test.example.com")
    assert record == "test", "_obtain_record should return the correct record!"
