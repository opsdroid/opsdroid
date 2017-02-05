# REST API

There is a RESTful API for opsdroid which by default is only accessible to `localhost` on port `8080`. See the [configuration reference](configuration-reference#web) for config options.

## Methods

### `/` _[GET]_

A test url you can use to check whether the API is running.

**Example response**

```json
{
  "timestamp": "2017-02-05T10:12:51.622981",
  "status": 200,
  "result": {
    "message": "Welcome to the opsdroid API"
  }
}
```

### `/stats/` _[GET]_

This method returns runtime statistics which could be useful in monitoring.

**Example response**

```json
{
  "timestamp": "2017-02-05T10:14:37.494541",
  "status": 200,
  "result": {
    "version": "0.6.0",
    "messages": {
      "total_parsed": 164,
      "webhooks_called": 28
    },
    "modules": {
      "skills": 13,
      "connectors": 1,
      "databases": 0
    }
  }
}
```

### `/skill/{skillname}/{webhookname}` _[POST]_

This method family will call skills which have been decorated with the [webhook matcher](parsers/webhook). The URI format includes the name of the skill from the `configuration.yaml` and the name of the webhook set in the decorator.

The response includes information on whether a skill was successfully triggered or not.

**Example response**

```json
{
  "timestamp": "2017-02-04T16:25:01.956323",
  "status": 200,
  "result": {
    "called_skill": "examplewebhookskill"
  }
}
```
