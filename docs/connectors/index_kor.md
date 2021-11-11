# Connectors

Connectors는 opsdroid를 외부 이벤트 자료와 연결 해주는 것이다. 이것은 Slack이나 Matrix처럼 채팅 서비스 일수 있고 webhook endpoint와 같은 이벤트일수도 있다. 

```eval_rst
.. toctree::
   :maxdepth: 1

   facebook
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

너가 필요하다면 너는 두가지 connector를 사용 할 수 있다. 예를 들어 너가 Slack connectors를 원한다면 

```yaml
connectors:
  slack:
      bot-token: "xoxb-abdcefghi-12345"
  slack-two:
      bot-token: "xoxb-12345-abdcefghi"
      module: opsdroid.connector.slack
```

아래와 같이 두가지를 읽어올 수 있다. 둘 중 하나만을 읽어오는 것도 가능하다.

```python
# Use 'slack-two' connector
slack_two = opsdroid.get_connector("slack-two")
```