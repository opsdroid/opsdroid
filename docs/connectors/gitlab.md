# GitLab

A connector for [GitLab](https://gitlab.com). 

Note that this connector emits only upports sending messages back
to the event (Issue, Merge Request), if you need to create more elaborate workflow, please
use the [GitLab API](https://docs.gitlab.com/ee/api/) in your skill.

## Requirements

- A GitLab Account
- A repository setup with a [webhook](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)
- A [personal Access token](https://gitlab.com/-/profile/personal_access_tokens) if you want to send messages to GitLab

## Configuration

```yaml
connectors:
  gitlab:
    # Optional but recommended
    webhook-token: "my-very-secret-webhook-secret"
    # Required if you want opsdroid to reply to issues/MRs
    token: "<personal access token>"
```

## Setup Webhook

You need to [expose Opsdroid to the internet](../exposing.md), when you have your url, you can go to your repository, click **Settings** and then select **Webhook**, you can then add the url with the `connector/<connector name>` enpoint. For example, assume that you are using `example.com` as your base url and using this connector with the default name, you can use the following url `https://example.com/connector/gitlab` to receive events from your repository.

You can then choose a secret token - this will be your `webhook-token` in the Opsdroid configuration. It's highly recommended that you choose
a strong token to validate the requests coming into the `https://example.com/connector/gitlab` endpoint.

Finally, you can choose which events you want Gitlab to send you and choose if you want to turn off SSL verification. It's recommended that
you use SSL at all times.

## Examples

The GitLab connector allows you to send back a message when an event is triggered. This is a great way to automate some workflows. For example, let's assume that you want to thank every user that opens a new issue in your repository.

Here's a small example of how the opsdroid configuration looks like:

```yaml
connectors:
  gitlab:
  webhook-token: "my-secret-token"
  token: "my-personal-token"
skills:
  thankyou:
    path: "<skill pwd>"
```

Then you can create a new folder for your skill and write the following:

```python
from opsdroid.skill import Skill
from opsdorid.matchers import match_event
from opsdroid.connector.gitlab.events import GitlabIssueCreated
from opsdroid.events import Message

class ThankUser(Skill):
    def __init__(self, opsdroid, config, *args, **kwargs):
        super().__init__(opsdroid, config, *args, **kwargs)
        self.opsdroid = opsdroid
    
    @match_event(GitlabIssueCreated)
    async def say_thank_you(self, event):
        """Send message to issue, thanking user."""
        await event.respond(
            Message(
                text="Thank you for opening this issue, a team member will be with you shortly!",
                target=event.target
            )
        )
```

Now let's assume that you want to notify a slack channel every time a label was changed in an MR. This can be useful if you want to alert your team that an MR is ready for code review.

A more robust opsdroid configuration:

```yaml
connectors:
  gitlab:
    webhook-token: "/secret-t0k3n|"
    token: "<your secret token>"
  slack:
    bot-token: "<your token>"
    socket-mode: false
    bot-name: "Review-Bot"
    default-room: "#code-reviews"
skills:
  alert-team:
    path: "<skill pwd>"
```

The skill will look somewhat similar to the previous example with a few changes:

```python
from opsdroid.skill import Skill
from opsdorid.matchers import match_event
from opsdroid.connector.gitlab.events import GitlabIssueCreated
from opsdroid.events import Message

class AlertTeam(Skill):
    def __init__(self, opsdroid, config, *args, **kwargs):
        super().__init__(opsdroid, config, *args, **kwargs)
        self.opsdroid = opsdroid
    
    @match_event(MRLabeled)
    async def mr_labeled(self, event):
        """Send message slack if MR was labeled as code-review."""
        slack = self.opsdroid.get_connector("slack")
        if "code-review" in event.labels:
            await slack.send(
                Message(
                    text=f"Hey folks, the MR ({event.url}) was just marked as ready for review!",
                )
            )
```

This skill will trigger every time an MR gets labeled with something but only sends the message to the 
Slack channel `#code-reviews` when the MR is labeled with the  `code-review` label.

## Events Available

Currently, the GitLab connector handles Merge Requests and Issues events, any other event such as pipeline events, for example, will be retured as `GenericGitlabEvent`.

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.GenericGitlabEvent
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.GitlabIssueCreated
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.GitlabIssueClosed
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.GitlabIssueEdited
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.GitlabIssueLabeled
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.GenericIssueEvent
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.MRCreated
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.MRMerged
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.MRClosed
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.MRLabeled
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.MRApproved
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.events.GenericMREvent
    :members:
```

## Reference

This dataclass is used internally within the Gitlab connector, but is worth noting a few things here.

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.GitlabPayload
    :members:
```

This is the Connector reference

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.ConnectorGitlab
    :members:
```