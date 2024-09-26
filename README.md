<h6 align=center>
<img src="https://github.com/opsdroid/style-guidelines/raw/master/logos/logo-wide-light.png" alt="Opsdroid Logo"/>
</h6>

<h4 align=center>An open source chat-ops bot framework</h4>

<p align=center>
<a href="https://pypi.python.org/pypi"><img src="https://img.shields.io/pypi/v/opsdroid.svg" alt="Current version of pypi" /></a>
<a href="https://github.com/opsdroid/opsdroid/actions"><img src="https://github.com/opsdroid/opsdroid/workflows/CI/badge.svg?event=push&branch=master" alt="Github CI Status"></img></a>
<a href="https://codecov.io/gh/opsdroid/opsdroid"><img src="https://img.shields.io/codecov/c/github/opsdroid/opsdroid.svg" alt="codecov" /></a>
<a href="https://bettercodehub.com/"><img src="https://bettercodehub.com/edge/badge/opsdroid/opsdroid?branch=master" alt="BCH compliance" /></a>
<a href="https://hub.docker.com/r/opsdroid/opsdroid/builds/"><img src="https://img.shields.io/docker/build/opsdroid/opsdroid.svg" alt="Docker Build" /></a>
<a href="https://hub.docker.com/r/opsdroid/opsdroid/builds/"><img alt="Docker Image Size (latest by date)" src="https://img.shields.io/docker/image-size/opsdroid/opsdroid?label=image%20size"></a><a href="https://microbadger.com/#/images/opsdroid/opsdroid"><img src="https://img.shields.io/microbadger/layers/opsdroid/opsdroid.svg" alt="Docker Layers" /></a>
<a href="http://opsdroid.readthedocs.io/en/stable/?badge=stable"><img src="https://img.shields.io/readthedocs/opsdroid/latest.svg" alt="Documentation Status" /></a>
<a href="https://app.element.io/#/room/#opsdroid-general:matrix.org"><img src="https://img.shields.io/matrix/opsdroid-general:matrix.org.svg?logo=matrix" alt="Matrix Chat" /></a>
<a href="#backers"><img src="https://opencollective.com/opsdroid/backers/badge.svg" alt="Backers on Open Collective" /></a>
<a href="#sponsors"><img src="https://opencollective.com/opsdroid/sponsors/badge.svg" alt="Sponsors on Open Collective" /></a>
<a href="https://www.codetriage.com/opsdroid/opsdroid"><img src="https://www.codetriage.com/opsdroid/opsdroid/badges/users.svg" alt="Open Source Helpers" /></a>
</p>

---

<p align="center">
  <a href="https://docs.opsdroid.dev/en/stable/quickstart.html">Quick Start</a> •
  <a href="https://docs.opsdroid.dev">Documentation</a> •
  <a href="https://playground.opsdroid.dev">Playground</a> •
  <a href="https://medium.com/opsdroid">Blog</a> •
  <a href="https://app.element.io/#/room/#opsdroid-general:matrix.org">Community</a>
</p>

---

An open source chatbot framework written in Python. It is designed to be extendable, scalable and simple.

This framework is designed to take events from chat services and other sources and execute Python functions (skills) based on their contents. Those functions can be anything you like, from simple conversational responses to running complex tasks. The true power of this project is to act as a glue library to bring the multitude of natural language APIs, chat services and third-party APIs together.

See [our full documentation](https://docs.opsdroid.dev) to get started.
## Quick Start

### Installation

Install Opsdroid with all dependencies:

```bash
pip install opsdroid[all]
```

For more specific installations, refer to the [installation docs](https://docs.opsdroid.dev/en/stable/installation/).

### Configuration

Opsdroid uses a YAML file for configuration. Create or edit the config file:

```bash
opsdroid config edit
```

Minimal configuration example:

```yaml
connectors:
  slack:
    token: "YOUR_SLACK_API_TOKEN"

skills:
  hello: {}
```

### Running Opsdroid

Start Opsdroid with:

```bash
opsdroid start
```

## Key Concepts

- **Connector**: A module that connects Opsdroid to a chat service (e.g., Slack).
- **Skill**: Functions or classes that define bot behaviors triggered by specific events.
- **Matcher**: A trigger for skills, such as a specific phrase in the chat.

## Creating a Custom Skill

1. Create a new Python file (e.g., `myskill.py`):

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class PingSkill(Skill):
    @match_regex(r"ping")
    async def ping(self, event):
        await event.respond("pong")
```

2. Add the skill to your configuration:

```yaml
skills:
  hello: {}
  ping:
    path: ~/opsdroid/myskill.py
```

## Next Steps

- Explore the [project overview](https://docs.opsdroid.dev/en/stable/overview.html) to learn more about Opsdroid's features.
- Try Opsdroid in the [Opsdroid Playground](https://playground.opsdroid.dev/).
- Check out the [documentation](https://docs.opsdroid.dev/) for detailed information on skills, connectors, and databases.

## Contributing

Contributions to Opsdroid are welcome! Please refer to the [contributing guidelines](https://docs.opsdroid.dev/en/stable/contributing/) for more information.

## Contributors

This project exists thanks to all the people who contribute. [[Contribute](https://docs.opsdroid.dev/en/stable/contributing/)].
<a href="https://github.com/opsdroid/opsdroid/graphs/contributors"><img src="https://opencollective.com/opsdroid/contributors.svg?width=890" /></a>

## Backers

Thank you to all our backers! 🙏 [[Become a backer](https://opencollective.com/opsdroid#backer)]

<a href="https://opencollective.com/opsdroid#backers" target="_blank"><img src="https://opencollective.com/opsdroid/backers.svg?width=890"></a>

## Sponsors

Support this project by becoming a sponsor. Your logo will show up here with a link to your website. [[Become a sponsor](https://opencollective.com/opsdroid#sponsor)]

<a href="https://opencollective.com/opsdroid/sponsor/0/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/0/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/1/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/1/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/2/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/2/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/3/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/3/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/4/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/4/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/5/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/5/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/6/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/6/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/7/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/7/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/8/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/8/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/9/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/9/avatar.svg"></a>
