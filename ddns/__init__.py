from .config import Config

root_config = Config()

def _get_config() -> Config:

    return root_config


from .cloudflare_service import Cloudflare_DDNS
from .duckdns_service import DuckDNS

__all__ = [
    'Cloudflare_DDNS',
    'DuckDns',
]