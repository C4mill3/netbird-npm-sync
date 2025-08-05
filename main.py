import schedule
import time
import json


def load_environ() -> dict:
    from os import environ
    keys=["NETBIRD_TOKEN", "NETBIRD_API_URL", "NPM_API_URL", "NPM_USERNAME",
          "NPM_PASSWORD", "RUN_EVERY_MINUTES", "GROUPS_WHITELIST", "IP_WHITELIST"]
    keys_types=["STR", "STR", "STR", "STR", "STR", "INT", "LIST", "DICT"]
    envs={}
    for i in range(len(keys)):
        envs[keys[i]]=environ.get(keys[i])

        if envs[keys[i]]=='':
            raise(f"Env Variable {keys[i]} is missing")

        if keys_types[i]=="STR":
            envs[keys[i]]=str(envs[keys[i]])

        elif keys_types[i]=="INT":
            envs[keys[i]]=int(envs[keys[i]])

        elif keys_types[i]=="LIST":
            envs[keys[i]]=list(json.loads(envs[keys[i]]))
            
        elif keys_types[i]=="DICT":
            envs[keys[i]]=dict(json.loads(envs[keys[i]]))

    return envs

def request_netbird(api_url: str, token: str) -> dict:
    ''' request the Netbird API to get the peers '''
    import requests

    url = f"{api_url}/peers"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Token {token}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Request to Netbird failed: {e}")
        return None

def request_npm(api_url: str) -> dict:
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
        print(f"Request to NPM failed: {e}")
        return None

def format_response_netbird(resp : dict, groups_whitelist : list, ip_whitelist: dict) -> dict:
    ''' Output format: {group1:[ip1,...], ...}'''
    import fnmatch

    output = {}

    for peer in resp:
        peer_ip= peer.get("ip", "")
        peer_groups= []
        for group in peer.get("groups", []):
            name=group.get("name", "")
            for pattern in groups_whitelist:
                if fnmatch.fnmatch(name, pattern):
                    peer_groups.append(f"nb-{name}")

        for group in peer_groups:
            if group not in output:
                output[group]=[]
            if peer_ip and peer_ip not in output[group]: #check peer_ip is not empty and not already in the group
                output[group].append(peer_ip)
    
    for group in ip_whitelist:
        if group not in output:
            output[group]=[]
        for ip in ip_whitelist[group]:
            if ip not in output[group]:
                output[group].append(ip)
    
    return output

def format_response_npm(resp : dict) -> dict:
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


def diff_resp(npm: dict, netbird: dict) -> dict:
    ''' return every action that should be done to update the old rules to the new rules '''

    actions = {"add_group": [], "update": [], "remove_group": []}

    for nb_group, nb_ips in netbird.items(): # the add or update action
        if nb_group not in npm:
            actions["add_group"].append((nb_group, nb_ips))
        else:
            # check if any change, delete or add, if so use netbird as new source
            if set(nb_ips) != set(npm[nb_group]["ip"]):
                actions["update"].append((nb_group, npm[nb_group]["id"], nb_ips))

    for npm_group in npm: # the remove action
        if npm_group not in netbird:
            actions["remove_group"].append(npm_group["id"])

    return actions # {'add_group': [(name, [ips]), ...], 'update': [(name, id, [ips]), ...], 'remove_group': [id]}


def update_npm_conf(actions: dict, envs: dict):
    ''' update the Nginx Proxy Manager configuration based on the actions list'''
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
            print(f"Added group {name} with IPs {ips} to NPM.")
        except requests.RequestException as e:
            print(f"Failed to add group {name} with IPs {ips} to NPM: {e}")
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
            print(f"Updated group {name} with IPs {ips} to NPM.")
        except requests.RequestException as e:
            print(f"Failed to update group {name} with IPs {ips} to NPM: {e}")
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
            print(f"Delete group {name} with IPs {ips} to NPM.")
        except requests.RequestException as e:
            print(f"Failed to delete group {name} with IPs {ips} to NPM: {e}")
            exit(1)
    

def request_npm_token(npm_api_url: str, username: str, password: str) -> str:
    ''' request the Nginx Proxy Manager API to get the token '''
    import requests
    from datetime import datetime

    global npm_token, npm_token_expires

    url = f"{npm_api_url}/tokens"

    if not npm_token or npm_token_expires <= time.time():
        print("Requesting new NPM token...")
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
            print(f"Request Token to Nginx Proxy Manager failed: {e}")
            exit(1)

    else:
        # Refresh token
        print("Refreshing NPM token...")
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
            print(f"Request Token to Nginx Proxy Manager failed: {e}")
            exit(1)

def main_first_run(envs : dict):
    ''' the entrypoint '''
    print("Doing initial run, fetching data from Netbird API...")
    resp=request_netbird(envs["NETBIRD_API_URL"], envs["NETBIRD_TOKEN"])
    if resp is None:
        print("Failed to fetch data from Netbird API while doing initial run.")
        exit(1)
    print("Netbird API: OK")

    formatted_netbird_response = format_response_netbird(resp, envs["GROUPS_WHITELIST"], envs["IP_WHITELIST"])

    request_npm_token(envs["NPM_API_URL"], envs["NPM_USERNAME"], envs["NPM_PASSWORD"])
    print("NPM Token: OK")
    
    resp=request_npm(envs["NPM_API_URL"])
    if resp is None:
        print("Failed to fetch data from NPM API while doing initial run.")
        exit(1)
    print("NPM API: OK")

    formatted_npm_response = format_response_npm(resp)

    actions = diff_resp(formatted_npm_response, formatted_netbird_response)
    
    update_npm_conf(actions, envs)
    



def main(envs: dict):
    ''' the main function that will be run every RUN_EVERY_MINUTES (less logs)'''

    print("Running scheduled task...")
    resp = request_netbird(envs["NETBIRD_API_URL"], envs["NETBIRD_TOKEN"])
    if resp is None:
        print("Failed to fetch data from Netbird API.")
        return
    formatted_netbird_response = format_response_netbird(resp, envs["GROUPS_WHITELIST"])

    request_npm_token(envs["NPM_API_URL"], envs["NPM_USERNAME"], envs["NPM_PASSWORD"])    
    resp=request_npm(envs["NPM_API_URL"])
    
    if resp is None:
        print("Failed to fetch data from NPM API while doing initial run.")
        exit(1)

    formatted_npm_response = format_response_npm(resp)

    actions = diff_resp(formatted_npm_response, formatted_netbird_response)
    
    update_npm_conf(actions, envs)


if __name__=='__main__':
    envs=load_environ()
    global npm_token, npm_token_expires
    npm_token=""
    npm_token_expires=0

    try:
        main_first_run(envs)
    except Exception as e:
        print(f"Error during initial run: {e}")
        exit(1) 
        
    schedule.every(envs["RUN_EVERY_MINUTES"]).minutes.do(main, envs)
    
    while True: # keep alive
        schedule.run_pending()
        time.sleep(1)