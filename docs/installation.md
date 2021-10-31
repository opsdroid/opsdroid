# Installation

```eval_rst
.. contents::
```

## Quickstart

```bash
$ pip3 install opsdroid[all]
$ opsdroid start
```

## Installation Methods

Check out the [Getting Started](https://www.youtube.com/watch?v=7wyIi_cpodE&list=PLViQCHlMbEq5nZL6VNrUxu--Of1uCpflq) video series on YouTube. The video series demonstrates how to install and configure opsdroid and opsdroid desktop on Ubuntu 16.04. It also demonstrates how to create your own skill in opsdroid.

### Ubuntu 16.04 LTS

```bash
# Update apt-get
$ sudo apt-get update

# Install pip for Python 3 and locales
$ sudo apt-get install python3-pip language-pack-en git

# Ensure pip is up-to-date
$ pip3 install --upgrade pip

# Install opsdroid
$ sudo pip3 install opsdroid[common]

# Run opsdroid
$ opsdroid start
```

### Windows 10

```
# Install Python from https://www.python.org/downloads/
# Launch powershell command prompt

# Install opsdroid
C:\Users\myaccount> pip install opsdroid[common]

# Create a starting configuration to work with
C:\Users\myaccount> opsdroid config gen | out-file "configuration.yaml" -encoding ascii

# Start opsdroid
C:\Users\myaccount> opsdroid start
```

### Selecting Modules

You can individually select modules to install dependencies for by specifying them
in the square brackets. For instance, to install the redis database and webex connector
module dependencies in addition to the opsdroid core package:
```
pip install opsdroid[database_redis,connector_webex]
```

`[common]` includes the matrix and slack connectors and sqlite database modules
You can also use `[all]`, `[all_connectors]`, `[all_databases]`, `[all_parsers]` and `[test]`.
Check out [this file](https://github.com/opsdroid/opsdroid/blob/master/setup.cfg#L79)
for a list of all the modules you can install this way.

### Docker Image

```bash
# Pull the container image
$ docker pull ghcr.io/opsdroid/opsdroid:latest

# Run the container
$ docker run --rm -it -v /path/to/config_folder:/home/opsdroid/.config/opsdroid ghcr.io/opsdroid/opsdroid:latest
```

The default docker image on Docker Hub contains all the module dependencies. To
specify modules, build the image using the Dockerfile and write them as before
in the build arg *EXTRAS* as follows **(Note the .)**:
```
$ docker build --build-arg EXTRAS=.[common] .
```

### Docker Service

```bash
# Create the opsdroid config file
$ docker config create OpsdroidConfig /path/to/configuration.yaml

# Create the service
$ docker service create --name opsdroid --config source=OpsdroidConfig,target=/home/opsdroid/.config/opsdroid/configuration.yaml --mount 'type=volume,src=OpsdroidData,dst=/home/opsdroid/.config/opsdroid' ghcr.io/opsdroid/opsdroid:latest
```

### Docker Swarm

```bash
# Create Directory Structure
├── config
│   ├── configuration.yaml
└── docker-compose.yml
```

```yaml
# docker-compose.yml
version: "3.5"

services:

  opsdroid:
    image: ghcr.io/opsdroid/opsdroid:latest
    networks:
      - opsdroid
    volumes:
      -  opsdroid:/home/opsdroid/.config/opsdroid
    configs:
      -  source: opsdroid_conf
         target: /home/opsdroid/.config/opsdroid/configuration.yaml
    deploy:
      restart_policy:
        condition: any
        delay: 10s
        max_attempts: 20
        window: 60s

networks:
  opsdroid:
    driver: overlay

configs:
  opsdroid_conf:
    file: ./config/configuration.yaml

volumes:
  opsdroid:
```

```bash
# Deploy to swarm
docker stack deploy --compose-file docker-compose.yml opsdroid
```
