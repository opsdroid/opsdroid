# Configuration reference

## Config file

For configuration you simply need to create a single YAML file named `configuration.yaml`. When you run opsdroid it will look for the file in the following places in order:

 * `./configuration.yaml`
 * `~/.opsdroid/configuration.yaml`
 * `/etc/opsdroid/configuration.yaml`

The opsdroid project itself is very simple and requires modules to give it functionality. In your configuration file you must specify the connector, skill and database* modules you wish to use and any options they may require.

**Connectors** are modules for connecting opsdroid to your specific chat service. **Skills** are modules which define what actions opsdroid should perform based on different chat messages. **Database** modules connect opsdroid to your chosen database and allows skills to store information between messages.

## Reference

### `connectors`

Connector modules which are installed and connect opsdroid to a specific chat service.

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

See [module options](#module-options) for installing custom connectors.

### `databases`

Database modules which connect opsdroid to a persistent data storage service.

Skills can store data in opsdroid's "memory", this is a dictionary which can be persisted in an external database.

_Config options of the databases themselves differ between databases, see the database documentation for details._

```yaml
databases:
  mongo:
    host: "mymongohost.mycompany.com"
    port: "27017"
    database: "opsdroid"
```

See [module options](#module-options) for installing custom databases.

### `logging`

Set the logging level of opsdroid.

All python logging levels are available in opsdroid. `logging` can be set to `debug`, `info`, `warning`, `error` and `critical`.

```yaml
logging: debug

connectors:
  shell:

skills:
  hello:
  seen:
```

### `module-path`

Set the path for opsdroid to use when installing skills. Defaults to the current working directory.

```yaml
module-path: "/etc/opsdroid/modules"

connectors:
  shell:

skills:
  hello:
  seen:
```

### `skills`

Skill modules which add functionality to opsdroid.

_Config options of the skills themselves differ between skills, see the skill documentation for details._

```yaml
skills:
  hello:
  seen:
```

See [module options](#module-options) for installing custom skills.

## Module options

All modules are installed from git repositories. By default if no additional options are specified opsdroid will look for the repository at `https://github.com/opsdroid/<moduletype>-<modulename>.git`.

However if you wish to install a module from a different location you can specify the some more options.

### `repo`

A git url to install the module from.

```yaml
connectors:
  slack:
    token: "mysecretslacktoken"
  mynewconnector:
    repo: https://github.com/username/myconnector.git
```

### `path`

A local path to install the module from.

```yaml
skills:
  myawesomeskill:
    path: /home/me/src/opsdroid-skills/myawesomeskill
```

Or you can specify a single file.

```yaml
skills:
  myawesomeskill:
    path: /home/me/src/opsdroid-skills/myawesomeskill/myskill.py
```

### `no-cache`

Set this to do a fresh git clone of the module whenever you start opsdroid.

```yaml
databases:
  mongodb:
    repo: https://github.com/username/mymongofork.git
    no-cache: true
```
