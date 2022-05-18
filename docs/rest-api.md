# REST API

There is a RESTful API for opsdroid accessible on port `8080`. See the [configuration reference](configuration.md) for config options.

## Methods

### `/` _[GET]_

A test URL you can use to check whether the API is running.

**Example response**

```json
{
  "message": "Welcome to the opsdroid API"
}
```

### `/stats/` _[GET]_

This method returns runtime statistics which could be useful in monitoring.

**Example response**

```json
{
  "version": "0.6.0",
  "messages": {
    "total_parsed": 164,
    "webhooks_called": 28,
    "total_response_time": 0,
    "total_responses": 108,
    "average_response_time": 0.62794
  },
  "modules": {
    "skills": 13,
    "connectors": 1,
    "databases": 0
  }
}
```

### `/skill/{skillname}/{webhookname}` _[POST]_

This method family will call skills which have been decorated with the [webhook matcher](skills/matchers/webhook.md). The URI format includes the name of the skill from the `configuration.yaml` and the name of the webhook set in the decorator.

The response includes information on whether a skill was successfully triggered or not.

**Example response**

```json
{
  "called_skill": "examplewebhookskill"
}
```
## Command Center Methods

These endpoints are only available if you have `command center` enabled. To enable the command center you can add it to your configuration file.

```yaml
web:
  command-center:
    enabled: True
    # Required
    token: <your chosen token>
```

You must provide a token used to validate requests hitting the command center endpoints. It's highly recommended that you choose a strong token if opsdroid is exposed to the internet.

## `/connectors` _[GET]_ _[PATCH]_

The GET method returns a list of all the connectors loaded in opsdroid and their respective configuration (sensitive parameters such as tokens are removed.)

**Example response (GET)**

```json
{
  "websocket": {
    "name": "websocket",
    "module": "",
    "bot-name": "mybot",
    "max-connections": 10,
    "connection-timeout": 10,
    "type": "connector",
    "enabled": true,
    "entrypoint": null,
    "module_path": "opsdroid.connector.websocket",
    "install_path": "/Users/fabiorosado/Library/Application Support/opsdroid/opsdroid_modules/connector/websocket", 
    "branch": "master"
  }
}
```

The PATCH method allows you to update a connector configuration. You can also turn it off/on by setting `enabled` to `false`. Note that for the connector to be updated, Opsdroid will disconnect the connector and load all the configurations again.

**Example Request(PATCH)**

```python
import requests

 requests.patch(
   "http://localhost:8080/connectors", 
   json={
      "module_type": "connectors",
      "module_name": "shell",
      "config": {
          "enabled": false
        }
    }
)
```

## `/skills` _[GET]_ _[PATCH]_

The GET method returns a list of all the skills loaded in opsdroid and their respective configuration (sensitive parameters such as tokens are removed.)

**Example response (GET)**

```json
{
  "dance": {
    "name": "dance",
    "module": "",
    "type": "skill",
    "enabled": true,
    "entrypoint": null,
    "is_builtin": null,
    "module_path": "opsdroid_modules.skill.dance",
    "install_path": "/Users/fabiorosado/Library/Application Support/opsdroid/opsdroid_modules/skill/dance",
    "branch": "master"
  },
  "hello": {
    "name": "hello",
    "module": "",
    "type": "skill",
    "enabled": true,
    "entrypoint": null,
    "is_builtin": null,
    "module_path": "opsdroid_modules.skill.hello",
    "install_path": "/Users/fabiorosado/Library/Application Support/opsdroid/opsdroid_modules/skill/hello",
    "branch": "master"
  },
  "loudnoises": {
    "name": "loudnoises",
    "module": "",
    "type": "skill",
    "enabled": true,
    "entrypoint": null,
    "is_builtin": null,
    "module_path": "opsdroid_modules.skill.loudnoises",
    "install_path": "/Users/fabiorosado/Library/Application Support/opsdroid/opsdroid_modules/skill/loudnoises",
    "branch": "master"
  },
  "seen": {
    "name": "seen",
    "module": "",
    "type": "skill",
    "enabled": true,
    "entrypoint": null,
    "is_builtin": null,
    "module_path": "opsdroid_modules.skill.seen",
    "install_path": "/Users/fabiorosado/Library/Application Support/opsdroid/opsdroid_modules/skill/seen",
    "branch": "master"
  }
}
```

The PATCH method allows you to update a skill configuration. You can also turn it off/on by setting `enabled` to `false`. Note that for the skill to be updated, Opsdroid will disconnect the connector and load all the configurations again.

**Example Request(PATCH)**

```python
import requests

 requests.patch(
   "http://localhost:8080/skills", 
   json={
      "module_type": "skills",
      "module_name": "seen",
      "config": {
          "enabled": false
        }
    }
)
```

## `/databases` _[GET]_ _[PATCH]_

This method returns a list of all the connectors loaded in opsdroid and their respective configuration (sensitive parameters such as tokens are removed.)

**Example response (GET)**

```json
{
  "sqlite": {
    "name": "sqlite",
    "module": "",
    "type": "database",
    "enabled": true,
    "entrypoint": null,
    "module_path": "opsdroid.database.sqlite",
    "install_path": "/Users/fabiorosado/Library/Application Support/opsdroid/opsdroid_modules/database/sqlite",
    "branch": "master"
  }
}
```

The PATCH method allows you to update a database configuration. You can also turn it off/on by setting `enabled` to `false`. Note that Opsdroid will stop all the modules and load the whole configuration for the database to be updated.

**Example Request(PATCH)**

```python
import requests

 requests.patch(
   "http://localhost:8080/databases", 
   json={
      "module_type": "databases",
      "module_name": "sqlite",
      "config": {
          "enabled": false
        }
    }
)
```

## `/parsers` _[GET]_ _[PATCH]_

The GET method returns a list of all the connectors loaded in opsdroid and their respective configuration (sensitive parameters such as tokens are removed.)

**Example response (GET)**

```json
{
  "regex": {
    "name": "regex",
    "module": "",
    "type": "parsers",
    "enabled": true,
    "entrypoint": null,
    "module_path": "opsdroid.parsers.regex",
    "install_path": "/Users/fabiorosado/Library/Application Support/opsdroid/opsdroid_modules/parsers/regex",
    "branch": "master"
  },
  "crontab": {
    "name": "crontab",
    "module": "",
    "enabled": false,
    "type": "parsers",
    "entrypoint": null,
    "module_path": "opsdroid.parsers.crontab",
    "install_path": "/Users/fabiorosado/Library/Application Support/opsdroid/opsdroid_modules/parsers/crontab",
    "branch": "master"
  }
}
```

The PATCH method allows you to update a parser configuration. You can also turn it off/on by setting `enabled` to `false`. Note that for the parser to be updated, Opsdroid will stop all the modules and load the whole configuration again.

**Example Request(PATCH)**

```python
import requests

requests.patch(
  "http://localhost:8080/parsers", 
    json={
      "module_type": "parsers",
      "module_name": "crontab",
      "config": {
          "enabled": false
        }
    }
  )
```