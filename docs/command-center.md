# Command Center

Opsdroid Command Center is the dashboard that allows you to interact with Opsdroid without the need to have any connector installed (other than the default websocket one). The dashboard allows you to enable/disable modules as well see your active modules and installed configuration from within your browser.

Opsdroid Command Center is powered by the [opsdroid web](https://github.com/opsdroid/opsdroid-web) package, you need to first install the package using `npm`.

## Configuration

Opsdroid Command Center configuration lives under the `web` section of Opsdroid configuration.

```yaml
web:
  command-center:
    enabled: true
    enable-dashboard: true
    dashboard-port: 8081
    token: <Your chosen secret token>
    excluded-keys:
      - module
      - path
```

Let's have a look at each of these configuration arguments.

- `enabled` - Toggles Command Centter on/off, if enabled new routes will be added to Opsdroid's [RESTful api](rest-api.md)
- `enabled-dashboard` - Start `opsdroid web` on the chosen `dashboard-port`
- `dashboard-port` - Port to use for opsdroid dashboard (defaults to 8081)
- `token` - Token to be used to authenticate requests done to the command center API endpoints.
- `excluded-keys` - The command Center API endpoints let you get the modules configuration. `excluded-keys` allow you to remove keys from the response.

## Examples

TBD