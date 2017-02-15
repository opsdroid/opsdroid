![opsdroid](https://github.com/opsdroid/style-guidelines/raw/master/logos/logo-wide-light.png)

[![Build Status](https://travis-ci.org/opsdroid/opsdroid.svg?branch=release)](https://travis-ci.org/opsdroid/opsdroid) [![Coverage Status](https://coveralls.io/repos/github/opsdroid/opsdroid/badge.svg?branch=release)](https://coveralls.io/github/opsdroid/opsdroid?branch=release) [![Updates](https://pyup.io/repos/github/opsdroid/opsdroid/shield.svg)](https://pyup.io/repos/github/opsdroid/opsdroid/)
[![Docker Image](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/opsdroid/opsdroid/) [![Docker Layers](https://images.microbadger.com/badges/image/opsdroid/opsdroid.svg)](https://microbadger.com/#/images/opsdroid/opsdroid) [![Documentation Status](https://img.shields.io/badge/docs-latest-red.svg?style=flat)](http://opsdroid.readthedocs.io/en/latest/?badge=latest)


An open source python chat-ops bot

## Building

`docker build -t opsdroid/opsdroid:dev .`

`docker run --rm opsdroid/opsdroid:dev`

## Configuration

Configuration is done in a yaml file called `configuration.yaml`.

Example:

```yaml
logging: "debug"

connectors:
  - name: shell

skills:
  - name: hello
```

## Development

Run tests
`docker run --rm -ti -v $(pwd):/usr/src/app opsdroid/opsdroid:dev tox`
