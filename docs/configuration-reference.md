# Configuration reference

## Config file

For configuration you simply need to create a single YAML file named `configuration.yaml`. When you run opsdroid it will look for the file in the following places in order:

 * `./configuration.yaml`
 * `~/.opsdroid/configuration.yaml`
 * `/etc/opsdroid/configuration.yaml`

The opsdroid project itself is very simple and requires modules to give it functionality. In your configuration file you must specify the connector, skill and database* modules you wish to use and any options they may require.

**Connectors** are modules for connecting opsdroid to your specific chat service. **Skills** are modules which define what actions opsdroid should perform based on different chat messages. **Database** modules connect opsdroid to your chosen database and allows skills to store information between messages.

## Reference

### connectors

Connector modules which are installed and connect opsdroid to a specific chat service.
