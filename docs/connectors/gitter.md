# Gitter

A connector for [Gitter](https://developer.gitter.im/docs/welcome).

**Note:** Gitter is sensitive to accounts that post duplicate messages, and
bots are liable to trip gitter's spam detection by posting multiple messages
with the same text. Gitter responds by permanently blocking all messages from
that account but _giving no indication from its API that it is doing so_.
This means that opsdroids' logs will indicate "success" but the messages may
not actually appear in gitter. This is a variation on
[shadow banning](https://en.wikipedia.org/wiki/Shadow_banning)
but even the banned account cannot see its own messages.
[Accounts older than two weeks may be exempt from duplicate detection](https://github.com/opsdroid/opsdroid/issues/1693#issuecomment-754629627),
so one possible workaround is to create an account for your bot and then wait
at least two weeks before making heavy use of it. If the account _is_ banned,
the only way to recover is to delete and remake the gitter account. (It can be
associated with the same {GitHub, GitLab, Twitter} account as before.) Note
that this resets the token.

## Requirements

To use the Gitter connector you will need a user for the bot to use and generate a personal `token`. It is recommended that you create a separate user from your own account for this.

### Creating your application

- Create Gitter user for the bot to use and log into it
- Create a [token](https://developer.gitter.im/apps)
- Get the [room-id](https://developer.gitter.im/docs/rooms-resource) of room you want to listen.

## Configuration

```yaml
connectors:
  gitter:
    # Required
    room-id: "to be added"
    token: "to be added"
    # optional
    bot-name: opsdroid # default 'opsdroid'
```
