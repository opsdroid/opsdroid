"""The config subcommand for opsdroid cli."""

import click

from opsdroid.cli.utils import (
    edit_files,
    warn_deprecated_cli_option,
    validate_config,
    list_modules,
)
from opsdroid.const import EXAMPLE_CONFIG_FILE


def print_example_config(ctx, param, value):
    """[Deprecated] Print out the example config.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        param (dict): a dictionary of all parameters pass to the click
            context when invoking this function as a callback.
        value (bool): the value of this parameter after invocation.
            Defaults to False, set to True when this flag is called.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    if not value or ctx.resilient_parsing:
        return
    if ctx.command.name == "cli":
        warn_deprecated_cli_option(
            "The flag --gen-config has been deprecated. "
            "Please run `opsdroid config gen` instead."
        )
    with open(EXAMPLE_CONFIG_FILE, "r") as conf:
        click.echo(conf.read())
    ctx.exit(0)


@click.group()
def config():
    """Subcommands related to opsdroid configuration."""


@config.command()
@click.pass_context
def gen(ctx):
    """Print out the example config."""
    print_example_config(ctx, None, True)


@config.command()
@click.pass_context
def edit(ctx):
    """Print out the example config."""
    edit_files(ctx, None, "config")


@config.command()
@click.pass_context
@click.option(
    "-f",
    "path",
    help="Validates opsdroid configuration from a path.",
    type=click.Path(exists=True),
)
def lint(ctx, path):
    """Validate the configuration."""
    validate_config(ctx, path, "config")


@config.command()
@click.pass_context
def list_connectors(ctx):
    """Print out a list of all active connectors."""
    list_modules(ctx, "connectors", "config")


@config.command()
@click.pass_context
def list_parsers(ctx):
    """Print out a list of all active parsers."""
    list_modules(ctx, "parsers", "config")


@config.command()
@click.pass_context
def list_databases(ctx):
    """Print out a list of all active databases."""
    list_modules(ctx, "databases", "config")


@config.command()
@click.pass_context
def list_skills(ctx):
    """Print out a list of all active skills."""
    list_modules(ctx, "skills", "config")
