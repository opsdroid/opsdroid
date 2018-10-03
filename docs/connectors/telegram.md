# Telegram connector

A connector for [Telegram](https://telegram.org/).

## Requirements

You need to [register a bot](https://core.telegram.org/bots) on Telegram and get an api token for it.

## Configuration

```yaml
connectors:
  - name: telegram
    # required
    token: "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ-ZYXWVUT"  # Telegram bot token
    # optional
    update_interval: 0.5  # Interval between checking for messages
    default_user: user1  # Default user to send messages to (overrides default room in connector)
    whitelisted_users:  # List of users who can speak to the bot, if not set anyone can speak
      - user1
      - user2
```
