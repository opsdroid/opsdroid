# Slack connector

A connector for [Slack](https://slack.com/).

## Requirements

 * A Slack account
 * The token from a [custom bot integration](https://my.slack.com/apps/A0F7YS25R-bots)

## Configuration

```yaml
connectors:
  - name: slack
    # required
    api-token: "zyxw-abdcefghi-12345"
    # optional
    bot-name: "mybot" # default "opsdroid"
    default-room: "#random" # default "#general"
    icon-emoji: ":smile:" # default ":robot_face:"
```

## Usage
