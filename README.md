 ![opsdroid](https://github.com/opsdroid/style-guidelines/raw/master/logos/logo-wide-light.png)[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20opsdroid,%20an%20awesome%20open%20source%20chatbot%20framework%20written%20in%20Python.&url=https://opsdroid.github.io/&via=opsdroid&hashtags=chatbots,chatops,devops,automation,opensource)

[![Current version of pypi](https://img.shields.io/pypi/v/opsdroid.svg)](https://pypi.python.org/pypi)
[![Build Status](https://img.shields.io/travis/opsdroid/opsdroid/master.svg?logo=travis)](https://travis-ci.org/opsdroid/opsdroid)
[![Build status](https://img.shields.io/appveyor/ci/jacobtomlinson/opsdroid/master.svg?logo=appveyor)](https://ci.appveyor.com/project/jacobtomlinson/opsdroid/branch/master)
[![codecov](https://img.shields.io/codecov/c/github/opsdroid/opsdroid.svg)](https://codecov.io/gh/opsdroid/opsdroid)
[![BCH compliance](https://bettercodehub.com/edge/badge/opsdroid/opsdroid?branch=master)](https://bettercodehub.com/)
[![Updates](https://pyup.io/repos/github/opsdroid/opsdroid/shield.svg)](https://pyup.io/repos/github/opsdroid/opsdroid/)
[![Dependency Status](https://tidelift.com/badges/github/opsdroid/opsdroid?style=flat)](https://dependencyci.com/github/opsdroid/opsdroid)
[![Docker Build](https://img.shields.io/docker/build/opsdroid/opsdroid.svg)](https://hub.docker.com/r/opsdroid/opsdroid/builds/)
[![Docker Image](https://img.shields.io/microbadger/image-size/opsdroid/opsdroid.svg)](https://hub.docker.com/r/opsdroid/opsdroid/)
[![Docker Layers](https://img.shields.io/microbadger/layers/opsdroid/opsdroid.svg)](https://microbadger.com/#/images/opsdroid/opsdroid)
[![Documentation Status](https://img.shields.io/readthedocs/opsdroid/latest.svg)](http://opsdroid.readthedocs.io/en/stable/?badge=stable)
[![Gitter Badge](https://img.shields.io/badge/gitter-join%20chat-4fb896.svg)](https://gitter.im/opsdroid)
[![Backers on Open Collective](https://opencollective.com/opsdroid/backers/badge.svg)](#backers)
[![Sponsors on Open Collective](https://opencollective.com/opsdroid/sponsors/badge.svg)](#sponsors)
[![Open Source Helpers](https://www.codetriage.com/opsdroid/opsdroid/badges/users.svg)](https://www.codetriage.com/opsdroid/opsdroid)

An open source chat bot framework written in python. It is designed to be extendable, scalable and simple.

This application is designed to take messages from chat services and execute python functions (skills) based on their contents. Those functions can be anything you like, from simple conversational responses to running complex tasks. The true power of this project is to act as a glue library to bring the multitude of natural language APIs, chat services and third party APIs together.

## ChatOps
_"ChatOps is an operational paradigm where work that is already happening in the background today is brought into a common chatroom. By doing this, you are unifying the communication about what work should get done with actual history of the work being done."_ - [StackStorm](https://docs.stackstorm.com/chatops/chatops.html)

In the new frontier of DevOps it is becoming more and more popular to interact with your automation tools via an instant messenger. opsdroid is a framework to make creating and extending your ChatOps workflows powerful but simple.

## Why use opsdroid?

 * It's open source
 * Simple to modify and extend
 * Add your own skills in under 10 lines of python
 * Easy to install
 * Designed with Docker in mind for simple deployment
 * Configurable with a single YAML file
 * Can connect to multiple chat services simultaneously
 * No coding necessary if using the official modules

## Quick start

```
pip3 install opsdroid
opsdroid
```

## Installation

Check out the [Getting Started](https://www.youtube.com/watch?v=7wyIi_cpodE&list=PLViQCHlMbEq5nZL6VNrUxu--Of1uCpflq) video series on YouTube. The video series demonstrates how to install and configure opsdroid and opsdroid desktop on Ubuntu 16.04. It also demonstrates how to create your own skill in opsdroid

### Docker

```bash
# Pull the container image
docker pull opsdroid/opsdroid:latest

# Run the container
docker run --rm -it -v /path/to/configuration.yaml:/etc/opsdroid/configuration.yaml:ro opsdroid/opsdroid:latest
```

### Ubuntu 16.04 LTS

```bash
# Update apt-get
sudo apt-get update

# Install pip for python3 and locales
sudo apt-get install python3-pip language-pack-en git

# Enure pip is up-to-date
pip3 install --upgrade pip

# Install opsdroid
sudo pip3 install opsdroid

# Run opsdroid
opsdroid
```

## Usage

When running the `opsdroid` command with no arguments the bot framework will start using the configuration in `~/.opsdroid/configuration.yaml`. Beginners should check out the [introduction tutorial](http://opsdroid.readthedocs.io/en/stable/tutorials/introduction/) for information on how to configure opsdroid.

For information on arguments that you can pass to opsdroid run `opsdroid --help`.

```
$ opsdroid --help
Usage: opsdroid [OPTIONS]

  Opsdroid is a chat bot framework written in python.

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
  - Contribute to [opsdroid audio](https://github.com/opsdroid/opsdroid-audio) (python voice client for opsdroid)
  - Submit lots of useful issues (5–10 good ones is probably sticker worthy)
  - Create [logo variations and banners](https://github.com/opsdroid/style-guidelines) for promotion
  - Contribute to [opsdroid desktop](https://github.com/opsdroid/opsdroid-desktop) (electron and react app)
  - Promote opsdroid in a meaningful way

To get started see the [contribution guide](http://opsdroid.readthedocs.io/en/latest/contributing/).

Do you need help? Do you want to chat? [Join our Gitter channel](https://gitter.im/opsdroid/)

-------

_\* databases are optional, however bot memory will not persist between different connectors or system reboots without one_

## Contributors

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


