import requests, logging, socket, re
from typing import Optional, Tuple
from datetime import datetime

from ddns import _get_config, _get_storage
from ddns.client import DDNS_Client

class DuckDNS(DDNS_Client):
    """
    DDNS Client for DuckDNS.

    This class interacts with the DuckDNS API to manage DNS records
    for domains hosted on DuckDNS."
    """

    def __init__(self, token: Optional[str] = None):
        logging.debug("DuckDNS: Initializing DuckDNS client.")
        self.url = "https://www.duckdns.org/update"
        self.serviceName = "Duckdns"

        self.config = _get_config()
        self.storage = _get_storage()
        self.token = token or self.config.get(self.serviceName, 'token')


    def _obtain_record(self, record_name: str) -> Optional[Tuple[str, datetime, Optional[str]]]:
        """
        Obtains database record for the domain name. 
        If no domain is found, this method obtains the current IP for the DuckDNS record and stores it in the Database

        Returns the database record.
        """

        record_name = self._parse_domain_name(record_name)
        
        if record_name is None:
            logging.error(f"DuckDNS: In _obtain_record: Record_name not provided.")
            raise ValueError("DuckDNS: Record name cannot be None")
        
        logging.debug(f"DuckDNS: Obtaining {record_name} from the database.")
        check_storage: Optional[Tuple[str, datetime, Optional[str]]] = self.storage.retrieve_record(record_name)
        
        if check_storage is not None:
            logging.debug(f"DuckDNS: Retrieved {check_storage} from database")
            return check_storage
        
        logging.debug(f"DuckDNS: {record_name} not found in database, proceeding to find IP and add service to DB.")
        current_ip = self.check_duckdns_ip(record_name)
        self.storage.add_service(self.serviceName, record_name, current_ip)

        return self.storage.retrieve_record(record_name)
        
    def _parse_domain_name(self, record_name: str) -> str:
        """
        Helper method that normalizes the domain name for the DuckDNS domain.

        EX: domain.duckdns.org -> domain
            domain -> domain
        """
        
        if record_name.endswith('.duckdns.org'):
            return record_name[:-len('.duckdns.org')]
        else:
            return record_name
        
    def _parse_api_response(self, response: str) -> Tuple[str, Optional[str], Optional[str], str]:
        """
        Helper Method that parses the verbose response from the DuckDNS API.
        """
        responses = response.splitlines()
        
        status = responses[0]  # OK or ERROR
        ipv4 = responses[1] or None   # IPv4 address
        ipv6 = responses[2] or None  # IPv6 address
        update_status = responses[3]  # UPDATED or NOCHANGE
        
        logging.debug(f"DuckDNS: Received {status, ipv4, ipv6, update_status} from DuckDNS API")
        return status, ipv4, ipv6, update_status

        
    def check_duckdns_ip(self, record_name: str) -> str:
        """
        Checks the current IP address for DuckDNS
        """
        logging.debug(f"DuckDNS: Performing DNS lookup for {record_name}")
        return socket.gethostbyname(f"{self._parse_domain_name(record_name)}.duckdns.org")

        

    def update_dns(self, ip_address: str, record_name: Optional[str] = None) -> None:
        """
        Updates the IP address for DuckDNS, and then updates the IP adress in the database.
        """
        
        record_name = record_name or self._parse_domain_name(self.config.get(self.serviceName, 'domains'))

        if not record_name:
            raise ValueError("DuckDNS: Record name cannot be None")
        
        logging.debug(f"DuckDNS: Preparing to update DuckDNS for {record_name} with IP: {ip_address}")
        record = self._obtain_record(self._parse_domain_name(record_name))

        if not record:
            logging.error(f"DuckDNS: No record found for {record_name}.")
            return

        current_ip = record[0]

        if current_ip == ip_address:
            logging.info(f"DuckDNS: No update needed for {record_name}.duckdns.org - Current IP is already {ip_address}.")
            return

        payload = {
            "domains": f"{self._parse_domain_name(record_name)}.duckdns.org",
            "token": self.token,
            "ip": ip_address,
            "verbose": 'true'
        }
        try:

            logging.debug(f"DuckDNS: Making API call to {self.url} with parameters {payload}")
            response = requests.get(self.url, params = payload)
            response.raise_for_status()

            status, ipv4, ipv6, update_status = self._parse_api_response(response.text)
            logging.debug(f"DuckDNS: Recieved {response.text} from DuckDNS API.")

            self.storage.update_ip(self.serviceName, self._parse_domain_name(record_name), ipv4)
            logging.info(f"DuckDNS:  Updated {ip_address} to {ipv4}.")
        
        except requests.HTTPError as err:
            logging.error(f"DuckDNS: API Call {err}")
            raise 
        except requests.ConnectionError as err:
            logging.error(f"DuckDNS: API Call {err}")
            raise
        except Exception as err:
            logging.error(f"DuckDNS: API Call {err}")
            raise
         

        

    