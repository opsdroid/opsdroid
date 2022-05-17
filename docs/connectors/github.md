# GitHub

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to comment on issues and pull requests on [GitHub](https://github.com). This connector also allows you to get events from the CI checks.

## Requirements

To use the GitHub connector you will need a user for the bot to use and generate a personal api token. It is recommended that you create a separate user from your own account for this. You also need to configure a webhook to send events to opsdroid, this will require you to [expose opsdroid to the internet](../exposing.md) via a tunnel.

### Creating your application

There are 2 ways to connect opsdroid to Github. You can create a Github App and point it at opsdroid for event handling. This app can be installed by multiple organizations and would only be configured once. The other way is to use a Webhook within Github and point that to opsdroid for event handling. Each webhook needs to be individually configured.

#### Github Apps method

- Create Github app under and organization or individuals `Settings` (in `Developer Settings` -> `Github Apps`.)
- Specify the Webhook URL pointing to your opsdroid url.
- Select which permissions you would like to ask the user for. Currently supported are:
  - "Checks"
  - "Contents"
  - "Issues"
  - "Pull requests"
- Based on your selection, you can check which events you would like Github to send to your opsdroid. Currently supported are:
  - "Check runs"
  - "Issues"
  - "Issue comment"
  - "Pull request"
  - "Pull request review"
  - "Pull request review comment"
  - "Push"
- After clicking "Create GitHub App", download the Private Key file for use in configuration.

_*Note:* You should add a secure secret when setting up your webhook, this will allow opsdroid to confirm that the event received is authentic and came from GitHub._

#### Webhook method

- Create GitHub user for the bot to use and log into it
  - If the bot sends too many messages to GitHub the account might get banned
- Create a [personal api token](https://github.com/blog/1509-personal-api-tokens)
- Navigate to the repo you wish the bot to comment on (or a [whole org](https://github.com/blog/1933-introducing-organization-webhooks) if you prefer)
- Go to the settings page
- In the webhook tab, click the "Add webhook" button
- Make sure you select `application/x-www-form-urlencoded` as Content type otherwise the connector won't work.
- Create a webhook pointing to your opsdroid url
- Select what kind of events should be sent to the bot, you can select "Let me select individual events" and check:
  - "Check runs"
  - "Issues"
  - "Issue comment"
  - "Pull request"
  - "Pull request review"
  - "Pull request review comment"
  - "Push"
  
_*Note:* You should add a secure secret when setting up your webhook, this will allow opsdroid to confirm that the event received is authentic and came from GitHub._

## Configuration

#### Github app

```yaml
connectors:
  github:
    # required
    app_id: 123456
    private_key_file: <path/to/private_key.pem>
    secret: <webhook secret>
```

#### Webhook method

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
.. autoclass:: opsdroid.connector.github.events.Push
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PROpened
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReopened
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PREdited
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
.. autoclass:: opsdroid.connector.github.events.PRReviewSubmitted
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewEdited
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewDismissed
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewCommentCreated
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewCommentEdited
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewCommentDeleted
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
