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

These endpoints are only available if you have [`command center`](command-center.md) enabled.

## `/connectors` _[GET]_

This method returns a list of all the connectors loaded in opsdroid and their respective configuration (sensitive parameters such as tokens are removed.)

**Example response**

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

## `/skills` _[GET]_

This method returns a list of all the skills loaded in opsdroid and their respective configuration (sensitive parameters such as tokens are removed.)

**Example response**

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
## `/databases` _[GET]_

This method returns a list of all the connectors loaded in opsdroid and their respective configuration (sensitive parameters such as tokens are removed.)

**Example response**

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

## `/parsers` _[GET]_

This method returns a list of all the connectors loaded in opsdroid and their respective configuration (sensitive parameters such as tokens are removed.)

**Example response**

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

## `/config` _[GET]_

This method returns the configuration that opsdroid was loaded with. Sensitive configuration parameters will not be shown.

**Example response**

```json
{
  "logging": {
    "level": "debug",
  },
  "welcome-message": true,
  "web": {
    "command-center": {
      "enabled": true
    },
  },
  "connectors": {
    "websocket": {
      "bot-name": "mybot",
      "max-connections": 10,
      "connection-timeout": 10
    }
  },
  "skills": {
    "dance": {},
    "hello": {},
    "loudnoises": {},
    "seen": {}
  }
}
```