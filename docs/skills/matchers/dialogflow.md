# Dialogflow

## Dialogflow Authentication

[Dialogflow](https://dialogflow.com/) is an NLP API for matching strings to [intents](https://cloud.google.com/dialogflow/docs/intents-overview) or [actions](https://cloud.google.com/dialogflow/docs/intents-actions-parameters). Intents are created on the Dialogflow website.

With version 2 of Dialogflow, you will need a service account - a Google account associated with your Google Cloud project. You will need to log into your Google Cloud Platform account and head to **Create service account key**, you can follow the steps in the official documentation - [Getting Started with Authentication](https://cloud.google.com/docs/authentication/getting-started).

Once you have your JSON file, you will need to place this file somewhere safe and add its path to an environment variable named **GOOGLE_APPLICATION_CREDENTIALS** (the official documentation explains how to do this as well). Once this is done you can start using the Dialogflow parser.

### Localization

If you use opsdroid in a language other than English, this parser will automatically grab the language code that you have set on your configuration.

If you want to run this parser in a different language you can overwrite the language configuration by adding the `lang` parameter on this parser configuration.

_Note: You need to add additional languages to be used with dialogflow, to do this you need to log into your [console](https://console.dialogflow.com) and under your bot name you can add additional languages._

## Configuring opsdroid

To use Dialogflow with opsdroid, you need to add it to your parsers list along with your project-id and set the correct authentication method as mentioned above.

You can also set a `min-score` option to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. The default for this is 0 which will match all messages.

```yaml

parsers:
  dialogflow:
    project-id: <your project id>  # Required
    min-score: 0.6 # optional
```

## Using the parser with a skill

Let's have a look at how you can use this parser and the `match_dialogflow_action` and `match_dialogflow_intent` decorators on a skill.

These decorator take one parameter (the name of the intent/action to match), any skill (function or class method) decorated with this matcher, will trigger that skill.

```yaml
prsers:
  dialogflow:
    project-id: <your project id>  # Required
    lang: 'pt'
```

This will make the parser to use the Portuguese language when matching the string to an intent or an action.

```eval_rst
.. autofunction:: opsdroid.matchers.match_dialogflow_action

.. autofunction:: opsdroid.matchers.match_dialogflow_intent
```


### Example 1

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_dialogflow_action

class MySkill(Skill):
  @match_dialogflow_action('mydomain.myaction')
  async def my_skill(self, message):
      await message.respond('An appropriate response!')
```

The above skill would be called on any intent which has an action of `'mydomain.myaction'`.

### Example 2

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_dialogflow_intent

class MySkill(Skill):
  @match_dialogflow_intent('myIntent')
  async def my_skill(self, message):
      await message.respond('An appropriate response!')
```

The above skill would be called on any intent which has a name of `'myIntent'`.

## Creating a Dialogflow bot

You can find a quick getting started with Dialogflow guide [here](https://cloud.google.com/dialogflow/docs/basics) and you can also follow the [quickstart guides](https://cloud.google.com/dialogflow/docs/quick/).

If you want to use Dialogflow in a different language other than English, all you need to do is specify the `lang` parameter in opsdroid's configuration. Then change/add another language to your Dialogflow agent in the Language tab of the agent settings.

_Useful Links: [Languages Reference](https://cloud.google.com/dialogflow/docs/reference/language), [Multi-language Agents Reference](https://cloud.google.com/dialogflow/docs/agents-multilingual)_

## Message object additional parameters

### `message.dialogflow`

Since version 2 Dialogflow will return a `google.cloud.dialogflow_v2.types.DetectIntentResponse` object when the API is called. This is a special object isn't iterable and subscriptable, so you will have to access each attribute by using dot notation like `message.dialogflow.query_text` to get the text that you just sent to dialogflow.

This object allows you to access any information from the matched intent including the queried text, action, reply, intent, confidence and language.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_dialogflow_action

class MySkill(Skill):
  @match_dialogflow_action('smalltalk.greetings')
  async def dump_response(self, message):
      print(message.dialogflow)
```

This example skill will print the following on the message "what's up?".

```
query_text: "what is up"
action: "smalltalk.greetings.whatsup"
parameters {
}
all_required_params_present: true
fulfillment_text: "Not much. What\'s new with you?"
fulfillment_messages {
  text {
    text: "Not much. What\'s new with you?"
  }
}
intent {
}
intent_detection_confidence: 1.0
language_code: "en"
```

If you want to access the text reply from dialogflow you would have to do it like this `message.dialogflow.fulfillment_text` which would give you `Not much. What\'s new with you?`

You can build your bot to get different replies and access different things depending on your actions and intents - this is the example of what you would get if you used the contact info action and asked opsdroid for the contact info:

```
query_text: "contact info"
action: "support.contacts"
parameters {
}
all_required_params_present: true
fulfillment_text: "Email us at support@example.com for any questions regarding our products and services."
fulfillment_messages {
text {
  text: "Email us at support@example.com for any questions regarding our products and services."
}
platform: SLACK
}
fulfillment_messages {
text {
  text: "Email us at support@example.com for any questions regarding our products and services."
}
}
intent {
name: "projects/test-ddd33/agent/intents/1bcf91d7-acdb-4583-abca-927d6efb0730"
display_name: "Contact us"
}
intent_detection_confidence: 1.0
language_code: "en"
```
