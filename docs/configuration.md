# Configuration

```eval_rst
.. contents::
```

## Config file

For configuration, opsdroid uses a single YAML file named `configuration.yaml`. When you run opsdroid it will look for the file in the following places in order:

- Local `./configuration.yaml`
- The default user data location:
  - Mac: `~/Library/Application Support/opsdroid`
  - Linux: `~/.local/share/opsdroid`
  - Windows: `C:\Documents and Settings\<User>\Application Data\Local Settings\opsdroid\opsdroid` or
    `C:\Documents and Settings\<User>\Application Data\opsdroid\opsdroid`
- System `/etc/opsdroid/configuration.yaml` (\*nix only)

_Note: If no file named `configuration.yaml` can be found on one of these folders, one will be created for you taken from the [example configuration file](https://github.com/opsdroid/opsdroid/blob/master/opsdroid/configuration/example_configuration.yaml)_

Suppose you are using one of the default locations. In that case, you can run the command `opsdroid config edit` to open the configuration with your favourite editor (taken from the environment variable `EDITOR`) or the default editor vim.

The opsdroid project itself is very simple and requires modules to give it functionality. You must specify the connector, skill, and database\* modules you wish to use in your configuration file and any options they may require.

**Connectors** are modules for connecting opsdroid to your specific chat service.

**Skills** are modules that define what actions opsdroid should perform based on different chat messages.

**Database** modules connect opsdroid to your chosen database and allow skills to store information between messages.

For example, a simple barebones configuration would look like this:

```yaml
connectors:
  shell: {}

skills:
  hello: {}
```

This tells opsdroid to use the built-in [shell connector](https://github.com/opsdroid/connector-shell) and [hello skill](https://github.com/opsdroid/skill-hello) from the official module library.

In opsdroid modules can be git repositories which will be cloned locally the first time they are used. By default, if you do not specify a location for a module opsdroid will first look to see if it is built into the core and then look at https://github.com/opsdroid/<moduletype>-<modulename>.git for a repository. Therefore in the above configuration, the connector-shell module is found at opsdroid.connector.shell and the hello skill is found in the skill-hello repository from the opsdroid organization on GitHub.
You are of course encouraged to write your modules and make them available on GitHub or any other repository host which is accessible by your opsdroid installation. We are especially keen for folks to contribute connectors and databases to the opsdroid core package.
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

Opsdroid comes with some built-in connectors out of the box. A connector is a module that is either installed as a plugin or built-in that connects opsdroid to a specific chat service.

The built-in connectors are:

```eval_rst
.. toctree::
   :maxdepth: 2

   connectors/index
```

_Note: More connectors will be added as built-in connectors into the opsdroid core over time._

_Config options of the connectors themselves differ between connectors, see the connector documentation for details._

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"

  matrix:
    mxid: "@username:matrix.org"
    password: "mypassword"
```

Some connectors will allow you to specify a delay to simulate a real user, you just need to add the delay option under a connector in the `configuration.yaml` file.

**Thinking Delay:** accepts an _int_, _float_ or a _list_ to delay reply by _x_ seconds.
**Typing Delay:** accepts an _int_, _float_ or a _list_ to delay reply by _x_ seconds - this is calculated by the length of opsdroid response text so waiting time will be variable.

Example:

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"
    thinking-delay: <int, float or two element list>
    typing-delay: <int, float or two element list>
```

_Note: As expected, this will cause a delay on opsdroid time of response so make sure you don't pass a high number._

See [module options](#module-options) for installing custom connectors.

### Database Modules

Opsdroid comes with some built-in databases out of the box. Databases are modules that connect opsdroid to a persistent data storage service.

Skills can store data in opsdroid's "memory", this is a dictionary which can be persisted in an external database.

The built-in databases are:

```eval_rst
.. toctree::
   :maxdepth: 2

   databases/index
```

_Config options of the databases themselves differ between databases. See the database documentation for details._

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

If set to true, then a welcome message is printed in the log at startup. It defaults to true.

```yaml
welcome-message: true
```

### Logging

Configure logging in opsdroid. If you don't have logging settings configured, opsdroid will use rich logging.

Setting `path` will configure where opsdroid writes the log file to. This location must be writable by the user running opsdroid. Setting this to `false` will disable log file output.

_Note: If you forget to declare a path for the logs but have logging active, one of the default locations will be used._

All python logging levels are available in opsdroid. `level` can be set to `debug`, `info`, `warning`, `error` and `critical`.

You may not want opsdroid to log to the console, for example, using the shell connector. However, if running in a container, you may want exactly that. Setting `rich: false` will log only critial level logs, removing any of the other logs.

The default locations for the logs are:

- Mac: `/Users/<User>/Library/Logs/opsdroid`
- Linux: `/home/<User>/.cache/opsdroid/log`
- Windows: `C:\Users\<User>\AppData\Local\opsdroid\Logs\`

If you are using one of the default paths for your log, you can run the command `opsdroid logs` to print the logs into the terminal.

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  rich: true
  console: false

connectors:
  shell: {}

skills:
  hello: {}
  seen: {}
```

#### Rich logging

When using rich logging, opsdroid will use the [RichHandler](https://rich.readthedocs.io/en/stable/logging.html) from the Rich library. These logs will contain a timestap, log location (file and line number) and will show different colours depending on which level the log was set. You can use some options to disable some of these things.

- set `timestamp: false` to disable timestamps
- set `extended: false` to disable log location

##### Automatic fallback

Opsdroid will fall back to simple console logging when running in a non-interactive shell (example: Docker container).

If this is the case then you will see the following message in the log upon Opsdroid start:

```
WARNING opsdroid.logging Running in non-interactive shell - falling back to simple logging. You can override this using 'logging.config: false'
```

Specifying `logging.console` in the configuration will override this.

#### Optional logging arguments

You can pass optional arguments to the logging configuration to extend the opsdroid logging.

##### Logs timestamp

Sometimes it is helpful to have the timestamp when logs happen. You can enable them with the `timestamp` boolean. Defaults to false

```yaml
logging:
  level: info
  timestamp: true
```

_example:_

```shell
2020-12-02 10:39:51,255 INFO opsdroid.logging: ========================================
2020-12-02 10:39:51,255 INFO opsdroid.logging: Started opsdroid v0.19.0+66.g8b839bc.dirty.
2020-12-02 10:39:51,255 INFO opsdroid: ========================================
```

##### Logs rotation

To keep the logs under control, the file will grow to 50MB before being rotated back. You can change the default value by passing the `file-size` argument.

```yaml
logging:
  level: info
  file-size: 100e6
```

This will change the size of the file to 100MB before being rotated back to zero.

##### extended mode

The extended mode will include the function or method name of where that log was called.

```yaml
logging:
  level: info
  path: ~/.opsdroid/output.log
  console: true
  extended: true
```

_example:_

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

_example:_

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

_example:_

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
and only the whitelist filter will be used. This behaviour was done because setting two filters causes an `RuntimeError` to be raised (_maximum recursion depth exceeded_).

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

###### Example

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

##### Logs formatter

You can create your formatter string to pass to the logs. This option will give you more flexibility and get logs in your prefered format. Note that this option only works if you set `console: true` since rich logging will have its own
formatter.

```yaml
logging:
  level: info
  console: true
  formatter: "%(name)s %(levelname)s - %(message)s"
```

###### Example

```shell
opsdroid.logging INFO - ========================================
opsdroid.logging INFO - Started opsdroid v0.8.1+976.g150b605.dirty.
opsdroid INFO - ========================================
opsdroid INFO - You can customise your opsdroid by modifying your configuration.yaml.
opsdroid INFO - Read more at: http://opsdroid.readthedocs.io/#configuration
opsdroid INFO - Watch the Get Started Videos at: http://bit.ly/2fnC0Fh
opsdroid INFO - Install Opsdroid Desktop at:
https://github.com/opsdroid/opsdroid-desktop/releases
opsdroid INFO - ========================================
opsdroid.loader WARNING - No databases in configuration. This will cause skills which store things in memory to lose data when opsdroid is restarted.
opsdroid.core INFO - Opsdroid is now running, press ctrl+c to exit.
opsdroid.web INFO - Started web server on http://0.0.0.0:8080
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
    train: True
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
timezone: "Europe/London"
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
  host: "0.0.0.0"
  port: 8080
  ssl:
    cert: /path/to/cert.pem
    key: /path/to/key.pem
```

#### CORS

By default, opsdroid handles CORS requests insecurely. This means that every request will be accepted. You can configure CORS by using the following configuration:

```yaml
web:
  cors:
    allow-all: false
    origins:
      - http://localhost:3000
    allow-headers:
      - X-Token
```

## Module options

### Install Location

Modules in opsdroid can be installed in a variety of ways. By default, if no additional options are specified, opsdroid will first look to see if the module is built into opsdroid's core library and then look for the repository https://github.com/opsdroid/<moduletype>-<modulename>.git`.

However, if you wish to install a module from a different location you can specify one of the following options.

#### Git Repository

A git URL to install the module.

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"
  mynewconnector:
    repo: https://github.com/username/myconnector.git
```

_Note: When using a git repository, opsdroid will try to update it at startup pulling with fast forward strategy._

#### Local Directory

A local path to install the module.

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

A gist URL to download and install the module. This downloads the gist
to a temporary file and then uses the single-file local installer above. Therefore
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

You can also directly specify the module name to import, which skips all of the opsdroid module generation.

```yaml
skills:
  ping:
    module: "module.to.import"
```

### Disable Caching

Set `no-cache` to true to generate the module whenever you start opsdroid. This will
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

_Note: This might be useful when developing a skill and already have the dependencies installed._

## Environment variables

You can use environment variables in your config. You need to specify the variable in the place of a value.

```yaml
skills:
  myawesomeskill:
    somekey: $ENVIRONMENT_VARIABLE
```

_Note: Your environment variable names must consist of uppercase characters and underscores only. The value must also be just the environment variable. You cannot currently mix env vars inside strings._

## Validating modules

Opsdroid runs two types of validation:

- Validates basic rules found on the file `configuration.yaml` (logging, web, module path and welcome message)
- Validates rules for each module if the constant variable `CONFIG_SCHEMA` is set in the module.

_Note: If the validation fails, opsdroid will exit with error code 1._

You can add rules to your custom made modules by setting the constant variable and adding rules to it. The `CONFIG_SCHEMA` variable needs to be a dictionary where you pass expected arguments and type.

To validate a module/configuration, we use the _voluptuous_ dependency, which means you need to follow specific patterns expected by the dependency.

- Required values need to be set with `voluptuous.Required()`
- Optional values can be set with or without `voluptuous.Optional()`

### Example

Let's take the example of our matrix connector. Inside the module, we set the const `CONFIG_SCHEMA` with some rules:

```python
from voluptuous import Required

CONFIG_SCHEMA = {
    Required("mxid"): str,
    Required("password"): str,
    Required("rooms"): dict,
    "homeserver": str,
    "nick": str,
    "room_specific_nicks": bool,
    "device_name": str,
    "device_id": str,
    "store_path": str,
}
```

As you can see `mxid`, `password` and `rooms` are required fields for this connector and we expect them to be either strings or a dictionary.

Since we don't need to declare a value as Optional explicitly, we can write the expected value and type.

_Note: If a module doesn't contain the const variable, the module will be loaded anyway and should handle any potential errors found in the configuration._

## HTTP proxy support

If you need to use a HTTP proxy, set the HTTP_PROXY and HTTPS_PROXY environment variables.

## Migrate to new configuration layout

Since version 0.17.0 came out we have migrated to a new configuration layout. We will check your configuration and give you a deprecation warning if your configuration uses the old layout.

### What changed

We have dropped the pattern `- name: <module name>` and replaced it with the pattern `<module name>: {}` or `<module name>:` followed by a blank line underneath.

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

If you need help migrating your configuration to the new layout please get in touch with us on the [official matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org).
