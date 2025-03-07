import json, logging
from typing import Any
from datetime import datetime

class DDNS_Cache:
    """ 
    JSON cache of the latest query for a service.

    Will save data in a standardized format:

    service_name: {
        'query': query,
        'timestamp': timestamp
    }

    If no filename is provided upon initilization the class will default to 'ddns.json'

    """

    def __init__(self, filename: str='ddns.json'):

        self.filename = filename
        self.data: dict = self.load_data()

    def load_data(self) -> dict:
        """ Loads data from JSON file if present, otherwise returns emply dict """
        try:
            with open(self.filename, 'r') as file:
                return json.load(file)
        
        except FileNotFoundError:

            logging.warning("No json file detected.")
            return {}

    def save_data(self) -> None:

        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=2)

    def store_query(self, service_name: str, domain_name: str, query: Any) -> None:
        """ 
        Stores data in a JSON file in the following format: 

        [service_name] = {
            'domain_name': {
                'query': query,
                'timestamp': timestamp
            } 
        }
        
        """
        timestamp = datetime.now().isoformat()

        if service_name not in self.data:
            self.data[service_name] = {}
        self.data[service_name][domain_name] = {
            'query': query,
            'timestamp': timestamp
        }

        self.save_data()


    def get_latest_query(self, service_name: str, domain_name: str) -> dict | None:
        """ Returns the last query made by the specified service. """
        
        if service_name in self.data and domain_name in self.data[service_name]:
            return self.data[service_name][domain_name]
        else:
            return None