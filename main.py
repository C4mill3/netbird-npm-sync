import schedule
import sqlite3
import json


def load_environ() -> dict:
    from os import environ
    keys=["NETBIRD_TOKEN", "NETBIRD_API_URL", "RUN_EVERY_MINUTES", "GROUPS_WHITELIST"]
    keys_types=["STR", "INT", "LIST"]
    envs={}
    for i in range(keys):
        envs[keys[i]]=environ.get(keys[i])
        
        if envs[keys[i]]=='':
            raise(f"Env Variable {keys[i]} is missing")
        
        if keys_types[i]=="STR":
            envs[keys[i]]=str(envs[keys[i]])
        
        elif keys_types[i]=="INT":
            envs[keys[i]]=int(envs[keys[i]])
            
        elif keys_types[i]=="LIST":
            envs[keys[i]]=list(json.loads(envs[keys[i]]))
            
    return envs
    
def diff_result(old: dict, new: dict) -> dict:
    ''' return every action that should be done to update the old dict to the new dict '''
    
    actions = {"add": [], "remove": []}
    
    for group in new: # the add action
        if group not in old:
            actions["add"].append(group)
        else:
            for ip in new[group]:
                if ip not in old[group]:
                    actions["add"].append((group, ip))
                    
    for group in old: # the remove action
        if group not in new:
            actions["remove"].append(group)
        else:
            for ip in old[group]:
                if ip not in new[group]:
                    actions["remove"].append((group, ip))
                    
    return actions

def format_response(resp : dict, groups_whitelist : list) -> dict:
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
                    peer_groups.append(name)

        for group in peer_groups:
            if group not in output:
                output[group] = []
            if peer_ip and peer_ip not in output[group]: #check peer_ip is not empty and not already in the group
                output[group].append(peer_ip)
    return output
            

def request_netbird(api_url: str, token: str):
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
    


def main_first_run(envs : dict):
    ''' the entrypoint '''
    
    print("Doing initial run, fetching data from Netbird API...")
    resp=request_netbird(envs["NETBIRD_API_URL"], envs["NETBIRD_TOKEN"])
    if resp is None:
        print("Failed to fetch data from Netbird API while doing initial run.")
        exit(1)
    print("Netbird API: OK")

def main(envs: dict):
    ''' the main function that will be run every RUN_EVERY_MINUTES '''

    


if __name__=='__main__':
    envs=load_environ()
    
    main_first_run(envs)
    schedule.every(envs["RUN_EVERY_MINUTES"]).minutes.do(main, envs)