# Slack connector

A connector for [Rocket.Chat](https://rocket.chat).

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
The connector itself won't allow opsdroid do much. It will connect to slack and be active on the `default-room`
but you will still need some skill to have opsdroid react to an input.

Luckily, opsdroid comes with a few skills out of the box as well. So once you run opsdroid you will see that it joined either the room that you set up on `default-room` parameter in the configuration or it will be in the `#general` room.

_Note: If opsdroid failed to join the room you can always invite him by clicking `info>Members section>invite more people...`_

You can also interact with opsdroid through direct message. To do so, just click on opsdroid's name and type something on the box that says "Message opsdroid".

Example of a private message:

```
fabiorosado [7:06 PM]
hi

opsdroid APP [7:06 PM]
Hi fabiorosado
```