# Discord

A connector for [Discord](https://discord.com/developers/docs/).

## Requirements

**This connector requires access token.**

Follow the steps to get access token :

 - Visit https://discord.com/developers/applications
 - Create a new app
 - Once the app is created, go to app’s Settings, and under Bot, click on Add Bot. 
 - There you can reset your `token` to see it.
 - If you want to add your bot to a discord channel, go under OAuth2 then URL Generator. Click on the bot scope and choose the permissions you want. An URL will be generated and you can use it to add your bot to your channel.

## Configuration

```yaml
connectors:
  discord:
    # required
    token: mytoken
    # optional
    bot-name: "mybot" # default "opsdroid"
```
