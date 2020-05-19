# Getting Started

## What is Opsdroid

Opsdroid is a framework to make creating and extending your ChatOps workflows powerful but simple. Opsdroid is a modular framework. It's event loop is power by the `asyncio` framework. The event loop starts with connectors, which allow Opsdroid to interface with services like Slack and Telegram, then Opsdroid sends the event to parsers and matchers, which will determine which skill to run.

## Installing Opsdroid

```bash
pip install opsdroid
```

For Windows and Docker installation, see the installation page.

## Using Opsdroid

### Configuration

As we mentioned earlier, Opsdroid is modular and built on a event loop. Connectors, parsers, and skills are setup in the `configuration.yaml` file, which is the backbone of any Opsdroid project.

First, we'll setup a shell connector. To do this add a list of connectors, then add shell.

```yaml
connectors:
  shell:
    bot-name: "mybot"
```

because `shell` prints to, well, the shell, let's disable logging

```yaml
logging:
  console: false
```

Next, we'll create a basic skill. We'll learn more about this later in the tutorial. Create a file called \_\_init\_\_.py, and import these libraries:

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
```

Then create a class that inherits from Skill like this:

```python
class HelloSkill(Skill):
    pass
```

After that, add a async `hello` function decorated with `@match_regex(r'hi')`. Essentially, this makes it so that if the user types "hi" this function runs. Let's add a response of "hey" like so:
```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class HelloSkill(Skill):
    @match_regex(r'hi')
    async def hello(self, message):
        await message.respond('Hey')
```
Then add your skill to you yaml file like this:

```yaml
skills:
  - name: exampleskill
    path: /path/to/my/example.py
    # Or /path/to/my/skill/ if you created a directory
    # with an __init__.py file in it
```
Amazing! You have created a bot! Run it with `opsdroid start`.
