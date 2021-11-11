# Rocket.Chat

Rocket.Chat을 위한 Connector.[Rocket.Chat](https://rocket.chat).

## Requirements

 * Rocket.Chat 계정을 생성하고 당신의 server에 chat service를 업로드한다.[Rocket.Chat](https://open.rocket.chat/home) 
 * Personal Access Token을 생성하고 계정 설정에 값을 넣는다.


## Configuration

```yaml
connectors:
  rocketchat:
    # required
    user-id: "1ioKHDIOD"
    token: "zyxw-abdcefghi-12345"
    # optional
    bot-name: "mybot" # default "opsdroid"
    default-room: "random" # default "general"
    group: "MyAwesomeGroup" # default to None
    channel-url: "http://127.0.0.1" # defaults to https://open.rocket.chat
    update-interval: 5 # defaults to 1
```

_Notes:_

-	Opsdroid는 동시에 각 하나의 channel과 그룹과의 소통만 가능하다.
-	그룹은 private하다 
-	서버와의 통신에서 채널보다 우위에 있다.
-	채널의 이름은 #없이 더해진다.
-	Opsdroid는 메시지가 수신되면 계속해서 채팅서버와 소통을 진행한다. 당신은 이 소통 주기를 update-interval을 통해 설정이 가능하다. Opsdroid는 마지막으로 수신한 메시지만 읽기가 가능하다.



## Usage


```
FabioRosado Owner 6:11 PM
hi

opsdroid @FabioRosado Owner 6:11 PM
Hi FabioRosado
```

이 예는 개인의 계정으로 opsdroid와 Rocket.Chat을 통해서 소통한 것이다. hi라고 타이핑 했더라도 후에 사용자의 개인 이름이 붙게된다. 이는 연결성을 테스트하는 과정에서 붙게 되는 것이다. 이것은 당신으로 하여금 하나의 계정으로 opsdroid와 소통하고 bot-name이 계속해서 바뀔 것이다.
