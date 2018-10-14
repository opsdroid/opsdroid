# Facebook Messenger connector

A connector for [Facebook Messenger](https://developers.facebook.com/docs/messenger-platform/).

## Requirements

**This connector requires access token for your facebook page.**

Follow the steps to get access token :

 - Create a Facbook page for your bot
 - Visit https://developers.facebook.com
 - Create a new app and add a messenger product
 - Generate a `page-access-token` for the page you created
 - Create a webhook pointing to `http(s)://your-bot-url.com:port/connector/facebook`
 - Randomly generate a `verify-token` and add that to the webhook

## Configuration

```yaml
connectors:
  - name: facebook
    # required
    verify-token: aabbccddee
    page-access-token: aabbccddee112233445566
    # optional
    bot-name: "mybot" # default "opsdroid"
```
