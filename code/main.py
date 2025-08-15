import schedule
import time

import netbird as nb
import npm
import utility


def main(envs : dict, verbose: bool = False):
    ''' the main  '''
    if verbose: utility.print_logs("Fetching data from Netbird API...")
    resp=nb.request_api(envs["NETBIRD_API_URL"], envs["NETBIRD_TOKEN"])
    if resp is None:
        utility.print_logs("Failed to fetch data from Netbird API, exiting.")
        exit(1)
    if verbose: utility.print_logs("Netbird API: OK")

    formatted_netbird_response = nb.format_resp(resp, envs["GROUPS_WHITELIST"], envs["GROUP_EXCEPT"])

    npm.request_token(envs["NPM_API_URL"], envs["NPM_USERNAME"], envs["NPM_PASSWORD"])
    if verbose: utility.print_logs("NPM Token: OK")
    
    resp=npm.request_api(envs["NPM_API_URL"])
    if resp is None:
        utility.print_logs("Failed to fetch data from NPM API, exiting.")
        exit(1)
    if verbose: utility.print_logs("NPM API: OK")

    formatted_npm_response = npm.format_resp(resp)

    actions = utility.diff_resp(formatted_npm_response, formatted_netbird_response)
    
    npm.update_conf(actions, envs)
    if verbose: utility.print_logs("Up to date")
    


if __name__=='__main__':
    envs=utility.load_environ()
    global npm_token, npm_token_expires, fail
    npm_token=""
    npm_token_expires=0
    fail=0

    try:
        utility.print_logs("Running initial run...")
        main(envs)
    except Exception as e:
        print(f"Error during initial run: {e}")
        exit(1) 

    schedule.every(envs["RUN_EVERY_MINUTES"]).minutes.do(main, envs)
    
    while True: # keep alive
        schedule.run_pending()
        time.sleep(1)