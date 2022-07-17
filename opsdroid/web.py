"""Submodule to handle web requests in opsdroid."""

import asyncio
import copy
import dataclasses
import json
import logging
import ssl
from json.decoder import JSONDecodeError
from typing import Optional

from aiohttp import web
from aiohttp.web import HTTPForbidden
from aiohttp.web_exceptions import HTTPBadRequest
from aiohttp_middlewares.cors import cors_middleware, DEFAULT_ALLOW_HEADERS

from opsdroid import __version__
from opsdroid.const import EXCLUDED_CONFIG_KEYS
from opsdroid.helper import Timeout

_LOGGER = logging.getLogger(__name__)

DEFAULT_HEADERS = list(
    DEFAULT_ALLOW_HEADERS
    + (
        "Host",
        "Content-Type",
        "Origin",
        "Content-Length",
        "Connection",
        "Accept",
        "User-Agent",
        "Referer",
        "Accept-Language",
        "Accept-Encoding",
        "Authorization",
    )
)


@dataclasses.dataclass
class Payload:
    module_type: str
    module_name: str
    config: dict

    def __post_init__(self):
        for name, field_type in self.__annotations__.items():
            provided_arg = self.__dict__[name]
            if not isinstance(provided_arg, field_type):
                raise TypeError(
                    f"The field '{name}' is of type '{type(provided_arg)}', but "
                    f"should be of type '{field_type}'"
                )

    @classmethod
    def from_dict(cls, payload: dict):
        """Create Payload object from dictionary."""
        required_keys = ("module_type", "module_name", "config")
        for key in required_keys:
            if key not in payload:
                raise KeyError(
                    f"Received payload is missing required key: '{key}', "
                    f"please include all required keys {required_keys} in "
                    "your payload."
                )

        module_type = payload["module_type"]

        allowed_module_types = ("connectors", "skills", "parsers", "config")

        if module_type not in allowed_module_types:
            raise TypeError(
                f"The change type '{module_type}' is not a supported type. "
                f"Please provide one of the allowed types {allowed_module_types}."
            )

        return cls(
            module_type=payload["module_type"],
            module_name=payload["module_name"],
            config=payload["config"],
        )


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
        self.cors = self.config.get("cors", {})
        self.web_app = web.Application(
            middlewares=[
                cors_middleware(
                    allow_all=self.cors.get("allow-all", True),
                    origins=self.cors.get("origins", ["*"]),
                    allow_headers=DEFAULT_HEADERS + self.cors.get("allow-headers", []),
                )
            ]
        )
        self.runner = web.AppRunner(self.web_app)
        self.site = None
        self.command_center = self.config.get("command-center", {})
        if not self.config.get("disable_web_index_handler_in_root", False):
            self.web_app.router.add_get("/", self.web_index_handler)
            self.web_app.router.add_get("", self.web_index_handler)

        self.excluded_keys = EXCLUDED_CONFIG_KEYS + self.command_center.get(
            "excluded-keys", []
        )
        self.authorization_token = self.command_center.get("token")
        if self.command_center and self.command_center.get("enabled"):
            self.web_app.router.add_get("/connectors", self.connectors_handler)
            self.web_app.router.add_get("/connectors/", self.connectors_handler)
            self.web_app.router.add_patch("/connectors", self.handle_patch)
            self.web_app.router.add_patch("/connectors/", self.handle_patch)
            self.web_app.router.add_get("/skills", self.skills_handler)
            self.web_app.router.add_get("/skills/", self.skills_handler)
            self.web_app.router.add_patch("/skills", self.handle_patch)
            self.web_app.router.add_patch("/skills/", self.handle_patch)
            self.web_app.router.add_get("/databases", self.databases_handler)
            self.web_app.router.add_get("/databases/", self.databases_handler)
            self.web_app.router.add_patch("/databases", self.handle_patch)
            self.web_app.router.add_patch("/databases/", self.handle_patch)
            self.web_app.router.add_get("/parsers", self.parsers_handler)
            self.web_app.router.add_get("/parsers/", self.parsers_handler)
            self.web_app.router.add_patch("/parsers", self.handle_patch)
            self.web_app.router.add_patch("/parsers/", self.handle_patch)
            self.web_app.router.add_get("/config", self.config_handler)
            self.web_app.router.add_get("/config/", self.config_handler)
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
        elif self.config.get("base-url"):
            return self.config.get("base-url")
        protocol = "http" if self.get_ssl_context is None else "https"
        return f"{protocol}://{self.get_host}:{self.get_port}"

    async def start(self):
        """Start web servers."""
        if self.command_center and not self.authorization_token:
            raise ValueError(
                "Command center is enabled, but no authorization token is set."
            )
        _LOGGER.info(_(f"started web server on {self.base_url}"))
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

    async def check_request(self, request):
        client_token = request.headers.get("Authorization")
        if (
            client_token is None
            or client_token != self.authorization_token
            or self.authorization_token is None
        ):
            raise HTTPForbidden()

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

    def get_scrubbed_module_config(self, module_list: Optional[list]) -> dict:
        """Get module config without sensitive keys.

        When reading the configuration from modules, there might be some
        sensitive information such as tokens, password. The configuration
        might have also pointers used for loading the module.

        This method will remove a list of default keys plus any extra keys
        that the user might ask to scrub when configuring command center.

        """
        config = {}
        if module_list:
            for module in module_list:
                try:
                    module_config = module.config.items()
                    try:
                        module_name = module.name
                    except AttributeError:
                        # Really modules should always have a name, the inmem database doesn't tho
                        module_name = module.config.get("name", "unknown_module")
                # If we are getting module from self.opsdroid.modules
                # we get a dictionary.
                except AttributeError:
                    module_config = module["config"].items()
                    module_name = module["config"]["name"]

                scrubbed_module_config = {
                    key: value
                    for key, value in module_config
                    if key not in self.excluded_keys
                }
                config[module_name] = scrubbed_module_config

        return config

    def update_config(
        self, provided_config: dict, module_type: str, module_name: str
    ) -> dict:
        """Update config from provided config.

        Users will be able to update the whole config or only parts
        of it - for example when toggling a module on/off all we need
        to do is set ``enabled: False``.

        This method will handle the update of the configuration by
        copying the current configuration, look for the ``module_type``
        and then update the ``module_name`` in the config.

        """
        config = copy.deepcopy(self.opsdroid.config)

        # If module type not in config add
        if module_type not in config:
            config[module_type] = {}
        # If module not in config, add it
        if module_name not in config[module_type]:
            config[module_type][module_name] = {}

        section = config[module_type][module_name]
        updated_module_config = {
            **config[module_type][module_name],
            **provided_config,
        }

        _LOGGER.debug(
            f"Original config: {section} was updated with {updated_module_config}"
        )

        config[module_type][module_name] = updated_module_config

        return config

    async def handle_patch(self, request):
        try:
            received_payload = await request.json()
            payload = Payload.from_dict(received_payload)
        except JSONDecodeError:
            data = await request.read()
            _LOGGER.error(f"Unable to decode json. Received - {data}")
            raise HTTPBadRequest(reason="Unable to decode json.")
        except (TypeError, KeyError) as error:
            raise HTTPBadRequest(reason=str(error))

        updated_config = self.update_config(
            provided_config=payload.config,
            module_type=payload.module_type,
            module_name=payload.module_name,
        )

        _LOGGER.debug(
            f"Configuration updated with user provided changes({payload.config}). "
            "Loading opsdroid configuration..."
        )

        [
            await module.disconnect()
            for module in self.opsdroid.connectors + self.opsdroid.memory.databases[:]
        ]

        await self.opsdroid.unload(unload_server=False)
        await self.opsdroid.load(updated_config)

        return web.Response(
            status=204,
            text=f"The module '{payload.module_name}' in the section '{payload.module_type}' was updated.",
        )

    async def connectors_handler(self, request):
        """Handle connectors request.

        Args:
            request: Web request to render opsdroid connectors

        Returns:
            dict: returns successful status code and dictionary with
                connectors.

        """
        await self.check_request(request)
        payload = self.get_scrubbed_module_config(self.opsdroid.connectors)
        return self.build_response(200, payload)

    async def skills_handler(self, request):
        """Handle get skills request.

        Args:
            request: Web request to render opsdroid skills

        Returns:
            dict: returns successful status code and dictionary with
                skills with their config scrubbed.

        """
        await self.check_request(request)
        payload = {
            connector.config["name"]: connector.config
            for connector in self.opsdroid.skills
        }

        return self.build_response(200, payload)

    async def databases_handler(self, request):
        """Handle get databases request.

        Args:
            request: Web request to render opsdroid databases

        Returns:
            dict: returns successful status code and dictionary with
                databases with their config scrubbed.

        """
        await self.check_request(request)
        databases_list = self.opsdroid.memory.databases[:]
        payload = self.get_scrubbed_module_config(databases_list)
        return self.build_response(200, payload)

    async def config_handler(self, request):
        """Handle get config request.

        Opsdroid config has different shapes, sometimes we get
        a string, other times we get a dictionary. Each section
        might return a single key and string as value, other times
        we might return a key and a dict as a value.

        This method is a bunch of for loops so we transverse the
        config shape, check if the values are in the list of
        ``self.excluded_keys``, if not we add them to the scrubbed
        config dictionary, otherwise we keep going.

        Args:
            request: Web request to render opsdroid config

        Returns:
            dict: returns successful status code and dictionary with
                the scrubbed config.

        """
        await self.check_request(request)

        scrubbed_config = {}
        for section, value in self.opsdroid.config.items():
            if isinstance(value, dict):
                scrubbed_config[section] = {}
                for module, config in value.items():
                    if isinstance(config, dict):
                        scrubbed_conf = {
                            key: value
                            for key, value in config.items()
                            if key not in self.excluded_keys
                        }
                        scrubbed_config[section][module] = scrubbed_conf
                    elif config not in self.excluded_keys:
                        scrubbed_config[section][module] = config
            elif value not in self.excluded_keys:
                scrubbed_config[section] = value

        return self.build_response(200, scrubbed_config)

    async def parsers_handler(self, request):
        """Handle get parsers request.

        Args:
            request: Web request to render opsdroid parsers

        Returns:
            dict: returns successful status code and dictionary with
                opsdroid parsers with their config scrubbed.

        """
        await self.check_request(request)
        # For some misterious reason this is returning None even though
        # self.opsdroid.modules is a dictionary?
        parsers_list = self.opsdroid.modules.get("parsers", [])
        payload = self.get_scrubbed_module_config(parsers_list)

        return self.build_response(200, payload)
