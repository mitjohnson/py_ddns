"""
DuckDNS Client Module

This module provides a DDNS client for DuckDNS, allowing users to manage
DNS records for domains hosted on DuckDNS. The `DuckDNS` class interacts
with the DuckDNS API to update DNS records based on the current public IP address.
"""

import logging
import socket
from typing import Optional, Tuple
from datetime import datetime

import requests

from pyddns.utils import _get_config, _get_storage
from pyddns.client import DDNSClient

class DuckDNS(DDNSClient):
    """
    DDNS Client for DuckDNS.

    This class interacts with the DuckDNS API to manage DNS records
    for domains hosted on DuckDNS."
    """

    def __init__(self, token: Optional[str] = None):
        logging.debug("DuckDNS: Initializing DuckDNS client.")
        self.url = "https://www.duckdns.org/update"
        self.service_name = "Duckdns"

        self.config = _get_config()
        self.storage = _get_storage()
        self.token = token or self.config.get(self.service_name, 'token')


    def _obtain_record(self, record_name: str) -> Optional[Tuple[str, datetime, Optional[str]]]:
        """
        Obtains database record for the domain name. 
        If not found, obtains the current IP for the record and stores it in the Database

        Returns the database record.
        """

        record_name = self._parse_domain_name(record_name)

        if record_name is None:
            logging.error("DuckDNS: In _obtain_record: Record_name not provided.")
            raise ValueError("DuckDNS: Record name cannot be None")

        logging.debug("DuckDNS: Obtaining %s from the database.", record_name)
        check_storage: Tuple[str, datetime, Optional[str]]=self.storage.retrieve_record(record_name)

        if check_storage is not None:
            logging.debug("DuckDNS: Retrieved %s from database", check_storage)
            return check_storage

        logging.debug(
            "DuckDNS: %s not found in database, proceeding to find IP and add service to DB.",
            record_name
        )
        current_ip = self.check_duckdns_ip(record_name)
        self.storage.add_service(self.service_name, record_name, current_ip)

        return self.storage.retrieve_record(record_name)

    def _parse_domain_name(self, record_name: str) -> str:
        """
        Helper method that normalizes the domain name for the DuckDNS domain.

        EX: domain.duckdns.org -> domain
            domain -> domain
        """

        if record_name.endswith('.duckdns.org'):
            return record_name[:-len('.duckdns.org')]

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

        logging.debug(
            "DuckDNS: Received %s, %s, %s, %s from DuckDNS API",
            status, ipv4, ipv6, update_status
        )
        return status, ipv4, ipv6, update_status

    def check_duckdns_ip(self, record_name: str) -> str:
        """
        Performs a DNS lookup for record name for DuckDNS
        """
        logging.debug("DuckDNS: Performing DNS lookup for %s", record_name)
        return socket.gethostbyname(f"{self._parse_domain_name(record_name)}.duckdns.org")

    def check_and_update_dns(self, record_name: Optional[str] = None) -> None:
        """
        Compares the actual DuckDNS A record with the local database record. 
        If they are different, updates DuckDNS with the current IP address.
        """
        record_name = record_name or self.config.get(self.service_name, 'domains')
        record_name = self._parse_domain_name(record_name)

        if not record_name:
            raise ValueError("DuckDNS: Record name cannot be None")

        logging.debug("DuckDNS: Checking current IP for %s", record_name)
        duck_ip = self.check_duckdns_ip(record_name)
        logging.debug("DuckDNS: Current IP for %s is %s", record_name, duck_ip)

        record = self._obtain_record(record_name)

        if not record:
            logging.error("DuckDNS: No record found for %s.", record_name)
            return

        current_ip = self.get_ipv4()
        db_ip = record[0]
        logging.debug("DuckDNS: IP from database is %s", db_ip)

        if current_ip != db_ip:
            logging.info("IP has changed from %s to %s, updating DuckDNS.", current_ip, db_ip)
            self.update_dns(current_ip, record_name)
            return

        if db_ip != duck_ip:
            logging.info(
                "DuckDNS: A record has changed from %s to %s for %s, updating DuckDNS",
                db_ip, duck_ip, record_name
            )
            self.update_dns(current_ip, record_name)
            return

        logging.info("DuckDNS: No update needed for %s - IP is still %s", record_name, db_ip)

    def update_dns(self, ip_address: str, record_name: Optional[str] = None) -> None:
        """
        Updates the IP address for DuckDNS in the database.
        This method assumes that the IP address has already been verified to be different.
        """
        record_name = record_name or self.config.get(self.service_name, 'domains')
        record_name = self._parse_domain_name(record_name)

        if not record_name:
            raise ValueError("DuckDNS: Record name cannot be None")

        payload = {
            "domains": f"{record_name}.duckdns.org",
            "token": self.token,
            "ip": ip_address,
            "verbose": 'true'
        }

        try:
            logging.debug("DuckDNS: Making API call to %s with parameters %s", self.url, payload)
            response = requests.get(self.url, params=payload, timeout=10)
            response.raise_for_status()

            ipv4 = self._parse_api_response(response.text)[1]
            logging.debug("DuckDNS: Received %s from DuckDNS API.", response.text)

            self.storage.update_ip(self.service_name, self._parse_domain_name(record_name), ipv4)
            logging.info("DuckDNS: Updated %s to %s.", ip_address, ipv4)

        except requests.HTTPError as err:
            logging.error("DuckDNS: API Call %s", err)
            raise
        except requests.ConnectionError as err:
            logging.error("DuckDNS: API Call %s", err)
            raise
        except Exception as err:
            logging.error("DuckDNS: API Call %s", err)
            raise
