import schedule
import time
import json


def load_environ() -> dict:
    from os import environ
    keys=["NETBIRD_TOKEN", "NETBIRD_API_URL", "NPM_API_URL", "NPM_USERNAME",
          "NPM_PASSWORD", "RUN_EVERY_MINUTES", "GROUPS_WHITELIST", "IP_WHITELIST"]
    keys_types=["STR", "STR", "STR", "STR", "STR", "INT", "LIST", "DICT"]
    envs={}
    for i in range(keys):
        envs[keys[i]]=environ.get(keys[i])

        if envs[keys[i]]=='':
            raise(f"Env Variable {keys[i]} is missing")

        if keys_types[i]=="STR":
            envs[keys[i]]=str(envs[keys[i]])

        elif keys_types[i]=="INT":
            envs[keys[i]]=int(envs[keys[i]])

        elif keys_types[i]=="LIST" or keys_types[i]=="DICT":
            envs[keys[i]]=list(json.loads(envs[keys[i]]))

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
        "Authorization": f"Token {npm_token}"
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


def diff_result(npm: dict, netbird: dict) -> dict:
    ''' return every action that should be done to update the old rules to the new rules '''

    actions = {"add_group": [], "update": [],  "remove": [], "remove_group": []}

    for nb_group, nb_ips in netbird.items(): # the add or update action
        if nb_group not in npm:
            actions["add_group"].append((nb_group, nb_ips))
        else:
            for nb_ip in nb_ips:
                if nb_ip not in npm[nb_group]["ip"]:
                    actions["update"].append((npm[nb_group]["id"], nb_ip))

    for npm_group in npm: # the remove action
        if npm_group not in netbird:
            actions["remove_group"].append(npm_group["id"])
        else:
            for npm_ip in npm[npm_group]["ip"]:
                if npm_ip not in netbird[npm_group]:
                    actions["remove"].append((npm[npm_group]["id"], npm_ip))

    return actions # {'add': [(name, [ips]), ...], 'update': [(id, ip), ...], 'remove': [(id, ip), 'remove_group': [id]}


def update_npm_conf(actions: dict, envs: dict):
    ''' update the Nginx Proxy Manager configuration based on the actions list'''
    pass


def request_npm_token(npm_api_url: str, username: str, password: str) -> str:
    ''' request the Nginx Proxy Manager API to get the token '''
    import requests
    from datetime import datetime

    global npm_token, npm_token_expires

    url = f"{npm_api_url}/tokens"

    if not npm_token or npm_token_expires < time.time():
        # Request token
        headers={
            "Accept": "application/json",
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

    formatted_netbird_response = format_response_netbird(resp, envs["GROUPS_WHITELIST"])

    request_npm_token(envs["NPM_API_URL"], envs["NPM_USERNAME"], envs["NPM_PASSWORD"])
    print("NPM Token: OK")
    
    resp=request_npm(envs["NPM_API_URL"])
    if resp is None:
        print("Failed to fetch data from NPM API while doing initial run.")
        exit(1)
    print("NPM API: OK")

    formatted_npm_response = format_response_npm(resp, envs["GROUPS_WHITELIST"])

    

    # TODO rewrite every existing rule and add the new ones




def main(envs: dict):
    ''' the main function that will be run every RUN_EVERY_MINUTES '''

    print("Running scheduled task...")
    resp = request_netbird(envs["NETBIRD_API_URL"], envs["NETBIRD_TOKEN"])
    if resp is None:
        print("Failed to fetch data from Netbird API.")
        return

    formatted_response = format_response_netbird(resp, envs["GROUPS_WHITELIST"])
    with open("/data/last_resp.json", "r") as f:
        try:
            last_resp = json.load(f)
        except json.JSONDecodeError:
            last_resp = {}

    actions = diff_result(last_resp, formatted_response)
    if actions["add"] or actions["remove"]:
        print("Changes detected, updating Nginx Proxy Manager configuration...")
        update_npm_conf(actions, envs)
        with open("/data/last_resp.json", "w") as f:
            json.dump(formatted_response, f)
    else:
        print("No changes detected, skipping update.")


if __name__=='__main__':
    envs=load_environ()
    global npm_token, npm_token_expires

    main_first_run(envs)
    schedule.every(envs["RUN_EVERY_MINUTES"]).minutes.do(main, envs)