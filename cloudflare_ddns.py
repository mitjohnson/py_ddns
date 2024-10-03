from requests.exceptions import HTTPError
from datetime import datetime, timezone
import requests
import argparse
import logging
import pickle
import json
import re
import os

class DDNS_Client:

    def __init__(self, record_name: str) -> None:
        """Initialization of Domain name"""
        self.record_name = record_name
        self.email = input("Enter the email associated with the domain: ")
        self.auth_method = ""
        self.api_key = input("Enter your API Key: ")
        self.zone_id = input("Enter the Zone ID of your domain: ") 
        self.dns_ttl: int = 3600            
        self.proxy: bool = True 
        
        validating = True
        while(validating):
            allowed_values = ["token", "global"]
            auth_method_input = input("Is this Token Authentication or Global?: ")

            for v in allowed_values:
                if v in auth_method_input:
                    self.auth_method = auth_method_input
                    validating = False
                else:
                    continue
        
        directory = "/var/log/cloudflare_ddns" # change this to your perferred location, ensure filename in logging is the same.
        if not os.path.exists(directory):
                os.makedirs(directory)

        # logging Options
        time_now = datetime.now(timezone.utc)

        logging.basicConfig(level=logging.DEBUG,
                            filename=f"{directory}/cloudflare_ddns{time_now}.log",
                            filemode="w",
                            format="%(asctime)s - %(levelname)s - %(message)s"
                            )
                       
    def get_ip(self) -> str:
        """ Retrieve current public IP """
        curr_ip = ""

        try:
            # Send GET request to ipify to get already formatted ip.
            response = requests.get('https://api.ipify.org')
            response.raise_for_status()
            curr_ip = response.text
            logging.info(f"sucesfully obtained IP adress: {curr_ip} from ipify")

        except HTTPError as http_err:
            # The status code is 400-600, try another service.
            curr_ip = "fail"
            logging.warning(f"HTTP error: {http_err}, attempting different service..")
        except Exception as err:
            # General error, try another service
            curr_ip = "fail"
            logging.warning(f"Error: {err}, attemting different service..")

        if curr_ip == "fail":
            try:
                # Send GET to cloudflare and process ip.
                response = requests.get('https://cloudflare.com/cdn-cgi/trace')
                response.raise_for_status()
                response_list: list[str] = response.text.split("\n")
                curr_ip = response_list[2].lstrip("ip=")
                logging.info(f"sucesfully obtained IP adress: {curr_ip} from cloudflare")

            except HTTPError as http_err:
                # The status code is 400-600, report failure and end.
                logging.exception(f"HTTP error: {http_err}, unable to resolve Public IP.")
                exit()
            except Exception as err:
                # General error, log and exit
                logging.exception(f"Error: {err}, unable to resolve Public IP.")
                exit()
        
        return curr_ip

    def query_cloudflare(self) -> dict:
        """Query cloudflare for old_ip and record_id."""
        record_name = self.record_name
        email = self.email
        zone_id = self.zone_id
        auth = self.craft_headers()

        try:
            response = requests.get(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={record_name}",
                headers={
                    "X-Auth-Email": email,
                    auth["auth_header"]:auth["api_key"],
                    "Content-Type":"application/json"
                })
            reply = json.loads(response.text)
            response.raise_for_status()
            logging.debug(f"Sent {response} to cloudflare.")
            logging.debug(f"recieved {reply} from cloudflare.")

            old_ip = reply["result"][0]["content"]
            record_id = reply["result"][0]["id"]
        except HTTPError as http_err:
            # The status code is 400-600, report failure and end.
            logging.exception(f"HTTP Error: {http_err}.  Unable to query cloudflare.")
            logging.exception(f"Cloudflare message: errors:{reply['errors']}")
            exit()
        except Exception as err:
            # General error, log and exit
            logging.exception(f"Error: {err}, unable to query cloudflare.")
            exit()

        return {"old_ip":old_ip, "record_id":record_id}

    def craft_headers(self) -> dict:
        """ Set proper headers for auth method. """
        auth_method: str = self.auth_method
        auth_header: str = ""

        if "global" in auth_method.lower():
            auth_header= "X-Auth-Key"
        else:
            auth_header = "Authorization"
            api_key = "Bearer " + self.api_key
        
        return {"auth_header":auth_header, "api_key":api_key}
    
    def is_same_IP(self) -> dict[bool, str, str ,str]:
        """compare the collected and current IP"""

        query: dict = self.query_cloudflare()
        curr_ip: str = self.get_ip()
        old_ip: str = query["old_ip"]
        record_id: str = query["record_id"]

        if query["old_ip"] == curr_ip:
            return [False, record_id, curr_ip, old_ip]
        
        return {"bool":True, "record_id":record_id, "curr_ip":curr_ip, "old_ip":old_ip}

    def update(self) -> None:
        """Update A record."""

        record_name = self.record_name
        email = self.email
        auth: dict = self.craft_headers()
        auth_header = auth["auth_header"]
        api_key = auth["api_key"]
        zone_id = self.zone_id
        dns_ttl = self.dns_ttl
        proxy = self.proxy


        answer = self.is_same_IP()
        record_id = answer["record_id"]

        if answer["bool"] == False:
            try:
                update = requests.patch(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}",
                    headers={"X-Auth-Email": email, auth_header:api_key, "Content-Type":"application/json"},
                    json={"content":answer["curr_ip"],"name":record_name,"type":"A","proxied":proxy,"ttl":dns_ttl,}) 
                reply: dict[dict[dict]] = json.loads(update.text)
                update.raise_for_status()
                logging.debug(f"Sent {update} to cloudflare.")
                logging.debug(f"recieved {reply} from cloudflare.")
            except HTTPError as http_err:
                logging.exception(f"HTTP Error: {http_err}. Unable to update IP for {record_name}")
                logging.debug(f"Cloudflare message: errors:{reply['errors']}")
                exit()
            except Exception as err:
                # General error, log and exit
                logging.exception(f"Error: {err}, Unable to update IP for {record_name}")
                exit()

            logging.info(f"IP for {record_name} has been changed from {answer["old_ip"]} to {answer["curr_ip"]}.")
            print(f"IP for {record_name} has been changed from {answer["old_ip"]} to {answer["curr_ip"]}.")
            exit()

        logging.info(f"IP: {answer["old_ip"]} for {record_name} is up to date and has not been changed.")
        print(f"IP: {answer["old_ip"]} for {record_name} is up to date and has not been changed.")
        exit()

def main(name: str, old_ip = False) -> None:
    
    # Start up desired DDNS Client.
    if os.path.exists(f"{os.path.curdir}/{name}.pickle"):
        with open(f"{name}.pickle", "rb") as file:
            instance: DDNS_Client = pickle.load(file)
    else:
        instance = DDNS_Client(name)

    # Process Arguments
    if old_ip:
        query = instance.query_cloudflare()
        print(query["old_ip"])
    else:  
        instance.update()

    # Save Instance in a pickle file.
    with open(f"{name}.pickle", "wb") as file:
        pickle.dump(instance, file)
    

if __name__ == "__main__" :

    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--name", required=True,
        help="Initialize or utilize a Domain name, update the IP if needed. * example.com")
    
    parser.add_argument("-i", "--getIP",action="store_true", 
        help="Used to quickly get IP Adress recorded in Cloudflare -- this option will not update IP address")
    
    args = parser.parse_args()

    if not args.getIP:
        main(args.name)
    main(args.name, args.getIP)

    