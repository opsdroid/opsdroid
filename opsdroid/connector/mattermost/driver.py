import asyncio
import logging
import aiohttp
from typing import Coroutine, Callable, Any
from .endpoints.channels import Channels
from .endpoints.posts import Posts
from .endpoints.teams import Teams
from .endpoints.users import Users
from aiohttp import WSMsgType
import ssl
import os

_LOGGER = logging.getLogger(__name__)


class Driver:
    """
    Contains the client, api and provides you with functions for
    login, logout and initializing a websocket connection.
    """

    _default_options = {
        "scheme": "https",
        "url": "localhost",
        "port": 8065,
        "basepath": "/api/v4",
        "timeout": 30,
        "request_timeout": None,
        "token": None,
        "mfa_token": None,
        "auth": None,
        "keepalive": False,
        "keepalive_delay": 5,
        "websocket_kw_args": None,
        "debug": False,
        "http2": False,
        "proxy": None,
    }
    """
    Required options
        - url
        - token (https://docs.mattermost.com/developer/personal-access-tokens.html)

    Optional
        - scheme ('https')
        - port (8065)
        - timeout (30)
        - request_timeout (None)
        - mfa_token (None)
        - auth (None)
        - debug (False)

    Should not be changed
        - basepath ('/api/v4') - unlikely this would do any good
    """

    def __init__(self, options):
        """
        :param options: A dict with the values from `default_options`
        :type options: dict
        """
        self._options = self._default_options.copy()
        if options is not None:
            self._options.update(options)

        self._client = None

    async def connect(self):
        """Connects the driver to the server, afterwards you can start the websocket event loop."""

        if self._client is not None and not self._client.closed:
            self._client.__aexit__(None, None, None)

        # Honor the environment variable to stay compatible with the previous Mattermost library
        # which has used the `requests` library
        cafile = os.environ.get("REQUESTS_CA_BUNDLE")
        if cafile:
            connector = aiohttp.TCPConnector(
                ssl_context=ssl.create_default_context(cafile=cafile)
            )
        else:
            connector = None

        # The client must not be initialized in `__init__` because it automatically stores the current asyncio event loop.
        # There is no running event loop at the time of initialization, so subsequent calls even from within an event loop will fail.
        self._client = aiohttp.ClientSession(
            raise_for_status=True,  # raise exceptions when status codes >=300 are encountered
            trust_env=True,  # Takes proxy configuration from env variables
            headers=[  # add the token directly to the client so we don't have to pass it around
                (
                    "Authorization",
                    "Bearer {token:s}".format(token=self._options["token"]),
                )
            ],
            connector=connector,
        )
        return await self.users.get_user("me")

    def build_base_url(self):
        """
        Builds the base URL for all Mattermost API calls

        :return: String that does not end in a "`/`"
        """
        return "{scheme:s}://{url:s}:{port:s}{basepath:s}".format(
            scheme=self._options["scheme"],
            url=self._options["url"],
            port=str(self._options["port"]),
            basepath=self._options["basepath"],
        )

    @property
    def teams(self):
        """
        Api endpoint for teams

        :return: Instance of :class:`~endpoints.teams.Teams`
        """
        return Teams(self._client, self.build_base_url())

    @property
    def channels(self):
        """
        Api endpoint for channels

        :return: Instance of :class:`~endpoints.channels.Channels`
        """
        return Channels(self._client, self.build_base_url())

    @property
    def posts(self):
        """
        Api endpoint for posts

        :return: Instance of :class:`~endpoints.posts.Posts`
        """
        return Posts(self._client, self.build_base_url())

    @property
    def users(self):
        """
        Api endpoint for users

        :return: Instance of :class:`~endpoints.users.Users`
        """
        return Users(self._client, self.build_base_url())

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        _LOGGER.debug(
            _("Mattermost: driver teardown initiated"),
        )
        return await self._client.__aexit__(*exc_info)

    async def init_websocket(
        self, event_handler: Callable[[dict], Coroutine[Any, Any, None]]
    ):
        """
        Will initialize the websocket connection to the mattermost server.
        assumes you are async aware and returns a coroutine that can be awaited.
        It will not return until __aexit__ is called.

        This should be run after login(), to ensure that the token is valid first.

        See https://api.mattermost.com/v4/#tag/WebSocket for which
        websocket events mattermost sends.

        Example of a really simple event_handler function

        .. code:: python

                async def my_event_handler(message):
                        print(repr(message))


        :param event_handler: The function to handle the websocket events. Takes one argument.
        :type event_handler: Function(message)
        :return: coroutine
        """
        while not self._client.closed:
            try:
                await self._websocket_loop(event_handler)
            except ValueError:
                raise
            except (
                aiohttp.WebSocketError,
                aiohttp.ClientResponseError,
                aiohttp.ClientConnectionError,
                # when the aiohttp-connection is closed because of teardown, this error is sometimes raised instead of a more meaningful one
                AttributeError,
            ) as ex:
                _LOGGER.info(
                    _("Mattermost: An exception occured in the Websocket: '%s'"),
                    repr(ex),
                )
            except Exception as ex:
                _LOGGER.error(
                    _(
                        "Mattermost: An unexpected exception occured in the Websocket: '%s'"
                    ),
                    repr(ex),
                )
                raise ex

    async def _websocket_loop(
        self, event_handler: Callable[[dict], Coroutine[Any, Any, None]]
    ):
        """
        Internal loop for receiving websocket events from Mattermost.
        Exceptions are allowed to be raised in here, as the calling function contains
        the (semi-)infinite loop that only breaks if the driver object is closed.
        """
        _LOGGER.debug(
            _("Mattermost: started inner websocket loop"),
        )
        if self._options["scheme"] == "https":
            scheme = "wss"
        elif self._options["scheme"] == "http":
            scheme = "ws"
        else:
            raise ValueError(
                "Mattermost invalid scheme '%s'. Only 'http' and 'https' are supported!"
            )

        url = "{scheme:s}://{url:s}:{port:s}{basepath:s}/websocket".format(
            scheme=scheme,
            url=self._options["url"],
            port=str(self._options["port"]),
            basepath=self._options["basepath"],
        )

        async with self._client.ws_connect(
            url=url,
            autoping=True,
            heartbeat=self._options["timeout"],
        ) as websocket:
            await websocket.send_json(
                {
                    "seq": 1,
                    "action": "authentication_challenge",
                    "data": {"token": self._options["token"]},
                }
            )
            while not websocket.closed and not self._client.closed:
                received = await websocket.receive()
                _LOGGER.debug(_("Mattermost received message: '%s'"), repr(received))
                if received.type == WSMsgType.TEXT:
                    message = received.json()
                    # We want to pass the events to the event_handler already
                    # because the hello event could arrive before the authentication ok response
                    await event_handler(message)
                    if "seq" in message and message["seq"] == 0:
                        if "event" in message and message["event"] == "hello":
                            _LOGGER.info(_("Mattermost Websocket authentification OK"))
                        else:
                            _LOGGER.error(
                                _("Mattermost Websocket authentification failed")
                            )
                            break
                elif received.type in [WSMsgType.CLOSE, WSMsgType.ERROR]:
                    break  # this happens if Mattermost is restarted or the network connection is lost, etc.

        return await asyncio.sleep(1)  # allow for graceful websocket removal
