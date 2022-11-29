# import logging
# import pytest
# import asynctest.mock as amock

# import asyncio

from opsdroid.connector.discord import ConnectorDiscord

# from opsdroid.events import Message


def test_init(opsdroid):
    connector = ConnectorDiscord({}, opsdroid)
    assert connector.default_target is None
    assert connector.name == "discord"
    assert connector.bot_name == "opsdroid"
    config = {"name":"toto",
              "bot-name":"bot",
              "token":"token"}
    connector = ConnectorDiscord(config,opsdroid)
    assert connector.name == "toto"
    assert connector.bot_name == "bot"
    