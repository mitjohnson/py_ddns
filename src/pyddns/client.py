"""
Dynamic DNS Client Abstract Base Class

This module defines an abstract base class for Dynamic DNS (DDNS) clients.
The `DDNS_Client` class serves as a blueprint for implementing specific DDNS
clients that interact with various DNS service providers. It includes methods
for obtaining the current public IP address and updating DNS records.
"""

from abc import ABC, abstractmethod
import logging

import requests


class DDNSClient(ABC):
    """
    An abstract base class for Dynamic DNS (DDNS) clients.

    This class defines the interface for DDNS clients, including methods
    for obtaining the current IP address and updating DNS records.

    Methods:
        INHERITED: get_ip() -> str: Retrieves the current public IP address.
        ABSTRACT: update_dns(ip_address: str, record_name: str) -> None"
    """

    def get_ipv4(self) -> str:
        """Obtains current IPv4 adress and returns as a str."""

        logging.debug("Attempting to retrieve current public IP address.")
        try:
            response = requests.get("https://api.ipify.org", timeout=10)
            response.raise_for_status()

            logging.info("Current IPv4 is %s", response.text)
            return response.text

        except requests.exceptions.RequestException as e:
            logging.error("Error getting IP: %s", e)
            raise

    @abstractmethod
    def update_dns(self, ip_address: str, record_name: str) -> None:
        """
        Abstract Method to force all clients to have an update_dns method.
        """
