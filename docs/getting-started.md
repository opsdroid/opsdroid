# Getting started

## Installation

You can simply install opsdroid using `pip`.

```
pip3 install opsdroid
```

Or you can use the official docker image.

```
docker pull opsdroid/opsdroid:latest
```

## Configuration

For configuration you simply need to create a single YAML file named `configuration.yaml`. When you run opsdroid it will look for the file in the following places in order:

 * `./configuration.yaml`
 * `~/.opsdroid/configuration.yaml`
 * `/etc/opsdroid/configuration.yaml`

 If none are found then `~/.opsdroid/configuration.yaml` will be created for you.

The opsdroid project itself is very simple and requires modules to give it functionality. In your configuration file you must specify the connector, skill and database* modules you wish to use and any options they may require.

**Connectors** are modules for connecting opsdroid to your specific chat service. **Skills** are modules which define what actions opsdroid should perform based on different chat messages. **Database** modules connect opsdroid to your chosen database and allows skills to store information between messages.

For example a simple barebones configuration would look like:

```yaml
connectors:
  - name: shell

skills:
  - name: hello
```

This tells opsdroid to use the [shell connector](https://github.com/opsdroid/connector-shell) and [hello skill](https://github.com/opsdroid/skill-hello) from the official module library.

In opsdroid all modules are git repositories which will be cloned locally the first time they are used. By default if you do not specify a repository opsdroid will look at `https://github.com/opsdroid/<moduletype>-<modulename>.git` for the repository. Therefore in the above configuration the `connector-shell` and `skill-hello` repositories were pulled from the opsdroid organisation on GitHub.

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

## Running

If you installed opsdroid using `pip` and have created your `configuration.yaml` file in the correct place you can simple start it by running:

```
opsdroid
```

If you are using the opsdroid docker image then ensure you add your configuration as a volume and run the container.

```
docker run --rm -v /path/to/configuration.yaml:/etc/configuration.yaml:ro opsdroid/opsdroid:latest
```

-------

_\* databases are optional, however bot memory will not persist between different connectors or system reboots without one_
