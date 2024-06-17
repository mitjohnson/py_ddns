import requests
import json
from requests.exceptions import HTTPError

# Required
email = ""
api_key = ""      
auth_method: str = ""          # Allowed values: token or global          
zone_id = ""                   # Found in "overview" tab.
dns_ttl: int = 3600            # DNS TTL (seconds)
record_name = ""               # example.com
proxy: bool = True                                 

# Optional
comment = ""                   #Comments or notes about the DNS record. This field has no effect on DNS responses.
tags: list[str] = []           #Custom tags for the DNS record. This field has no effect on DNS responses.

# Retrieve current public IP
curr_ip: str = ""

try:
    # Send GET request to ipify to get already formatted ip.
    response = requests.get('https://api.ipify.org')
    response.raise_for_status()
    curr_ip = response.text

except HTTPError as http_err:
    # The status code is 400-600, try another service.
    curr_ip = "fail"
    print(f"HTTP error: {http_err}, attempting different service..")

except Exception as err:
    # General error, try another service
    curr_ip = "fail"
    print(f"Error: {err}, attemting different service..")

if curr_ip == "fail":
    try:
        # Send GET to cloudflare and process ip.
        response = requests.get('https://cloudflare.com/cdn-cgi/trace')
        response.raise_for_status()
        response_list: list[str] = response.text.split("\n")
        curr_ip = response_list[2].lstrip("ip=")

    except HTTPError as http_err:
        # The status code is 400-600, report failure and end.
        print(f"HTTP error: {http_err}, unable to resolve Public IP.")
        exit()
    except Exception as err:
        # General error, log and exit
        print(f"Error: {err}, unable to resolve Public IP.")
        quit()

# Set proper headers for auth method.
if "global" in auth_method.lower():
    auth_header = "X-Auth-Key"
else:
    auth_header = "Authorization"
    api_key = "Bearer " + api_key

# Query cloudflare
try:
    response = requests.get(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={record_name}",
        headers={"X-Auth-Email": email, auth_header:api_key, "Content-Type":"application/json"})
    response.raise_for_status()

except HTTPError as http_err:
    print(f"HTTP Error: {http_err}.  Unable to query cloudflare, check.")

# Parse out IP recorded in cloudflare.
old_ip: str = json.loads(response.text)["result"][0]["content"]
record_id: str = json.loads(response.text)["result"][0]["id"]

# Check if IP needs to be changed
if old_ip == curr_ip:
   print(f"IP: {curr_ip} for {record_name} is up to date and has not been changed.")
   exit()

try:
    update = requests.patch(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}",
        headers={"X-Auth-Email": email, auth_header:api_key, "Content-Type":"application/json"},
        json={"content":curr_ip,"name":record_name,"type":"A","proxied":proxy,"comment":comment, "tags":tags,"ttl":dns_ttl,})
    
    reply = json.loads(update.text)
    success: bool = reply["success"]

    update.raise_for_status()
except HTTPError as http_err:
    print(f"HTTP Error: {http_err}.")
    print(f"Cloudflare message: errors:{reply['errors']}")
    exit()

print(f"IP for {record_name} has been changed from {old_ip} to {curr_ip}.")