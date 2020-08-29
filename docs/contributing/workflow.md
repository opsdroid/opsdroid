# Workflow

All contributors to the project, including maintainers, contribute using the following process:

 * Fork the main project to your own account
 * Work on your changes on a feature branch
 * Create a pull request back to the main project
 * Tests and test coverage will be checked automatically
 * A project maintainer will review and merge the pull request

# Developing

```shell
# clone the repo
git clone https://github.com/opsdroid/opsdroid.git
cd opsdroid

# install the project in "editable" mode
# specify modules to install dependencies for in the square brackets
pip install -e .[all]

# run opsdroid
opsdroid start
```

## Running the tests

```shell
# install pre-commit hooks
pip install -U pre-commit

# set up pre-commit hooks (only needs to be done once)
pre-commit install

# install test runner
pip install -U tox

# install test dependencies
pip install -e .[test]

# run tests
tox
```

## Developing in containers

Developing in containers can be a great way to ensure that opsdroid will run in a clean python environment and that all dependencies are captured.

```shell
# build the container
# specify modules in the EXTRAS build arg
docker build --build-arg EXTRAS=.[common] -t opsdroid/opsdroid:myfeature .

# run opsdroid
docker run --rm -ti -v $(pwd):/usr/src/app opsdroid/opsdroid:myfeature
```

## Running the tests

```shell
# run tests (make sure the image is built with the `[test]` extras)
docker run --rm -ti -v $(pwd):/usr/src/app opsdroid/opsdroid:myfeature tox
```

## Automatic Linting with Black

Opsdroid is running [Black](https://black.readthedocs.io/en/stable/) to deal with linting issues and it will be triggered when Travis runs our tests automatically. You can install Black on your machine and have it correct any linting issues that you might have.

### Install Black

Run the following command to install Black on your machine.

```shell
pip install black
```

_Note: You need to be running Python 3.6.0+ to have Black running._

You also need to have [pre-commit](https://pre-commit.com) installed and set up in order to have Black check your code and work on each git commit. If you followed the instructions on running the tests earlier on [Developing](#developing), you should have pre-commit set up already, and if not, please do it now.


### Using Black

Black will be triggered when you commit changes with the command `git commit`. You can then check your terminal for what sort of message you get from Black - either all is good or some files would be formatted.

#### Example of issues with linting

Let's imagine that you have added your files to stating and did `git commit -m 'my awesome feature`, then black will run on your terminal and show you something like this:

```bash
lint run-test-pre: PYTHONHASHSEED='4023478313'
lint run-test: commands[0] | flake8 --builtins=_ opsdroid
lint run-test: commands[1] | pydocstyle opsdroid tests
lint run-test: commands[2] | black --check opsdroid tests scripts setup.py versioneer.py
would reformat /home/travis/build/opsdroid/opsdroid/tests/test_connector_ciscospark.py
All done! 💥 💔 💥
1 file would be reformatted, 87 files would be left unchanged.
ERROR: InvocationError for command /home/travis/build/opsdroid/opsdroid/.tox/lint/bin/black --check opsdroid tests scripts setup.py versioneer.py (exited with code 1)
```

As you can see black tells you that it found some issues with linting on 1 file and since it reformats your code to fix the linting issues, it tells you that the file would be reformatted.

Black will change your file and if you go to `git status` you will see that your file was modified. You just need to add the files to starting again and commit them with the previous commit message. Afterwards, you can push the changes to your repository/PR.

#### Example of good linting

If your linting is good when you commit your changes you will see the following message:

```bash
lint run-test-pre: PYTHONHASHSEED='3517441289'
lint run-test: commands[0] | flake8 --builtins=_ opsdroid
lint run-test: commands[1] | pydocstyle opsdroid tests
lint run-test: commands[2] | black --check opsdroid tests scripts setup.py versioneer.py
All done! ✨ 🍰 ✨
88 files would be left unchanged.
___________________________________ summary ____________________________________
lint: commands succeeded
congratulations :)
```

This tells you that your linting is good and you can push these changes to Github.
