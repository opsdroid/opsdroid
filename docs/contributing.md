# Contributing to the project

Contributing to the opsdroid ecosystem is strongly encouraged. You can do this by creating modules to be used by opsdroid or by contributing to the project itself.

## Workflow

All contributors to the project, including [jacobtomlinson](https://github.com/jacobtomlinson), contribute using the following process:

 * Fork the main project to your own account
 * Work on your changes on a feature branch
 * Create a pull request back to the main project
 * Tests and test coverage will be checked automatically
 * A project maintainer will review and merge the pull request

## Developing

```shell
# clone the repo
git clone https://github.com/opsdroid/opsdroid.git
cd opsdroid

# install project dependancies
pip install -r requirements.txt

# run opsdroid
python -m opsdroid
```

Running the tests

```shell
# install test runner
pip install -U tox

# run tests
tox
```


## Developing in containers

Developing in containers can be a great way to ensure that opsdroid will run in a clean python environment and that all dependancies are captured.

```shell
# build the container
docker build -t opsdroid/opsdroid:myfeature .

# run opsdroid
docker run --rm -ti -v $(pwd):/usr/src/app opsdroid/opsdroid:myfeature
```

Running the tests

```shell
# run tests
docker run --rm -ti -v $(pwd):/usr/src/app opsdroid/opsdroid:myfeature tox
```
