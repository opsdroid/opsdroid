"""The version subcommand for opsdroid cli."""

import click

from opsdroid import __version__


@click.command()
@click.pass_context
def version(ctx):
    """Print out the version of opsdroid that is installed and exits.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    click.echo("opsdroid {version}".format(version=__version__))
    ctx.exit(0)
