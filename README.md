![opsdroid](https://github.com/opsdroid/style-guidelines/raw/master/logos/logo-wide-light.png)

[![Build Status](https://travis-ci.org/opsdroid/opsdroid.svg?branch=release)](https://travis-ci.org/opsdroid/opsdroid) [![Coverage Status](https://coveralls.io/repos/github/opsdroid/opsdroid/badge.svg?branch=release)](https://coveralls.io/github/opsdroid/opsdroid?branch=release) [![Updates](https://pyup.io/repos/github/opsdroid/opsdroid/shield.svg)](https://pyup.io/repos/github/opsdroid/opsdroid/) [![Dependency Status](https://dependencyci.com/github/opsdroid/opsdroid/badge)](https://dependencyci.com/github/opsdroid/opsdroid)
[![Docker Image](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/opsdroid/opsdroid/) [![Docker Layers](https://images.microbadger.com/badges/image/opsdroid/opsdroid.svg)](https://microbadger.com/#/images/opsdroid/opsdroid) [![Documentation Status](https://readthedocs.org/projects/opsdroid/badge/?version=stable)](http://opsdroid.readthedocs.io/en/stable/?badge=stable) [![Gitter Badge](https://badges.gitter.im/opsdroid.png)](https://gitter.im/opsdroid)

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
docker run --rm -v /path/to/configuration.yaml:/etc/opsdroid/configuration.yaml:ro opsdroid/opsdroid:latest
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

## Configuration

Configuration is done in a yaml file called `configuration.yaml`. When you run opsdroid it will look for the file in the following places in order:

 * `./configuration.yaml`
 * `~/.opsdroid/configuration.yaml`
 * `/etc/opsdroid/configuration.yaml`

If none are found then `~/.opsdroid/configuration.yaml` will be created for you.

See the [full reference](http://opsdroid.readthedocs.io/en/latest/configuration-reference/).

### Example config

```yaml
##                      _           _     _
##   ___  _ __  ___  __| |_ __ ___ (_) __| |
##  / _ \| '_ \/ __|/ _` | '__/ _ \| |/ _` |
## | (_) | |_) \__ \ (_| | | | (_) | | (_| |
##  \___/| .__/|___/\__,_|_|  \___/|_|\__,_|
##       |_|
##                   __ _
##   ___ ___  _ __  / _(_) __ _
##  / __/ _ \| '_ \| |_| |/ _` |
## | (_| (_) | | | |  _| | (_| |
##  \___\___/|_| |_|_| |_|\__, |
##                        |___/
##
## A default config file to use with opsdroid

## Set the logging level
# logging:
#   level: info
#   path: opsdroid.log
#   console: true

## Set the location for opsdroid to install modules
# module-path: "."

## Parsers
# parsers:
#   - name: regex
#     enabled: true
#
#   - name: crontab
#     enabled: true
#
#   - name: apiai
#     access-token: "youraccesstoken"
#     min-score: 0.6

## Connector modules
connectors:
  - name: shell

## Database modules (optional)
# databases:

## Skill modules
skills:

  ## Hello world (https://github.com/opsdroid/skill-hello)
  - name: hello

  ## Last seen (https://github.com/opsdroid/skill-seen)
  - name: seen

  ## Dance (https://github.com/opsdroid/skill-dance)
  - name: dance

  ## Loud noises (https://github.com/opsdroid/skill-loudnoises)
  - name: loudnoises

```

The opsdroid project itself is very simple and requires modules to give it functionality. In your configuration file you must specify the connector, skill and database* modules you wish to use and any options they may require.

**Connectors** are modules for connecting opsdroid to your specific chat service. **Skills** are modules which define what actions opsdroid should perform based on different chat messages. **Database** modules connect opsdroid to your chosen database and allows skills to store information between messages.

For example a simple barebones configuration would look like:

```yaml
connectors:
  - name: shell

skills:
  - name: hello
```

This tells opsdroid to use the [shell connector](https://github.com/opsdroid/connector-shell) and [hello skill](https://github.com/opsdroid/skill-hello) from the official module library.

In opsdroid all modules are git repositories which will be cloned locally the first time they are used. By default if you do not specify a repository opsdroid will look at `https://github.com/opsdroid/<moduletype>-<modulename>.git` for the repository. Therefore in the above configuration the `connector-shell` and `skill-hello` repositories were pulled from the opsdroid organisation on GitHub.

You are of course encouraged to write your own modules and make them available on GitHub or any other repository host which is accessible by your opsdroid installation.

A more advanced config would like similar to the following:

```yaml
connectors:
  - name: slack
    token: "mysecretslacktoken"

databases:
  - name: mongo
    host: "mymongohost.mycompany.com"
    port: "27017"
    database: "opsdroid"

skills:
  - name: hello
  - name: seen
  - name: myawesomeskill
    repo: "https://github.com/username/myawesomeskill.git"
```

In this configuration we are using the [slack connector](https://github.com/opsdroid/connector-slack) with a slack [auth token](https://api.slack.com/tokens) supplied, a [mongo database](https://github.com/opsdroid/database-mongo) connection for persisting data, `hello` and `seen` skills from the official repos and finally a custom skill hosted on GitHub.

Configuration options such as the `token` in the slack connector or the `host`, `port` and `database` options in the mongo database are specific to those modules. Ensure you check each module's required configuration items before you use them.

## Contributing

[Stickers for contributors!](https://medium.com/opsdroid/stickers-for-contributors-a0a1f9c30ec1)

Contributing to the opsdroid ecosystem is strongly encouraged. You can do this by creating modules to be used by opsdroid or by contributing to the project itself.

All contributors to the project, including [jacobtomlinson](https://github.com/jacobtomlinson), contribute using the following process:

 * Fork the main project to your own account
 * Work on your changes on a feature branch
 * Create a pull request back to the main project
 * Tests and test coverage will be checked automatically
 * A project maintainer will review and merge the pull request

For more information see the [contribution documentation](http://opsdroid.readthedocs.io/en/latest/contributing/).

-------

_\* databases are optional, however bot memory will not persist between different connectors or system reboots without one_
