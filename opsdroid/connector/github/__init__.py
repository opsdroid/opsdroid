"""A connector for GitHub."""
import json
import logging

import aiohttp

from opsdroid.connector import Connector
from opsdroid.message import Message


_LOGGER = logging.getLogger(__name__)
GITHUB_API_URL = "https://api.github.com"


class ConnectorGitHub(Connector):
    """A connector for GitHub."""

    def __init__(self, config):
        """Create the connector."""
        super().__init__(config)
        logging.debug("Loaded GitHub connector")
        self.config = config
        try:
            self.github_token = config["token"]
        except KeyError:
            _LOGGER.error("Missing auth token!"
                          "You must set 'token' in your config")
        self.name = self.config.get("name", "github")
        self.default_room = None
        self.opsdroid = None
        self.github_username = None

    async def connect(self, opsdroid):
        """Connect to GitHub."""
        self.opsdroid = opsdroid
        url = '{}/user?access_token={}'.format(
            GITHUB_API_URL, self.github_token)
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)
            if response.status >= 300:
                _LOGGER.error("Error connecting to github: %s",
                              response.text())
                return False
            _LOGGER.debug("Reading bot information...")
            bot_data = await response.json()
        _LOGGER.debug("Done.")
        self.github_username = bot_data["login"]

        self.opsdroid.web_server.web_app.router.add_post(
            "/connector/{}".format(self.name),
            self.github_message_handler)

    async def disconnect(self, opsdroid):
        """Disconnect from GitHub."""

    async def listen(self, opsdroid):
        """Listen for new message.

        Listening is handled by the aiohttp web server

        """

    async def github_message_handler(self, request):
        """Handle event from GitHub."""
        req = await request.post()
        payload = json.loads(req["payload"])
        try:
            if payload["action"] == "created" and "comment" in payload:
                issue_number = payload["issue"]["number"]
                body = payload["comment"]["body"]
            elif payload["action"] == "opened" and "issue" in payload:
                issue_number = payload["issue"]["number"]
                body = payload["issue"]["body"]
            elif payload["action"] == "opened" and "pull_request" in payload:
                issue_number = payload["pull_request"]["number"]
                body = payload["pull_request"]["body"]
            else:
                _LOGGER.debug("No message to respond to.")
                _LOGGER.debug(payload)
                return aiohttp.web.Response(
                    text=json.dumps("No message to respond to."),
                    status=200)

            issue = "{}/{}#{}".format(payload["repository"]["owner"]["login"],
                                      payload["repository"]["name"],
                                      issue_number)
            message = Message(body,
                              payload["sender"]["login"],
                              issue,
                              self)
            await self.opsdroid.parse(message)
        except KeyError as error:
            _LOGGER.error("Key %s not found in payload", error)
            _LOGGER.debug(payload)
        return aiohttp.web.Response(
            text=json.dumps("Received"), status=201)

    async def respond(self, message, room=None):
        """Respond with a message."""
        # stop immediately if the message is from the bot itself.
        if message.user == self.github_username:
            return True
        _LOGGER.debug("Responding via GitHub")
        repo, issue = message.room.split('#')
        url = "{}/repos/{}/issues/{}/comments".format(
            GITHUB_API_URL, repo, issue)
        headers = {'Authorization': ' token {}'.format(self.github_token)}
        async with aiohttp.ClientSession() as session:
            resp = await session.post(url,
                                      json={"body": message.text},
                                      headers=headers)
            if resp.status == 201:
                _LOGGER.info("Message sent.")
                return True
            _LOGGER.error(await resp.json())
            return False
