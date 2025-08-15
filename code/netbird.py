import utility

def request_api(api_url: str, token: str) -> dict:
    ''' request the Netbird API to get the peers '''
    import requests
    

    url = f"{api_url}/peers"
    print(url)
    headers = {
        "Accept": "application/json",
        "Authorization": f"Token {token}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        utility.print_log(f"Request to Netbird failed: {e}")
        return None
    
def format_resp(resp : dict, groups_whitelist : list, group_except: dict) -> dict:
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
    
    for group in group_except:
        if group not in output:
            output[group]=[]
        for ip in group_except[group]:
            if ip not in output[group]:
                output[group].append(ip)
    
    return output