![opsdroid](https://github.com/opsdroid/style-guidelines/raw/master/logos/logo-wide-light.png)

[![Build Status](https://travis-ci.org/opsdroid/opsdroid.svg?branch=release)](https://travis-ci.org/opsdroid/opsdroid) [![Coverage Status](https://coveralls.io/repos/github/opsdroid/opsdroid/badge.svg?branch=release)](https://coveralls.io/github/opsdroid/opsdroid?branch=release) [![Updates](https://pyup.io/repos/github/opsdroid/opsdroid/shield.svg)](https://pyup.io/repos/github/opsdroid/opsdroid/) [![Dependency Status](https://dependencyci.com/github/opsdroid/opsdroid/badge)](https://dependencyci.com/github/opsdroid/opsdroid)
[![Docker Image](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/opsdroid/opsdroid/) [![Docker Layers](https://images.microbadger.com/badges/image/opsdroid/opsdroid.svg)](https://microbadger.com/#/images/opsdroid/opsdroid) [![Documentation Status](https://img.shields.io/badge/docs-latest-red.svg?style=flat)](http://opsdroid.readthedocs.io/en/latest/?badge=latest)


An open source python chat-ops bot framework.

## Quick start

```
pip3 install opsdroid
opsdroid
```

## Configuration

Configuration is done in a yaml file called `configuration.yaml`. This will be created automatically for you in `~/.opsdroid`. See the [full reference](http://opsdroid.readthedocs.io/en/latest/configuration-reference/).

Example config:

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

## Contributing

Contributing to the opsdroid ecosystem is strongly encouraged. You can do this by creating modules to be used by opsdroid or by contributing to the project itself.

All contributors to the project, including [jacobtomlinson](https://github.com/jacobtomlinson), contribute using the following process:

 * Fork the main project to your own account
 * Work on your changes on a feature branch
 * Create a pull request back to the main project
 * Tests and test coverage will be checked automatically
 * A project maintainer will review and merge the pull request

For more information see the [contribution documentation](http://opsdroid.readthedocs.io/en/latest/contributing/).
