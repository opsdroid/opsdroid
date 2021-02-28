"""Events for the GitHub Connector."""
from opsdroid import events


class IssueCreated(events.Event):
    """Event class that triggers when a new issue is created."""

    def __init__(self, title, user, description, *args, **kwargs):
        """Event that is triggered when a user creates a new issue.

        GitHub allows us to have access to a lot of things when a
        user creates a new issue. The most relevant information can
        be accessed with the following attributes:

        * ``title`` - The issue title
        * ``description`` - The full body of the issue
        * ``user`` - The user who created the issue

        """
        super().__init__(*args, **kwargs)
        self.title = title
        self.user = user
        self.description = description


class IssueClosed(events.Event):
    """Event class that triggers when an issue is closed."""

    def __init__(self, title, user, description, *args, **kwargs):
        """Event that is triggered when an issue is closed.

        GitHub allows us to have access to a lot of things when a
        user creates a new issue. The most relevant information can
        be accessed with the following attributes:

        * ``title`` - The issue title
        * ``description`` - The full body of the issue
        * ``user`` - The user who created the issue

        """
        super().__init__(*args, **kwargs)
        self.title = title
        self.user = user
        self.description = description


class IssueCommented(events.Event):
    """Event class that triggers when a user comments on an issue."""

    def __init__(self, comment, user, issue_title, comment_url, *args, **kwargs):
        """Event that is triggered when a user comment on an issue.

        * ``user`` - The user who created the issue
        * ``comment`` - The comment made by the user
        * ``issue_title` - The title of the issue where the user made the comment
        * ``comment_url`` - The URL of the comment

        """
        super().__init__(*args, **kwargs)
        self.user = user
        self.comment = comment
        self.issue_title = issue_title
        self.comment_url = comment_url


class PROpened(events.Event):
    """Event class that triggers when a PR is opened."""

    def __init__(self, title, user, description, *args, **kwargs):
        """Event that is triggered when a user opens a PR.


        * ``title`` - The PR title
        * ``description`` - The full body of the PR
        * ``user`` - The user who created the PR

        """
        super().__init__(*args, **kwargs)
        self.title = title
        self.user = user
        self.description = description


class PRMerged(events.Event):
    """Event class that triggers when a PR is merged."""

    def __init__(self, title, user, merger, description, *args, **kwargs):
        """Event that is triggered when a user merges a PR.


        * ``title`` - The PR title
        * ``description`` - The full body of the PR
        * ``user`` - The user who created the PR
        * ``merger`` - The user who merged the PR

        """
        super().__init__(*args, **kwargs)
        self.title = title
        self.user = user
        self.description = description
        self.merger = merger


class Labeled(events.Event):
    """Event class that triggers when an issue/PR is labeled.."""

    def __init__(self, labels, state, *args, **kwargs):
        """Event that is triggered when a user adds a label.

        Note that if a user creates a new issue/PR and labels it at the same time,
        GitHub will trigger two events, one for the issue/PR created and one for the
        labeling.

        The whole payload can be accessed through the ``raw_event`` attribute, you
        might see that the payload contains both a ``labels`` field and a ``label``
        field. In this event we only care about the labels one since the ``label``
        is the first one that you add and you might want to label the issue/PR with
        multiple labels. This allows you to iterate over the list of ``labels`` and
        do actions on it.

        * ``labels`` - A list of dicts, containing all the labels. Each label contains
            an ``id``, ``url``, `name``, ``color``, ``description``, ``default`` and
            ``node_id`` key.
        * ``state`` - The state of the issue/PR it can be opened or closed.

        """
        super().__init__(*args, **kwargs)
        self.labels = labels
        self.state = state


class Unlabeled(events.Event):
    """Event class that triggers when a label is removed from an issue/PR."""

    def __init__(self, labels, state, *args, **kwargs):
        """Event that is triggered when a user removes a label.

        If you have an issue/PR with multiple labels, you need to do some checking to
        figure out which label was removed from the list. This is because GitHub will
        update the ``labels`` list, but won't really tell you explicitly which label
        was removed from that list.

        You could keep a track of the ``labels`` list when you first received an ``Labeled``
        event and then check which label is missing from the list.

        Note that the labels list can be empty if we remove all the labels!

        * ``labels`` - A list of dicts, containing all the labels. Each label contains
            an ``id``, ``url``, `name``, ``color``, ``description``, ``default`` and
            ``node_id`` key.
        * ``state`` - The state of the issue/PR it can be opened or closed.

        """
        super().__init__(*args, **kwargs)
        self.labels = labels
        self.state = state
