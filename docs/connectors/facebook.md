# Facebook Messenger

A connector for [Facebook Messenger](https://developers.facebook.com/docs/messenger-platform/).

## Requirements

**This connector requires access token for your Facebook page.**

Follow the steps to get access token :

 - Create a Facebook page for your bot
 - Visit https://developers.facebook.com
 - Create a new app
 - Once the app is created, go to app’s Settings, and under PRODUCTS, click Add Product. Select Messenger, and choose to Set up the messenger product.
 - Generate a `page-access-token` for the page you created to start using Facebook APIs
 - Create a webhook pointing to `http(s)://your-bot-url.com:port/connector/facebook`
 - Randomly generate a `verify-token` and add that to the webhook

## Configuration

```yaml
connectors:
  facebook:
    # required
    verify-token: aabbccddee
    page-access-token: aabbccddee112233445566
    # optional
    bot-name: "mybot" # default "opsdroid"
```
