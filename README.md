# nginxpm-netbird-acl
Nebird group acces list generator for nginx proxy manager



## Environment Variables

* `NETBIRD_API_URL`: The Netbird API URL. exemple: `https://netbird.domain.com/api` or `https://api.domain.com`
* NETBIRD_TOKEN: Your Netbird token, to get one go to your Netbird dashboard then `Team` -> `Service Users` -> `Create Service User` and now `Create Access Token`

* `NPM_API_URL`: The NPM API URL. exemple:  priority to internal: `http://DOCKER_NAME:81/api` or `https://npm.domain.com/api`
* `NPM_USERNAME`: npm user email, you should create a user with `ACL` permission
* `NPM_PASSWORD`: npm user password

* `RUN_EVERY_MINUTES`: How often the acl should be updated, in minutes. exemple: `30`
* `GROUPS_WHITELIST`: Should be in list format, you can use joker cards. exemple: `["/home*", "admin"]`
* `IP_WHITELIST`: The ip will be able to access everything, should be in dict format, you can precise submask. exemple: `{group1:{"192.168.1.0/24", "10.0.0.1/32"}}`

You can find npm api doc in: `https://npm.domain.com/api/schema`.
