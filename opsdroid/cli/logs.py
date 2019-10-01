"""The logs subcommand for opsdroid cli."""


import click

from opsdroid.cli.utils import edit_files


@click.command()
@click.pass_context
def logs(ctx):
    """Open opsdroid logs with your favorite editor and exits."""
    edit_files(ctx, None, "log")
