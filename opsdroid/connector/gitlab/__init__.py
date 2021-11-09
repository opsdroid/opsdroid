"""A connector for Gitlab."""
# import asyncio
import json

# import aiohttp
import logging

from aiohttp.web_request import Request
from aiohttp.web_response import Response


from typing import Optional
from opsdroid.connector.gitlab.events import MRApproved, MRClosed, MRCreated

from opsdroid.core import OpsDroid
from opsdroid.connector import Connector
from opsdroid.events import Event

# from opsdroid.events import Message

# from . import events as gitlab_events


CONFIG_SCHEMA = {"webhook-token": str, "forward-url": str}


_LOGGER = logging.getLogger(__name__)


class ConnectorGitlab(Connector):
    """A connector for Gitlab."""

    def __init__(self, config: dict, opsdroid: Optional[OpsDroid] = None):
        _LOGGER.debug(_("Starting Gitlab connector."))
        self.name = config.get("name", "gitlab")
        self.opsdroid = opsdroid
        self.webhook_token = config.get("webhook-token")
        try:
            self.base_url = opsdroid.config["web"]["base-url"]  # type: ignore
        except KeyError:
            self.base_url = config.get("forward-url")

    async def connect(self):
        """Connect method for Gitlab.

        This connector is using webhook events only. This method is used only to create
        the routes for the webhooks.

        """
        if self.opsdroid and self.opsdroid.web_server:
            self.opsdroid.web_server.web_app.router.add_post(
                f"/connector/{self.name}", self.gitlab_webhook_handler
            )

            _LOGGER.debug(
                _(f"Created webhook route '/connector/{self.name}' successfully.")
            )

    async def validate_request(self, request) -> bool:
        """Validate webhook request.

        Gitlab allow us to add a secret token to be added to the X-Gitlab-Token HTTP header,
        this method will simply check the request and compare the value of this header against
        the token that the user specified in the configuration.

        If no secret is specified in opsdroid configuration, then we are
        assuming that every request is a valid one. Note that, you should
        add a secret otherwise anyone could submit a POST request to the
        URL and pretent to be GitLab.

        """
        # TODO: Confirm type of request!
        _LOGGER.debug(f"Request is of type: {type(request)}")
        _LOGGER.debug(f"Request has headers: {request.headers}")
        gitlab_token = request.headers.get("X-Gitlab-Token")

        if self.webhook_token:
            return gitlab_token == self.webhook_token
        return True

    async def listen(self):
        """Listen method of the connector.

        Since we are using webhook events, this method does nothing.
        """

    async def gitlab_webhook_handler(self, request: Request) -> Response:
        """Handle event from Gitlab webhooks."""
        valid = await self.validate_request(request)
        payload = None
        try:
            payload = await request.json()
        # TODO: Narrow this exception!
        except Exception as error:
            _LOGGER.exception(
                _(
                    f"Unable to get JSON from request. Reason - {str(error)}. Request is: {request}"
                )
            )

        if valid and payload:
            attributes = payload.get("object_attributes", {})
            labels = await self.get_labels(payload)
            project_name = await self.get_project_name(payload)
            username = await self.get_username(payload)
            url = attributes.get("url", "")
            description = attributes.get("description")
            title = attributes.get("title")

            if payload.get("event_type") == "merge_request":
                event = await self.handle_merge_request_event(
                    labels=labels,
                    project_name=project_name,
                    username=username,
                    url=url,
                    title=title,
                    action=attributes.get("action"),
                    description=description,
                )

            await self.opsdroid.parse(event)
            return Response(text=json.dumps("Received"), status=200)
        return Response(text=json.dumps("Unauthorized"), status=401)

    async def get_labels(self, payload: dict) -> list:
        """Get labels from labels payload.

        Gitlab returns a list of dictionaries for each label added,
        we want to get a list of label titles only. This method will
        return just that.

        """
        labels = payload.get("labels", [])
        return [label["title"] for label in labels]

    async def get_project_name(self, payload: dict) -> str:
        """Get project name from payload.

        Helper method to get project name from the project section
        of the payload.

        """
        return payload.get("project", {}).get("name", "")

    async def get_username(self, payload: dict) -> str:
        """Get username from payload."""

        return payload.get("user", {}).get("username", "")

    async def handle_merge_request_event(
        self,
        labels: list,
        project_name: str,
        username: str,
        url: str,
        title: str,
        action: str,
        description: str,
    ) -> Event:
        """Handle Merge Request Events.

        When a user opens a MR Gitlab will throw an event, then when something
        happens within that particular MR (labels, commits, milestones), Gitlab
        will emit new events. This method handles all of these events based on
        the payload and builds the appropriate opsdroid events.

        """
        if action == "approved":
            event = MRApproved(
                project=project_name,
                user=username,
                title=title,
                description=description,
                url=url,
                labels=labels,
            )
        elif action == "opened":
            event = MRCreated(
                project=project_name,
                user=username,
                title=title,
                description=description,
                url=url,
                labels=labels,
            )
        elif action == "closed":
            event = MRClosed(
                project=project_name,
                user=username,
                title=title,
                description=description,
                url=url,
                labels=labels,
            )
        return event
