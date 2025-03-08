import requests, logging, socket, re
from typing import Optional, Tuple
from datetime import datetime

from ddns import _get_config
from .client import DDNS_Client
from .cache import Storage

class DuckDNS(DDNS_Client):

    def __init__(self, token: Optional[str] = None):
        self.url = "https://www.duckdns.org/update"
        self.serviceName = "Duckdns"

        self.config = _get_config()
        self.storage = Storage()
        self.token = token or self.config.get(self.serviceName, 'token')


    def _obtain_record(self, record_name: str) -> Optional[Tuple[str, datetime, Optional[str]]]:
         
        if record_name is None:
            logging.error(f"DuckDNS: In _obtain_record: Record_name not provided.")
            raise ValueError("Record name cannot be None")
        
        check_storage: Optional[Tuple[str, datetime, Optional[str]]] = self.storage.retrieve_record(self._parse_domain_name(record_name))
        
        if check_storage is not None:
            logging.debug(f"Cloudflare_ddns: Retrieved {check_storage} from database")
            return check_storage
        
        current_ip = self.check_duckdns_ip(record_name)
        self.storage.add_service(self.serviceName, self._parse_domain_name(record_name), current_ip)

        return self.storage.retrieve_record(self._parse_domain_name(record_name))
        
    def _parse_domain_name(self, record_name: str) -> str:
        
        if record_name.endswith('.duckdns.org'):
            return record_name[:-len('.duckdns.org')]
        else:
            return record_name
        
    def _parse_api_response(self, response: str) -> Tuple[str, Optional[str], Optional[str], str]:

        
        responses = response.splitlines()
        
        status = responses[0]  # OK or ERROR
        ipv4 = responses[1] or None   # IPv4 address
        ipv6 = responses[2] or None  # IPv6 address
        update_status = responses[3]  # UPDATED or NOCHANGE
        
        return status, ipv4, ipv6, update_status

        
    def check_duckdns_ip(self, record_name: str) -> str:
        return socket.gethostbyname(f"{self._parse_domain_name(record_name)}.duckdns.org")

        

    def update_dns(self, ip_address: str, record_name: Optional[str] = None) -> None:

        
        record_name = record_name or self._parse_domain_name(self.config.get(self.serviceName, 'domains'))

        if not record_name:
            raise ValueError("Duckddns: Record name cannot be None")

        record = self._obtain_record(self._parse_domain_name(record_name))

        if not record:
            logging.error(f"Duckddns: No record found for {record_name}.")
            return

        current_ip = record[0]

        if current_ip == ip_address:
            logging.info(f"Duckddns: No update needed for {record_name}.duckdns.org. Current IP is already {ip_address}.")
            return

        payload = {
            "domains": f"{self._parse_domain_name(record_name)}.duckdns.org",
            "token": self.token,
            "ip": ip_address,
            "verbose": 'true'
        }
        try:

            response = requests.get(self.url, params = payload)
            response.raise_for_status()

            status, ipv4, ipv6, update_status = self._parse_api_response(response.text)

            self.storage.update_ip(self.serviceName, self._parse_domain_name(record_name), ipv4)
            print(f"Duckdns: Updated {ip_address} to {ipv4}.")
            logging.info(f"Duckdns: Updated {ip_address} to {ipv4}.")
        
        except requests.HTTPError as err:
            logging.error(f"DuckDNS: API Call {err}")
            raise 
        except requests.ConnectionError as err:
            logging.error(f"DuckDNS: API Call {err}")
            raise
        except Exception as err:
            logging.error(f"DuckDNS: API Call {err}")
            raise
         

        

    