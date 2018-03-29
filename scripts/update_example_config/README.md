# Update example configuration file

This script uses the GitHub API to pull the configuration options for all official skill modules and updates the example configuration file with them all commented out.

# Requirements
This script requires two dependencies to run:
- PyGithub
- Pyyaml
- jinja2

You can run the command: `pip install -r requirements_dev.txt` in the root of the project to install the dependencies or you can install them manually if you wish.

# Running the script

You should run the script within the root directory of the project with the command:

`python3 scripts/update_example_config/update_example_config.py`

You can also pass a few optional arguments when running the above command in your command line:

- first argument - path and file to be updated by the script. If this is not provided the default is the file located in [configuration/example_configuration.yaml](/opsdroid/configuration/example_configuration.yaml)
- `-t` or `--token` - Your personal GitHub API token. If not used, GitHub will only accept 60 calls to its API from your IP address, instead of the 5000 calls allowed if authenticated.
- `-a` or `--active-modules` -  A list of all the modules(skills, connectors, databases and parsers) you wish to mark as active when the file gets updated, the order in which you specify the modules doesn't matter.
