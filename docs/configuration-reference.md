# Configuration reference

**Quick Links:**

- [Configuration reference](#configuration-reference)
  - [Config file](#config-file)
  - [Reference](#reference)
    - [Connector Modules](#connector-modules)
    - [Database Modules](#database-modules)
    - [Welcome-message](#welcome-message)
    - [Logging](#logging)
      - [Optional logging arguments](#optional-logging-arguments)
        - [extended mode](#extended-mode)
        - [Whitelist log names](#whitelist-log-names)
        - [Blacklist log names](#blacklist-log-names)
        - [Using both whitelist and blacklist filter](#using-both-whitelist-and-blacklist-filter)
    - [Installation Path](#installation-path)
    - [Parsers](#parsers)
    - [Skills](#skills)
    - [Time Zone](#time-zone)
    - [Language](#language)
    - [Web Server](#web-server)
  - [Module options](#module-options)
    - [Install Location](#install-location)
      - [Git Repository](#git-repository)
      - [Local Directory](#local-directory)
      - [GitHub Gist](#github-gist)
    - [Disable Caching](#disable-caching)
    - [Disable dependency install](#disable-dependency-install)
  - [Environment variables](#environment-variables)
  - [Include additional yaml files](#include-additional-yaml-files)
  - [Migrating to new configuration layout - post v0.16.0](#migrate-to-new-configuration-layout)

## Config file

For configuration, opsdroid uses a single YAML file named `configuration.yaml`. When you run opsdroid it will look for the file in the following places in order:

- `./configuration.yaml`
- `/etc/opsdroid/configuration.yaml`
- one of the default locations:
  - Mac: `~/Library/Application Support/opsdroid`
  - Linux: `~/.local/share/opsdroid`
  - Windows: `C:\<User>\<Application Data>\<Local Settings>\opsdroid\` or
             `C:\Users\<User>\AppData\Local\opsdroid`

_Note: If no file named `configuration.yaml` can be found on one of these folders one will be created for you taken from the [example configuration file](https://github.com/opsdroid/opsdroid/blob/master/opsdroid/configuration/example_configuration.yaml)_

If you are using one of the default locations you can run the command `opsdroid -e` or `opsdroid --edit-config` to open the configuration with your favorite editor(taken from the environment variable `EDITOR`) or the default editor [vim](tutorials/introduction-vim.md).

The opsdroid project itself is very simple and requires modules to give it functionality. In your configuration file, you must specify the connector, skill, and database* modules you wish to use and any options they may require.

**Connectors** are modules for connecting opsdroid to your specific chat service.

**Skills** are modules which define what actions opsdroid should perform based on different chat messages.

**Database** modules connect opsdroid to your chosen database and allow skills to store information between messages.

For example, a simple barebones configuration would look like:

```yaml
connectors:
  shell: {}

skills:
  hello: {}
```

This tells opsdroid to use the [shell connector](https://github.com/opsdroid/connector-shell) and [hello skill](https://github.com/opsdroid/skill-hello) from the official module library.

In opsdroid all modules are git repositories which will be cloned locally the first time they are used. By default, if you do not specify a repository opsdroid will look at `https://github.com/opsdroid/<moduletype>-<modulename>.git` for the repository. Therefore in the above configuration, the `connector-shell` and `skill-hello` repositories were pulled from the opsdroid organization on GitHub.

You are of course encouraged to write your own modules and make them available on GitHub or any other repository host which is accessible by your opsdroid installation.

A more advanced config would like similar to the following:

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"

databases:
  mongo:
    host: "mymongohost.mycompany.com"
    port: "27017"
    database: "opsdroid"

skills:
  hello: {}
  seen: {}
  myawesomeskill:
    repo: "https://github.com/username/myawesomeskill.git"
```

In this configuration, we are using the [slack connector](connectors/slack.md) with a slack [auth token](https://api.slack.com/tokens) supplied, a built-in mongo database connection for persisting data, `hello` and `seen` skills from the official repos and finally a custom skill hosted on GitHub.

Configuration options such as the `token` in the slack connector or the `host`, `port` and `database` options in the mongo database are specific to those modules. Ensure you check each module's required configuration items before you use them.

## Reference

### Connector Modules

Opsdroid comes with some built-in connectors out of the box. A connector is a module which is either installed as a plugin or built-in that connect opsdroid to a specific chat service.

The built-in connectors are:

- [Facebook](connectors/facebook.md)
- [GitHub](connectors/github.md)
- [Gitter](connectors/gitter.md)
- [Matrix](connectors/matrix.md)
- [Rocket.Chat](connectors/rocketchat.md)
- [Shell](connectors/shell.md)
- [Slack](connectors/slack.md)
- [Telegram](connectors/telegram.md)
- [Websockets](connectors/websocket.md)
- [Webex Teams](connectors/webexteams.md)

_Note: More connectors will be added as built-in connectors into the opsdroid over time._

_Config options of the connectors themselves differ between connectors, see the connector documentation for details._

```yaml
connectors:

  slack:
    token: "mysecretslacktoken"

  # conceptual connector
  twitter:
    oauth_key: "myoauthkey"
    secret_key: "myoauthsecret"
```

Some connectors will allow you to specify a delay to simulate a real user, you just need to add the delay option under a connector in the `configuration.yaml` file.

**Thinking Delay:** accepts a _int_, _float_ or a _list_ to delay reply by _x_ seconds.
**Typing Delay:** accepts a _int_, _float_ or a _list_ to delay reply by _x_ seconds - this is calculated by the length of opsdroid response text so waiting time will be variable.

Example:

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"
    thinking-delay: <int, float or two element list>
    typing-delay: <int, float or two element list>
```

_Note: As expected this will cause a delay on opsdroid time of response so make sure you don't pass a high number._

See [module options](#module-options) for installing custom connectors.

### Database Modules

Opsdroid comes with some built-in databases out of the box. Database modules which connect opsdroid to a persistent data storage service.

Skills can store data in opsdroid's "memory", this is a dictionary which can be persisted in an external database.

The built-in databases are:

- [Mongo DB](databases/mongo.md)
- [Redis](databases/redis.md)
- [SQLite](databases/sqlite.md)

_Config options of the databases themselves differ between databases, see the database documentation for details._

```yaml
databases:
  mongo:
    host: "mymongohost.mycompany.com"
    port: "27017"
    database: "opsdroid"
```

See [module options](#module-options) for installing custom databases.

### Welcome-message

Configure the welcome message.

If set to true then a welcome message is printed in the log at startup. It defaults to true.

```yaml
welcome-message: true
```

### Logging

Configure logging in opsdroid.

Setting `path` will configure where opsdroid writes the log file to. This location must be writable by the user running opsdroid. Setting this to `false` will disable log file output.

_Note: If you forget to declare a path for the logs but have logging active, one of the default locations will be used._

All python logging levels are available in opsdroid. `level` can be set to `debug`, `info`, `warning`, `error` and `critical`.

You may not want opsdroid to log to the console, for example, if you are using the shell connector. However, if running in a container you may want exactly that. Setting `console` to `true` or `false` will enable or disable console logging.

The default locations for the logs are:

- Mac: `/Users/<User>/Library/Logs/opsdroid`
- Linux: `/home/<User>/.cache/opsdroid/log`
- Windows: `C:\Users\<User>\AppData\Local\opsdroid\Logs\`

If you are using one of the default paths for your log you can run the command `opsdroid -l` or `opsdroid --view-log` to open the logs with your favorite editor(taken from the environment variable `EDITOR`) or the default editor [vim](tutorials/introduction-vim.md).

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true

connectors:
  shell: {}

skills:
  hello: {}
  seen: {}
```

#### Optional logging arguments

You can pass optional arguments to the logging configuration to extend the opsdroid logging.

##### extended mode

The extended mode will include the function or method name of where that log was called.

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true
  extended: true
```

*example:*
```shell
INFO opsdroid.logging.configure_logging(): ========================================
INFO opsdroid.logging.configure_logging(): Started opsdroid v0.14.1
```

##### Whitelist log names

You can choose which logs should be shown by whitelisting them. If you are interested only in the log files located in the core, you can whitelist `opsdroid.core` and opsdroid will only show you the logs in this file.

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true
  filter:
    whitelist:
      - "opsdroid.core"
      - "opsdroid.logging"
```

*example:*
```shell
DEBUG opsdroid.core: Loaded 5 skills
DEBUG opsdroid.core: Adding database: DatabaseSqlite
```

_Note: You can also use the extended mode to filter out logs - this should allow you to have even more flexibility while dealing with your logs._

##### Blacklist log names

If you want to get logs from all the files but one, you can choose a file to blacklist and opsdroid will filter that result from the logs. This is particularly important if you have huge objects inside your database.
```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true
  filter:
    blacklist:
      - "opsdroid.loader"
      - "aiosqlite"
```

*example:*
```shell
INFO opsdroid.logging: ========================================
INFO opsdroid.logging: Started opsdroid v0.14.1+93.g3513177.dirty
INFO opsdroid: ========================================
INFO opsdroid: You can customise your opsdroid by modifying your configuration.yaml
INFO opsdroid: Read more at: http://opsdroid.readthedocs.io/#configuration
INFO opsdroid: Watch the Get Started Videos at: http://bit.ly/2fnC0Fh
INFO opsdroid: Install Opsdroid Desktop at:
https://github.com/opsdroid/opsdroid-desktop/releases
INFO opsdroid: ========================================
DEBUG asyncio: Using selector: KqueueSelector
DEBUG opsdroid.core: Loaded 5 skills
DEBUG root: Loaded hello module
WARNING opsdroid.core: <skill module>.setup() is deprecated and will be removed in a future release. Please use class-based skills instead.
DEBUG opsdroid.core: Adding database: DatabaseSqlite
DEBUG opsdroid.database.sqlite: Loaded sqlite database connector
INFO opsdroid.database.sqlite: Connected to sqlite /Users/fabiorosado/Library/Application Support/opsdroid/sqlite.db
DEBUG opsdroid-modules.connector.shell: Loaded shell connector
DEBUG opsdroid.connector.websocket: Starting Websocket connector
INFO opsdroid.connector.rocketchat: Connecting to Rocket.Chat
DEBUG opsdroid.connector.rocketchat: Connected to Rocket.Chat as FabioRosado
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
DEBUG opsdroid-modules.connector.shell: Connecting to shell
INFO opsdroid.web: Started web server on http://0.0.0.0:8080
```

_Note: You can also use the extended mode to filter out logs - this should allow you to have even more flexibility while dealing with your logs._

##### Using both whitelist and blacklist filter
You are only able to filter either with the whitelist filter or the blacklist filter. If you add both in your configuration file, you will get a warning
and only the whitelist filter will be used. This behavior was done because setting two filters causes an RuntimeError exception to be raised(_maximum recursion depth exceeded_).

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true
  filter:
    whitelist:
      - "opsdroid.core"
      - "opsdroid.logging"
      - "opsdroid.web"
    blacklist:
      - "opsdroid.loader"
      - "aiosqlite"
```

*example:*

```shell
WARNING opsdroid.logging: Both whitelist and blacklist filters found in configuration. Only one can be used at a time - only the whitelist filter will be used.
INFO opsdroid.logging: ========================================
INFO opsdroid.logging: Started opsdroid v0.14.1+103.g122e010.dirty
DEBUG opsdroid.core: Loaded 5 skills
DEBUG root: Loaded hello module
WARNING opsdroid.core: <skill module>.setup() is deprecated and will be removed in a future release. Please use class-based skills instead.
DEBUG opsdroid.core: Adding database: DatabaseSqlite
INFO opsdroid.core: Opsdroid is now running, press ctrl+c to exit.
INFO opsdroid.web: Started web server on http://0.0.0.0:8080
```

### Installation Path

Set the path for opsdroid to use when installing skills. Defaults to the current working directory.

```yaml
module-path: "/etc/opsdroid/modules"

connectors:
  shell: {}

skills:
  hello: {}
  seen: {}
```

### Parsers

When writing skills for opsdroid there are multiple parsers you can use for matching messages to your functions.

_Config options of the parsers themselves differ between parsers, see the parser/matcher documentation for details._

```yaml
parsers:
  regex:
    enabled: true

# NLU parser
  rasanlu:
    url: http://localhost:5000
    project: opsdroid
    token: 85769fjoso084jd
    min-score: 0.8
```

Some parsers will allow you to specify a min-score to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. You just need to add the required min-score under a parser in the configuration.yaml file.

See the matchers section for more details.

### Skills

Skill modules which add functionality to opsdroid.

_Config options of the skills themselves differ between skills, see the skill documentation for details._

```yaml
skills:
  hello: {}
  seen: {}
```

See [module options](#module-options) for installing custom skills.

### Time Zone

Configure the timezone.

This timezone will be used in crontab skills if the timezone has not been set as a kwarg in the crontab decorator. All [timezone names](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) from the [tz database](https://www.iana.org/time-zones) are valid here.

```yaml
timezone: 'Europe/London'
```

### Language

Configure the language to use opsdroid.

To use opsdroid with a different language other than English you can specify it in your configuration.yaml. The language code needs to be in the standardized [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes).

_Note: If no language is specified, opsdroid will default to English._

```yaml
lang: <ISO 639-1 code -  example: 'en'>
```

### Web Server

Configure the REST API in opsdroid.

By default, opsdroid will start a web server on port `8080` (or `8443` if SSL details are provided). For more information see the [REST API docs](rest-api.md).

```yaml
web:
  host: '0.0.0.0'
  port: 8080
  ssl:
    cert: /path/to/cert.pem
    key: /path/to/key.pem
```

## Module options

### Install Location

All modules are installed from git repositories. By default, if no additional options are specified opsdroid will look for the repository at `https://github.com/opsdroid/<moduletype>-<modulename>.git`.

However, if you wish to install a module from a different location you can specify one of the following options.

#### Git Repository

A git URL to install the module from.

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"
  mynewconnector:
    repo: https://github.com/username/myconnector.git
```

_Note: When using a git repository, opsdroid will try to update it at startup pulling with fast forward strategy._

#### Local Directory

A local path to install the module from.

```yaml
skills:
  myawesomeskill:
    path: /home/me/src/opsdroid-skills/myawesomeskill
```

You can specify a single file.

```yaml
skills:
  myawesomeskill:
    path: /home/me/src/opsdroid-skills/myawesomeskill/myskill.py
```

Or even an [IPython/Jupyter Notebook](http://jupyter.org/).

```yaml
skills:
  myawesomeskill:
    path: /home/me/src/opsdroid-skills/myawesomeskill/myskill.ipynb
```

#### GitHub Gist

A gist URL to download and install the module from. This downloads the gist
to a temporary file and then uses the single file local installer above. Therefore
Notebooks are also supported.

```yaml
skills:
 ping:
   gist: https://gist.github.com/jacobtomlinson/6dd35e0f62d6b779d3d0d140f338d3e5
```

Or you can specify the Gist ID without the full URL.

```yaml
skills:
 ping:
   gist: 6dd35e0f62d6b779d3d0d140f338d3e5
```

### Disable Caching

Set `no-cache` to true to do a fresh git clone of the module whenever you start opsdroid. This will
default to `true` for modules configured with a local `path`.

```yaml
databases:
  mongodb:
    repo: https://github.com/username/mymongofork.git
    no-cache: true
```

### Disable dependency install

Set `no-dep` to true to skip the installation of dependencies on every start of opsdroid.

```yaml
skills:
  myawesomeskill:
    no-cache: true
    no-deps: true
```

_Note: This might be useful when you are developing a skill and already have the dependencies installed._

## Environment variables

You can use environment variables in your config. You need to specify the variable in the place of a value.

```yaml
skills:
  myawesomeskill:
    somekey: $ENVIRONMENT_VARIABLE
```

_Note: Your environment variable names must consist of uppercase characters and underscores only. The value must also be just the environment variable, you cannot currently mix env vars inside strings._

## Include additional yaml files

You can split the config into smaller modules by using the value `!include file.yaml` to import the contents of a yaml file into the main config.

```yaml
skills: !include skills.yaml

```

_Note: The file.yaml that you wish to include in the config must be in the same directory as your configuration.yaml (e.g ~/.opsdroid)_

## Migrate to new configuration layout

Since version 0.17.0 came out we have migrated to a new configuration layout. We will check your configuration and give you a deprecation warning if your configuration is using the old layout.

### What changed

We have dropped the pattern `- name:  <module name>`  and replaced it with the pattern `<module name>: {}` or `<module name>:` followed by a blank line underneath.

This change makes sure we stop using lists containing dictionaries that carry the configuration for each module. In the new layout, we replace lists with a dictionary that uses the name of a module for a key and the additional configuration parameters inside a dictionary as a key.

### Example

We will use the slack connector as an example. The new configuration layout would set the Slack connection like this:

```yaml
connectors:
  slack:
    token: <API token>
```

Which would be represented in a dictionary format like this:

```python
{
    'connectors': { 
        'slack': { 
            'token': <API token>
        } 
    } 
}
```

You can have a look at the [example configuration file](https://github.com/opsdroid/opsdroid/blob/master/opsdroid/configuration/example_configuration.yaml) for a better grasp of the new layout.

If you need help migrating your configuration to the new layout please get in touch with us on the [official matrix channel](https://riot.im/app/#/room/#opsdroid-general:matrix.org).
