import pytest
from unittest.mock import MagicMock
from pyddns.services.cloudflare_service import CloudflareDNS


def test_cloudflare_dns_initialization():
    with pytest.raises(KeyError):
        CloudflareDNS(api_token=None, zone_id=None)

    client = CloudflareDNS(api_token="test_token", zone_id="test_zone")
    assert client is not None, "Failed to initialize CloudflareDNS!"


def test_cloudflare_dns_update():
    client = CloudflareDNS(api_token="test_token", zone_id="test_zone")
    client.cf_client = MagicMock()

    try:
        client.update_dns("127.0.0.1", "test.example.com")
    except Exception as e:
        pytest.fail(f"update_dns raised an exception: {e}")


def test_cloudflare_dns_obtain_record():
    client = CloudflareDNS(api_token="test_token", zone_id="test_zone")
    client.cf_client = MagicMock()
    client.cf_client.dns.records.list = MagicMock(
        return_value=MagicMock(result=[])
    )

    record = client._obtain_record("test.example.com")
    assert (
        record is None
    ), "_obtain_record should return None if no records are found!"
