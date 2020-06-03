# Getting Started

```eval_rst
.. note::
    This tutorial is not complete. It will give you a basic understanding of opsdroid, but we are always improving it. If you see a mistake, please let us know.
```

## Installing Opsdroid

```bash
pip install opsdroid
```

For Windows and Docker installation, see the [installation page](https://docs.opsdroid.dev/en/stable/installation.html).

## Using Opsdroid

### Configuration

Opsdroid is modular and built on an event loop. Connectors, parsers, and skills are setup in the `configuration.yaml` file, which is the backbone of any Opsdroid project.

First, we'll setup a shell connector. To do this add a list of connectors to the configuration, then add shell. To see a list of avalible connectors, [check out this page](https://docs.opsdroid.dev/en/stable/connectors/index.html)

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

Next, we'll create a basic skill. We'll learn more about this later in the tutorial. Create a file called hello.py, and import these libraries:

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
    path: /path/to/my/hello.py
```

Amazing! You have created a bot! Run it with `opsdroid start`. You should then see a prompt which says `opsdroid >`. If you type `hi`, the bot will respond "Hey". Currently, we are working on adding more tutorials, including custom skills and matchers, additionally, check out the Examples section to learn more!
