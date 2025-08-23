def load_environ() -> dict:
    from os import environ
    import json
    envs={}

    #Mandatory env variables
    envs["NETBIRD_API_URL"]=str(environ.get("NETBIRD_API_URL")).rstrip('/')
    envs["NETBIRD_TOKEN"]=str(environ.get("NETBIRD_TOKEN"))
    envs["NPM_API_URL"]=str(environ.get("NPM_API_URL")).rstrip('/')
    envs["NPM_USERNAME"]=str(environ.get("NPM_USERNAME"))
    envs["NPM_PASSWORD"]=str(environ.get("NPM_PASSWORD"))
    
    for key in envs:
        if envs[key]=='':
            raise(f"Env Variable {key} is missing")
    
    
    # Optional env variables
    try:
        envs["RUN_EVERY_MINUTES"]=int(environ.get("RUN_EVERY_MINUTES", 30))

        envs["SOCKET_LIMIT"]=int(environ.get("SOCKET_LIMIT", 0))
        
        envs["GROUPS_WHITELIST"]=list(json.loads(environ.get("GROUPS_WHITELIST", '["*"]')))
        if not isinstance(envs["GROUPS_WHITELIST"], list) or not all(isinstance(item, str) for item in envs["GROUPS_WHITELIST"]):
            raise ValueError("GROUPS_WHITELIST must be a list of str")
        
        envs["GROUP_EXCEPT"]=dict(json.loads(environ.get("GROUP_EXCEPT", '{}'))) 
        # Validate GROUP_EXCEPT format: must be {"str": ["str", ...]} for {"group1": ["192.168.1.1", ...]}
        if not isinstance(envs["GROUP_EXCEPT"], dict):
            raise ValueError("GROUP_EXCEPT must be a dict")
        for k, v in envs["GROUP_EXCEPT"].items():
            if not isinstance(k, str) or not isinstance(v, list) or not all(isinstance(item, str) for item in v):
                raise ValueError("GROUP_EXCEPT must be in the format {\"str\": [\"str\", ...]}")
    except json.JSONDecodeError as e:
        raise(f"Error parsing environment variables: {e}")
    except ValueError as e:
        raise(f"Error converting environment variables: {e}")
    except Exception as e:
        raise(f"Unexpected error while loading environment variables: {e}")
    return envs

def print_logs(text : str):
    from datetime import datetime
    print(f"[{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}] {text}")


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
            actions["remove_group"].append(npm[npm_group]["id"])

    return actions # {'add_group': [(name, [ips]), ...], 'update': [(name, id, [ips]), ...], 'remove_group': [id]}