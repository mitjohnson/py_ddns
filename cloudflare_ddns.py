import requests
import os
from datetime import datetime, timezone
import logging
import json
from requests.exceptions import HTTPError

# create logging directory
directory = "/cloudflare_ddns_logs" # change this to your perferred location, ensure filename in logging is the same.

if not os.path.exists(directory):
        os.makedirs(directory)

# logging Options
time_now = datetime.now(timezone.utc)
print(str(time_now))
logging.basicConfig(level=logging.DEBUG, filename=f"/cloudflare_ddns_logs/cloudflare_ddns{time_now}.log", filemode="w",
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Required
email = ""
api_key = ""      
auth_method = ""               # Allowed values: token or global          
zone_id = ""                   # Found in "overview" tab.
dns_ttl: int = 3600            # DNS TTL (seconds)
record_name = ""               # example.com
proxy: bool = True             # This option can change cloudflare proxy status                    

# Optional
comment = ""                   # Comments or notes about the DNS record. This field has no effect on DNS responses.
tags: list[str] = []           # Custom tags for the DNS record. This field has no effect on DNS responses.

""" Retrieve current public IP """
curr_ip :str = ""

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

""" Set proper headers for auth method. """
auth_header: str = ""

if "global" in auth_method.lower():
    auth_header= "X-Auth-Key"
else:
    auth_header = "Authorization"
    api_key = "Bearer " + api_key

""" 
Query cloudflare for old IP and Record ID. API Refrence:
https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-list-dns-records """

try:
    response = requests.get(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={record_name}",
        headers={"X-Auth-Email": email, auth_header:api_key, "Content-Type":"application/json"})
    reply: dict[dict[dict]] = json.loads(response.text)
    response.raise_for_status()
    logging.debug(f"Sent {response} to cloudflare.")
    logging.debug(f"recieved {reply} from cloudflare.")

    old_ip: str = reply["result"][0]["content"]
    record_id: str = reply["result"][0]["id"]
except HTTPError as http_err:
    # The status code is 400-600, report failure and end.
    logging.exception(f"HTTP Error: {http_err}.  Unable to query cloudflare.")
    logging.exception(f"Cloudflare message: errors:{reply['errors']}")
    exit()
except Exception as err:
    # General error, log and exit
    logging.exception(f"Error: {err}, unable to query cloudflare.")
    exit()

""" 
Update A record. API ref:
https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-patch-dns-record """

# Check if IP needs to be changed
if old_ip == curr_ip:
   logging.info(f"IP: {curr_ip} for {record_name} is up to date and has not been changed.")
   print(f"IP: {curr_ip} for {record_name} is up to date and has not been changed.")
   exit()

try:
    update = requests.patch(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}",
        headers={"X-Auth-Email": email, auth_header:api_key, "Content-Type":"application/json"},
        json={"content":curr_ip,"name":record_name,"type":"A","proxied":proxy,"comment":comment, "tags":tags,"ttl":dns_ttl,}) 
    reply: dict[dict[dict]] = json.loads(update.text)
    update.raise_for_status()
    logging.debug(f"Sent {response} to cloudflare.")
    logging.debug(f"recieved {reply} from cloudflare.")
except HTTPError as http_err:
    logging.exception(f"HTTP Error: {http_err}. Unable to update IP for {record_name}")
    logging.debug(f"Cloudflare message: errors:{reply['errors']}")
    exit()
except Exception as err:
    # General error, log and exit
    logging.exception(f"Error: {err}, Unable to update IP for {record_name}")
    exit()

logging.info(f"IP for {record_name} has been changed from {old_ip} to {curr_ip}.")
print(f"IP for {record_name} has been changed from {old_ip} to {curr_ip}.")