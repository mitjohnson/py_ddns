__doc__ = """
pyddns - a simple programmable ddns client for Python
=====================================================================

**pyddns** is a Python package providing easy, programmable ddns clients
for multiple services.
"""

from .services.duckdns_service import DuckDNS
from .services.cloudflare_service import CloudflareDNS

__all__ = [
    "CloudflareDNS",
    "DuckDNS",
]
