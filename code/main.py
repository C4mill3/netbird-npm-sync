import time

import utility

def main(envs : dict, verbose: bool = False):
    import netbird as nb
    import npm
    ''' the main  '''
    global npm_token, npm_token_expires
    utility.print_logs("Running Task")
    
    if verbose: utility.print_logs("Fetching data from Netbird API...")
    resp=nb.request_api(envs["NETBIRD_API_URL"], envs["NETBIRD_TOKEN"])
    if resp is None:
        utility.print_logs("Failed to fetch data from Netbird API, exiting.")
        exit(1)
    if verbose: utility.print_logs("Netbird API: OK")

    formatted_netbird_response = nb.format_resp(resp, envs["GROUPS_WHITELIST"], envs["GROUP_EXCEPT"])

    npm_token, npm_token_expires = npm.request_token(envs["NPM_API_URL"], envs["NPM_USERNAME"], envs["NPM_PASSWORD"], npm_token, npm_token_expires)
    if verbose: utility.print_logs("NPM Token: OK")
    
    resp=npm.request_api(envs["NPM_API_URL"], npm_token)
    if resp is None:
        utility.print_logs("Failed to fetch data from NPM API, exiting.")
        exit(1)
    if verbose: utility.print_logs("NPM API: OK")

    formatted_npm_response = npm.format_resp(resp)

    actions = utility.diff_resp(formatted_npm_response, formatted_netbird_response)
    
    npm.update_conf(actions, envs, npm_token)
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
    
    import threading

    def run_schedule():
        utility.print_logs(f"Task scheduled to run every {envs['RUN_EVERY_MINUTES']} minutes.")
        import schedule
        schedule.every(envs["RUN_EVERY_MINUTES"]).minutes.do(main, envs)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def run_socket():
        utility.print_logs(f"Socket server enabled on port 8080 with a limit of {envs['SOCKET_LIMIT']} requests per hour.")
        from socket_ import run
        run(envs)

    threads = []
    if envs["RUN_EVERY_MINUTES"] > 0:
        t = threading.Thread(target=run_schedule, daemon=True)
        threads.append(t)
        t.start()

    if envs["SOCKET_LIMIT"] > 0:
        t = threading.Thread(target=run_socket, daemon=True)
        threads.append(t)
        t.start()

    if threads: # keep alive till any fatal error in any thread
        while all(t.is_alive() for t in threads):
            time.sleep(1)