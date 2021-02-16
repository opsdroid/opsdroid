"""A connector for GitHub."""
import json
import logging

import aiohttp

from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message
from . import events as github_events


_LOGGER = logging.getLogger(__name__)
GITHUB_API_URL = "https://api.github.com"
CONFIG_SCHEMA = {Required("token"): str}


class ConnectorGitHub(Connector):
    """A connector for GitHub."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        logging.debug("Loaded GitHub connector.")
        try:
            self.github_token = config["token"]
        except KeyError:
            _LOGGER.error(_("Missing auth token! You must set 'token' in your config."))
        self.name = self.config.get("name", "github")
        self.opsdroid = opsdroid
        self.github_username = None
        self.github_api_url = self.config.get("api_base_url", GITHUB_API_URL)

    async def connect(self):
        """Connect to GitHub."""
        headers = {"Authorization": f"token {self.github_token}"}
        async with aiohttp.ClientSession(trust_env=True, headers=headers) as session:
            url = f"{self.github_api_url}/user"
            response = await session.get(url)
            if response.status >= 300:
                response_text = await response.text()
                _LOGGER.error(_("Error connecting to GitHub: %s."), response_text)
                return False
            _LOGGER.debug(_("Reading bot information..."))
            bot_data = await response.json()
        _LOGGER.debug(_("Done."))
        self.github_username = bot_data["login"]

        self.opsdroid.web_server.web_app.router.add_post(
            "/connector/{}".format(self.name), self.github_message_handler
        )

    async def disconnect(self):
        """Disconnect from GitHub."""

    async def listen(self):
        """Listen for new message.

        Listening is handled by the aiohttp web server

        """

    async def github_message_handler(self, request):
        """Handle event from GitHub."""
        req = await request.post()
        payload = json.loads(req["payload"])
        try:
            repo = f"{payload['repository']['owner']['login']}/{payload['repository']['name']}#"
            user = payload["sender"]["login"]
            if payload["action"] == "created" and "comment" in payload:
                event = github_events.IssueCommented(
                    comment=payload["comment"]["body"],
                    user=user,
                    issue_title=payload["issue"]["tittle"],
                    comment_url=payload["comment"]["body"],
                    target=f"{repo}{payload['issue']['number']}",
                    connector=self,
                    raw_event=payload,
                )
            elif payload["action"] == "opened" and "issue" in payload:
                event = github_events.IssueCreated(
                    title=payload["issue"]["title"],
                    description=payload["issue"]["body"],
                    user=user,
                    target=f"{repo}{payload['issue']['number']}",
                    connector=self,
                    raw_event=payload,
                )
            elif payload["action"] == "closed" and "issue" in payload:
                event = github_events.IssueClosed(
                    title=payload["issue"]["title"],
                    user=user,
                    description=payload["issue"]["body"],
                    target=f"{repo}{payload['issue']['number']}",
                    connector=self,
                    raw_event=payload,
                )
            elif payload["action"] == "opened" and "pull_request" in payload:
                event = github_events.PROpened(
                    title=payload["pull_request"]["title"],
                    description=payload["pull_request"]["body"],
                    user=user,
                    target=f"{repo}{payload['pull_request']['number']}",
                    connector=self,
                    raw_event=payload,
                )
            elif payload["action"] == "opened" and "pull_request" in payload:
                event = github_events.PRMerged(
                    title=payload["pull_request"]["title"],
                    description=payload["pull_request"]["body"],
                    user=payload["pull_request"]["user"]["login"],
                    merger=payload["pull_request"]["merged_by"]["login"],
                    target=f"{repo}{payload['pull_request']['number']}",
                    connector=self,
                    raw_event=payload,
                )
            else:
                _LOGGER.debug(_("No message to respond to."))
                _LOGGER.debug(payload)
                return aiohttp.web.Response(
                    text=json.dumps("No message to respond to."), status=200
                )

            await self.opsdroid.parse(event)
        except KeyError as error:
            _LOGGER.error(_("Key %s not found in payload."), error)
            _LOGGER.debug(payload)
        return aiohttp.web.Response(text=json.dumps("Received"), status=201)

    # @register_event(Message)
    # async def send_message(self, message):
    #     """Respond with a message."""
    #     # stop immediately if the message is from the bot itself.
    #     if message.user == self.github_username:
    #         return True
    #     _LOGGER.debug(_("Responding via GitHub."))
    #     repo, issue = message.target.split("#")
    #     url = "{}/repos/{}/issues/{}/comments".format(self.github_api_url, repo, issue)
    #     headers = {"Authorization": " token {}".format(self.github_token)}
    #     async with aiohttp.ClientSession(trust_env=True) as session:
    #         resp = await session.post(url, json={"body": message.text}, headers=headers)
    #         if resp.status == 201:
    #             _LOGGER.info(_("Message sent."))
    #             return True
    #         _LOGGER.error(await resp.json())
    #         return False
    @register_event(Message)
    async def pass_message(self, message):
        pass
