# opsdroid connector GitHub

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to comment on issues and pull requests on [GitHub](https://github.com).

## Requirements

To use the GitHub connecter you will need a user for the bot to use and generate a personal api token. It is recommended that you create a separate user from your own account for this. You also need to configure a webhook to send events to opsdroid.

### Creating your application

- Create GitHub user for the bot to use and log into it
- Create a [personal api token](https://github.com/blog/1509-personal-api-tokens)
- Navigate to the repo you wish the bot to comment on (or a [whole org](https://github.com/blog/1933-introducing-organization-webhooks) if you prefer)
- Go to the settings page
- Create a webhook pointing to your opsdroid instance
- Ensure you check 'Issues', 'Issue Comment' and 'Pull request'

## Configuration

```yaml
connectors:
  - name: github
    # required
    token: aaabbbcccdddeee111222333444
```
