"""Test the opsdroid web."""
import ssl

import aiohttp.web
import asynctest.mock as amock
import pytest
from opsdroid import web
from opsdroid.cli.start import configure_lang

configure_lang({})


async def test_web(opsdroid):
    """Create a web object and check the config."""
    app = web.Web(opsdroid)
    assert app.config == {}


async def test_web_get_port(opsdroid):
    """Check the port getter."""
    opsdroid.config["web"] = {}
    app = web.Web(opsdroid)
    assert app.get_port == 8080

    opsdroid.config["web"] = {"port": 8000}
    app = web.Web(opsdroid)
    assert app.get_port == 8000


async def test_web_get_host(opsdroid):
    """Check the host getter."""
    opsdroid.config["web"] = {}
    app = web.Web(opsdroid)
    assert app.get_host == "0.0.0.0"

    opsdroid.config["web"] = {"host": "127.0.0.1"}
    app = web.Web(opsdroid)
    assert app.get_host == "127.0.0.1"


async def test_web_disable_web_index_handler_in_root(opsdroid):
    """Check disabling of web index handler in root."""
    opsdroid.config["web"] = {"disable_web_index_handler_in_root": True}
    app = web.Web(opsdroid)
    canonicals = [resource.canonical for resource in app.web_app._router.resources()]
    assert "/" not in canonicals

    opsdroid.config["web"] = {"disable_web_index_handler_in_root": False}
    app = web.Web(opsdroid)
    canonicals = [resource.canonical for resource in app.web_app._router.resources()]
    assert "/" in canonicals

    opsdroid.config["web"] = {}
    app = web.Web(opsdroid)
    canonicals = [resource.canonical for resource in app.web_app._router.resources()]
    assert "/" in canonicals


async def test_web_get_ssl(opsdroid):
    """Check the host getter."""
    opsdroid.config["web"] = {}
    app = web.Web(opsdroid)
    assert app.get_ssl_context is None

    opsdroid.config["web"] = {
        "ssl": {"cert": "tests/ssl/cert.pem", "key": "tests/ssl/key.pem"}
    }
    app = web.Web(opsdroid)
    assert isinstance(app.get_ssl_context, type(ssl.SSLContext(ssl.PROTOCOL_SSLv23)))
    assert app.get_port == 8443

    opsdroid.config["web"] = {
        "ssl": {"cert": "/path/to/nonexistant/cert", "key": "/path/to/nonexistant/key"}
    }
    app = web.Web(opsdroid)
    assert app.get_ssl_context is None


async def test_web_build_response(opsdroid):
    """Check the response builder."""
    opsdroid.config["web"] = {}
    app = web.Web(opsdroid)
    response = {"test": "test"}
    resp = app.build_response(200, response)
    assert type(resp) == aiohttp.web.Response


async def test_web_index_handler(opsdroid):
    """Check the index handler."""
    opsdroid.config["web"] = {}
    app = web.Web(opsdroid)
    assert type(await app.web_index_handler(None)) == aiohttp.web.Response


async def test_web_stats_handler(opsdroid):
    """Check the stats handler."""
    opsdroid.config["web"] = {}
    app = web.Web(opsdroid)
    assert type(await app.web_stats_handler(None)) == aiohttp.web.Response


async def test_web_start(opsdroid):
    """Check the stats handler."""
    with amock.patch("aiohttp.web.AppRunner.setup") as mock_runner, amock.patch(
        "aiohttp.web.TCPSite.__init__"
    ) as mock_tcpsite, amock.patch("aiohttp.web.TCPSite.start") as mock_tcpsite_start:
        mock_tcpsite.return_value = None
        app = web.Web(opsdroid)
        await app.start()
        assert mock_runner.called
        assert mock_tcpsite.called
        assert mock_tcpsite_start.called


async def test_web_stop(opsdroid):
    """Check the stats handler."""
    app = web.Web(opsdroid)
    app.runner = amock.CoroutineMock()
    app.runner.cleanup = amock.CoroutineMock()
    await app.stop()
    assert app.runner.cleanup.called


async def test_web_port_in_use(opsdroid, bound_address):
    """Check retry/timeout handling when the port is in use."""
    opsdroid.config["web"] = {"host": bound_address[0], "port": bound_address[1]}
    app = web.Web(opsdroid)
    app.start_timeout = 0.5  # no need to retry for 10 seconds
    # linux: Errno 98 (ADDRINUSE)
    # windows: Errno 10013 (WSAEACCESS) or 10048 (WSAEADDRINUSE)
    with pytest.raises(OSError):
        await app.start()


def test_payload():
    request_payload = {
        "change_type": "connector",
        "module_name": "shell",
        "config": {"enabled": False},
    }

    payload_dataclass = web.Payload.from_dict(request_payload)

    assert payload_dataclass.change_type == request_payload["change_type"]
    assert payload_dataclass.module_name == "shell"
    assert payload_dataclass.config == request_payload["config"]


def test_payload_raises_validation_exceptions():
    request_payload = {
        "change_type": "connector",
        "module_name": 1,
        "config": {"enabled": False},
    }

    expected_error_message = (
        "The field 'module_name' is of type '<class 'int'>', but should "
        "be of type '<class 'str'>'"
    )

    with pytest.raises(TypeError, match=expected_error_message):
        web.Payload.from_dict(request_payload)

    request_payload = {"module_name": "shell"}

    expected_error_message = "Received payload is missing required key: 'change_type',"

    with pytest.raises(KeyError, match=expected_error_message):
        web.Payload.from_dict(request_payload)

    request_payload = {
        "change_type": "web",
        "module_name": "port",
        "config": {"port": 80},
    }

    expected_error_message = "The change type 'web' is not a supported type."

    with pytest.raises(TypeError, match=expected_error_message):
        web.Payload.from_dict(request_payload)


def test_update_config(opsdroid):
    opsdroid.config = {"connectors": {"gitlab": {"webhook-token": "my-token"}}}
    app = web.Web(opsdroid)

    with pytest.raises(KeyError, match="Unable to update configuration"):
        app.update_config({"token": "123"}, "connectors", "github")
        app.update_config({"new": "config"}, "parsers", "rasa")

    updated_config = app.update_config({"token": "123"}, "connectors", "gitlab")

    assert "token" in updated_config["connectors"]["gitlab"]
    assert updated_config["connectors"]["gitlab"] == {
        "webhook-token": "my-token",
        "token": "123",
    }


@pytest.mark.asyncio
async def test_get_scrubbed_module_config(opsdroid):
    app = web.Web(opsdroid)

    # This is an empty list
    module_list = opsdroid.connectors
    scrubbed_config = app.get_scrubbed_module_config(module_list)

    # Since the module_list is empty, we should get an empty dict.
    assert scrubbed_config == {}

    # Let's load some modules and see if it works
    config = {"connectors": {"shell": {"token": "123"}}}

    await opsdroid.load(config)
    connectors_list = opsdroid.connectors
    scrubbed_modules_config = app.get_scrubbed_module_config(connectors_list)
    assert "token" not in scrubbed_modules_config["shell"]
    assert "name" in scrubbed_modules_config["shell"]
    assert "type" in scrubbed_modules_config["shell"]
    assert "enabled" in scrubbed_modules_config["shell"]


@pytest.mark.asyncio
async def test_get_scrubbed_module_config_with_user_provided_keys(opsdroid):
    """

    Let's test that user provided keys are removed as well. Scrubbed logs with only
    the default keys set, will contain the following keys:
    ['name', 'module', 'type', 'enabled', 'entrypoint', 'module_path', 'install_path', 'branch']

    """
    config = {
        "web": {
            "command-center": {
                "enabled": True,
                "excluded-keys": ["module", "type", "enabled"],
            }
        },
        "connectors": {"shell": {"token": "456"}},
    }

    await opsdroid.load(config)

    app = web.Web(opsdroid)
    connectors_list = opsdroid.connectors
    extra_scrubbed_config = app.get_scrubbed_module_config(connectors_list)
    assert "module" not in extra_scrubbed_config["shell"]
    assert "type" not in extra_scrubbed_config["shell"]
    assert "enabled" not in extra_scrubbed_config["shell"]
    assert "name" in extra_scrubbed_config["shell"]
    assert "install_path" in extra_scrubbed_config["shell"]
