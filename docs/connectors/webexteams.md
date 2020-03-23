# Webex Teams

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to interact with [Webex Teams](https://www.webex.com/team-collaboration.html).
_Note: Webex Teams was used to be called cisco spark. We changed cisco spark connector to webex teams connector_

## Usage

**This connector requires that the opsdroid web server is internet facing.**

 - Visit https://developer.webex.com/ and log in
 - Go to "My Apps"
 - Click the plus button to create a new app and select "Create a Bot"
 - Fill in the details and click "Add Bot"
 - Scroll down and find your access token

## Configuration

```yaml
connectors:
  webexteams:
    # required
    webhook-url: http(s)://<host>:<port>  # Url for Webex Teams to connect to your bot
    token: <your bot access token>  # Your access token
```
