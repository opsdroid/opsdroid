"""Command line manager for opsdroid."""

import click

from opsdroid.cli.config import config, print_example_config
from opsdroid.cli.logs import logs
from opsdroid.cli.start import start
from opsdroid.cli.version import version, print_version
from opsdroid.cli.utils import edit_files, warn_deprecated_cli_option


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "--gen-config",
    is_flag=True,
    callback=print_example_config,
    expose_value=False,
    default=False,
    help="[Deprecated] Print an example config and exit.",
)
@click.option(
    "--version",
    "-v",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    default=False,
    is_eager=True,
    help="[Deprecated] Print the version and exit.",
)
@click.option(
    "--edit-config",
    "-e",
    is_flag=True,
    callback=edit_files,
    default=False,
    flag_value="config",
    expose_value=False,
    help="[Deprecated] Open configuration.yaml with your favorite editor and exits.",
)
@click.option(
    "--view-log",
    "-l",
    is_flag=True,
    callback=edit_files,
    default=False,
    flag_value="log",
    expose_value=False,
    help="[Deprecated] Open opsdroid logs with your favorite editor and exits.",
)
def cli(ctx):
    """Opsdroid is a chat bot framework written in Python.

    It is designed to be extendable, scalable and simple.
    See https://opsdroid.github.io/ for more information.
    """
    if ctx.invoked_subcommand is None:
        warn_deprecated_cli_option(
            "Running `opsdroid` without a subcommand is now deprecated. "
            "Please run `opsdroid start` instead. "
            "You can also run `opsdroid --help` to learn about the other subcommands."
        )
        ctx.invoke(start)


cli.add_command(config)
cli.add_command(logs)
cli.add_command(start)
cli.add_command(version)
