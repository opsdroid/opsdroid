# GitHub

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to comment on issues and pull requests on [GitHub](https://github.com). This connector also allows you to get events from the CI checks.

## Requirements

To use the GitHub connector you will need a user for the bot to use and generate a personal api token. It is recommended that you create a separate user from your own account for this. You also need to configure a webhook to send events to opsdroid, this will require you to [expose opsdroid to the internet](https://docs.opsdroid.dev/en/stable/exposing.html) via a tunnel.

### Creating your application

- Create GitHub user for the bot to use and log into it
  - If the bot sends too many messages to GitHub the account might get banned
- Create a [personal api token](https://github.com/blog/1509-personal-api-tokens)
- Navigate to the repo you wish the bot to comment on (or a [whole org](https://github.com/blog/1933-introducing-organization-webhooks) if you prefer)
- Go to the settings page
- In the webhook tab, click the "Add webhook" button
- Make sure you select `application/x-www-form-urlencoded` as Content type otherwise the connector won't work.
- Create a webhook pointing to your opsdroid url
- Select what kind of events should be sent to the bot, you can select "Let me select individual events" and check:
  - "Issues"
  - "Issue comment"
  - "Pull request"
  - "Check runs
  
_*Note:* You should add a secure secret when setting up your webhook, this will allow opsdroid to confirm that the event received is authentic and came from GitHub._

## Configuration

```yaml
connectors:
  github:
    # required
    token: aaabbbcccdddeee111222333444
    secret: <webhook secret>
```

## Reference

```eval_rst
.. autoclass:: opsdroid.connector.github.ConnectorGitHub
  :members:
```

## Events Reference

```eval_rst
.. autoclass:: opsdroid.connector.github.events.IssueCreated
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.IssueClosed
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.IssueCommented
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PROpened
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRMerged
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRClosed
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.Labeled
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.Unlabeled
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.CheckStarted
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.CheckCompleted
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.CheckPassed
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.CheckFailed
  :members:
```