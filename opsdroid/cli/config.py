"""The config subcommand for opsdroid cli."""

import click

from opsdroid.cli.utils import (
    build_config,
    edit_config,
    list_all_modules,
    path_option,
    validate_config,
)
from opsdroid.const import EXAMPLE_CONFIG_FILE


@click.group()
@path_option
@click.pass_context
def config(ctx, path):
    """Subcommands related to opsdroid configuration."""
    ctx.obj = path


@config.command()
@click.pass_context
def gen(ctx):
    """Print out the example config.

    Open the example configuration file and print it into the terminal.
    If the -f flag was used with the config command, then this path will be
    set on `ctx.obj` and will be passed into this subcommand and the contents
    of the file set in the path will be print into the terminal instead.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    path = ctx.obj or EXAMPLE_CONFIG_FILE
    with open(path, "r") as conf:
        click.echo(conf.read())
    ctx.exit(0)


@config.command()
@click.pass_context
def edit(ctx):
    """Open config file with your favourite editor.

    By default this command will open the configuration file with
    vi/vim. If you have a different editor that you would like to sure,
    you need to change the environment variable - `EDITOR`.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    edit_config(ctx, ctx.obj)


@config.command()
@click.pass_context
def lint(ctx):
    """Validate the configuration.

    This subcommand allows you to validate your configuration or a configuration
    from a file if the -f flag is used. This avoids the need to start the bot just
    to have it crash because of a configuration error.

    This command could also be helpful if you need to do changes to the configuration but
    you are unsure if everything is set correct. You could have the new config
    file located somewhere and test it before using it to start opsdroid.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    validate_config(ctx, ctx.obj)


@config.command()
@click.pass_context
def list_modules(ctx):
    """Print out a list of all active modules.

    This function will try to get information from the modules that are active in the
    configuration file and print them as a table or will just print a sentence saying that
    there are no active modules for that type.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    list_all_modules(ctx, ctx.obj)


@config.command()
@click.pass_context
@click.option(
    "--verbose",
    "verbose",
    is_flag=True,
    help="Turns logging level to debug to see all logging messages.",
)
def build(ctx, verbose):
    """Load configuration, load modules and install dependencies.

    This function loads the configuration and install all necessary
    dependencies defined on a `requirements.txt` file inside the module.
    If the flag `--verbose` is passed the logging level will be set as debug and
    all logs will be shown to the user.


    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        verbose (bool): set the logging level to debug.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    build_config(ctx, {"path": ctx.obj, "verbose": verbose})
