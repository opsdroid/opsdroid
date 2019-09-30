"""The version subcommand for opsdroid cli."""


import click

from opsdroid import __version__
from opsdroid.cli.utils import warn_deprecated_cli_option


def print_version(ctx, param, value):
    """[Deprecated] Print out the version of opsdroid that is installed."""
    if not value or ctx.resilient_parsing:
        return
    if ctx.command.name == "cli":
        warn_deprecated_cli_option(
            "The flag --version has been deprecated. "
            "Please run `opsdroid version` instead."
        )
    click.echo("opsdroid {version}".format(version=__version__))
    ctx.exit(0)


@click.command()
@click.pass_context
def version(ctx):
    """Print the version and exit."""
    print_version(ctx, None, True)
