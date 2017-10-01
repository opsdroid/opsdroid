# Configuration reference

## Config file

For configuration you simply need to create a single YAML file named `configuration.yaml`. When you run opsdroid it will look for the file in the following places in order:

 * `./configuration.yaml`
 * `~/.opsdroid/configuration.yaml`
 * `/etc/opsdroid/configuration.yaml`

The opsdroid project itself is very simple and requires modules to give it functionality. In your configuration file you must specify the connector, skill and database* modules you wish to use and any options they may require.

**Connectors** are modules for connecting opsdroid to your specific chat service. **Skills** are modules which define what actions opsdroid should perform based on different chat messages. **Database** modules connect opsdroid to your chosen database and allows skills to store information between messages.

## Reference

### Connector Modules

Connector modules which are installed and connect opsdroid to a specific chat service.

_Config options of the connectors themselves differ between connectors, see the connector documentation for details._

```yaml
connectors:

  - name: slack
    token: "mysecretslacktoken"

  # conceptual connector
  - name: twitter
    oauth_key: "myoauthkey"
    secret_key: "myoauthsecret"
```

See [module options](#module-options) for installing custom connectors.

### Database Modules

Database modules which connect opsdroid to a persistent data storage service.

Skills can store data in opsdroid's "memory", this is a dictionary which can be persisted in an external database.

_Config options of the databases themselves differ between databases, see the database documentation for details._

```yaml
databases:
  - name: mongo
    host: "mymongohost.mycompany.com"
    port: "27017"
    database: "opsdroid"
```

See [module options](#module-options) for installing custom databases.

### Logging

Configure logging in opsdroid.

Setting `path` will configure where opsdroid writes the log file to. This location must be writeable by the user running opsdroid. Setting this to `false` will disable log file output.

All python logging levels are available in opsdroid. `level` can be set to `debug`, `info`, `warning`, `error` and `critical`.

You may not want opsdroid to log to the console, for example if you are using the shell connector. However if running in a container you may want exactly that. Setting `console` to `true` or `false` will enable or disable console logging.

```yaml
logging:
  path: ~/.opsdroid/output.log
  level: info
  console: true

connectors:
  - name: shell

skills:
  - name: hello
  - name: seen
```

### Installation Path

Set the path for opsdroid to use when installing skills. Defaults to the current working directory.

```yaml
module-path: "/etc/opsdroid/modules"

connectors:
  - name: shell

skills:
  - name: hello
  - name: seen
```

### Skills

Skill modules which add functionality to opsdroid.

_Config options of the skills themselves differ between skills, see the skill documentation for details._

```yaml
skills:
  - name: hello
  - name: seen
```

See [module options](#module-options) for installing custom skills.

### Time Zone

Configure the timezone.

This timezone will be used in crontab skills if the timezone has not been set as a kwarg in the crontab decorator. All [timezone names](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) from the [tz database](https://www.iana.org/time-zones) are valid here.

```yaml
timezone: 'Europe/London'
```

### Web Server

Configure the REST API in opsdroid.

By default opsdroid will start a web server accessible only to localhost on port `8080` (or `8443` if ssl details are provided). For more information see the [REST API docs](rest-api).

```yaml
web:
  host: '127.0.0.1'  # set to '0.0.0.0' to allow all traffic
  port: 8080
  ssl:
    cert: /path/to/cert.pem
    key: /path/to/key.pem
```

## Module options

All modules are installed from git repositories. By default if no additional options are specified opsdroid will look for the repository at `https://github.com/opsdroid/<moduletype>-<modulename>.git`.

However if you wish to install a module from a different location you can specify the some more options.

### Git Repository

A git url to install the module from.

```yaml
connectors:
  - name: slack
    token: "mysecretslacktoken"
  - name: mynewconnector
    repo: https://github.com/username/myconnector.git
```

### Local Directory

A local path to install the module from.

```yaml
skills:
  - name: myawesomeskill
    path: /home/me/src/opsdroid-skills/myawesomeskill
```

Or you can specify a single file.

```yaml
skills:
  - name: myawesomeskill
    path: /home/me/src/opsdroid-skills/myawesomeskill/myskill.py
```

### Disable Caching

Set `no-cache` to true to do a fresh git clone of the module whenever you start opsdroid.

```yaml
databases:
  - name: mongodb
    repo: https://github.com/username/mymongofork.git
    no-cache: true
```

## Environment variables

You can use environment variables in your config. You need to specify the variable in the place of a value.

```yaml
skills:
  - name: myawesomeskill
    somekey: $ENVIRONMENT_VARIABLE
```

_Note: Your environment variable names must consist of uppercase characters and underscores only. The value must also be just the environment variable, you cannot currently mix env vars inside strings._

## Include additional yaml files

You can split the config into smaller modules by using the value `!include file.yaml` to import the contents of a yaml file into the main config. 


```yaml
skills: !include skills.yaml

```

_Note: The file.yaml that you wish to include in the config must be in the same directory as your configuration.yaml (e.g ~/.opsdroid)_