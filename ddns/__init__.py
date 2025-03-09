from ddns.config import Config
from ddns.cache import Storage

root_config = Config()

def _get_config() -> Config:
    return root_config

root_storage = Storage()

def _get_storage() -> Storage:
    return root_storage


from ddns.services.cloudflare_service import CloudflareDNS
from ddns.services.duckdns_service import DuckDNS

__all__ = [
    'CloudflareDNS',
    'DuckDns',
]