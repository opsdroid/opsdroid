"""Test the opsdroid web."""
import json
import random
import ssl
from dataclasses import dataclass

import aiohttp.web
import asynctest.mock as amock
import pytest
from opsdroid import web
from opsdroid.cli.start import configure_lang
from opsdroid.testing import MINIMAL_CONFIG, call_endpoint, run_unit_test

configure_lang({})


@pytest.fixture
def command_center_config():
    MINIMAL_CONFIG["web"] = {
        "command-center": {"enabled": True, "token": "test-token"},
        # Need to pass a random port because opsdroid doesn't close
        # the connection quick enough. Tried to write a cleanup fixture
        # but didn't seem to work - most likely I was doing it wrong.
        "port": random.randrange(8000, 9000),
    }
    yield MINIMAL_CONFIG


@pytest.fixture
def command_center_config_no_token():
    MINIMAL_CONFIG["web"] = {
        "command-center": {"enabled": True},
        # Need to pass a random port because opsdroid doesn't close
        # the connection quick enough. Tried to write a cleanup fixture
        # but didn't seem to work - most likely I was doing it wrong.
        "port": random.randrange(8000, 9000),
    }
    yield MINIMAL_CONFIG


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
        "module_type": "connectors",
        "module_name": "shell",
        "config": {"enabled": False},
    }

    payload_dataclass = web.Payload.from_dict(request_payload)

    assert payload_dataclass.module_type == request_payload["module_type"]
    assert payload_dataclass.module_name == "shell"
    assert payload_dataclass.config == request_payload["config"]


def test_payload_raises_validation_exceptions():
    request_payload = {
        "module_type": "connectors",
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

    expected_error_message = "Received payload is missing required key: 'module_type',"

    with pytest.raises(KeyError, match=expected_error_message):
        web.Payload.from_dict(request_payload)

    request_payload = {
        "module_type": "web",
        "module_name": "port",
        "config": {"port": 80},
    }

    expected_error_message = "The change type 'web' is not a supported type."

    with pytest.raises(TypeError, match=expected_error_message):
        web.Payload.from_dict(request_payload)


def test_update_config(opsdroid):
    opsdroid.config = {"connectors": {"gitlab": {"webhook-token": "my-token"}}}
    app = web.Web(opsdroid)

    updated_config = app.update_config({"token": "123"}, "connectors", "gitlab")

    assert "token" in updated_config["connectors"]["gitlab"]
    assert updated_config["connectors"]["gitlab"] == {
        "webhook-token": "my-token",
        "token": "123",
    }


@pytest.mark.asyncio
async def test_get_scrubbed_module_config(opsdroid):
    app = web.Web(opsdroid)

    # This is an empty list as no modules are currently loaded
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

    # Let's check that modules obtained from self.opsdroid.modules
    # also work
    modules_list = opsdroid.modules.get("connectors")
    scrubbed_modules_config = app.get_scrubbed_module_config(modules_list)
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


@pytest.mark.asyncio
async def test_config_handler(opsdroid, command_center_config):
    config = {
        "logging": {"level": "debug"},
        "welcome-message": True,
        "web": {
            "command-center": {"enabled": True, "token": "test-token"},
        },
        "parsers": {"regex": {}, "crontab": {"enabled": False}},
        "connectors": {
            "gitlab": {"webhook-token": "secret-token", "token": "my-token"},
            "websocket": {
                "bot-name": "mybot",
                "max-connections": 10,
                "connection-timeout": 10,
            },
        },
        "databases": {"sqlite": {}},
    }
    await opsdroid.load(config)

    app = web.Web(opsdroid)

    app.check_request = amock.CoroutineMock()

    response = await app.config_handler(None)

    assert response.status == 200
    assert response.text

    payload = json.loads(response.text)

    gitlab_config = payload["connectors"]["gitlab"]
    assert "token" not in gitlab_config
    assert "webhook-token" not in gitlab_config


@pytest.mark.asyncio
async def test_base_url(opsdroid):
    opsdroid.config["web"] = {"base_url": "localhost"}
    app = web.Web(opsdroid)
    assert app.base_url == "localhost"

    opsdroid.config["web"] = {"base-url": "example.com"}
    app2 = web.Web(opsdroid)
    assert app2.base_url == "example.com"


@pytest.mark.asyncio
async def test_web_command_center_no_token(opsdroid, command_center_config_no_token):
    """Check that we get an exception if command centre and no token is provided"""
    await opsdroid.load(command_center_config_no_token)
    with pytest.raises(Exception, match="no authorization token"):
        app = web.Web(opsdroid)
        await app.start()


@pytest.mark.asyncio
async def test_check_request_no_token_provided(opsdroid, command_center_config):
    await opsdroid.load(config=command_center_config)

    async def test():
        resp = await call_endpoint(
            opsdroid,
            "/connectors",
            "GET",
        )
        assert resp.status == 403
        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_check_request(opsdroid, command_center_config):
    await opsdroid.load(config=command_center_config)

    async def test():
        resp = await call_endpoint(
            opsdroid,
            "/connectors",
            "GET",
            headers={"Authorization": "test-token"},
        )
        assert resp.status == 200
        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_check_request_empty_auth(opsdroid, command_center_config):
    await opsdroid.load(config=command_center_config)

    async def test():
        resp = await call_endpoint(
            opsdroid,
            "/connectors",
            "GET",
            headers={"Authorization": ""},
        )
        assert resp.status == 403
        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_check_request_bad_token(opsdroid):
    MINIMAL_CONFIG["web"] = {"command-center": {"enabled": True, "token": "blah"}}

    assert "command-center" in MINIMAL_CONFIG["web"]
    await opsdroid.load(config=MINIMAL_CONFIG)

    async def test():
        resp = await call_endpoint(
            opsdroid, "/connectors", "GET", headers={"Authorization": "Basic 123"}
        )
        assert resp.status == 403
        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_update_config_live(opsdroid, command_center_config):
    await opsdroid.load(config=command_center_config)

    async def test():
        data = {
            "module_type": "parsers",
            "module_name": "crontab",
            "config": {"enabled": True},
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "test-token",
        }
        resp = await call_endpoint(
            opsdroid, "/connectors", "PATCH", json=data, headers=headers
        )

        assert resp.status == 204
        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_handle_patch(opsdroid, command_center_config, caplog):
    await opsdroid.load(config=command_center_config)

    async def test_bad_json():
        data = {
            "module_type": "connectors",
            "module_name": "shell",
            "config": {"enabled": True},
        }

        resp = await call_endpoint(
            opsdroid,
            "/connectors",
            "PATCH",
            data=data,
            headers={"Authorization": "test-token"},
        )
        assert "Unable to decode json" in caplog.text
        assert "Unable to decode json" in resp.reason
        assert resp.status == 400
        return True

    assert await run_unit_test(opsdroid, test_bad_json)

    async def test_bad_type():
        data = {
            "module_type": "connectors",
            "module_name": 12,
            "config": {"enabled": True},
        }

        resp = await call_endpoint(
            opsdroid,
            "/connectors",
            "PATCH",
            json=data,
            headers={"Authorization": "test-token"},
        )
        assert resp.status == 400
        assert (
            "The field 'module_name' is of type '<class 'int'>', but should be of type '<class 'str'>'"
            in resp.reason
        )
        return True

    assert await run_unit_test(opsdroid, test_bad_type)

    async def test_key_error():
        data = {
            "module_type": "connectors",
            "module_name": "shell",
        }

        resp = await call_endpoint(
            opsdroid,
            "/connectors",
            "PATCH",
            json=data,
            headers={"Authorization": "test-token"},
        )
        assert resp.status == 400
        assert "Received payload is missing required key: 'config'" in resp.reason
        return True

    assert await run_unit_test(opsdroid, test_key_error)


@pytest.mark.asyncio
async def test_get_connectors(opsdroid, command_center_config):
    await opsdroid.load(config=command_center_config)

    async def test():
        resp = await call_endpoint(
            opsdroid,
            "/connectors",
            "GET",
            headers={"Authorization": "test-token"},
        )
        assert resp.status == 200
        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_get_databases(opsdroid, command_center_config):
    await opsdroid.load(config=command_center_config)

    async def test():
        resp = await call_endpoint(
            opsdroid, "/databases", "GET", headers={"Authorization": "test-token"}
        )
        assert resp.status == 200
        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_get_parsers(opsdroid, command_center_config):
    await opsdroid.load(config=command_center_config)

    async def test():
        resp = await call_endpoint(
            opsdroid, "/parsers", "GET", headers={"Authorization": "test-token"}
        )
        assert resp.status == 200
        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_get_skills(opsdroid, command_center_config):
    await opsdroid.load(config=command_center_config)

    async def test():
        resp = await call_endpoint(
            opsdroid, "/skills", "GET", headers={"Authorization": "test-token"}
        )
        assert resp.status == 200
        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_get_scrubbed_module_config_funky_module(opsdroid):
    @dataclass
    class Module:
        config: dict

    mock_module = Module(config={"enabled": True, "token": "very-secret-stuff!"})

    app = web.Web(opsdroid)

    scrubbed_config = app.get_scrubbed_module_config(module_list=[mock_module])

    assert "unknown_module" in scrubbed_config
    assert scrubbed_config == {"unknown_module": {"enabled": True}}
