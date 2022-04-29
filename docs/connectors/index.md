# Connectors

Connectors are modules which connect opsdroid to an external event source. This could be a chat client such as Slack or Matrix, or another source of events such as webhook endpoints. If an event is triggered by something outside opsdroid it happens in a connector.

```eval_rst
.. toctree::
   :maxdepth: 1

   facebook
   gitlab
   github
   gitter
   mattermost
   matrix
   rocketchat
   shell
   slack
   teams
   telegram
   twitch
   webexteams
   websocket
   custom
```

## Using two of the same connector type

If you need, you can use two of the same connector by adding the ``module`` parameter in your configuration. For example, if you wish to use two Slack connectors pointing to different workspaces, you can do such with:

```yaml
connectors:
  slack:
      bot-token: "xoxb-abdcefghi-12345"
  slack-two:
      bot-token: "xoxb-12345-abdcefghi"
      module: opsdroid.connector.slack
```

You can then select one connector or the other by using opsdroid's method `get_connector()`. For example:

```python
# Use 'slack-two' connector
slack_two = opsdroid.get_connector("slack-two")
```