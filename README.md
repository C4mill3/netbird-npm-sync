# Netbird NPM Sync Service
This python service is used to sync group permissions from Netbird to Nginx Proxy Manager (NPM) using both API.

## Table of Contents
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Other](#other)


## Usage
You can run this service in a docker container or directly on your host machine.

### Docker
`docker-compose.yaml`
```yaml
services:
  npm:
    image: 'jc21/nginx-proxy-manager:latest'
    container_name: 'npm'
    ...
    healthcheck:
      test: ['CMD', '/usr/bin/check-health']
      interval: '10s'
      timeout: '3s'


  netbird-sync:
    image: 'ghcr.io/c4mill3/netbird-npm-sync:latest'

    environment:
      # Mandatory
      NETBIRD_API_URL: 'https://sub.domain.com/api'
      NETBIRD_TOKEN: 'X'
      NPM_API_URL: 'http://npm:81/api'
      NPM_USERNAME: 'X'
      NPM_PASSWORD: 'X'

      # Optional
      RUN_EVERY_MINUTES: '30'
      GROUPS_WHITELIST: '["home-*", "admin"]'
      GROUP_EXCEPT: '{"groupname": ["192.168.1.0/24"]}'
    depends_on:
      npm:
        condition: 'service_healthy'
```


### Run directly
You need to setup Env Variable
```bash
git clone https://github.com/C4mill3/netbird-npm-sync.git
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 code/main.py
``` 


## Environment Variables

* `NETBIRD_API_URL`: The Netbird API URL. exemple: `https://netbird.domain.com/api` or `https://api.domain.com`
* `NETBIRD_TOKEN`: Your Netbird token. See [Get an API Netbird Token](#get-an-api-netbird-token).

* `NPM_API_URL`: The NPM API URL. exemple:  priority to internal: `http://DOCKER_NAME:81/api` or `https://npm.domain.com/api`
* `NPM_USERNAME`: npm user email, you should create a user with `ACL` permission. See [Recommended Permissions](#recommended-account-permissions-for-nginx-proxy-manager).
* `NPM_PASSWORD`: npm user password

* `RUN_EVERY_MINUTES`: How often the `ACL` should be updated, in minutes. Default is `30`. If you want to run it only at start, set it to `0`.
* `GROUPS_WHITELIST`: Should be in list format, you can use joker cards. exemple: `["/home*", "admin"]`
* `GROUP_EXCEPT`: The ip will be able to access everything, should be in dict format, you can precise submask.exemple: `{group1:["192.168.1.0/24", ...]}`

You can find npm api doc in: `https://npm.domain.com/api/schema`.



## Other

### Recommended Account Permissions for Nginx Proxy Manager
![Recommended Permissions](README/permissions.png)

### Get an API Netbird Token
Go to your Netbird dashboard then `Team` -> `Service Users` -> `Create Service User` and now `Create Access Token`
