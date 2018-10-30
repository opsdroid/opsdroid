# Twitter connector

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to send messages using [Twitter](https://twitter.com/).

## Requirements

To use the twitter connecter you will need a Twitter account which you want the bot to control and you will need an application to authenticate with.

### Creating your application

* Go to https://apps.twitter.com/
* Log in with the account you want the bot to use
* Create a new application (fill in the name, description and website)
* Go to the application settings pages
* Select the 'permissions' tab and allow 'Read, Write and Access direct messages'
* Select the 'Keys and Access Tokens' tab and generate an Access Token and Token Secret
* Make note of your Tokens and Consumer Tokens

## Configuration

```yaml
connectors:
  - name: twitter
    # required
    consumer_key: "zyxw-abdcefghi-12345"
    consumer_secret: "zyxw-abdcefghi-12345-zyxw-abdcefghi-12345"
    oauth_token: "zyxw-abdcefghi-12345-zyxw-abdcefghi-12345"
    oauth_token_secret: "zyxw-abdcefghi-12345-zyxw-abdcefghi-12345"
    # optional
    enable_dms: true  # Should the bot respond to Direct Messages
    enable_tweets: true  # Should the bot respond to tweets
```
