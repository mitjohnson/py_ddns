from cloudflare import Cloudflare, NOT_GIVEN, APIConnectionError, APIStatusError, RateLimitError
from cloudflare.types.dns import RecordResponse

import logging
from configparser import *
from typing import Callable, Optional, Any, cast

from client import DDNS_Client
from cache import DDNS_Cache
from config import Config

class Cloudflare_DDNS(DDNS_Client):
    """DDNS Client for cloudflare"""

    def __init__(self, api_token: str | None = None, zone_id: str | None = None) -> None:

        self.config = Config()
        self.storage = DDNS_Cache()

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
    def _obtain_record(self, record_name: str) -> Optional[RecordResponse]:
        """
        Obtains requested record by name, ex: example.com
        
        returns comment, content (IP), name, proxied, settings, tags, type, id
        """

        if record_name is None:
            raise ValueError("Record name cannot be None")
        
        check_storage = self.storage.get_latest_query('Cloudflare', record_name)
        if check_storage:
            return cast(RecordResponse, check_storage)
        
        result = self.cf_client.dns.records.list(zone_id=self.zone_id).result
        records: dict[str, RecordResponse] = {
            record.name or 'domain': record for record in result
            }
        
        domain_record = records.get(record_name)
        self.storage.store_query('Cloudflare', record_name, domain_record)
    
        return domain_record

                
    @cf_error_handler
    def update_dns(self, ip_address: str, record_name: str) -> None:

        """ 
        Updates IP address for specified record 

        Automatically infers record_name if it is defined in the ddns.ini file.
        """
        record_name = record_name or self.config.get('cloudflare','record_name')

        if not record_name:
            raise ValueError("Record name cannot be None")
        
        record: RecordResponse = self._obtain_record(record_name)
        if not record:
            logging.error(f"No record found for {record_name}.")
            return
        
        if record.content == ip_address:
            logging.info(f"No update needed for {record_name}. Current IP is already {ip_address}.")
            return

        response = self.cf_client.dns.records.update(
            content = ip_address,
            zone_id = self.zone_id,
            dns_record_id = record.id,
            comment= "python_bot_updated",
            name = record.name or NOT_GIVEN,
            type = record.type or NOT_GIVEN, # type: ignore
            ttl = record.ttl or NOT_GIVEN,
            proxied = record.proxied or NOT_GIVEN,
        )
        
        if response:
            self.storage.store_query('Cloudflare', record_name, response)
            logging.info(f"Updated {record_name} to new IP: {ip_address}.")
