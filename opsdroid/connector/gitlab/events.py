"""events.Events for the Gitlab Connector."""
from typing import Optional

from opsdroid import events


class GenericGitlabEvent(events.Event):
    """Event class that triggers when an unhandled event is sent."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class GitlabIssueCreated(events.Event):
    """Event class that triggers when a new issue is created."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class GitlabIssueClosed(events.Event):
    """Event class that triggers when an issue is closed."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class GitlabIssueEdited(events.Event):
    """Event class that triggers when an issue is edited."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class GitlabIssueLabeled(events.Event):
    """Event class that triggers when an issue is labeled."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class GenericIssueEvent(events.Event):
    """Event class that triggers when any other issue action happen."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class MRCreated(events.Event):
    """Event class that triggers when a MR is created."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class MRMerged(events.Event):
    """Event class that triggers when a MR is merged."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class MRClosed(events.Event):
    """Event class that triggers when a MR is closed."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class MRLabeled(events.Event):
    """Event class that triggers when a MR label is updated."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class MRApproved(events.Event):
    """Event class that triggers when a MR is approved."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels


class GenericMREvent(events.Event):
    """Event class that triggers when a Generic MR events.Event happens."""

    def __init__(
        self,
        project: str,
        user: str,
        title: Optional[str],
        description: Optional[str],
        labels: list,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.title = title
        self.description = description
        self.labels = labels
