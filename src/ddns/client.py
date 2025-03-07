from abc import ABC, abstractmethod
import requests, logging

class DDNS_Client(ABC):
    def _get_ip(self) -> str:
        try:
            response = requests.get('https://api.ipify.org')
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting IP: {e}")
            raise

    @abstractmethod
    def update_dns(self, ip_address: str, record_name: str) -> None:
        ...
