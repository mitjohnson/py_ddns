from abc import ABC, abstractmethod
import requests, logging

class DDNS_Client(ABC):
    """
    An abstract base class for Dynamic DNS (DDNS) clients.

    This class defines the interface for DDNS clients, including methods
    for obtaining the current IP address and updating DNS records.

    Methods:
        INHERITED: get_ip() -> str: Retrieves the current public IP address.
        ABSTRACT: update_dns(ip_address: str, record_name: str) -> None: Updates the DNS record with the specified IP address."
        """
    
    def get_ip(self) -> str:

        logging.debug("Attempting to retrieve current public IP address.")
        try:
            response = requests.get('https://api.ipify.org')
            response.raise_for_status()

            logging.info(f"Current IPv4 is {response.text}")
            return response.text
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting IP: {e}")
            raise

    @abstractmethod
    def update_dns(self, ip_address: str, record_name: str) -> None:
        ...
