import time
import threading

import utility

def main(config : dict, verbose: bool = False):
    import netbird as nb
    import npm

    ''' the main  '''
    utility.print_logs("Running Task")

    if verbose: utility.print_logs("Fetching data from Netbird API...")
    resp=nb.request_api(config['netbird']['api_url'], config['netbird']['token'])
    if resp is None:
        utility.print_logs("Failed to fetch data from Netbird API, exiting.")
        exit(1)
    if verbose: utility.print_logs("Netbird API: OK")

    formatted_netbird_response = nb.format_resp(resp, config['netbird']['group_whitelist'], config['npm']['group_rule_excep'])

    with config['token_lock']:
        token = config['token_data']['npm_token']
        expires = config['token_data']['npm_token_expires']
        new_token, new_expires = npm.request_token(
            config['npm']['api_url'],
            config['npm']['username'],
            config['npm']['password'],
            token,
            expires
        )
        config['token_data']['npm_token'] = new_token
        config['token_data']['npm_token_expires'] = new_expires
        npm_token = new_token

    if verbose: utility.print_logs("NPM Token: OK")

    resp=npm.request_api(config['npm']['api_url'], npm_token)
    if resp is None:
        utility.print_logs("Failed to fetch data from NPM API, exiting.")
        exit(1)
    if verbose: utility.print_logs("NPM API: OK")

    formatted_npm_response = npm.format_resp(resp)

    actions = utility.diff_resp(formatted_npm_response, formatted_netbird_response)

    npm.update_conf(actions, config, npm_token)
    if verbose: utility.print_logs("Up to date")


if __name__=='__main__':
    # Use a shared dict and lock for thread-safe token access
    token_data = {'npm_token': '', 'npm_token_expires': 0}
    token_lock = threading.Lock()
    config=utility.load_config()
    config['token_data'] = token_data
    config['token_lock'] = token_lock

    try:
        utility.print_logs("Running initial run...")
        main(config, verbose=True)
    except Exception as e:
        print(f"Error during initial run: {e}")
        exit(1)
    utility.print_logs("Initial run completed successfully.")

    def run_schedule():
        utility.print_logs(f"Task scheduled to run every {config['refresh_every_minutes']} minutes.")
        import schedule
        schedule.every(config['refresh_every_minutes']).minutes.do(main, config)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def run_socket():
        utility.print_logs(f"Socket server enabled on port {config['socket']['port']} with a limit of {config['socket']['limit_per_hour']} requests per hour.")
        from socket_ import run
        run(config)

    threads = []
    if config['refresh_every_minutes'] > 0:
        t = threading.Thread(target=run_schedule, daemon=True)
        threads.append(t)
        t.start()

    if config['socket']['enable']:
        t = threading.Thread(target=run_socket, daemon=True)
        threads.append(t)
        t.start()

    if threads: # keep alive till any fatal error in any thread
        while all(t.is_alive() for t in threads):
            time.sleep(1)