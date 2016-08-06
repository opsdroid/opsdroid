# Contributing to the project

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

Run tests
`docker run --rm -ti -v $(pwd):/usr/src/app opsdroid/opsdroid:dev tox`
