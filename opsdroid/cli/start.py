"""The start subcommand for opsdroid cli."""


import gettext
import logging
import signal
import anyio

import asyncclick as click
from opsdroid.cli.utils import (
    configure_lang,
    path_option,
    welcome_message,
)
from opsdroid.configuration import load_config_file, new_load_config_file
from opsdroid.const import DEFAULT_CONFIG_LOCATIONS
from opsdroid.core import OpsDroid
from opsdroid.logging import configure_logging

gettext.install("opsdroid")
_LOGGER = logging.getLogger("opsdroid")


@click.command()
@click.option("-f", "path", help="Load a configuration from a path instead of using the default location.", type=click.Path(exists=True))
async def start(path):
    """Start the opsdroid bot.

    If the `-f` flag is used with this command, opsdroid will load the
    configuration specified on that path otherwise it will use the default
    configuration.

    """

    config_path = [path] if path else DEFAULT_CONFIG_LOCATIONS
    config = await new_load_config_file(config_path)

    await anyio.to_thread.run_sync(configure_lang, config)
    await anyio.to_thread.run_sync(configure_logging, config.get("logging", {}))
    await anyio.to_thread.run_sync(welcome_message, config)
    await async_start(config, config_path)


async def async_start(config, config_path):
    # Create a task group
    async with anyio.create_task_group() as task_group:
        with OpsDroid(config=config, config_path=config_path, taskgroup=task_group) as opsdroid:
            task_group.start_soon(signal_handler, opsdroid, task_group.cancel_scope)
            task_group.start_soon(start_droid, opsdroid)


async def handle_signals(opsdroid, task_status=anyio.TASK_STATUS_IGNORED):
    """Handle signals."""
    async with anyio.open_signal_receiver(signal.SIGTERM, signal.SIGHUP) as signals:
        async for signum in signals:
            if signum == signal.SIGTERM:
                await opsdroid.stop()
            elif signum == signal.SIGHUP:
                await opsdroid.reload()
        task_status.started()

async def signal_handler(opsdroid, scope):
    with anyio.open_signal_receiver(signal.SIGTERM, signal.SIGHUP) as signals:
        async for signum in signals:
            if signum == signal.SIGTERM:
                await opsdroid.stop()
                scope.cancel()
            elif signum == signal.SIGHUP:
                await opsdroid.reload()
            return


async def start_droid(opsdroid):
    """Encapsulate the Opsdroid run to be callable by anyio.run()"""
    try:
        await opsdroid.new_run()
    except Exception as e:
        _LOGGER.exception(
            _("Something bad happened running OpsDroid")
        )
        raise e
