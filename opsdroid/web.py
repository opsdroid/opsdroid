"""Submodule to handle web requests in opsdroid."""

import json
import logging
import ssl

from aiohttp import web

from opsdroid import __version__


_LOGGER = logging.getLogger(__name__)


class Web:
    """Web server for opsdroid."""

    def __init__(self, opsdroid):
        """Create web object."""
        self.opsdroid = opsdroid
        try:
            self.config = self.opsdroid.config["web"]
        except KeyError:
            self.config = {}
        self.web_app = web.Application(loop=self.opsdroid.eventloop)
        self.web_app.router.add_get('/', self.web_index_handler)
        self.web_app.router.add_get('', self.web_index_handler)
        self.web_app.router.add_get('/stats', self.web_stats_handler)
        self.web_app.router.add_get('/stats/', self.web_stats_handler)

    @property
    def get_port(self):
        """Return port from config or the default."""
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
        """Return host from config or the default."""
        try:
            host = self.config["host"]
        except KeyError:
            host = '127.0.0.1'
        return host

    @property
    def get_ssl_context(self):
        """Return the ssl context or None."""
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

    def start(self):
        """Start web servers."""
        _LOGGER.debug(_(
            "Starting web server with host %s and port %s"),
                      self.get_host, self.get_port)
        web.run_app(self.web_app, host=self.get_host,
                    port=self.get_port, print=_LOGGER.info,
                    ssl_context=self.get_ssl_context)

    @staticmethod
    def build_response(status, result):
        """Build a json response object."""
        return web.Response(text=json.dumps(result), status=status)

    def web_index_handler(self, request):
        """Handle root web request."""
        return self.build_response(200, {
            "message": "Welcome to the opsdroid API"})

    def web_stats_handler(self, request):
        """Handle stats request."""
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
