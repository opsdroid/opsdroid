"""A connector for GitHub."""
import hashlib
import hmac
import json
import jwt
import logging
import time

import aiohttp
from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

from . import events as github_events

_LOGGER = logging.getLogger(__name__)
GITHUB_API_URL = "https://api.github.com"
CONFIG_SCHEMA = {"token": str, "private_key_file": str, "app_id": int, "secret": str}


class ConnectorGitHub(Connector):
    """A connector for GitHub."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        logging.debug("Loaded GitHub connector.")
        self.name = config.get("name", "github")
        self.opsdroid = opsdroid
        self.github_username = None
        self.github_api_url = self.config.get("api_base_url", GITHUB_API_URL)
        try:
            if config.get("token"):
                self.github_token = config["token"]
            else:
                self.private_key_file = config["private_key_file"]
                self.app_id = config["app_id"]
        except KeyError:
            _LOGGER.error(
                _(
                    "Missing auth token or app settings! You must either set an 'token' in your config or a 'private_key' and 'app_id'."
                )
            )

        self.secret = self.config.get("secret")
        if not self.secret:
            _LOGGER.warning(
                _(
                    "Secret is missing from your configuration. You should use it to improve security."
                )
            )

    async def connect(self):
        """Connect to GitHub."""
        if not hasattr(self, "github_token"):
            current_time = int(time.time())
            payload = {
                "iat": current_time - 60,
                "exp": current_time + (10 * 60),
                "iss": self.app_id,
            }
            private_key = open(self.private_key_file, "rt").read()
            installation_access_token = jwt.encode(
                payload, private_key, algorithm="RS256"
            ).decode("utf-8")
            headers = {"Authorization": f"Bearer {installation_access_token}"}

            async with aiohttp.ClientSession(
                trust_env=True, headers=headers
            ) as session:
                url = f"{self.github_api_url}/app/installations"
                response = await session.get(url)
                if response.status >= 300:
                    response_text = await response.text()
                    _LOGGER.error(_("Error connecting to GitHub: %s."), response_text)
                    return False
                _LOGGER.debug(_("Reading installation information..."))
                installations = await response.json()
                installation_id = installations[0]["id"]

            async with aiohttp.ClientSession(
                trust_env=True, headers=headers
            ) as session:
                url = f"{self.github_api_url}/app/installations/{installation_id}/access_tokens"
                response = await session.post(url)
                if response.status >= 300:
                    response_text = await response.text()
                    _LOGGER.error(_("Error connecting to GitHub: %s."), response_text)
                    return False
                _LOGGER.debug(_("Reading installation access token information..."))
                access_token = await response.json()
                self.github_token = access_token["token"]
        else:
            headers = {"Authorization": f"token {self.github_token}"}
            async with aiohttp.ClientSession(
                trust_env=True, headers=headers
            ) as session:
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

    async def validate_request(self, request, secret: str) -> bool:
        """Compute the sha256 hash of the request and secret.

        It's recommended that you select a secure secret when using webhooks, otherwise
        someone could craft a request in a way that might make the bot react to unexpected
        events that didn't come from github.

        You can read more about secrets here:
        https://docs.github.com/en/developers/webhooks-and-events/creating-webhooks#secret

        If no secret is provided then we will assume that the request is a valid one.

        """
        if self.secret:
            signature = request.headers.get("X-Hub-Signature-256")

            if signature:
                signature = signature.replace("sha256=", "")

            payload = await request.read()

            computed_hash = hmac.new(
                secret.encode(), msg=payload, digestmod=hashlib.sha256
            ).hexdigest()

            return signature == computed_hash
        return True

    async def handle_check_event(self, payload: dict, user: str) -> github_events:
        """Handle check events.

        Since we created a few check events, this method should make it
        easy to keep the ``github_message_handler`` a bit cleaner.

        """
        if payload["action"] == "created" in ["created", "rerequested"]:
            event = github_events.CheckStarted(
                action=payload["action"],
                status=payload["check_run"]["status"],
                conclusion=payload["check_run"]["conclusion"],
                repository=payload["repository"]["name"],
                sender=user,
            )

        elif payload["action"] == "completed":
            if payload["check_run"]["conclusion"] == "success":
                event = github_events.CheckPassed(
                    action=payload["action"],
                    status=payload["check_run"]["status"],
                    conclusion=payload["check_run"]["conclusion"],
                    repository=payload["repository"]["name"],
                    sender=user,
                )
            elif payload["check_run"]["conclusion"] == "failure":
                event = github_events.CheckFailed(
                    action=payload["action"],
                    status=payload["check_run"]["status"],
                    conclusion=payload["check_run"]["conclusion"],
                    repository=payload["repository"]["name"],
                    sender=user,
                )
            else:
                event = github_events.CheckCompleted(
                    action=payload["action"],
                    status=payload["check_run"]["status"],
                    conclusion=payload["check_run"]["conclusion"],
                    repository=payload["repository"]["name"],
                    sender=user,
                )
        return event

    async def handle_issue_event(
        self, payload: dict, repo: str, user: str
    ) -> github_events:
        """Handle issue events."""
        if payload["action"] == "opened":
            event = github_events.IssueCreated(
                title=payload["issue"]["title"],
                description=payload["issue"]["body"],
                user=user,
                target=f"{repo}{payload['issue']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "closed":
            event = github_events.IssueClosed(
                title=payload["issue"]["title"],
                user=payload["issue"]["user"]["login"],
                closed_by=user,
                description=payload["issue"]["body"],
                target=f"{repo}{payload['issue']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif "comment" in payload:
            event = github_events.IssueCommented(
                comment=payload["comment"]["body"],
                user=user,
                issue_title=payload["issue"]["title"],
                comment_url=payload["comment"]["url"],
                target=f"{repo}{payload['issue']['number']}",
                connector=self,
                raw_event=payload,
            )
        return event

    async def handle_pr_event(
        self, payload: dict, repo: str, user: str
    ) -> github_events:
        """Handle PR events."""
        if payload["action"] == "submitted" and "review" in payload:
            event = github_events.PRReviewSubmitted(
                body=payload["review"]["body"],
                user=user,
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "edited" and "review" in payload:
            event = github_events.PRReviewEdited(
                body=payload["review"]["body"],
                user=payload["review"]["user"]["login"],
                edited_by=user,
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "dismissed" and "review" in payload:
            event = github_events.PRReviewDismissed(
                body=payload["review"]["body"],
                user=payload["review"]["user"]["login"],
                dismissed_by=user,
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "created" and "comment" in payload:
            event = github_events.PRReviewCommentCreated(
                body=payload["comment"]["body"],
                user=user,
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "edited" and "comment" in payload:
            event = github_events.PRReviewCommentEdited(
                body=payload["comment"]["body"],
                user=payload["comment"]["user"]["login"],
                edited_by=user,
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "deleted" and "comment" in payload:
            event = github_events.PRReviewCommentDeleted(
                body=payload["comment"]["body"],
                user=payload["comment"]["user"]["login"],
                deleted_by=user,
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "opened":
            event = github_events.PROpened(
                title=payload["pull_request"]["title"],
                description=payload["pull_request"]["body"],
                user=payload["pull_request"]["user"]["login"],
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "reopened":
            event = github_events.PRReopened(
                title=payload["pull_request"]["title"],
                description=payload["pull_request"]["body"],
                user=payload["pull_request"]["user"]["login"],
                reopened_by=user,
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "edited":
            event = github_events.PREdited(
                title=payload["pull_request"]["title"],
                description=payload["pull_request"]["body"],
                user=payload["pull_request"]["user"]["login"],
                edited_by=user,
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "closed" and payload["pull_request"]["merged"]:
            event = github_events.PRMerged(
                title=payload["pull_request"]["title"],
                description=payload["pull_request"]["body"],
                user=payload["pull_request"]["user"]["login"],
                merged_by=payload["pull_request"]["merged_by"],
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        elif payload["action"] == "closed":
            event = github_events.PRClosed(
                title=payload["pull_request"]["title"],
                user=payload["pull_request"]["user"]["login"],
                closed_by=user,
                target=f"{repo}{payload['pull_request']['number']}",
                connector=self,
                raw_event=payload,
            )
        return event

    async def handle_push_event(
        self, payload: dict, repo: str, user: str
    ) -> github_events:
        """Handle PR events."""
        event = github_events.Push(
            user=user,
            pushed_by=payload["pusher"]["name"],
            target=payload["ref"],
            connector=self,
            raw_event=payload,
        )
        return event

    async def github_message_handler(self, request):
        """Handle event from GitHub."""
        try:
            payload = await request.json()
        except Exception:
            req = await request.post()
            payload = json.loads(req["payload"])
        is_valid_request = await self.validate_request(request, self.secret)

        if is_valid_request:
            try:
                repo = f"{payload['repository']['owner']['login']}/{payload['repository']['name']}#"
                user = payload["sender"]["login"]
                if "pusher" in payload:
                    event = await self.handle_push_event(payload, repo, user)
                elif payload["action"] == "labeled":
                    event = github_events.Labeled(
                        label_added=payload["label"]["name"],
                        labels=payload["issue"]["labels"],
                        state=payload["issue"]["state"],
                        user=user,
                        target=f"{repo}{payload['issue']['number']}",
                        connector=self,
                        raw_event=payload,
                    )
                elif payload["action"] == "unlabeled":
                    event = github_events.Unlabeled(
                        label_removed=payload["label"]["name"],
                        labels=payload["issue"]["labels"],
                        state=payload["issue"]["state"],
                        user=user,
                        target=f"{repo}{payload['issue']['number']}",
                        connector=self,
                        raw_event=payload,
                    )
                elif "issue" in payload:
                    event = await self.handle_issue_event(payload, repo, user)
                elif "pull_request" in payload:
                    event = await self.handle_pr_event(payload, repo, user)
                elif payload.get("check_run"):
                    event = await self.handle_check_event(payload, user)
                else:
                    _LOGGER.debug(
                        _("No message to respond to. Got payload: \n %s"), payload
                    )
                    return aiohttp.web.Response(
                        text=json.dumps("No message to respond to."), status=200
                    )
                await self.opsdroid.parse(event)
            except KeyError as error:
                _LOGGER.error(_("Key %s not found in payload."), error)
                _LOGGER.debug(payload)
            return aiohttp.web.Response(text=json.dumps("Received"), status=201)
        return aiohttp.web.Response(status=401)

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        # stop immediately if the message is from the bot itself.
        if message.user == self.github_username:
            return True
        _LOGGER.debug(_("Responding via GitHub."))
        repo, issue = message.target.split("#")
        url = f"{self.github_api_url}/repos/{repo}/issues/{issue}/comments"
        headers = {"Authorization": f" token {self.github_token}"}
        async with aiohttp.ClientSession(trust_env=True) as session:
            resp = await session.post(url, json={"body": message.text}, headers=headers)
            if resp.status == 201:
                _LOGGER.info(_("Message sent."))
                return True
            _LOGGER.error(await resp.json())
            return False
