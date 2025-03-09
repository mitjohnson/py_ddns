"""
CloudflareDNS Module

This module provides a Dynamic DNS (DDNS) client for managing DNS records
on Cloudflare. It allows users to update DNS records automatically based on
the current IP address, leveraging the Cloudflare API.
"""
import logging
from typing import Callable, Optional, Any, Tuple
from datetime import datetime

from cloudflare import Cloudflare, NOT_GIVEN, APIConnectionError, APIStatusError, RateLimitError
from cloudflare.types.dns import RecordResponse

from pyddns.utils import _get_config, _get_storage
from pyddns.client import DDNSClient

class CloudflareDNS(DDNSClient):
    """
    DDNS Client for Cloudflare.

    This class interacts with the Cloudflare API to manage DNS records
    for domains hosted on Cloudflare.
    """

    def __init__(self, api_token: str | None = None, zone_id: str | None = None) -> None:
        logging.debug("CloudFlare DNS: Initializing Cloudflare_DDNS client.")
        self.service_name = 'Cloudflare'
        self.config = _get_config()
        self.storage = _get_storage()

        self.zone_id: str = zone_id or self.config.get(self.service_name, 'zone_id')
        self.api_token: str = api_token or self.config.get(self.service_name, 'api_token')

        if not self.zone_id or not self.api_token:
            raise ValueError("CloudFlare DNS: API token and Zone ID must be provided.")

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
                logging.error("CloudFlare DNS: %s", error_message)
                raise
            except RateLimitError:
                error_message = "A 429 status code was received; we should back off a bit."
                logging.warning("CloudFlare DNS: %s", error_message)
                raise
            except APIStatusError as e:
                error_message = f"Non-200-range status code: {e.status_code}, Response:{e.response}"
                logging.error("CloudFlare DNS: %s", error_message)
                raise
        return wrapper

    @cf_error_handler
    def _obtain_record(self, record_name: str) -> Optional[Tuple[str, datetime, Optional[str]]]:
        """
        Obtains requested record by name, ex: example.com
        
        returns comment, content (IP), name, proxied, settings, tags, type, id
        """

        if record_name is None:
            logging.error("CloudFlare DNS: In _obtain_record: Record_name not provided.")
            raise ValueError("CloudFlare DNS: Record name cannot be None")

        logging.debug("CloudFlare DNS: Obtaining %s from the database.", record_name)
        check_storage: Tuple[str, datetime, str] = self.storage.retrieve_record(record_name)

        if check_storage is not None:
            logging.debug("CloudFlare DNS: Retrieved %s from database.", check_storage)
            return check_storage

        result = self.cf_client.dns.records.list(zone_id=self.zone_id).result
        logging.debug("CloudFlare DNS: Retrieved from cloudflare: %s", result)
        records: dict[str, RecordResponse] = {
            record.name or 'domain': record for record in result
            }

        domain_record = records.get(record_name)

        if domain_record is None:
            logging.debug("CloudFlare DNS: Domain Record is None")
            return domain_record

        self.storage.add_service(
            self.service_name, domain_record.name, domain_record.content, domain_record.id
        )
        logging.info("CloudFlare DNS:  Added Service to database")
        return self.storage.retrieve_record(record_name)

    @cf_error_handler
    def update_dns(self, ip_address: str, record_name: Optional[str] = None) -> None:

        """ 
        Updates IP address for specified record 

        Automatically infers record_name if it is defined in the ddns.ini file.
        """
        record_name = record_name or self.config.get(self.service_name,'record_name')

        if not record_name:
            raise ValueError("CloudFlare DNS: Record name cannot be None")

        logging.debug("CloudFlare DNS: Preparing to uppdate %s with IP:", record_name)

        record: Optional[Tuple[str, datetime, str]] = self._obtain_record(record_name)

        if not record:
            logging.error("CloudFlare DNS: No record found for %s.", record_name)
            return

        current_ip: str = record[0]
        record_id: str = record[2]

        if current_ip == ip_address:
            logging.info(
                "CloudFlare DNS: No update needed for %s - IP is already %s.",
                record_name, ip_address
            )
            return

        response = self.cf_client.dns.records.update(
            content = ip_address,
            zone_id = self.zone_id,
            name = record_name or NOT_GIVEN,
            dns_record_id = record_id,
            comment= f"Updated on {datetime.now()} by py_ddns.",
        )

        if response is None:
            logging.error("CloudFlare DNS: No response recienved from cloudflare.")
            return

        self.storage.update_ip(self.service_name, record_name, response.content)
        logging.info("CloudFlare DNS: Updated %s to new IP: %s.", record_name, ip_address)
