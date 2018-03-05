# Getting started

This first part of the tutorial will give a brief introduction to the yaml files, explain some basic things about opsdroid configuration, connectors, parsers and what to expect on the first run of opsdroid.

If you need any help to get started with opsdroid or if you just want to chat, make sure to join our [Gitter channel.](https://gitter.im/opsdroid/)



## Configuration and Yaml files
The configuration of opsdroid is done in a yaml file called `configuration.yaml`.  When you run opsdroid it will look for the file in the following places in order:

- `./configuration.yaml`
-  `~/.opsdroid/configuration.yaml`
- `/etc/opsdroid/configuration.yaml`

_note: if no configuration file is found then opsdroid will use the `example_configuration.yaml` and place it in `~/.opsdroid/configuration.yaml`_



Using a single yaml file for every configuration of opsdroid makes things easier and effortless when configuring our bot.

Yaml files use a key-value structure and there are a few things you must take into consideration while using yaml:

- indentation is very important
- use spaces instead of tabs
- anything after a hash is a comment
- a value before a colon is a key
- a value with a dash is part of a list

### example
```yaml
## Skill modules
skills:

  ## Hello world (https://github.com/opsdroid/skill-hello)
  - name: hello

  ## Last seen (https://github.com/opsdroid/skill-seen)
  - name: seen

  ## Dance (https://github.com/opsdroid/skill-dance)
  - name: dance

  ## Loud noises (https://github.com/opsdroid/skill-loudnoises)
  - name: loudnoises
```
_note: we use two spaces indentation before using `-name: <skillname>`_

This part of the configuration will be represented as:

```python
{'skills': [{'name': 'hello'}, {'name': 'seen'}, {'name': 'dance'}, {'name': 'loudnoises']}
```
As you can see, anything starting with a hash was ignored and the key skills contain a list of dictionaries with the value `{'name':<skillname>}`

_note: The keys: [type, module_path, install_path, branch] are added to every skill when the configuration.yaml is loaded._


## Connectors, skills and Databases
**Connectors** are modules for connecting opsdroid to your specific chat service.
**Skills** are modules which define what actions opsdroid should perform based on different chat messages.
**Database** modules connect opsdroid to your chosen database and allow skills to store information between messages.


For example, a simple barebones configuration would look like:

```yaml
connectors:
  - name: shell

skills:
  - name: hello
```

This tells opsdroid to use the [shell connector](https://github.com/opsdroid/connector-shell) and [hello skill](https://github.com/opsdroid/skill-hello) from the official module library.

In opsdroid all modules are git repositories which will be cloned locally the first time they are used. By default, if you do not specify a repository opsdroid will look at `https://github.com/opsdroid/<moduletype>-<modulename>.git` for the repository. Therefore in the above configuration, the `connector-shell` and `skill-hello` repositories were pulled from the opsdroid organisation on GitHub.

You are of course encouraged to write your own modules and make them available on GitHub or any other repository host which is accessible by your opsdroid installation.

A more advanced config would like similar to the following:

```yaml
connectors:
  - name: slack
    token: "mysecretslacktoken"

databases:
  - name: mongo
    host: "mymongohost.mycompany.com"
    port: "27017"
    database: "opsdroid"

skills:
  - name: hello
  - name: seen
  - name: myawesomeskill
    repo: "https://github.com/username/myawesomeskill.git"
```

In this configuration we are using the [slack connector](https://github.com/opsdroid/connector-slack) with a slack [auth token](https://api.slack.com/tokens) supplied, a [mongo database](https://github.com/opsdroid/database-mongo) connection for persisting data, `hello` and `seen` skills from the official repos and finally a custom skill hosted on GitHub.

Configuration options such as the `token` in the slack connector or the `host`, `port` and `database` options in the mongo database are specific to those modules. Ensure you check each module's required configuration items before you use them.

## Asynchronous functions(Asyncio)
In a standard sequential program, all the instructions you send to the interpreter will be executed one by one. It is easy to visualize and predict the output of such a code. But let’s say you have a script that requests data from 3 different servers. Sometimes the request to one of those servers may take unexpectedly too much time to execute. Imagine that it takes 10 seconds to get data from the second server. While you are waiting, the whole script is actually doing nothing.

What if you could write a script that, instead of waiting for the second request, simply skip it and start executing the third request, then go back to the second one, and proceed from where it left off? That’s the nature of an asynchronous program. You minimize idle time by switching tasks.

An asynchronous function in Python is typically called a 'coroutine', which is just a function that uses the async keyword. The function below would work as an asynchronous function:

```
async def ping_server(ip):  
    pass

```
To actually call these asynchronous functions, we use the `await` keyword:
```
async def ping_local():  
    return await ping_server('192.168.1.1')
```
The await keyword must be used within another function (typically an asyncio function). Otherwise, it will result in a syntax error.

## Matchers available
Matchers are used to match a message, sent by a user, to a connector and a skill. Opsdroid comes ready with 8 different matchers, each one of them has its own settings and specification.

- Basic matcher
  - [Regular Expressions](/matchers/regex.md)
- NPL Matchers
  - [Dialogflow(previous Api.ai)](/matchers/dialogflow.md)
  - [Wit.ai](/matchers/wit.ai.md)
  - [Lui.ai](/matchers/luis.ai.md)
- Special Matcher
  - [Always](/matchers/always.md)
  - [Crontab](/matchers/crontab.md)
  - [Webhook](/matchers/webhook.md)

Read the [Matchers overview page](matchers/overview) for a quick reference guide on how to use them.


## First run - Skills available
The opsdroid project itself is very simple and requires modules to give it functionality.  So, when you run opsdroid for the first time only 4 skills (hello, seen, dance and loudnoises) are available. What means that opsdroid won't do much yet.

To expand opsdroid functionality you need to make some changes in your configuration file. You must specify the connector, skill and database* modules you wish to use and any options they may require.

The ` example_configuration.yaml`  contains all the official modules to help you shape opsdroid to your liking. Simply uncomment(remove the #) the modules that you wish to use, provide any required options and everything should work just fine.

_Note: Spacing might be off when uncommenting modules, make sure to check your indentation before running opsdroid. Opsdroid won't start if indentation is off._


## Expanding opsdroid functionality
Now that you have the basics of how opsdroid works, you can see how skills can empower opsdroid. You can make opsdroid work with pretty much everything, But how do you make a new skill for opsdroid to use?

You probably noticed the demo on [opsdroid main page](https://opsdroid.github.io) in which opsdroid seems to have a conversation with a user. At the moment opsdroid can only reply to a few commands (hello, goodbye, dancing, etc).


The next step in the tutorial will teach you how to make your opsdroid reply to the message "how are you", just like you seen on the main page.

---
<p style="text-align: right;">Write your first skill > </p>

---

