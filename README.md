# nginxpm-netbird-acl
Nebird group acces list generator for nginx proxy manager



## Environment Variables

* NETBIRD_TOKEN: Your Netbird token, to get one go to your Netbird dashboard then `Team` -> `Service Users` -> `Create Service User` and now `Create Access Token`
* `NETBIRD_API_URL`: The Netbird API URL. exemple: `https://sub.domain.com/api` or `https://api.domain.com`
* `RUN_EVERY_MINUTES`: How often the acl should be updated, in minutes. exemple: `30`
* `GROUPS_WHITELIST`: Should be in list format, you can use joker cards. exemple: `["/home*", "admin"]`
* `IP_WHITELIST`: The ip will be able to access everything, should be in list format, you should use mask: `["192.168.1.0/24", "10.0.0.1/32"]`