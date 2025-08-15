import utility

def request_token(npm_api_url: str, username: str, password: str) -> str:
    ''' request the NPM API to get the token '''
    import requests
    from datetime import datetime
    import time

    global npm_token, npm_token_expires

    url = f"{npm_api_url}/tokens"

    if not npm_token or npm_token_expires <= time.time():
        ## utility.print_log("Requesting new NPM token...")
        # Request token
        headers={
            "Accept":  "application/json",
            "Content-Type": "application/json"
        }
        data = {
            "identity": username,
            "secret": password
        }

        try:
            resp = requests.post(url, headers=headers, json=data)
            resp.raise_for_status()

            npm_token=resp.json().get("token")
            npm_token_expires_str = resp.json().get("expires")
            # Parse ISO 8601 string to a timestamp (seconds since epoch)
            npm_token_expires = int(datetime.strptime(npm_token_expires_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())

        except requests.RequestException as e:
            utility.print_log(f"Request Token to NPM failed: {e}")
            exit(1)

    else:
        # Refresh token
        ## utility.print_log("Refreshing NPM token...")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {npm_token}"
        }
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            
            npm_token=resp.json().get("token")
            npm_token_expires_str = resp.json().get("expires")
            # Parse ISO 8601 string to a timestamp (seconds since epoch)
            npm_token_expires = int(datetime.strptime(npm_token_expires_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
            
        except requests.RequestException as e:
            utility.print_log(f"Request Token to NPM failed: {e}")
            exit(1)

def request_api(api_url: str) -> dict:
    ''' request the Netbird API to get the peers '''
    import requests
    
    global npm_token

    url = f"{api_url}/nginx/access-lists?expand=clients"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {npm_token}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        utility.print_log(f"Request to NPM failed: {e}")
        return None



def format_resp(resp : dict) -> dict:
    ''' Output format: {group1:{id: "", ip: [ip1,...]}, ...}'''
    output = {}

    for acl in resp:
        name = acl.get("name", "")
        if name.startswith("nb-"):
            output[name] = {"id": acl.get("id", ""), "ip": []}
            clients = acl.get("clients", [])
            for client in clients:
                ip = client.get("address", "")
                if ip:
                    output[name]["ip"].append(ip)
            
        
    return output


def update_conf(actions: dict, envs: dict):
    ''' update the NPM conf based on the actions list'''
    import requests
    
    global npm_token
    
    for name, ips in actions["add_group"]:
        
        url = f"{envs['NPM_API_URL']}/nginx/access-lists"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {npm_token}",
            "Content-Type": "application/json"
        }
        clients = []
        for ip in ips:
            clients.append({"address": ip, "directive": "allow"})
        data = {
            "name": name,
            "satisfy_any": False,
            "pass_auth": False,
            "items": [],
            "clients": clients
            }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            utility.print_log(f"Added group {name} with IPs {ips} to NPM.")
        except requests.RequestException as e:
            utility.print_log(f"Failed to add group {name} with IPs {ips} to NPM: {e}")
            exit(1)
    
    for name, id_, ips in actions["update"]:
        url = f"{envs['NPM_API_URL']}/nginx/access-lists/{id_}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {npm_token}",
            "Content-Type": "application/json"
        }
        clients = []
        for ip in ips:
            clients.append({"address": ip, "directive": "allow"})
        data = {
            "name": name,
            "satisfy_any": False,
            "pass_auth": False,
            "items": [],
            "clients": clients
            }
        
        try:
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            utility.print_log(f"Updated group {name} with IPs {ips} to NPM.")
        except requests.RequestException as e:
            utility.print_log(f"Failed to update group {name} with IPs {ips} to NPM: {e}")
            exit(1)

    for id_ in actions["remove_group"]:
        url = f"{envs['NPM_API_URL']}/nginx/access-lists/{id_}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {npm_token}",
            "Content-Type": "application/json"
        }        
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            utility.print_log(f"Delete group {name} with IPs {ips} to NPM.")
        except requests.RequestException as e:
            utility.print_log(f"Failed to delete group {name} with IPs {ips} to NPM: {e}")
            exit(1)
    


