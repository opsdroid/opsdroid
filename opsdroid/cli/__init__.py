"""Command line manager for opsdroid."""

import click

from opsdroid.cli.config import config
from opsdroid.cli.logs import logs
from opsdroid.cli.start import start
from opsdroid.cli.version import version


@click.group()
@click.pass_context
def cli(ctx):
    """Opsdroid is a chat bot framework written in Python.

    It is designed to be extendable, scalable and simple.
    See https://opsdroid.github.io/ for more information.
    """


cli.add_command(config)
cli.add_command(logs)
cli.add_command(start)
cli.add_command(version)
