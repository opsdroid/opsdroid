# GitLab

A connector for [GitLab](https://gitlab.com). 

Note that this connector emits Events only, currently, it doesn't support actions and you should
use the GitLab API in your skill if you want to create custom workflows for these events.

## Requirements

- A GitLab Account
- A repository setup with a [webhook](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)

## Configuration

```yaml
connectors:
  gitlab:
    # Optional but recommended
    webhook-token: "my-very-secret-webhook-secret"
```

## Setup Webhook

You need to [expose Opsdroid to the internet](../exposing.md), when you have your url, you can go to your repository, click **Settings** and then select **Webhook**, you can then add the url with the `connector/<connector name>` enpoint. For example, assume that you are using `example.com` as your base url and using this connector with the default name, you can use the following url `https://example.com/connector/gitlab` to receive events from your repository.

You can then choose a secret token - this will be your `webhook-token` in the Opsdroid configuration. It's highly recommended that you choose
a strong token to validate the requests coming into the `https://example/com/connector/gitlab` endpoint.

Finally, you can choose which events you want Gitlab to send you and choose if you want to turn off SSL verification. It's recommended that
you use SSL at all times.

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

```eval_rst
.. autoclass:: opsdroid.connector.gitlab.ConnectorGitlab
    :members:
```