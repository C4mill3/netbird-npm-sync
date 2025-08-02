import schedule
import sqlite3
import json
import requests


def load_environ() -> dict:
    from os import environ
    keys=["NETBIRD_TOKEN", "RUN_EVERY_MINUTES", "GROUPS_WHITELIST"]
    keys_types=["STR", "INT", "LIST"]
    envs={}
    for i in range(keys):
        envs[keys[i]]=environ.get(keys[i])
        
        if keys_types[i]=="STR":
            envs[keys[i]]=str(envs[keys[i]])
        
        if keys_types[i]=="INT":
            envs[keys[i]]=int(envs[keys[i]])
            
        if keys_types[i]=="LIST":
            envs[keys[i]]=list(json.loads(envs[keys[i]]))
    return envs
    



def main(envs : dict, first_run : bool = False):
    ''' the entrypoint

    '''
    if first_run:
        pass


if __name__=='__main__':
    envs=load_environ()
    main(envs, first_run=True)
    schedule.every(envs["RUN_EVERY_MINUTES"]).minutes.do(main, envs)