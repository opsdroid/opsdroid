"""Submodule to handle web requests in opsdroid."""

import asyncio
import json
import logging
import ssl

from aiohttp import web

from opsdroid import __version__
from opsdroid.helper import Timeout


_LOGGER = logging.getLogger(__name__)


class Web:
    """Create class for opsdroid Web server."""

    start_timeout = 10  # seconds

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
        if not self.config.get("disable_web_index_handler_in_root", False):
            self.web_app.router.add_get("/", self.web_index_handler)
            self.web_app.router.add_get("", self.web_index_handler)

        self.web_app.router.add_get("/stats", self.web_stats_handler)
        self.web_app.router.add_get("/stats/", self.web_stats_handler)

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
            host = "0.0.0.0"
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

    @property
    def base_url(self):
        """Return the base url of the opsdroid web server."""
        if self.config.get("base_url"):
            return self.config.get("base_url")
        protocol = "http" if self.get_ssl_context is None else "https"
        return f"{protocol}://{self.get_host}:{self.get_port}"

    async def start(self):
        """Start web servers."""
        _LOGGER.info(_(f"Started web server on {self.base_url}"))
        await self.runner.setup()

        timeout = Timeout(self.start_timeout, "Timed out starting web server")
        while timeout.run():
            try:
                # We need to recreate the site each time we retry after an OSError.
                # Just repeatedly calling site.start() results in RuntimeErrors that
                # say the site was already registered in the runner.
                self.site = web.TCPSite(
                    self.runner,
                    host=self.get_host,
                    port=self.get_port,
                    ssl_context=self.get_ssl_context,
                )
                await self.site.start()
                break
            except OSError as e:
                await asyncio.sleep(0.1)
                timeout.set_exception(e)
                await self.site.stop()

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
            webhook_token = self.config.get("webhook-token", None)
            authorization_header = []
            if req is not None:
                authorization_header = req.headers.get("Authorization", "").split()

            if webhook_token is not None:
                if not (
                    len(authorization_header) == 2
                    and authorization_header[0] == "Bearer"
                    and authorization_header[1] == webhook_token
                ):
                    _LOGGER.error(
                        _("Unauthorized to run skill %s via webhook"), webhook
                    )
                    return Web.build_response(403, {"called_skill": webhook})

            _LOGGER.info(_("Running skill %s via webhook."), webhook)
            opsdroid.stats["webhooks_called"] = opsdroid.stats["webhooks_called"] + 1
            resp = await opsdroid.run_skill(skill, config, req)
            if isinstance(resp, web.Response):
                return resp
            return Web.build_response(200, {"called_skill": webhook})

        self.web_app.router.add_post(
            "/skill/{}/{}".format(skill.config["name"], webhook), wrapper
        )
        self.web_app.router.add_post(
            "/skill/{}/{}/".format(skill.config["name"], webhook), wrapper
        )

    def setup_webhooks(self, skills):
        """Add the webhooks for the webhook skills to the router."""
        for skill in skills:
            for matcher in skill.matchers:
                if "webhook" in matcher:
                    self.register_skill(self.opsdroid, skill, matcher["webhook"])

    async def web_index_handler(self, request):
        """Handle root web request to opsdroid API.

        Args:
            request: web request to the root (index)

        Returns:
            dict: returns successful status code and greeting for the root page

        """
        return self.build_response(200, {"message": "Welcome to the opsdroid API"})

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
            stats["average_response_time"] = (
                stats["total_response_time"] / stats["total_responses"]
            )
        except ZeroDivisionError:
            stats["average_response_time"] = 0

        return self.build_response(
            200,
            {
                "version": __version__,
                "messages": {
                    "total_parsed": stats["messages_parsed"],
                    "webhooks_called": stats["webhooks_called"],
                    "total_response_time": stats["total_response_time"],
                    "total_responses": stats["total_responses"],
                    "average_response_time": stats["average_response_time"],
                },
                "modules": {
                    "skills": len(self.opsdroid.skills),
                    "connectors": len(self.opsdroid.connectors),
                    "databases": len(self.opsdroid.memory.databases),
                },
            },
        )
