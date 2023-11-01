# Discord

A connector for [Discord](https://discord.com/developers/docs/).

## Requirements

**This connector requires access token.**

Follow the steps to get access token :

 - Visit https://discord.com/developers/applications
 - Create a new app
 - Once the app is created, go to app’s Settings, and under Bot, click on Add Bot. 
 - There you can reset your `token` to see it.
 - If you want to add your bot to a discord channel, go under OAuth2 then URL Generator. Click on the bot scope and choose the permissions you want. An URL will be generated and you can use it to add your bot to your channel.

## Configuration

```yaml
connectors:
  discord:
    # required
    token: mytoken
    # optional
    bot-name: "mybot" # default "opsdroid"
```


## Events Available

The Discord connector contains 3 events that you can access on your skills. It is possible to either send or receive these events.

```eval_rst
.. autoclass:: opsdroid.events.Message
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.File
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.Image
    :members:
```


## Skill examples

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.events import File, Image

class MySkill(Skill):

    @match_regex('file')
    async def file(self, message):
        with open('opsdroid.txt', 'rb') as f:
            file = File(file_bytes=f.read(), name="opsdroid.txt")
        await message.respond(file)
    
    @match_regex('image')
    async def image(self, message):
        with open('opsdroid.png', 'rb') as f:
            img = Image(file_bytes=f.read(), name="opsdroid.png")
        await message.respond(img)
```
