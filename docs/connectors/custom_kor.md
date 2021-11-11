## Creating a custom connector

Connectors는 opsdroid Connector를 확장시켜주는 class이다. Connect, listen, respond 이 세가지 method가 존재한다. 기본 변수들은 __init__함수를 통해 사용할 수 있다. 해당 함수가 제공하는 기본 변수들이 모두 설정되어 있는지 확인해야한다.
#### configuration  (property)
Configuration 은 Connector class의 속성이다. Connector의 구성 변수를 접근하는데 사용된다. Configuration.yaml에서 Connector의 특정 매개변수를 검색할 수 있다.
#### connect
Connect는 특정한 대화 서비스에 연결하는 method이다.

### Methods

#### listen
각 메시지들은 모두 opsdriod Message object 포멧으로 변환되고 파싱된다. 무한루프를 방지함과 동시에 다음 메시지를 기다려 opsdroid와 함께 파싱해야 하기 때문에 await함수를 사용한다. Event loop를 허용함으로서 다른 메시지를 기다리는 동안 다른 함수들을 사용할 수 있게끔 한다.
#### user_typing
User_typing은 connector가 허락한 경우 ‘user is typing’ 이벤트 메시지를 출력한다. 이것을 이용해서 trigger 변수를 통해 이벤트 on/off를 boolean값으로 관리한다.
#### disconnect
Disconnect 말고도 upon shutdown이라는 disconnect 함수가 존재한다. Connector의 disconnect를 나타낸다.

### Handling Events

Opsdroid는 여러 종류의 송/수신 이벤트를 지원한다. Events documentation 파일을 통해서 여러 종류의 정보를 파악할 수 있다.

Connectors는 여러가지 송신 이벤트들을 opsdroid.connector.register_event decorator를 통해 implements할 수 있다. 이 decorator는 각기 다른 종류의 connector support의 method를 정의하는데 사용된다.

```python

@register_event(Message)
async def send(self, message):
    await myservice.send(message.text)

```

위 그림은 Connector.send가 Message object와 함께 불러오는 method이다. 이러한 종류의 method는 Connector가 지원하는 모든 이벤트를 정의할 수 있다.
```python

import time

# We recommend you use the official library
# for your chat service and import it here
import chatlibrary

# Import opsdroid dependencies
from opsdroid.connector import Connector, register_event
from opsdroid.events import Message


class MyConnector(Connector):

  def __init__(self, config, opsdroid):
    # Init the config for the connector
    self.name = "MyConnector" # The name of your connector
    self.config = config # The config dictionary to be accessed later
    self.default_target = "MyDefaultRoom" # The default room for messages to go
    self.opsdroid = opsdroid # An instance of opsdroid.core.

  async def connect(self, opsdroid):
    # Create connection object with chat library
    self.connection = await chatlibrary.connect()

  async def listen(self):
    # Listen for new messages from the chat service
    while True:
      # Get raw message from chat
      raw_message = await self.connection.get_next_message()

      # Convert to opsdroid Message object
      #
      # Message objects take a pointer to the connector to
      # allow the skills to call the respond method
      message = Message(raw_message.text, raw_message.user,
                        raw_message.room, self)

      # Parse the message with opsdroid
      await opsdroid.parse(message)

  @register_event(Message)
  async def send(self, message):
    # Send message.text back to the chat service
    await self.connection.send(message.text, message.user,
                               message.target)

  async def disconnect(self):
    # Disconnect from the chat service
    await self.connection.disconnect()

```

---
You might also be interested in reading the [configuration reference - Connector Modules](../configuration.html#connector-modules) in the documentation.
*If you need help or if you are unsure about something join our* [matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org) *and ask away! We are more than happy to help you.*
