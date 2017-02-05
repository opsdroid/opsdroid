
import asynctest

from opsdroid.core import OpsDroid
from opsdroid import web
import aiohttp.web


class TestWeb(asynctest.TestCase):
    """Test the opsdroid web class."""

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
                type(app.web_index_handler(None)), aiohttp.web.Response)

    async def test_web_stats_handler(self):
        """Check the stats handler."""
        with OpsDroid() as opsdroid:
            opsdroid.config["web"] = {}
            app = web.Web(opsdroid)
            self.assertEqual(
                type(app.web_stats_handler(None)), aiohttp.web.Response)
