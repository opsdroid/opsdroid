# Mattermost connector

A connector for [Mattermost](https://mattermost.com/).

## Requirements

* A Mattermost account
* A [Mattermost App bot account](https://docs.mattermost.com/developer/bot-accounts.html).
  * Create a [new Mattermost bot](https://docs.mattermost.com/developer/bot-accounts.html).
  * Take note of the "Bot Account Access Token" as this will be the `atoken` you need for your configuration.

## Configuration

```yaml
connectors:
  mattermost:
    # Required
    token: "zyxw-abdcefghi-12345"
    url: "mattermost.server.com"
    team-name: "myteam"
    # Optional
    scheme: "http" # default: https
    port: 8065 # default: 8065
    ssl-verify: false # default: true
    connect-timeout: 30 # default: 30
```

## Usage
The connector itself won't allow opsdroid to do much. It will connect to Mattermost and be active to the users,
but you will still need to add it to teams and channels and include some skill to have opsdroid react to an input.

Luckily, opsdroid comes with few skills out of the box as well. So once you run opsdroid you will see that it is available to the users.

_Note: If opsdroid is not available in a chat room you can always invite him to the teams and channels`_

You can also interact with opsdroid through direct message. To do so, just click on opsdroid's name and type something on the box that says "Message opsdroid".

Example of a private message:

```
daniccan [9:06 PM]
hi

opsdroid APP [9:06 PM]
Hi daniccan
```

The connector doesn't parse messages that have been posted by the bot itself.
