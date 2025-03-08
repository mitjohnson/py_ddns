from cloudflare import Cloudflare, NOT_GIVEN, APIConnectionError, APIStatusError, RateLimitError
from cloudflare.types.dns import RecordResponse

import logging
from typing import Callable, Optional, Any, cast, Dict, Tuple
from datetime import datetime

from ddns import _get_config
from .cache import Storage
from .client import DDNS_Client

class Cloudflare_DDNS(DDNS_Client):
    """DDNS Client for cloudflare"""

    def __init__(self, api_token: str | None = None, zone_id: str | None = None) -> None:

        self.serviceName = 'Cloudflare'
        self.config = _get_config()
        self.storage = Storage()

        self.zone_id: str = zone_id or self.config.get('Cloudflare', 'zone_id')
        self.api_token: str = api_token or self.config.get('Cloudflare', 'api_token')

        if not self.zone_id or not self.api_token:
            raise ValueError("API token and Zone ID must be provided.")
        
        self.cf_client = Cloudflare( api_token = self.api_token )

    @staticmethod
    def cf_error_handler(func: Callable) -> Callable:
        """
        Wrapper used inside the Cloudflare_DDNS class to handle errors from the Cloudflare API

        When API request fails this decoration will process, log, and return APIConnetion Error,
        RateLimitError, and APIStatusError's.
        
        """
        def wrapper(*args, **kwargs) -> Any:
            try:

                return func(*args, **kwargs)
            
            except APIConnectionError as e:
                error_message = f"The server could not be reached: {e.__cause__}"
                logging.error(error_message)
                raise
            except RateLimitError as e:
                error_message = "A 429 status code was received; we should back off a bit."
                logging.warning(error_message)
                raise
            except APIStatusError as e:
                error_message = f"Another non-200-range status code was received, Status Code: {e.status_code}, Response: {e.response}"
                logging.error(error_message)
                raise

        return wrapper
                   
    @cf_error_handler
    def _obtain_record(self, record_name: str) -> Optional[Tuple[str, str, datetime]]:
        """
        Obtains requested record by name, ex: example.com
        
        returns comment, content (IP), name, proxied, settings, tags, type, id
        """

        if record_name is None:
            logging.error(f"Cloudflare_ddns: In _obtain_record: Record_name not provided.")
            raise ValueError("Record name cannot be None")
        
        check_storage: Optional[Tuple[str, str, datetime]] = self.storage.retrieve_record(record_name)
        
        if check_storage is not None:
            return check_storage 
            
        result = self.cf_client.dns.records.list(zone_id=self.zone_id).result
        logging.debug(f"Cloudflare_ddns: Retrieved from cloudflare: {result}")
        records: dict[str, RecordResponse] = {
            record.name or 'domain': record for record in result
            }
        
        domain_record = records.get(record_name)

        if domain_record is None:
            logging.debug("Cloudflare_ddns: Domain Record is None")
            return domain_record

        self.storage.add_service(self.serviceName, domain_record.name, domain_record.content, domain_record.id)
        logging.info("Cloudflare_ddns: Added Service to database")
        return self.storage.retrieve_record(record_name)

                
    @cf_error_handler
    def update_dns(self, ip_address: str, record_name: Optional[str] = None) -> None:

        """ 
        Updates IP address for specified record 

        Automatically infers record_name if it is defined in the ddns.ini file.
        """
        record_name = record_name or self.config.get(self.serviceName,'record_name')

        if not record_name:
            raise ValueError("Cloudflare_ddns: Record name cannot be None")
        
        record: Optional[Tuple[str, datetime, str]] = self._obtain_record(record_name)

        if not record:
            logging.error(f"Cloudflare_ddns: No record found for {record_name}.")
            return
        
        current_ip: str = record[0]
        ip_timestamp: datetime = record[1]
        record_id: str = record[2]
        
        if current_ip == ip_address:
            logging.info(f"Cloudflare_ddns: No update needed for {record_name}. Current IP is already {ip_address}.")
            return

        response = self.cf_client.dns.records.update(
            content = ip_address,
            zone_id = self.zone_id,
            name = record_name or NOT_GIVEN,
            dns_record_id = record_id,
            comment= f"Updated on {datetime.now()} by py_ddns.",
        )
        
        if response is None:
            logging.error("Cloudflare_ddns: No response recienved from cloudflare.")
            return
           
        self.storage.update_ip(self.serviceName, record_name, response.content)
        logging.info(f"Cloudflare_ddns: Updated {record_name} to new IP: {ip_address}.")
