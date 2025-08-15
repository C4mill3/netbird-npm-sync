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
    global npm_token, npm_token_expires
    npm_token=""
    npm_token_expires=0
    envs=utility.load_environ()

    try:
        utility.print_logs("Running initial run...")
        main(envs, verbose=True)
    except Exception as e:
        print(f"Error during initial run: {e}")
        exit(1) 
    utility.print_logs("Initial run completed successfully.")
    
    if envs["RUN_EVERY_MINUTES"] > 0:
        schedule.every(envs["RUN_EVERY_MINUTES"]).minutes.do(main, envs)
        utility.print_logs(f"Task scheduled to run every {envs['RUN_EVERY_MINUTES']} minutes.")
        while True: # keep alive
            schedule.run_pending()
            time.sleep(1)