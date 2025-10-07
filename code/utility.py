def load_config() -> dict:
    import yaml
    try:
        with open("/app/config.yaml", "r") as f:
            file_config=yaml.safe_load(f)
    except FileNotFoundError:
        raise("Config file /app/config.yaml not found")
    except yaml.YAMLError as e:
        raise(f"Error parsing config file: {e}")
    except Exception as e:
        raise(f"Unexpected error while loading config file: {e}")
    assert isinstance(file_config, dict), "Config file is not a valid YAML dictionary"
    
    clean_config = {'netbird': {}, 'npm': {}, 'socket': {}} # init 1st level keys
    
    #Mandatory conf variables
    try:
        clean_config['netbird']['api_url']=str(file_config.get('netbird', {}).get('api_url', '')).rstrip('/')
        clean_config['netbird']['token']=str(file_config.get('netbird', {}).get('token', ''))
        clean_config['npm']['api_url']=str(file_config.get('npm', {}).get('api_url', '')).rstrip('/')
        clean_config['npm']['username']=str(file_config.get('npm', {}).get('username', ''))
        clean_config['npm']['password']=str(file_config.get('npm', {}).get('password', ''))
    except KeyError as e:
        raise(f"Missing mandatory config key: {e}")
    except ValueError as e:
        raise(f"Error converting config key: {e}")
    except Exception as e:
        raise(f"Unexpected error while loading config key: {e}")
    
    for k, v in clean_config['netbird'].items():
        if v == '':
            raise ValueError(f"Mandatory config key netbird:{k} is empty")
    
    # Optional conf variables
    try:
        clean_config['refresh_every_minutes']=int(file_config.get("refresh_every_minutes", 30))
        assert clean_config['refresh_every_minutes'] >= 0, "refresh_every_minutes must be a positive integer or null (0)"

        clean_config['socket']['enable']=bool(file_config.get('socket', {}).get('enable', False))
        clean_config['socket']['limit_per_hour']=int(file_config.get('socket', {}).get('limit_per_hour', 10))
        clean_config['socket']['port']=int(file_config.get('socket', {}).get('port', 8080))
        
        if clean_config['socket']['enable']:
            assert clean_config['socket']['limit_per_hour'] > 0, "limit_per_hour must be a positive integer"
            assert 1 <= clean_config['socket']['port'] <= 65535, "port must be between 1 and 65535"
        
        clean_config['netbird']['group_whitelist']=list(file_config.get('netbird', {}).get('group_whitelist', ['*']))
        if not isinstance(clean_config['netbird']['group_whitelist'], list) or not all(isinstance(item, str) for item in clean_config['netbird']['group_whitelist']):
            raise ValueError("group_whitelist must be a list of str")
        
        clean_config['npm']['group_rule_excep']=dict(file_config.get('npm', {}).get('group_rule_excep', {})) 
        # Validate clean_config format: must be {"str": ["str", ...]} for {"group1": ["192.168.1.1", ...]}
        if not isinstance(clean_config['npm']['group_rule_excep'], dict):
            raise ValueError("clean_config must be a dict")
        for k, v in clean_config['npm']['group_rule_excep'].items():
            if not isinstance(k, str) or not isinstance(v, list) or not all(isinstance(item, str) for item in v):
                raise ValueError("group_rule_excep must be in the format {\"str\": [\"str\", ...]}")
    except ValueError as e:
        raise(f"Error converting conf variables: {e}")
    except Exception as e:
        raise(f"Unexpected error while loading conf variables: {e}")
    
    return clean_config

def print_logs(text : str):
    from datetime import datetime
    print(f"[{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}] {text}")


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