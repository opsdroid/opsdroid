"""The logs subcommand for opsdroid cli."""


import click


@click.command()
@click.pass_context
def logs(ctx):
    """Open the log file with your favourite editor.

    By default this command will open the configuration file with
    vi/vim. If you have a different editor that you would like to sure,
    you need to change the environment variable - `EDITOR`.

    This file will be updated if you are using the configuration option
    `logging.path`. Notice that depending on your `logging.level` and how
    long you run opsdroid, this file will grow quite quickly.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    edit_files(ctx, None)
