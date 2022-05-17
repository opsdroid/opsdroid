# Microsoft Teams

A connector for [Microsoft Teams](https://www.microsoft.com/en-gb/microsoft-365/microsoft-teams/group-chat-software).

## Creating a teams app

* Navigate to "Apps" in Teams and install the App Studio

![App Studio](https://i.imgur.com/3fIuhIq.png)

* Head to the manifest editor tab and create a new app

![Manifest editor](https://i.imgur.com/F4IpEMP.png)

* Fill in the required fields under App Details (you can skip the icons)

![App Details](https://i.imgur.com/poWcVT5.png)

* Under the bot menu set up a new bot. Give it all the required scopes.

![Creating bot user](https://i.imgur.com/uTg4dOL.png)

* Enter the URL of your bot followed by the `/connector/teams` endpoint and generate a new password.
  * Your but must be exposed to the internet to work. See the [exposing page](../exposing.md) for details. Teams recommends using `ngrok`.

![Bot URL and password](https://i.imgur.com/a93glAU.png)

* Take note of the app ID (under the bot name) and the password for later.

* Head to "Test and distribute" and install your app.

![Install your app](https://i.imgur.com/gKfOyyK.png)

* Under the add menu choose a team or chat to add the bot to. You can add it to more later.

![Add the bot](https://i.imgur.com/9N2HcjW.png)

## Configuration

```yaml
connectors:
  teams:
    # required
    app-id: "yourappid"
    password: "yourpassword"
    # optional
    bot-name: "mybot" # default "opsdroid"

databases:
    sqlite: {}  # Teams assumes one database is configured to preserve state
```

## Usage

Your bot will only respond to messages where it was mentioned. So take this into account when designing your skills.

The bot can also only talk in channels where it has been spoken to at least once.

![Example message to Opsdroid](https://i.imgur.com/rl1FHAD.png)
