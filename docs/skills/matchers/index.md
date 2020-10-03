# Matchers

Matching is performed in multiple stages.

When opsdroid receives a `Message` event it is checked against all conversation matchers. All of the skills that match the message are then ranked in order of how confidently the parser understood the message. The most confident skill is then executed on the event.

```eval_rst
.. note::
   NLU parsers generally give back a confidence score that is provided by the statistical model that powers the NLU service. This makes skills easy to rank. However more simple parsers like regular expression and parse format use a more primitive method of checking length and complexity to try and provide a pseudo-confidence score. See each matcher's documentation for info on how it is scored.
```

After an event has been through the conversation matching stage we then also check the event against all non-chat matchers. These are matchers which are not related to conversation and therefore multiple skills can be matched to a message. This could be matching a specific event type (maybe we want to run some code every time we get a message) or perhaps the event was not a `Message` and therefore has a specific matcher like `match_crontab`.

**Conversation matchers**

```eval_rst
.. toctree::
   :titlesonly:
   :caption: Simple

   parse
   regex
```

```eval_rst
.. toctree::
   :titlesonly:
   :caption: Third party NLU

   dialogflow
   luis.ai
   rasanlu
   sapcai
   watson
   wit.ai
```

**Other matchers**

```eval_rst
.. toctree::
   :titlesonly:
   :caption: Non-chat

   always
   catchall
   crontab
   event
   webhook
```
