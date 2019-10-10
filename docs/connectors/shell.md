# opsdroid connector shell

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to send messages using the command line.

**Note:** _This connector only works on unix systems. It will not work on windows, it's recommended that you download the 
[Opsdroid Desktop App](https://github.com/opsdroid/opsdroid-desktop) to have opsdroid running on windows._

## Requirements

The shell connector requires access to user input, this means you should probably set the logging not to go to the console. 

## Configuration

```yaml
connectors:
  - name: shell
    # optional
    bot-name: "mybot" # default "opsdroid"
```

## Disable Logging
It's recommended to deactivate console logging in your `configuration.yaml` file if you intend to use this connector.

Just add the following in your configuration file:

```yaml
logging:
  console: false
```

