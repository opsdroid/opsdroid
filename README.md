![opsdroid](https://github.com/opsdroid/style-guidelines/raw/master/logos/logo-wide-light.png)

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
