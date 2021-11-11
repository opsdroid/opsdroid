# Mattermost connector

Mattermost를 위한 connector [Mattermost](https://mattermost.com/).

## Requirements

-	Mattermost 계정
-	Mattermost bot 계정(https://docs.mattermost.com/developer/bot-accounts.html).
  * Mattermost bot을 새로 생성한다.(https://docs.mattermost.com/developer/bot-accounts.html).
  * Bot Account Access Token”을 클릭해서 atoken을 발급 받는다.

## Configuration

```yaml
connectors:
  mattermost:
    # Required
    token: "zyxw-abdcefghi-12345"
    url: "mattermost.server.com"
    team-name: "myteam"
    # Optional
    scheme: "http" # default: https
    port: 8065 # default: 8065
    ssl-verify: false # default: true
    connect-timeout: 30 # default: 30
```

## Usage
Connector는 개인만으로는 opsdroid의 기능을 많이 끌어오지 못한다. Mattermost와 연결 되어도 사용자는 계속해서 opsdroid에 값을 넣으면서 진행 해야한다.
운이 좋게도 opsdroid는 몇몇 기능들이 존재한다. 당신이 opsdroid를 실행하면 이 기능들을 알 수 있다.
Opsdroid가 채팅방에서 활성화 되지 않으면 너는 상대방을 팀이나 채널로 초대가 가능하다.
당신은 opsdorid를 통해 직접 메시지를 주고 받을 수 있다. 그렇게 하기 위해서 opsdroid의 이르을 클릭하고 Message opsdroid에 해당하는 box에 정보를 적어넣으면 된다.

Example of a private message:

```
daniccan [9:06 PM]
hi

opsdroid APP [9:06 PM]
Hi daniccan
```

Connector 자체가 bot의 메시지를 파싱해주진 않는다.
