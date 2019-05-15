"""Submodule to handle web requests in opsdroid."""

import json
import logging
import ssl

from aiohttp import web

from opsdroid import __version__


_LOGGER = logging.getLogger(__name__)


class Web:
    """Create class for opsdroid Web server."""

    def __init__(self, opsdroid):
        """Create web object."""
        self.opsdroid = opsdroid
        try:
            self.config = self.opsdroid.config["web"]
        except KeyError:
            self.config = {}
        self.web_app = web.Application()
        self.runner = web.AppRunner(self.web_app)
        self.site = None
        self.web_app.router.add_get('/', self.web_index_handler)
        self.web_app.router.add_get('', self.web_index_handler)
        self.web_app.router.add_get('/stats', self.web_stats_handler)
        self.web_app.router.add_get('/stats/', self.web_stats_handler)

    @property
    def get_port(self):
        """Return port from config or the default.

        Args:
            self: instance method

        Returns:
            int: returns value of port being used, config or default

        """
        try:
            port = self.config["port"]
        except KeyError:
            if self.get_ssl_context is not None:
                port = 8443
            else:
                port = 8080
        return port

    @property
    def get_host(self):
        """Return host from config or the default.

        Args:
            self: instance method

        Returns:
            string: returns address of host being used, config or default

        """
        try:
            host = self.config["host"]
        except KeyError:
            host = '0.0.0.0'
        return host

    @property
    def get_ssl_context(self):
        """Return the ssl context or None.

        Args:
            self: instance method

        Returns:
            string (or NoneType): returns ssl context of None.

        """
        try:
            ssl_config = self.config["ssl"]
            sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            sslcontext.load_cert_chain(ssl_config["cert"], ssl_config["key"])
            return sslcontext
        except FileNotFoundError:
            _LOGGER.error(_("Cannot find ssl cert or key."))
            return None
        except KeyError:
            return None

    async def start(self):
        """Start web servers."""
        _LOGGER.info(_("Started web server on %s://%s%s"),
                     "http" if self.get_ssl_context is None else "https",
                     self.get_host,
                     ":{}".format(self.get_port)
                     if self.get_port not in (80, 443) else "")
        await self.runner.setup()
        self.site = web.TCPSite(self.runner,
                                host=self.get_host,
                                port=self.get_port,
                                ssl_context=self.get_ssl_context)
        await self.site.start()

    async def stop(self):
        """Stop the web server."""
        await self.runner.cleanup()

    @staticmethod
    def build_response(status, result):
        """Build a json response object to power the bot reponses.

        Args:
            result: serialize obj as a JSON formated stream

        Returns:
            json: returns json object with list of responses for the bot

        """
        return web.Response(text=json.dumps(result), status=status)

    def register_skill(self, opsdroid, skill, webhook):
        """Register a new skill in the web app router."""
        async def wrapper(req, opsdroid=opsdroid, config=skill.config):
            """Wrap up the aiohttp handler."""
            _LOGGER.info(_("Running skill %s via webhook"), webhook)
            opsdroid.stats["webhooks_called"] = \
                opsdroid.stats["webhooks_called"] + 1
            resp = await skill(opsdroid, config, req)
            if isinstance(resp, web.Response):
                return resp
            return Web.build_response(200, {"called_skill": webhook})

        self.web_app.router.add_post(
            "/skill/{}/{}".format(skill.config["name"], webhook), wrapper)
        self.web_app.router.add_post(
            "/skill/{}/{}/".format(skill.config["name"], webhook), wrapper)

    def setup_webhooks(self, skills):
        """Add the webhooks for the webhook skills to the router."""
        for skill in skills:
            for matcher in skill.matchers:
                if "webhook" in matcher:
                    self.register_skill(
                        self.opsdroid, skill, matcher["webhook"]
                    )

    async def web_index_handler(self, request):
        """Handle root web request to opsdroid API.

        Args:
            request: web request to the root (index)

        Returns:
            dict: returns successful status code and greeting for the root page

        """
        return self.build_response(200, {
            "message": "Welcome to the opsdroid API"})

    async def web_stats_handler(self, request):
        """Handle stats request.

        Args:
            request: web request to render opsdroid stats

        Returns:
            dict: returns successful status code and dictionary with
                  stats requested

        """
        stats = self.opsdroid.stats
        try:
            stats["average_response_time"] = \
                stats["total_response_time"] / stats["total_responses"]
        except ZeroDivisionError:
            stats["average_response_time"] = 0

        return self.build_response(200, {
            "version": __version__,
            "messages": {
                "total_parsed": stats["messages_parsed"],
                "webhooks_called": stats["webhooks_called"],
                "total_response_time": stats["total_response_time"],
                "total_responses": stats["total_responses"],
                "average_response_time": stats["average_response_time"]
            },
            "modules": {
                "skills": len(self.opsdroid.skills),
                "connectors": len(self.opsdroid.connectors),
                "databases": len(self.opsdroid.memory.databases)
            }
        })
