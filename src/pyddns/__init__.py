from .services.duckdns_service import DuckDNS
from .services.cloudflare_service import CloudflareDNS

__all__ = [
    'CloudflareDNS',
    'DuckDns',
]