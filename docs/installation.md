# Installation

```eval_rst
.. toctree::

   installation
```

## Quickstart

```bash
$ pip3 install opsdroid
$ opsdroid start
```

## Installation Methods

Check out the [Getting Started](https://www.youtube.com/watch?v=7wyIi_cpodE&list=PLViQCHlMbEq5nZL6VNrUxu--Of1uCpflq) video series on YouTube. The video series demonstrates how to install and configure opsdroid and opsdroid desktop on Ubuntu 16.04. It also demonstrates how to create your own skill in opsdroid

### Ubuntu 16.04 LTS

```bash
# Update apt-get
$ sudo apt-get update

# Install pip for Python 3 and locales
$ sudo apt-get install python3-pip language-pack-en git

# Ensure pip is up-to-date
$ pip3 install --upgrade pip

# Install opsdroid
$ sudo pip3 install opsdroid

# Run opsdroid
$ opsdroid start
```

### Windows 10

```powershell
# Install Python from https://www.python.org/downloads/
# Launch powershell command prompt

# Install opsdroid
C:\Users\myaccount> pip install opsdroid

# Create a starting configuration to work with
C:\Users\myaccount> opsdroid config gen | out-file "configuration.yaml" -encoding ascii

# Start opsdroid
C:\Users\myaccount> opsdroid start
```

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

### Docker Swarm ###

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
    image: opsdroid/opsdroid:latest
    networks:
      - opsdroid
    volumes:
      -  opsdroid:/root/.config/opsdroid
    configs:
      -  source: opsdroid_conf
         target: /root/.config/opsdroid/configuration.yaml
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
