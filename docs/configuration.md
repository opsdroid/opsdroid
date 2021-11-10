# Configuration

```eval_rst
.. contents::
```

## Config file

환경 설정을 위해, opsdroid는 `configuration.yaml`라는 하나의 YMAL 파일을 이용합니다. opsdroid를 실행할 때, 다음과 같은 순서로 파일을 찾을 것입니다:

- 로컬 `./configuration.yaml`
-  기본 사용자 데이터 위치:
    * Mac: `~/Library/Application Support/opsdroid`
    * Linux: `~/.local/share/opsdroid`
    * Windows: `C:\Documents and Settings\<User>\Application Data\Local Settings\opsdroid\opsdroid` or
                `C:\Documents and Settings\<User>\Application Data\opsdroid\opsdroid`
- System `/etc/opsdroid/configuration.yaml` (*nix only)

_참고: 만약 위 폴더들 중 하나에서 `configuration.yaml`라는 파일이 없으면, [example configuration file]에서 가져온 파일이 생성될 것입니다._(https://github.com/opsdroid/opsdroid/blob/master/opsdroid/configuration/example_configuration.yaml)

만약 기본 위치 중 하나를 사용중이라면, `opsdroid config edit`라는 명령어를 사용하여 (`EDITOR`라는 환경변수로 부터 가져온) 선호하는 에디터또는 기본 에디터 vim으로 설정 파일을 열 수 있습니다. 

opsdroid 프로젝트 자체는 매우 단순하고 기능을 제공하기위해 모듈을 요구합니다. 설정 파일 안에 사용하고 싶은 Connector, Skills 그리고 Database 모듈, 그리고 이것들이 요구하는 옵션을 지정해야 합니다.

**Connectors**는 특정 챗 서비스에 opsdroid를 연결하기위한 모듈들입니다.

**Skills**는 다른 채팅 메시지에 기반하여 opsdroid가 수행해야하는 행동을 정의하는 모듈들입니다.

**Database**모듈은 선택한 데이터베이스에 opsdroid를 연결하여 skills 모듈이 메시지 사이의 정보를 저장하도록 허용합니다.

예를 들어, 단순한 기본 설정파일은 다음과 같습니다:

```yaml
connectors:
  shell: {}

skills:
  hello: {}
```

이것은 opsdroid에게 공식 모둘 라이브러리에 내장된 [shell connector](https://github.com/opsdroid/connector-shell)와 [hello skill](https://github.com/opsdroid/skill-hello)을 사용하라고 말합니다.

opsdroid에서 모듈들은 처음 사용될 때 로컬에서 클론되는 깃 리포지토리가 될 수 있습니다. 기본적으로, 모듈의 위치를 정의하지 않으면, opsdroid는 먼저 코어에 내장되어 있는지 확인한 후 https://github.com/opsdroid/<moduletype>-<modulename>.git에서 리포지토리에 대해 확인할 것입니다. 따라서 위의 설정에서, connector-shell 모듈은 opsdroid.connector.shell에서 발견되며 hello skill은 GitHub의 opsdroid organization의 skill-hello 리포지토리에서 발견됩니다.
물론 모듈을 작성해서 opsdroid 설치를 통해 Github나 다른 리포지토리 호스트에서 사용 가능하도록 하는 것이 좋습니다 우리는 특히 사람들이 opsdroid 코어 패키지에 connector와 databases를 기여하길 바라고 있습니다.
더 고급적인 설정은 다음과 비슷할 것입니다:

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"

databases:
  mongo:
    host: "mymongohost.mycompany.com"
    port: "27017"
    database: "opsdroid"

skills:
  hello: {}
  seen: {}
  myawesomeskill:
    repo: "https://github.com/username/myawesomeskill.git"
```

이 설정에서, [slack connector](connectors/slack.md)을  [auth token](https://api.slack.com/tokens)에서 제공한 slack, 데이터 지속을 위한 내장된 monga 데이터베이스, 공식 리포지토리의 `hello`와 `seen` skills, 그리고 마지막으로 GitHub에서 호스팅한 커스텀 skill을 사용하고 있습니다.

slack 커넥터의 `token`과 mongo 데이터베이스의 `host`, `port`, `database` 옵션같은 설정 옵션은 모듈들마다 다릅니다. 사용하기 전에 각 모듈의 요구되는 설정 항목을 확인해주세요.

## Reference

### Connector Modules

Opsdroid는 즉시 사용 가능한 내장된 커넥터들과 같이 제공됩니다. 커넥터는 opsdroid를 특정 채팅 서비스에 연결하는 플러그인으로 설치되거나 내장되는 모듈입니다

내장 커넥터는 다음과 같습니다:

```eval_rst
.. toctree::
   :maxdepth: 2

   connectors/index
```

_참고: 시간이 지남에 따라 더 많은 커넥터들이 opsdroid 코어에 내장 커넥터로 추가 될 것입니다._
_커넥터의 Config 옵션 자체는 커넥터끼리 다르므로, 자세한 내용은 커넥터 문서를 보시길 바랍니다._

```yaml
connectors:

  slack:
    token: "mysecretslacktoken"

  matrix:
    mxid: "@username:matrix.org"
    password: "mypassword"
```

일부 커넥터는 실제 사용자를 시뮬레이션 하기위해 딜레이를 지정할 수 있도록 하므로, `configuration.yaml` 파일의 connector 밑에 딜레이 옵션을 추가하기만 하면 됩니다.

**Thinking Delay:** _x_초 회신을 늦추기 위해  _int_, _float_, _list_를 받아들입니다.
**Typing Delay:** _x_초 회신을 늦추기 위해  _int_, _float_, _list_를 받아들입니다. - 이 값은 opsdroid의 응답 텍스트의 길이로 계산되기 때문에 대기 시간이 가변적입니다.

예시:

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"
    thinking-delay: <int, float or two element list>
    typing-delay: <int, float or two element list>
```

_참고: 예상대로 opsdroid에 응답 시간이 지연을 일으키므로 높은 값을 넘기지 마세요._

커스텀 커넥터 설치를 위해 [module options](#module-options)를 확인하세요.

### Database Modules

Opsdroid는 즉시 사용 가능한 내장된 데이터베이스와 같이 제공됩니다. 데이터베이스는 opsdroid를 지속되는 데이터 저장공간 서비스에 연결하는 모듈들입니다.

Skills은 데이터를 opsdroid의 "memory"에 저장할 수 있으며, 외부 데이터베이스에 유지될 수 있는 딕셔너리 입니다.

내장된 데이터베이스는 다음과 같습니다:

```eval_rst
.. toctree::
   :maxdepth: 2

   databases/index
```

_데이터베이스의 Config 옵션 자체는 데이터베이스끼리 다르므로, 자세한 내용은 데이터베이스 문서를 보시길 바랍니다._

```yaml
databases:
  mongo:
    host: "mymongohost.mycompany.com"
    port: "27017"
    database: "opsdroid"
```

커스텀 데이터베이스 설치는 [module options](#module-options)을 확인하세요.

### Welcome-message

환영 메시지를 설정해보세요.

true로 설정하면 시작 시 환영 메시지가 로그에 출력됩니다. 기본값은 true입니다.

```yaml
welcome-message: true
```

### Logging

opsroid에 로깅을 설정해보세요.

`path` 설정은 opsdroid가 어디에 로그 파일을 작성할지 설정합니다. 이 위치는 반드시 opsdroid를 실행하고 있는 사용자에 의해 작성가능한 곳이어야 합니다. `false`로 설정하면 로그 파일 출력 기능을 비활성화 합니다.

_참고: 로그 경로 설정을 잊었으나 로깅이 활성화 되어 있다면, 기본 위치 중 하나가 사용될 것입니다._

모든 파이썬 로깅 레벨은 opsdroid에서 이용 가능합니다. `level`은 `debug`, `info`, `warning`, `error`, `critical`로 설정될 수 있습니다.

opsdroid가 로그를 콘솔에 기록하는것을 원하지 않을 수도 있는데, 예를 들면 shell connector를 사용하는 상황일 것입니다. 하지만 container에서 실행된다면 분명 원할 것입니다. `console` 을 `true` 나 `false`로 설정하면 로깅을 활성화하거나 비활성화 할 수 있습니다.

로그의 기본 위치는 다음과 같습니다:

- Mac: `/Users/<User>/Library/Logs/opsdroid`
- Linux: `/home/<User>/.cache/opsdroid/log`
- Windows: `C:\Users\<User>\AppData\Local\opsdroid\Logs\`

로그의 기본 경로중 하나를 사용하고 있다면, `opsdroid logs` 명령어를 실행하여 터미널에 로그를 출력할 수 있습니다.

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true

connectors:
  shell: {}

skills:
  hello: {}
  seen: {}
```

#### Optional logging arguments

opsdroid 로깅을 확장하기위해 선택적 매개변수를 로깅 설정에 넘길 수 있습니다.

##### Logs timestamp
가끔 로그가 일어날때 타임스탬프가 유용할 것입니다. `timestamp` boolean으로 활성화할 수 있습니다. 기본값은 False입니다.

```yaml
logging:
  level: info
  timestamp: true
```

*example:*
```shell
2020-12-02 10:39:51,255 INFO opsdroid.logging: ========================================                                 
2020-12-02 10:39:51,255 INFO opsdroid.logging: Started opsdroid v0.19.0+66.g8b839bc.dirty.                             
2020-12-02 10:39:51,255 INFO opsdroid: ========================================
```

##### Logs rotation
로그를 제어하기 위해 파일은 다시 되돌아가기 전 50MB까지 용량이 늘어날 것입니다. `file-size` 매개변수를 보내는 것으로 기본 값을 바꿀 수 있습니다.

```yaml
logging:
  level: info
  file-size: 100e6
```

이 예시는 0으로 되돌아가기 전 파일 사이즈를 100MB로 바꿀 것 입니다

##### extended mode

확장모드는 로그가 어디서 호출되었는지에 대한 함수나 메서드 이름을 포함할 것입니다.

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true
  extended: true
```

*예시:*
```shell
INFO opsdroid.logging.configure_logging(): ========================================
INFO opsdroid.logging.configure_logging(): Started opsdroid v0.14.1
```

##### Whitelist log names

화이트리스트를 설정하는 것으로 어떤 로그가 보여져야 할지 고를 수 있습니다. 만약 코어에 위치한 로그 파일만 원한다면 `opsdroid.core`를 화이트리스트로 하면 opsdroid는 이 파일의 로그만 보여줄 것입니다.

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true
  filter:
    whitelist:
      - "opsdroid.core"
      - "opsdroid.logging"
```

*예시:*
```shell
DEBUG opsdroid.core: Loaded 5 skills
DEBUG opsdroid.core: Adding database: DatabaseSqlite
```

_참고: 로그를 걸러내기 위해 확장모드를 사용할 수도 있습니다 - 이것은 로그를 다루는데 훨씬 더 큰 유연성을 허용할 것입니다._

##### Blacklist log names

한 가지만 제외한 모든 파일에서 로그를 가져오고 싶다면, 블랙리스트할 파일을 선택할 수 있고 opsdroid는 로그로부터 그 결과를 걸러낼 것입니다. 이것은 데이터베이스 안에 큰 프로젝트가 있다면 특히 중요합니다
```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true
  filter:
    blacklist:
      - "opsdroid.loader"
      - "aiosqlite"
```

*예시:*
```shell
INFO opsdroid.logging: ========================================
INFO opsdroid.logging: Started opsdroid v0.14.1+93.g3513177.dirty
INFO opsdroid: ========================================
INFO opsdroid: You can customise your opsdroid by modifying your configuration.yaml
INFO opsdroid: Read more at: http://opsdroid.readthedocs.io/#configuration
INFO opsdroid: Watch the Get Started Videos at: http://bit.ly/2fnC0Fh
INFO opsdroid: Install Opsdroid Desktop at:
https://github.com/opsdroid/opsdroid-desktop/releases
INFO opsdroid: ========================================
DEBUG asyncio: Using selector: KqueueSelector
DEBUG opsdroid.core: Loaded 5 skills
DEBUG root: Loaded hello module
WARNING opsdroid.core: <skill module>.setup() is deprecated and will be removed in a future release. Please use class-based skills instead.
DEBUG opsdroid.core: Adding database: DatabaseSqlite
DEBUG opsdroid.database.sqlite: Loaded sqlite database connector
INFO opsdroid.database.sqlite: Connected to sqlite /Users/fabiorosado/Library/Application Support/opsdroid/sqlite.db
DEBUG opsdroid-modules.connector.shell: Loaded shell connector
DEBUG opsdroid.connector.websocket: Starting Websocket connector
INFO opsdroid.connector.rocketchat: Connecting to Rocket.Chat
DEBUG opsdroid.connector.rocketchat: Connected to Rocket.Chat as FabioRosado
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
DEBUG opsdroid-modules.connector.shell: Connecting to shell
INFO opsdroid.web: Started web server on http://0.0.0.0:8080
```

_참고: 로그를 걸러내기 위해 확장모드를 사용할 수도 있습니다 - 이것은 로그를 다루는데 훨씬 더 큰 유연성을 허용할 것입니다._

##### Using both whitelist and blacklist filter
화이트리스트 필터와 블랙리스트 필터중 하나만 사용 가능합니다. 설정 파일에 둘 다 추가할 경우, 경고 메시지를 받을 것이며 화이트리스트 필터만 사용됩니다. 이 동작은 두 필터를 설정하면 `RuntimeError`에러가 발생하기 때문에 수행되었습니다 (_maximum recursion depth exceeded_).

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true
  filter:
    whitelist:
      - "opsdroid.core"
      - "opsdroid.logging"
      - "opsdroid.web"
    blacklist:
      - "opsdroid.loader"
      - "aiosqlite"
```

###### example

```shell
WARNING opsdroid.logging: Both whitelist and blacklist filters found in configuration. Only one can be used at a time - only the whitelist filter will be used.
INFO opsdroid.logging: ========================================
INFO opsdroid.logging: Started opsdroid v0.14.1+103.g122e010.dirty
DEBUG opsdroid.core: Loaded 5 skills
DEBUG root: Loaded hello module
WARNING opsdroid.core: <skill module>.setup() is deprecated and will be removed in a future release. Please use class-based skills instead.
DEBUG opsdroid.core: Adding database: DatabaseSqlite
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
INFO opsdroid.web: Started web server on http://0.0.0.0:8080
```

### Installation Path

skills를 설치할 때 opsdroid가 사용할 경로를 설정해주세요. 기본값은 현재 작업중인 디렉토리입니다.

```yaml
module-path: "/etc/opsdroid/modules"

connectors:
  shell: {}

skills:
  hello: {}
  seen: {}
```

### Parsers

opsdroid의 skills 작성 시, 함수에 맞게 메시지를 매칭해주는 다양한 parser를 사용할 수 있습니다.

_parser의 설정 옵션 자체는 parser마다 다릅니다. 자세한 사항은 parser/matcher 문서를 확인하세요._

```yaml
parsers:
  regex:
    enabled: true

# NLU parser
  rasanlu:
    url: http://localhost:5000
    project: opsdroid
    token: 85769fjoso084jd
    min-score: 0.8
    train: True
```

일부 parser는 opsdroid에게 0부터 1사이의 주어진 스코어보다 낮은 match들을 무시하도록 min-score를 지정할 수 있습니다. 단순히 configuration.yaml 파일의 parser 밑에 필요한 min-score를 추가하면 됩니다.

자세한 정보는 matchers 섹션을 확인하세요.

### Skills

Skill 모듈은 opsdroid에게 기능을 추가합니다.

_skills의 Config 옵션 자체는 skills끼리 다르므로, 자세한 내용은 skills 문서를 보시길 바랍니다._

```yaml
skills:
  hello: {}
  seen: {}
```

커스텀 skills 설치를 위해 [module options](#module-options)를 확인하세요.

### Time Zone

시간대를 설정하세요.

이 시간대는 crontab decorator에서 kwarg로 설정이 안되어있으면 crontab skills에서 사용될 것입니다. [tz database](https://www.iana.org/time-zones)의 모든 [timezone names](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)은 여기서 유효합니다.

```yaml
timezone: 'Europe/London'
```

### Language

Opsdroid를 사용하기 위해 언어를 설정하세요.

To use opsdroid with a different language other than English you can specify it in your configuration.yaml. 언어 코드는 [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)에서 표준화 되어있어야 합니다.

_참고: 언어가 지정되지 않으면, opsdroid는 기본값으로 영어를 사용할 것입니다._

```yaml
lang: <ISO 639-1 code -  example: 'en'>
```

### Web Server

opsroid에서 REST API를 설정하세요.

기본적으로, opsdroid는 웹서버를 포트 `8080` (혹은 SSL의 상세정보를 제공하는 경우 `8443`)으로 시작할 것입니다. 더 많은 정보는 [REST API docs](rest-api.md)에서 확인하세요.

```yaml
web:
  host: '0.0.0.0'
  port: 8080
  ssl:
    cert: /path/to/cert.pem
    key: /path/to/key.pem
```

## Module options

### Install Location

opsdroid의 모듈은 다양한 방법으로 설치가 가능합니다. 기본적으로 추가 옵션이 지정되지 않으면 opsdroid는 먼저 모듈이 opsdroid의 코어 라이브러리에 내장되어 있는지 확인하고 `https://github.com/opsdroid/<moduletype>-<modulename>.git`의 리포지토리를 확인할 것입니다. 

하지만 다른 위치로부터 모듈을 설치하고 싶다면 다음 옵션 중 하나를 지정할 수 있습니다.

#### Git Repository

모듈을 설치할 Git URL입니다.

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"
  mynewconnector:
    repo: https://github.com/username/myconnector.git
```

_Note: Git 리포지토리를 사용할 때, opsdroid는 시작할 때 fast forword strategy를 가져와서 업데이트를 시도할 것입니다.._

#### Local Directory

모듈을 설치할 로컬 경로입니다.

```yaml
skills:
  myawesomeskill:
    path: /home/me/src/opsdroid-skills/myawesomeskill
```

파일 하나를 지정할 수 있습니다.

```yaml
skills:
  myawesomeskill:
    path: /home/me/src/opsdroid-skills/myawesomeskill/myskill.py
```

또는 [IPython/Jupyter Notebook](http://jupyter.org/)에서.

```yaml
skills:
  myawesomeskill:
    path: /home/me/src/opsdroid-skills/myawesomeskill/myskill.ipynb
```

#### GitHub Gist

모듈을 다운로드하고 설치할 gist URL to download 입니다. 이것은 gist를 임시 파일로 다운로드하고 그 다음 위의 단일 파일 로컬 설치 프로그램을 사용합니다. 따라서 노트북 또한 지원됩니다.  


```yaml
skills:
 ping:
   gist: https://gist.github.com/jacobtomlinson/6dd35e0f62d6b779d3d0d140f338d3e5
```

또는 완전한 URL 없이 Gist ID를 지정할 수도 있습니다..

```yaml
skills:
 ping:
   gist: 6dd35e0f62d6b779d3d0d140f338d3e5
```

또한 모든 opsroid 모듈 생성을 건너뛰는 불러올 모듈 이름을 바로 지정하는 것도 가능합니다.

```yaml
skills:
 ping:
   module: 'module.to.import'
```

### Disable Caching

Set `no-cache` to true to generate the module whenever you start opsdroid.opsdroid를 시작할 때 마다 모듈을 생성하려면 `no-cache` 를 설정하세요. 로컬 `path`로 설정된 모듈의 기본값은 `true`일 것입니다.

```yaml
databases:
  mongodb:
    repo: https://github.com/username/mymongofork.git
    no-cache: true
```

### Disable dependency install

opsdroid의 매 시작마다 dependencies 설치를 건너뛰려면 `no-dep` 를 true로 설정하세요.

```yaml
skills:
  myawesomeskill:
    no-cache: true
    no-deps: true
```

_참고: skill을 개발할 때 이미 설치된 dependencies가 있으면 유용할 것입니다._

## Environment variables

환경 설정에서 환경변수를 사용할 수 있습니다. 값을 대신할 변수는 지정해줘야 합니다

```yaml
skills:
  myawesomeskill:
    somekey: $ENVIRONMENT_VARIABLE
```

_참고: 환경변수 이름은 대문자와 _(밑줄)로만 구성되어야 합니다. 값은 환경변수여야만 하며 현재는 문자열 내부에 환경 변수를 혼용할 수 없습니다._

## Validating modules

opsdroid는 두 가지 유형의 유효성 검사를 실행합니다:

-  `configuration.yaml`파일에 있는 기본 규칙 검증 (로깅, 웹, 모듈 경로, 환영 메시지)
- 모듈에 상수 `CONFIG_SCHEMA`이 설정되어있으면 각 모듈의 규칙을 검증합니다

_참고: 유효성 검사에 실패하면 opsdroid는 에러코드 1을 보내면서 종료됩니다._

상수를 설정하고 규칙을 더하는 것으로 커스텀 모듈에 규칙을 추가할 수 있습니다. `CONFIG_SCHEMA`변수는 예상 인수 및 타입을 전달하는 dictionary여야 합니다.

모듈/환경설정을 검증하기 위해 _voluptuous_ dependency를 사용하는데 이는 dependency에 의해 예상되는 특정 패턴을 따라야 한다는 겁니다.

- 필요한 값은 `voluptuous.Required()`으로 설정되어야 합니다
- 선택적 값은 `voluptuous.Optional()`으로 또는 없이 설정될 수 있습니다.

### Example

매트릭스 커넥터의 예를 들어봅시다. 모듈 안에 상수 `CONFIG_SCHEMA`를 일부 규칙과 함께 설정합니다:

```python
from voluptuous import Required

CONFIG_SCHEMA = {
    Required("mxid"): str,
    Required("password"): str,
    Required("rooms"): dict,
    "homeserver": str,
    "nick": str,
    "room_specific_nicks": bool,
    "device_name": str,
    "device_id": str,
    "store_path": str,
}
```

볼 수 있듯이 `mxid`, `password`,  `rooms`는 이 커넥터에 요구되는 필드이며 string이나 dictionary일 것으로 예상합니다.

값을 선택적으로 명시적으로 선언할 필요가 없기 때문에 예상되는 값과 타입만 쓸 수 있습니다.

_참고: 모듈이 상수를 포함하고 있지 않으면, 모듈이 로드는 되겠지만 환경 설정에서 발견되는 모든 잠재적 에러를 처리해야 합니다._

## HTTP proxy support

HTTP 프록시가 필요하다면 HTTP_PROXY와 HTTP_PROXY 환경 변수를 설정하세요.

## Migrate to new configuration layout

버전 0.17.0이 출시되었기 때문에 새로운 환경설정 레이아웃으로 마이그레이션 했습니다. 여러분의 환경 설정이 오래된 레이아웃을 사용한다면 환경 설정을 확인할 것이고 사용 중지 경고를 줄 것입니다.

### What changed

우리는`- name:  <module name>`패턴을 없애고 빈 줄 바로 아래에`<module name>: {}` 또는 `<module name>:` 패턴으로 대체했습니다.

이렇게 변경하면 각 모듈의 환경 설정을 들고 있는 딕셔너리들을 포함하는 리스트를 사용하는걸 멈출 수 있습니다
새 레이아웃에서, 키에 대한 모듈 이름과 딕셔너리 안의 추가적인 환경설정 파라미터를 키로 사용하는 딕셔너리를 리스트로 대체합니다.

### Example

예시로 slack 커넥터를 사용할 것입니다. 새 환경설정 레이아웃은 다음과같이 Slack 연결을 설정할 것입니다:

```yaml
connectors:
  slack:
    token: <API token>
```

다음과 같이 딕셔너리 형태로 표현될 수 있습니다:

```python
{
    'connectors': {
        'slack': {
            'token': <API token>
        }
    }
}
```

새 레이아웃에 대한 더 나은 파악을 위해 [example configuration file](https://github.com/opsdroid/opsdroid/blob/master/opsdroid/configuration/example_configuration.yaml)를 확인할 수 있습니다.

새 레이아웃을 마이그레이션 하는데 도움이 필요하면 [official matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org) 에서 연락 주시길 바랍니다
