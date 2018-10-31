
import ssl

import asynctest
import asynctest.mock as amock

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid import web
import aiohttp.web


class TestWeb(asynctest.TestCase):
    """Test the opsdroid web class."""

    def setUp(self):
        configure_lang({})

    async def test_web(self):
        """Create a web object and check the config."""
        with OpsDroid() as opsdroid:
            app = web.Web(opsdroid)
            self.assertEqual(app.config, {})

    async def test_web_get_port(self):
        """Check the port getter."""
        with OpsDroid() as opsdroid:
            opsdroid.config["web"] = {}
            app = web.Web(opsdroid)
            self.assertEqual(app.get_port, 8080)

            opsdroid.config["web"] = {"port": 8000}
            app = web.Web(opsdroid)
            self.assertEqual(app.get_port, 8000)

    async def test_web_get_host(self):
        """Check the host getter."""
        with OpsDroid() as opsdroid:
            opsdroid.config["web"] = {}
            app = web.Web(opsdroid)
            self.assertEqual(app.get_host, "127.0.0.1")

            opsdroid.config["web"] = {"host": "0.0.0.0"}
            app = web.Web(opsdroid)
            self.assertEqual(app.get_host, "0.0.0.0")

    async def test_web_get_ssl(self):
        """Check the host getter."""
        with OpsDroid() as opsdroid:
            opsdroid.config["web"] = {}
            app = web.Web(opsdroid)
            self.assertEqual(app.get_ssl_context, None)

            opsdroid.config["web"] = {"ssl":
                                      {"cert": "tests/ssl/cert.pem",
                                       "key": "tests/ssl/key.pem"}}
            app = web.Web(opsdroid)
            self.assertEqual(type(app.get_ssl_context),
                             type(ssl.SSLContext(ssl.PROTOCOL_SSLv23)))
            self.assertEqual(app.get_port, 8443)

            opsdroid.config["web"] = {"ssl":
                                      {"cert": "/path/to/nonexistant/cert",
                                       "key": "/path/to/nonexistant/key"}}
            app = web.Web(opsdroid)
            self.assertEqual(app.get_ssl_context, None)

    async def test_web_build_response(self):
        """Check the response builder."""
        with OpsDroid() as opsdroid:
            opsdroid.config["web"] = {}
            app = web.Web(opsdroid)
            response = {"test": "test"}
            resp = app.build_response(200, response)
            self.assertEqual(type(resp), aiohttp.web.Response)

    async def test_web_index_handler(self):
        """Check the index handler."""
        with OpsDroid() as opsdroid:
            opsdroid.config["web"] = {}
            app = web.Web(opsdroid)
            self.assertEqual(
                type(await app.web_index_handler(None)), aiohttp.web.Response)

    async def test_web_stats_handler(self):
        """Check the stats handler."""
        with OpsDroid() as opsdroid:
            opsdroid.config["web"] = {}
            app = web.Web(opsdroid)
            self.assertEqual(
                type(await app.web_stats_handler(None)), aiohttp.web.Response)

    async def test_web_start(self):
        """Check the stats handler."""
        with OpsDroid() as opsdroid:
            with amock.patch('aiohttp.web.AppRunner.setup') as mock_runner, \
                    amock.patch('aiohttp.web.TCPSite.__init__') as mock_tcpsite, \
                    amock.patch('aiohttp.web.TCPSite.start') as mock_tcpsite_start:
                mock_tcpsite.return_value = None
                app = web.Web(opsdroid)
                await app.start()
                self.assertTrue(mock_runner.called)
                self.assertTrue(mock_tcpsite.called)
                self.assertTrue(mock_tcpsite_start.called)

    async def test_web_stop(self):
        """Check the stats handler."""
        with OpsDroid() as opsdroid:
            app = web.Web(opsdroid)
            app.runner = amock.CoroutineMock()
            app.runner.cleanup = amock.CoroutineMock()
            await app.stop()
            self.assertTrue(app.runner.cleanup.called)
