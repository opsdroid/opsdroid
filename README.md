<p align=center>
<img src="https://github.com/opsdroid/style-guidelines/raw/master/logos/logo-wide-light.png"/>
<p>
 
<h4 align=center>An open source chat-ops bot framework</h4>

<p align=center><a href="https://pypi.python.org/pypi"><img src="https://img.shields.io/pypi/v/opsdroid.svg" alt="Current version of pypi" /></a>
<a href="https://travis-ci.org/opsdroid/opsdroid"><img src="https://img.shields.io/travis/opsdroid/opsdroid/master.svg?logo=travis" alt="Build Status" /></a>
<a href="https://ci.appveyor.com/project/opsdroid/opsdroid/branch/master"><img src="https://img.shields.io/appveyor/ci/opsdroid/opsdroid/master.svg?logo=appveyor" alt="Build status" /></a>
<a href="https://codecov.io/gh/opsdroid/opsdroid"><img src="https://img.shields.io/codecov/c/github/opsdroid/opsdroid.svg" alt="codecov" /></a>
<a href="https://bettercodehub.com/"><img src="https://bettercodehub.com/edge/badge/opsdroid/opsdroid?branch=master" alt="BCH compliance" /></a>
<a href="https://pyup.io/repos/github/opsdroid/opsdroid/"><img src="https://pyup.io/repos/github/opsdroid/opsdroid/shield.svg" alt="Updates" /></a>
<a href="https://hub.docker.com/r/opsdroid/opsdroid/builds/"><img src="https://img.shields.io/docker/build/opsdroid/opsdroid.svg" alt="Docker Build" /></a>
<a href="https://hub.docker.com/r/opsdroid/opsdroid/"><img src="https://img.shields.io/microbadger/image-size/opsdroid/opsdroid.svg" alt="Docker Image" /></a>
<a href="https://microbadger.com/#/images/opsdroid/opsdroid"><img src="https://img.shields.io/microbadger/layers/opsdroid/opsdroid.svg" alt="Docker Layers" /></a>
<a href="http://opsdroid.readthedocs.io/en/stable/?badge=stable"><img src="https://img.shields.io/readthedocs/opsdroid/latest.svg" alt="Documentation Status" /></a>
<a href="https://riot.im/app/#/room/#opsdroid-general:matrix.org"><img src="https://img.shields.io/matrix/opsdroid-general:matrix.org.svg?logo=matrix" alt="Matrix Chat" /></a>
<a href="https://gitter.im/opsdroid"><img src="https://img.shields.io/badge/gitter-join%20chat-4fb896.svg" alt="Gitter Badge" /></a>
<a href="#backers"><img src="https://opencollective.com/opsdroid/backers/badge.svg" alt="Backers on Open Collective" /></a>
<a href="#sponsors"><img src="https://opencollective.com/opsdroid/sponsors/badge.svg" alt="Sponsors on Open Collective" /></a>
<a href="https://www.codetriage.com/opsdroid/opsdroid"><img src="https://www.codetriage.com/opsdroid/opsdroid/badges/users.svg" alt="Open Source Helpers" /></a></p>


<p align="center">
  <a href="#chatops">ChatOps</a> •
  <a href="#why-use-opsdroid">Why use opsdroid?</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#installation-guide">Installation Guide</a> •
  <a href="#usage">Usage</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#backers">Backers</a> •
  <a href="#sponsors">Sponsers</a>
</p>

An open source chat bot framework written in Python. It is designed to be extendable, scalable and simple.

This application is designed to take messages from chat services and execute Python functions (skills) based on their contents. Those functions can be anything you like, from simple conversational responses to running complex tasks. The true power of this project is to act as a glue library to bring the multitude of natural language APIs, chat services and third party APIs together.

Help support opsdroid in one click by pressing [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20opsdroid,%20an%20awesome%20open%20source%20chatbot%20framework%20written%20in%20Python.&url=https://opsdroid.github.io/&via=opsdroid&hashtags=chatbots,chatops,devops,automation,opensource)

## ChatOps
_"ChatOps is an operational paradigm where work that is already happening in the background today is brought into a common chatroom. By doing this, you are unifying the communication about what work should get done with actual history of the work being done."_ - [StackStorm](https://docs.stackstorm.com/chatops/chatops.html)

In this new frontier of DevOps, it is becoming more and more popular to interact with your automation tools via an instant messenger. Opsdroid is a framework to make creating and extending your ChatOps workflows powerful but simple.

## Why use opsdroid?

 * It's open source
 * Simple to modify and extend
 * Add your own skills in under 10 lines of Python
 * Easy to install
 * Designed with Docker in mind for simple deployment
 * Configurable with a single YAML file
 * Can connect to multiple chat services simultaneously
 * No coding necessary if using the official modules

## Quick start

```bash
$ pip3 install opsdroid
$ opsdroid
```

## Installation Guide

Check out the [Getting Started](https://www.youtube.com/watch?v=7wyIi_cpodE&list=PLViQCHlMbEq5nZL6VNrUxu--Of1uCpflq) video series on YouTube. The video series demonstrates how to install and configure opsdroid and opsdroid desktop on Ubuntu 16.04. It also demonstrates how to create your own skill in opsdroid

### Docker Image

```bash
# Pull the container image
$ docker pull opsdroid/opsdroid:latest

# Run the container
$ docker run --rm -it -v /path/to/config_folder:/root/.config/opsdroid opsdroid/opsdroid:latest
```

### Docker Service

```bash
# Create the opsdroid config file
$ docker config create OpsdroidConfig /path/to/configuration.yaml

# Create the service
$ docker service create --name opsdroid --config source=OpsdroidConfig,target=/root/.config/opsdroid/configuration.yaml --mount 'type=volume,src=OpsdroidData,dst=/root/.config/opsdroid' opsdroid/opsdroid:latest
```

### Ubuntu 16.04 LTS

```bash
# Update apt-get
$ sudo apt-get update

# Install pip for Python3 and locales
$ sudo apt-get install python3-pip language-pack-en git

# Ensure pip is up-to-date
$ pip3 install --upgrade pip

# Install opsdroid
$ sudo pip3 install opsdroid

# Run opsdroid
$ opsdroid
```

## Usage

When running the `opsdroid` command with no arguments the bot framework will start using the configuration in `~/.opsdroid/configuration.yaml`. Beginners should check out the [introduction tutorial](http://opsdroid.readthedocs.io/en/stable/tutorials/introduction/) for information on how to configure opsdroid.

For information on arguments that you can pass to opsdroid run `opsdroid --help`.

```
$ opsdroid --help
Usage: opsdroid [OPTIONS]

  Opsdroid is a chat bot framework written in Python.

  It is designed to be extendable, scalable and simple. See
  https://opsdroid.github.io/ for more information.

Options:
  --gen-config          Print an example config and exit.
  -v, --version         Print the version and exit.
  -e, --edit-config     Edit configuration.yaml
  -l, --view-log        Open opsdroid logs
  --help                Show this message and exit.
```

## Contributing

Contributing to the opsdroid ecosystem is strongly encouraged and every little bit counts! We even send [sticker packs](https://medium.com/opsdroid/contributor-sticker-packs-738058ceda59) to our contributors to say thank you! There are so many ways to contribute to opsdroid:

  - Write code to [solve issues](https://github.com/opsdroid/opsdroid/issues) in the opsdroid core repository
  - Improve the [documentation](https://github.com/opsdroid/opsdroid/tree/master/docs) to help others get started
  - Write [skills](http://opsdroid.readthedocs.io/en/latest/extending/skills/), [connectors](http://opsdroid.readthedocs.io/en/latest/extending/connectors/) or [database](http://opsdroid.readthedocs.io/en/latest/extending/databases/) modules
  - Contribute to the [opsdroid home page](https://github.com/opsdroid/opsdroid.github.io) (it’s a Jekyll website)
  - Post about your experience using opsdroid on your own blog
  - Contribute to [opsdroid audio](https://github.com/opsdroid/opsdroid-audio) (Python voice client for opsdroid)
  - Submit lots of useful issues (5–10 good ones is probably sticker worthy)
  - Create [logo variations and banners](https://github.com/opsdroid/style-guidelines) for promotion
  - Contribute to [opsdroid desktop](https://github.com/opsdroid/opsdroid-desktop) (electron and react app)
  - Promote opsdroid in a meaningful way

**To get started see the [contribution guide](http://opsdroid.readthedocs.io/en/latest/contributing/).**

Do you need help? Do you want to chat? [Join our Gitter channel](https://gitter.im/opsdroid/)

-------

_\* databases are optional, however bot memory will not persist between different connectors or system reboots without one_

### Contributors

This project exists thanks to all the people who contribute. [[Contribute](/docs/contributing.md)].
<a href="graphs/contributors"><img src="https://opencollective.com/opsdroid/contributors.svg?width=890" /></a>


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
