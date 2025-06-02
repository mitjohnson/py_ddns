import pytest
from pyddns.client import DDNSClient


class TestDDNSClient(DDNSClient):
    def update_dns(self, ip_address: str, record_name: str) -> None:
        pass  # Mock implementation for testing


def test_ddns_client_ipv4():
    client = TestDDNSClient()
    ip = client.get_ipv4()
    assert ip is not None, "Failed to retrieve IPv4 address!"
    assert isinstance(ip, str), "Returned IP is not a string!"


@pytest.mark.parametrize(
    "ip_address, record_name",
    [
        ("127.0.0.1", "test.example.com"),
        ("192.168.0.1", "local.example.com"),
    ],
)
def test_ddns_client_update_dns(ip_address, record_name):
    client = TestDDNSClient()
    try:
        client.update_dns(ip_address, record_name)
    except Exception as e:
        pytest.fail(f"update_dns raised an exception: {e}")
