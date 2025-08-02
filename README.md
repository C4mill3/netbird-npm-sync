# nginxpm-netbird-acl
Nebird group acces list generator for nginx proxy manager



## Environment Variables

* NETBIRD_TOKEN: Your Netbird token, to get one go to your Netbird dashboard then `Team` -> `Service Users` -> `Create Service User` and now `Create Access Token`
* RUN_EVERY_MINUTES: How often the acl should be updated, in minutes. exemple: `30`
* `GROUPS_WHITELIST`: Should be in list format, you can use joker cards. exemple: `["/home*", "admin"]`