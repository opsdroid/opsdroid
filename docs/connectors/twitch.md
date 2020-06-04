# Twitch

A connector for [Twitch](https://twitch.tv/).

## Requirements

- A Twitch Account
- A Twitch App obtained from [Twitch developers page](https://dev.twitch.tv/console/apps)
- The `code` obtained from the first step of OAuth

## Configuration

```yaml
connectors:
  twitch:
    # required
    code: "hfu923hfks02nd2821jfislf"  # Code obtained from the first oauth step
    client-id: "e0asdj48jfkspod0284"
    client-secret: "kdksd0458j93847j"
    channel: theflyingdev # Broadcaster channel
    redirect: http://localhost # Url to be passed to get oath token - defaults to localhost
    foward-url: 'http://94jfsd9ff.ngrok.io' # Either an URL provided by a forwarding service or an exposed ip address
    # optional
    always-listening: false # Turn on to connect to the chat server even if stream is offline.
```

## Setup Twitch App

You need to create a [Twitch App](https://dev.twitch.tv/console/apps) to use the Twitch Connector. Click the `+ Register Your Application` button, give this app a name and a redirect url - using `http://localhost` is fine. Once created, you can click the `Manage` button and get your `client-id`, you can then get a `client-secret` by pressing the `New Secret` button (keep this secret safe as it won't be shown to you again).

## Getting OAuth code

Twitch OAuth has two steps, first you need to make a `GET` request to a specific URL to obtain a `code`. After you've received the code, you need to make a `POST` request to the same URL and Twitch will send you an `access_token` and `refresh_token`. 

After a certain period, the `access_token` will expire and you have to make a new request with your `refresh_token` to re-authenticate yourself. 

_NOTE: The Twitch Connector will handle token expiration and re-authentication for you._

### Step 1 - Getting Code

To get your code, you need to make a request to `https://id.twitch.tv/oauth2/authorize` with the following parameters:

- client_id
- redirect_uri
- response_type
- scope

Both the `client_id` and `redirect_uri` can be obtained when you click the `Manage` button on your app. The `response_type` that we want will be `code` and we will ask for a lot of scopes. You can check the [API Scopes](https://dev.twitch.tv/docs/v5/guides/migration#scopes) and the [IRC Scopes](https://dev.twitch.tv/docs/irc/guide#scopes-for-irc-commands) to read more about what we are asking and why.

The Twitch Connector interacts with a wide range of services - IRC server, New API, V5 API - so we need to pass a big number of scopes to make sure everything works as expected.

#### Recommended scopes

```
channel:read:subscriptions+channel_subscriptions+analytics:read:games+chat:read+chat:edit+viewing_activity_read+channel_feed_read+channel_editor+channel:read:subscriptions+user:read:broadcast+user:edit:broadcast+user:edit:follows+channel:moderate+channel_read
```

#### Example: OAuth URL

You can use this example url to make your request - make sure you add your `client_id` before making the request. After adding your client id, you can open the url on a browser window, accept the request and Twitch will send you back to your `redirect_url`. Look at the address bar and you will see that it contains a `code=jfsd98hjh8d7da983j` this is what you need to add to your opsdroid config.

```
https://id.twitch.tv/oauth2/authorize?client_id=<your client id>&redirect_uri=http://localhost&response_type=code&scope=channel:read:subscriptions+channel_subscriptions+analytics:read:games+chat:read+chat:edit+viewing_activity_read+channel_feed_read+channel_editor+channel:read:subscriptions+user:read:broadcast+user:edit:broadcast+user:edit:follows+channel:moderate+channel_read
```

## Usage

The connector will subscribe to three webhooks - follower alert, stream status and subscribers. These webhooks allow Twitch to make a post request with data of certain actions, these actions will trigger events specific to the Twitch connector. By default, opsdroid will only connect to the chat service when the streamer is live, but you can set the optional configuration setting `always-listening` to true and make opsdroid connect to the chat whenever opsdroid is active.

You can write your skills to interact with the connector and with all the events triggered by the connector, or you can use the [Twitch Skill](https://github.com/FabioRosado/skill-twitch).


```eval_rst
.. automodule:: opsdroid.connectors.twitch
    :members:
```


