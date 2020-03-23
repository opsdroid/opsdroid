# IBM Watson

[IBM Watson](https://www.ibm.com/watson) is an NLP API for matching strings to [intents](https://cloud.ibm.com/docs/services/assistant?topic=assistant-intents). Intents are created on your assistant intent page.

## Configuring opsdroid

To enable Watson skills, you must specify an `token`, an `assistant-id` and a `gateway` for your bot in the parsers section of the opsdroid configuration file.
You can find this information inside your Assistant Settings under the `API Details`. Note that depending on where your bot is located the gateway will be different, just use this. For example: `gateway-fra`.

You can also set a `min-score` option to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. The default for this is 0 which will match all messages.

```yaml

parsers:
  watson:
    gateway: 'gateway-fra' # Required
    token: XJF475SKGITJ98KHFO # Required
    assistant-id: '74yhfhis9-kfirj1e-jfir34-kfdir345' # Required
    min-score: 0.6
```

### Localization

If you want to use Watson in a different language you will have to create different intents and entities to handle the languages that you wish to support.

## Using the parser with a skill

In this example we have a Watson assistant set up with the default Customer Care Sample Skill - this will show you how you can get entities and replies from the assistant and include them with opsdroid.

```eval_rst
.. autofunction:: opsdroid.matchers.match_watson
```

### [Example 1](#example1)

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_watson
import logging

_LOGGER = logging.getLogger(__name__)

class MySkill(Skill):
    @match_watson('Customer_Care_Appointments')
    async def book_slot(self, message):
        """Book an appointment"""
        booking_date = message.entities['sys-date']['value'][0]
        booking_time = message.entities['sys-time']['value'][0]

        await message.respond("Done! Booked you for {} at {}".format(booking_date, booking_time))
```

The above skill would be called on any intent which has a name of `'Customer_Care_Appointment'`.

#### Usage example

> user: Book me an appointment for tomorrow at 11am
>
> opsdroid: Done! Booked you for 2019-10-12 at 11:00:00

This is the JSON response that opsdroid will get from this text:

```json
{
  "output": {
    "generic": [
      {
        "response_type": "text",
        "text": "Let me confirm: You want an appointment for Saturday at 11 AM. Is this correct?"
      }
    ],
    "intents": [
      {
        "intent": "Customer_Care_Appointments",
        "confidence": 0.9975103855133056
      }
    ],
    "entities": [
      {
        "entity": "sys-date",
        "location": [24, 40],
        "value": "2019-10-12",
        "confidence": 1,
        "metadata": {"calendar_type": "GREGORIAN", "timezone": "GMT"}
      },
      {
        "entity": "sys-time",
        "location": [24, 40],
        "value": "11:00:00",
        "confidence": 1,
        "metadata": {"calendar_type": "GREGORIAN", "timezone": "GMT"}}]}}
```

### [Example 2](#example2)

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_watson


class MySkill(Skill):
    @match_watson('Customer_Care_Appointments')
    async def book_slot(self, message):
        """Book an appointment"""
        reply = message.watson['output']['generic'][0]['text']


        await message.respond(reply)
```

_Note: This example uses the default intent `Customer_Care_Store_Hours` from the `Customer Care Sample Skill` pack to get opening hours of a store._

#### Usage example

> user: What time do you open?
>
> opsdroid: Our hours are Monday to Friday 10am to 8pm and Friday and Saturday 11am to 6pm.

This is the JSON response that opsdroid will get from this text:

```json
{
  "output": {
    "generic": [
      {
        "response_type": "text",
        "text": "Our hours are Monday to Friday 10am to 8pm and Friday and Saturday 11am to 6pm."
      }
    ],
    "intents": [
      {
        "intent": "Customer_Care_Store_Hours",
        "confidence": 0.972700834274292
      }
    ],
    "entities": []}}
```

## Creating a Watson App

You need to register on [IBM Watson website](https://www.ibm.com/), head over to the IBM Watson Assistant and create an assistant - you can call it whatever you like.

You can find a guide to get started with the IBM Watson on the [Getting Started With Watson Assistant guide](https://cloud.ibm.com/docs/services/assistant?topic=assistant-getting-started).


## Message object additional parameters

### `message.watson`

An http response object which has been returned by the Watson API. This allows you to access any information from the matched intent including other entities, intents, values, etc.


## Example Skill

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_watson

import json

class MySkill(Skill):
    @match_watson('hello')
    async def dumpResponse(self, message):
        print(json.dumps(message.watson))
```

### Return Value on "Hi"

The example skill will print the following on the message "Hi".

```json
{
   "output":{
      "generic":[
         {
            "response_type":"text",
            "text":"Hey hows it going?"
         }
      ],
      "intents":[
         {
            "intent":"hello",
            "confidence":1
         }
      ],
      "entities":[
         {
            "entity":"greetings",
            "location":[
               0,
               2
            ],
            "value":"hello",
            "confidence":1
         },
         {
            "entity":"greetings",
            "location":[
               0,
               2
            ],
            "value":"hi",
            "confidence":1
         }
      ]
   }
}
```
