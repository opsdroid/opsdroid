# Quickstart

Follow these quick steps to learn the basics and get up and running with Opsdroid.

## Terminology

There are a few terms you will need to be familiar with when using Opsdroid. Here is a quick overview of the
terms used in this document.

- **Connector** - A module to connect to a chat service like Slack.
- **Skill** - Skills are functions/classes that you write that get called when something specific happens in your chat service.
- **Matcher** - A trigger for your skill, like someone saying a phrase in the chat.

## Installation

As there is support for a wide range of connectors, all with their own set of dependencies, Opsdroid can be installed modularly. See the [installation docs](./installation.md) for details.

For now let's install everything.

```shell
$ pip install opsdroid[all]
```

## Configuration

Opsdroid is configured via a YAML file. This is where we specify which modules we want to use and pass them configuration options.

We can open the config in our default editor with `opsdroid config edit`.

When you open this for the first time you will see the default configuration. Let's delete everything and start with a minimal config (you can always view this default config with `opsdroid config gen`).

```yaml
connectors:
  slack:
    token: "MY API TOKEN"

skills:
  hello: {}
```

Here I have configured the [Slack connector module](./connectors/slack.md) and the included hello skill module. For information on configuring your preferred chat client see the [connector docs](./connectors/index.md).

You can find the full [configuration reference here](./configuration.md).

## Start opsdroid

Now we can run Opsdroid for the first time.

```shell
$ opsdroid start
INFO opsdroid.logging: ========================================
WARNING opsdroid.loader: No databases in configuration. This will cause skills which store things in memory to lose data when opsdroid is restarted.
INFO opsdroid.connector.slack: Connecting to Slack.
INFO opsdroid.connector.slack: Connected successfully.
INFO opsdroid.web: Started web server on http://0.0.0.0:8080
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
```

We can see here that Opsdroid has started and connected to Slack. So we should be able to head to Slack and say hello to our bot.

![I say hi and Opsdroid says hi back in Slack](https://i.imgur.com/kaW6yb1.png)

## Writing my own skill

Now that we have Opsdroid working let's write a simple skill. Skills are Python modules and can be created and configured in a few ways. For this example we will create a very simple single file skill.

### Skill code

Somewhere on your filesystem open a new Python file. I'm going to call mine `~/opsdroid/myskill.py`.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex


class PingSkill(Skill):

    @match_regex(r"ping")
    async def ping(self, event):
        await event.respond("pong")
```

In our file we have created a very simple skill. We start by importing the `Skill` base class and the `match_regex` matcher.

Then we create a new skill class with one async method called `ping`. Our method takes one argument which is the [event](./skills/events.md) that triggered
the skill.

To set our trigger we decorate that method with `match_regex`. This means that every message that comes from Slack will be compared with that [regular expression](https://en.wikipedia.org/wiki/Regular_expression), and if it is a match the method will be called.

We then respond to the event with the string `"pong"`. By sending a string here this will result in the bot sending a message back to Slack.

There are many [event types](./skills/events.md) which can be matched and responded with, and many more [complex matchers](./skills/matchers/index.md) for triggering skills.

### Configuration

We also need to add our new skill to our configuration. This time we specify the path because this is not a built-in skill.

```yaml
connectors:
  slack:
    token: "MY API TOKEN"

skills:
  hello: {}
  ping:
    path: ~/opsdroid/myskill.py
```

### Testing

Now we can start Opsdroid again and test our skill by saying "ping" in Slack.

```shell
$ opsdroid start
```

![I say ping, Opsdroid says pong in Slack](https://i.imgur.com/hVsWUTT.png)

## Next steps

Now that you know the basics you should check out the [project overview](./overview.md) to learn about how Opsdroid works and everything that it offers.

You can also try Opsdroid in the [Opsdroid Playground](https://playground.opsdroid.dev).
