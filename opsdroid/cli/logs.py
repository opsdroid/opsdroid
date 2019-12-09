"""The logs subcommand for opsdroid cli."""

import click
import tailer
from opsdroid.const import DEFAULT_LOG_FILENAME


@click.group(invoke_without_command=True)
@click.option("-f", "follow", is_flag=True, help="Print the logs in real time")
@click.pass_context
def logs(ctx, follow):
    """Print the content of the log file into the terminal.

    Open opsdroid logs and prints the contents of the file into the terminal.
    If you wish to follow the logs in real time you can use the `-f` flag which
    will allow you to do this.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        follow(bool): Set by the `-f` flag to trigger the print of the logs in real time.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    with open(DEFAULT_LOG_FILENAME, "r") as log:
        if follow:
            click.echo("Now following logs in real time, press CTRL+C to stop.")
            for line in tailer.follow(log):
                click.echo(line)

        click.echo(log.read())
    ctx.exit(0)
