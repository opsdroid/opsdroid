# Authorization

Combining [constrain_users](https://docs.opsdroid.dev/en/stable/skills/constraints.html#constrain-users) and a simple user list, authorization for a particular skill is straightforward.

In this example, we use an AWS IAM group for authorization. Note, you would need to reload should the group members change.

```python
import boto3
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.constraints import constrain_users

def _get_admins():
    admins = []
    try:
        groupname = "opsdroid_admins"
        client = boto3.client("iam")
        group = client.get_group(GroupName=groupname)
        admins = [user.get("UserName") for user in group.get("Users")]
    except Exception as e:
        logging.exception("unable to get admin group members!")
    return admins

admins = _get_admins()

class AdminSkill(Skill):
    @match_regex(r'stop all the things!')
    @constrain_users(admins)
    async def stop_everything(self, message):
        # do admin stuff
        await message.respond('done!')
```
