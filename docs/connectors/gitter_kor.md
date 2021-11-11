# Gitter

Gitter를 위한 Connector[Gitter](https://developer.gitter.im/docs/welcome).

Gitter는 중복된 메시지에 치명적이다. Bot이 스팸 메시지를 판별하는 방법은 중복된 메시지를 일정 메시지에 지속해서 포스팅하는 것이다. 이를 통해 해당하는 모든 메시지를 차단 할 수 있다. 이를 통해서 opsdroid는 수신에 성공했다고 제시되어도 해당하는 메시지를 전달 받지 못할 수 있다. 따라서 이를 해결하는 방법 중 하나로는 bot을 위한 계정을 하나 생성해서 이를 최소 2주동안은 유지하는 것이다. 만약 계정이 잠겼다면 이를 푸는 방법은 삭제하고 gitter 계정을 새로 만드는 것 뿐이다. 
[shadow banning](https://en.wikipedia.org/wiki/Shadow_banning)
[Accounts older than two weeks may be exempt from duplicate detection](https://github.com/opsdroid/opsdroid/issues/1693#issuecomment-754629627)


## Requirements

Gitter Connector를 사용하기 위해서 사용자의 개인 token이 필요하다. 사용하는 본 계정과 별도의 계정을 생성하는 것을 추천한다.
### Creating your application

- Bot을 위한 Gitter 사용자를 생성하고 로그인한다.
- Token을 생성한다.(https://developer.gitter.im/apps)
- 원하는 Room-id를 입력한다.(https://developer.gitter.im/docs/rooms-resource).

## Configuration

```yaml
connectors:
  gitter:
    # Required
    room-id: "to be added"
    token: "to be added"
    # optional
    bot-name: opsdroid # default 'opsdroid'
```
