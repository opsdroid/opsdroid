"""The logs subcommand for opsdroid cli."""

import click
import tailer
from opsdroid.const import DEFAULT_LOG_FILENAME

lines_argument = click.argument("lines", type=click.INT, required=False, default=20)


@click.group(invoke_without_command=True)
@click.pass_context
def logs(ctx):
    """Print the content of the log file into the terminal.

    Open opsdroid logs and prints the contents of the file into the terminal.
    Since the logs can grow quite quickly, expect a large amount of lines being
    printed into your terminal.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    if not ctx.invoked_subcommand:
        with open(DEFAULT_LOG_FILENAME, "r") as log:
            click.echo(log.read())
        ctx.exit(0)


@logs.command()
@click.pass_context
@lines_argument
@click.option("-f", "follow", is_flag=True, help="Print the logs in real time")
def tail(ctx, lines, follow):
    """Print the last lines of the logs.

    By default this subcommand will print the last 5 lines of the logs, but this can be
    changed if you pass an integer after calling the subcommand like such `opsdroid logs tail 10`
    this will print the last 10 lines instead of the default 20.

    Alternatively you can also add the `-f` flag to the subcommand to follow the logs in real time.
    If this flag is passed no logs will be shown unless they are received from the bot.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        lines(int): Number of lines that should be shown from the end up.
        follow(bool): Flag that sets the subcommand to print the logs in real time.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    with open(DEFAULT_LOG_FILENAME) as file:
        if follow:
            click.echo("Now following logs in real time, press CTRL+C to stop.")
            for line in tailer.follow(file):
                click.echo(line)

        for line in tailer.tail(file, lines):
            click.echo(line)
            ctx.exit(0)


@logs.command()
@click.pass_context
@lines_argument
def head(ctx, lines):
    """Print the first lines of the logs.

    This subcommand by default will print the first 5 lines from the logs. But you can change
    the default number by passing an int to the subcommand like such: `opsdroid logs head 50`.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        lines(int): Number of lines that should be shown from the end up.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    with open(DEFAULT_LOG_FILENAME) as file:
        for line in tailer.head(file, lines):
            click.echo(line)

    ctx.exit(0)
