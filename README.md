# Ops Droid
An open source python chat-ops bot

## Building

`docker build -t opsdroid/opsdroid:dev .`

`docker run --rm opsdroid/opsdroid:dev`

## Configuration

Configuration is done in a yaml file called `configuration.yaml`.

Example:

```
logging: "debug"

connectors:
  shell:

skills:
  hello:
```

## Development

`docker run --rm -ti -v $(pwd):/usr/src/app opsdroid/opsdroid:dev`
