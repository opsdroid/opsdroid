# REST API

There is a RESTful API for opsdroid accessible on port `8080`. See the [configuration reference](configuration-reference#web) for config options.

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

This method family will call skills which have been decorated with the [webhook matcher](parsers/webhook). The URI format includes the name of the skill from the `configuration.yaml` and the name of the webhook set in the decorator.

The response includes information on whether a skill was successfully triggered or not.

**Example response**

```json
{
  "called_skill": "examplewebhookskill"
}
```
