"""
CloudflareDNS Module

This module provides a Dynamic DNS (DDNS) client for managing DNS records
on Cloudflare. It allows users to update DNS records automatically based on
the current IP address, leveraging the Cloudflare API.
"""

import logging
import socket
from typing import Callable, Optional, Any, Tuple
from datetime import datetime

from cloudflare import (
    Cloudflare,
    NOT_GIVEN,
    APIConnectionError,
    APIStatusError,
    RateLimitError,
)
from cloudflare.types.dns import RecordResponse

from pyddns.config import Config
from pyddns.storage import Storage
from pyddns.client import DDNSClient


class CloudflareDNS(DDNSClient):
    """
    DDNS Client for Cloudflare.

    This class interacts with the Cloudflare API to manage DNS records
    for domains hosted on Cloudflare.
    """

    def __init__(
        self, api_token: Optional[str] = None, zone_id: Optional[str] = None
    ) -> None:
        logging.debug("CloudFlare DNS: Initializing Cloudflare_DDNS client.")
        self.service_name = "Cloudflare"
        self.config = Config()
        self.storage = Storage()

        self.zone_id: str = zone_id or self.config.get(
            self.service_name, "zone_id"
        )
        self.api_token: str = api_token or self.config.get(
            self.service_name, "api_token"
        )

        if not self.zone_id or not self.api_token:
            raise ValueError(
                "CloudFlare DNS: API token and Zone ID must be provided."
            )

        self.cf_client = Cloudflare(api_token=self.api_token)

    @staticmethod
    def cf_error_handler(func: Callable) -> Callable:
        """
        Wrapper used inside the Cloudflare_DDNS class to handle errors

        Processes, logs, and returns APIConnetion Error,
        RateLimitError, and APIStatusError's.

        """

        def wrapper(*args, **kwargs) -> Any:
            try:

                return func(*args, **kwargs)

            except APIConnectionError as e:
                error_message = (
                    f"The server could not be reached: {e.__cause__}"
                )
                logging.error("CloudFlare DNS: %s", error_message)
                raise
            except RateLimitError:
                error_message = (
                    "A 429 status code was received; we should back off a bit."
                )
                logging.warning("CloudFlare DNS: %s", error_message)
                raise
            except APIStatusError as e:
                error_message = (
                        f"Non-200-range status code: {e.status_code},"
                        f"Response:{e.response}"
                )
                logging.error("CloudFlare DNS: %s", error_message)
                raise

        return wrapper

    @cf_error_handler
    def _obtain_record(
        self, record_name: str
    ) -> Optional[Tuple[str, datetime, Optional[str]]]:
        """
        Obtains requested record by name, ex: example.com

        Returns comment, content (IP), name, proxies, settings, tags, type, id
        """

        if record_name is None:
            logging.error(
                "CloudFlare DNS: In _obtain_record: Record_name not provided."
            )
            raise ValueError("CloudFlare DNS: Record name cannot be None")

        logging.debug(
            "CloudFlare DNS: Obtaining %s from the database.", record_name
        )
        check_storage: Tuple[str, datetime, str] = (
            self.storage.retrieve_record(record_name)
        )

        if check_storage is not None:
            logging.debug(
                "CloudFlare DNS: Retrieved %s from database.", check_storage
            )
            return check_storage

        result = self.cf_client.dns.records.list(zone_id=self.zone_id).result
        logging.debug("CloudFlare DNS: Retrieved from cloudflare: %s", result)
        records: dict[str, RecordResponse] = {
            record.name or "domain": record for record in result
        }

        domain_record = records.get(record_name)

        if domain_record is None:
            logging.debug("CloudFlare DNS: Domain Record is None")
            return domain_record

        self.storage.add_service(
            self.service_name,
            domain_record.name,
            domain_record.content,
            domain_record.id,
        )
        logging.info("CloudFlare DNS:  Added Service to database")
        return self.storage.retrieve_record(record_name)

    @cf_error_handler
    def check_cloudflare_ip(self, record_name: str) -> Optional[str]:
        """
        Checks the A record IP address in cloudflare utilizing the API

        This is recommended if you have a proxied connection.
        """

        if record_name is None:
            logging.error(
                "CloudFlare DNS: In _obtain_record: Record_name not provided."
            )
            raise ValueError("CloudFlare DNS: Record name cannot be None")

        response = self.storage.retrieve_record(record_name)

        if not response:
            response = self._obtain_record(record_name)

        record_id = response[2]
        api_res = self.cf_client.dns.records.get(
            zone_id=self.zone_id, dns_record_id=record_id
        )

        if not api_res:
            logging.error("Cloudflare DNS: API call failed.")
            return None

        return api_res.content

    def cloudflare_dns_lookup(self, record_name: str) -> str:
        """
        Performs a DNS lookup for the record name for Cloudflare.

        This will not return the correct IP if you have a proxied connection.
        """
        logging.debug(
            "CloudFlare DNS: Performing DNS lookup for %s", record_name
        )
        return socket.gethostbyname(record_name)

    def check_and_update_dns(self, record_name: Optional[str] = None) -> None:
        """
        Compares the actual Cloudflare A record with the local database record.
        If they are different, updates Cloudflare with the current IP address.
        """
        record_name = record_name or self.config.get(
            self.service_name, "record_name"
        )

        if not record_name:
            raise ValueError("CloudFlare DNS: Record name cannot be None")

        logging.debug(
            "CloudFlare DNS: Checking current IP for %s", record_name
        )
        cloudflare_ip = self.check_cloudflare_ip(record_name)
        logging.debug(
            "CloudFlare DNS: Current IP for %s is %s",
            record_name,
            cloudflare_ip,
        )

        record: Optional[Tuple[str, datetime, str]] = self._obtain_record(
            record_name
        )

        if not record:
            logging.error(
                "CloudFlare DNS: No record found for %s.", record_name
            )
            return

        current_ip = self.get_ipv4()
        db_ip = record[0]
        logging.debug("CloudFlare DNS: IP from database is %s", db_ip)

        if current_ip != db_ip:
            logging.info(
                "CloudFlare DNS: Local IP has changed from %s to %s,"
                "updating Cloudflare.",
                db_ip,
                current_ip,
            )
            self.update_dns(current_ip, record_name)
            return

        if db_ip != cloudflare_ip:
            logging.info(
                "CloudFlare DNS: A record has changed from %s to %s for %s,"
                "updating Cloudflare",
                db_ip,
                cloudflare_ip,
                record_name,
            )
            self.update_dns(current_ip, record_name)
            return

        logging.info(
            "CloudFlare DNS: No update needed for %s - IP is still %s",
            record_name,
            db_ip,
        )
        return

    @cf_error_handler
    def update_dns(
        self, ip_address: str, record_name: Optional[str] = None
    ) -> None:
        """
        Updates IP address for specified record
        Automatically infers record_name if it is defined in the ddns.ini file.
        """
        record_name = record_name or self.config.get(
            self.service_name, "record_name"
        )

        if not record_name:
            raise ValueError("CloudFlare DNS: Record name cannot be None")

        logging.info(
            "CloudFlare DNS: Preparing to update %s with IP: %s",
            record_name,
            ip_address,
        )

        record: Optional[Tuple[str, datetime, str]] = self._obtain_record(
            record_name
        )

        if not record:
            logging.error(
                "CloudFlare DNS: No record found for %s.", record_name
            )
            return

        record_id: str = record[2]

        comment = f"Updated on {datetime.now()} by py_ddns."
        response = self.cf_client.dns.records.update(
            content=ip_address,
            zone_id=self.zone_id,
            type="A",
            proxied=True,
            name=record_name or NOT_GIVEN,
            dns_record_id=record_id,
            comment=comment,
        )

        if response is None:
            logging.error(
                "CloudFlare DNS: No response received from Cloudflare."
            )
            return

        self.storage.update_ip(
            self.service_name, record_name, response.content
        )
        logging.info(
            "CloudFlare DNS: Updated %s to new IP: %s.",
            record_name,
            ip_address,
        )
