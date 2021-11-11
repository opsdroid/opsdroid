# Matrix

Matrix는 실시간 소통에 있어서 기본적인 보안방법이다. Opsdroid를 위한 Matrix connector는 대부분의 이벤트 송수신들을 담당한다.

## Requirements

이 Connector를 사용하기 위해서 다음이 필요하다.
-	Bot을 위한 matrix 계정 아이디 비밀번호가 필요하다.
-	당신의 home server를 알아야한다.[homeserver](https://matrix.org/faq/#what-is-a-homeserver%3F)
-	당신 room의 주소를 알아야한다.


## Configuration
간단한 configuration은 다음과 같다.

```yaml
connectors:
  matrix:
    # Required
    mxid: "@username:matrix.org"
    password: "mypassword"
    rooms:
      'main': '#matrix:matrix.org'
    # Optional
    homeserver: "https://matrix.org"
    nick: "Botty McBotface"  # The nick will be set on startup
```

Connector는 이름을 가진 방이라면 몇 개라도 구성할 수 있다. 첫번째 방의 이름은 무조건 “main”이어야 한다. Configuration options 사용 예제는 다음과 같다.


```yaml
connectors:
  matrix:
    # Required
    mxid: "@username:matrix.org"
    password: "mypassword"
    # A dictionary of rooms to connect to
    # One of these have to be named 'main'
    rooms:
      'main': '#matrix:matrix.org'
      'other': '#element-web:matrix.org'
    # Optional
    homeserver: "https://matrix.org"
    nick: "Botty McBotface"  # The nick will be set on startup
    room_specific_nicks: False  # Look up room specific nicknames of senders (expensive in large rooms)
    device_name: "opsdroid"
    enable_encryption: False
    device_id: "opsdroid" # A unique string to use as an ID for a persistent opsdroid device
    store_path: "path/to/store/" # Path to the directory where the matrix store will be saved
```


## End to End Encryption

E2EE를 사용하기 위해서 “olm” 라이브러리가 필요하다. Pip 설치로는 불가능하고 다음 링크에서 다운로드 가능하다. (https://gitlab.matrix.org/matrix-org/olm/) olm을 설치한 다음에는 opsdroid를 connector_matrix_e2e를 다운로드 해야한다. 이는 기본적으로 다운로드 되는 파일이 아니라 별도의 다운로드가 필요하다. 추가적으로 enable_encryption : True를 설정해야한다. 이 Connector는 E2EE를 지원한다.