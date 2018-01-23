 ![opsdroid](https://github.com/opsdroid/style-guidelines/raw/master/logos/logo-wide-light.png)[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20opsdroid,%20an%20awesome%20open%20source%20chatbot%20framework%20written%20in%20Python.&url=https://opsdroid.github.io/&via=opsdroid&hashtags=chatbots,chatops,devops,automation,opensource)

[![Backers on Open Collective](https://opencollective.com/opsdroid/backers/badge.svg)](#backers) [![Sponsors on Open Collective](https://opencollective.com/opsdroid/sponsors/badge.svg)](#sponsors)
[![Build Status](https://travis-ci.org/opsdroid/opsdroid.svg?branch=release)](https://travis-ci.org/opsdroid/opsdroid) [![Build status](https://ci.appveyor.com/api/projects/status/9qodmi74r234x4cv/branch/master?svg=true)](https://ci.appveyor.com/project/jacobtomlinson/opsdroid/branch/master) [![codecov](https://codecov.io/gh/opsdroid/opsdroid/branch/master/graph/badge.svg)](https://codecov.io/gh/opsdroid/opsdroid) [![Updates](https://pyup.io/repos/github/opsdroid/opsdroid/shield.svg)](https://pyup.io/repos/github/opsdroid/opsdroid/) [![Dependency Status](https://dependencyci.com/github/opsdroid/opsdroid/badge)](https://dependencyci.com/github/opsdroid/opsdroid) [![Docker Image](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/opsdroid/opsdroid/) [![Docker Layers](https://images.microbadger.com/badges/image/opsdroid/opsdroid.svg)](https://microbadger.com/#/images/opsdroid/opsdroid) [![Documentation Status](https://readthedocs.org/projects/opsdroid/badge/?version=stable)](http://opsdroid.readthedocs.io/en/stable/?badge=stable) [![Gitter Badge](https://img.shields.io/badge/gitter-join%20chat-4fb896.svg)](https://gitter.im/opsdroid)

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

Check out the [Getting Started](https://www.youtube.com/watch?v=7wyIi_cpodE&list=PLViQCHlMbEq5nZL6VNrUxu--Of1uCpflq) video series on YouTube.

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


## Contributing

[Stickers for contributors!](https://medium.com/opsdroid/stickers-for-contributors-a0a1f9c30ec1)

Contributing to the opsdroid ecosystem is strongly encouraged and every little bit counts! You can do this by creating modules to be used by opsdroid or by contributing to the project itself.

All contributors to the project, including the project founder [jacobtomlinson](https://github.com/jacobtomlinson), contribute using the following process:

 * Fork the main project to your own account
 * Work on your changes on a feature branch
 * Create a pull request back to the main project
 * Tests and test coverage will be checked automatically
 * A project maintainer will review and merge the pull request

For more information see the [contribution documentation](http://opsdroid.readthedocs.io/en/latest/contributing/).

Do you need help? Do you want to chat? [Join our Gitter channel](https://gitter.im/opsdroid/)

-------

_\* databases are optional, however bot memory will not persist between different connectors or system reboots without one_

## Contributors

This project exists thanks to all the people who contribute. [[Contribute](CONTRIBUTING.md)].
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


