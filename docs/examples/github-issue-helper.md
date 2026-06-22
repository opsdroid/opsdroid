\# GitHub Issue Helper



The GitHub Issue Helper skill lets you look up and summarize GitHub issues

without leaving your chat client. Ask opsdroid for a specific issue number

and it will reply with the title, status, author, and a short excerpt of the

description. You can also ask it to summarize the most recently opened

issues for a repository, which is handy for quick triage during standups or

when you just want a pulse check on a project.



This skill talks directly to the \[GitHub REST API](https://docs.github.com/en/rest)

and works with any connector you have configured (Slack, Matrix, Telegram,

and so on).



\## Requirements



\- A \*\*GitHub Personal Access Token (PAT)\*\*. A token with the `public\_repo`

&#x20; scope is enough for public repositories; use the full `repo` scope if you

&#x20; need access to a private repository.

\- The `aiohttp` library, used to make asynchronous calls to the GitHub API.

&#x20; opsdroid already depends on `aiohttp`, so in most installs there is

&#x20; nothing extra to install.

\- Outbound network access from the machine running opsdroid to

&#x20; `api.github.com`.



\## Configuration



Add the skill to your `configuration.yaml`, pointing `path` at the folder

that contains the skill's code, and set `repo` to the repository you want

to query in `owner/name` format.



```yaml

skills:

&#x20; github-issue-helper:

&#x20;   path: skills/github-issue-helper

&#x20;   repo: "opsdroid/opsdroid"

&#x20;   token: "ghp\_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

```



It's best practice to keep secrets like your PAT out of version control.

opsdroid supports pulling values from environment variables with the

`!ENV` tag, so you can configure the token like this instead:



```yaml

skills:

&#x20; github-issue-helper:

&#x20;   path: skills/github-issue-helper

&#x20;   repo: "opsdroid/opsdroid"

&#x20;   token: !ENV "${GITHUB\_TOKEN}"

```



\## Usage



\- `opsdroid show issue #123` — fetches issue `#123` from the configured

&#x20; repository and replies with its title, current status, author, a short

&#x20; excerpt of the description, and a link to the issue on GitHub.

\- `opsdroid summarize issues` — replies with a bulleted list of the most

&#x20; recently opened issues in the configured repository, each with its number,

&#x20; title, and link.



```

You:      opsdroid show issue #42

opsdroid: \*\*Issue #42: Connector crashes on reconnect\*\*

&#x20;         Status: Open

&#x20;         Opened by: jane-doe

&#x20;         The Slack connector throws a KeyError after a websocket

&#x20;         reconnect when...

&#x20;         https://github.com/opsdroid/opsdroid/issues/42



You:      opsdroid summarize issues

opsdroid: Here are the latest open issues in opsdroid/opsdroid:

&#x20;         - #42: Connector crashes on reconnect (https://github.com/opsdroid/opsdroid/issues/42)

&#x20;         - #41: Docs typo in skills tutorial (https://github.com/opsdroid/opsdroid/issues/41)

&#x20;         - #39: Add support for matrix threads (https://github.com/opsdroid/opsdroid/issues/39)

```



\## The Code



Save the code below as `\_\_init\_\_.py` inside the skill folder referenced by

`path` in your configuration (for example `skills/github-issue-helper/\_\_init\_\_.py`).



```python

"""An opsdroid skill for fetching and summarizing GitHub issues."""



import aiohttp



from opsdroid.skill import Skill

from opsdroid.matchers import match\_regex





class GitHubIssueHelper(Skill):

&#x20;   """Fetch and summarize GitHub issues from a configured repository."""



&#x20;   def \_\_init\_\_(self, opsdroid, config):

&#x20;       super().\_\_init\_\_(opsdroid, config)

&#x20;       self.repo = config.get("repo")

&#x20;       self.token = config.get("token")

&#x20;       self.api\_base = "https://api.github.com"



&#x20;       if not self.repo:

&#x20;           self.log.error(

&#x20;               "No 'repo' configured for github-issue-helper. "

&#x20;               "Set 'repo' in configuration.yaml as 'owner/name'."

&#x20;           )



&#x20;   def \_headers(self):

&#x20;       """Build the headers used for every request to the GitHub API."""

&#x20;       headers = {"Accept": "application/vnd.github+json"}

&#x20;       if self.token:

&#x20;           headers\["Authorization"] = f"token {self.token}"

&#x20;       return headers



&#x20;   async def \_fetch\_issue(self, issue\_number):

&#x20;       """Fetch a single issue by number. Returns None if not found."""

&#x20;       url = f"{self.api\_base}/repos/{self.repo}/issues/{issue\_number}"

&#x20;       async with aiohttp.ClientSession() as session:

&#x20;           async with session.get(url, headers=self.\_headers()) as response:

&#x20;               if response.status == 200:

&#x20;                   return await response.json()

&#x20;               self.log.warning(

&#x20;                   "GitHub API returned status %s for issue #%s",

&#x20;                   response.status,

&#x20;                   issue\_number,

&#x20;               )

&#x20;               return None



&#x20;   async def \_fetch\_open\_issues(self, limit=5):

&#x20;       """Fetch the most recently updated open issues for the repo."""

&#x20;       url = f"{self.api\_base}/repos/{self.repo}/issues"

&#x20;       params = {"state": "open", "per\_page": limit, "sort": "created"}

&#x20;       async with aiohttp.ClientSession() as session:

&#x20;           async with session.get(

&#x20;               url, headers=self.\_headers(), params=params

&#x20;           ) as response:

&#x20;               if response.status == 200:

&#x20;                   return await response.json()

&#x20;               self.log.warning(

&#x20;                   "GitHub API returned status %s when listing issues",

&#x20;                   response.status,

&#x20;               )

&#x20;               return \[]



&#x20;   @staticmethod

&#x20;   def \_truncate(text, length=280):

&#x20;       """Trim long issue bodies down to a chat-friendly excerpt."""

&#x20;       text = (text or "No description provided.").strip()

&#x20;       if len(text) > length:

&#x20;           return f"{text\[:length]}..."

&#x20;       return text



&#x20;   @match\_regex(r"opsdroid show issue #(?P<number>\\d+)", case\_sensitive=False)

&#x20;   async def show\_issue(self, message):

&#x20;       """Reply with full details for a single GitHub issue."""

&#x20;       issue\_number = message.regex.group("number")

&#x20;       issue = await self.\_fetch\_issue(issue\_number)



&#x20;       if issue is None:

&#x20;           await message.respond(

&#x20;               f"Sorry, I couldn't find issue #{issue\_number} in {self.repo}."

&#x20;           )

&#x20;           return



&#x20;       reply = (

&#x20;           f"\*\*Issue #{issue\_number}: {issue\['title']}\*\*\\n"

&#x20;           f"Status: {issue\['state'].capitalize()}\\n"

&#x20;           f"Opened by: {issue\['user']\['login']}\\n"

&#x20;           f"{self.\_truncate(issue.get('body'))}\\n"

&#x20;           f"{issue\['html\_url']}"

&#x20;       )

&#x20;       await message.respond(reply)



&#x20;   @match\_regex(r"opsdroid summarize issues", case\_sensitive=False)

&#x20;   async def summarize\_issues(self, message):

&#x20;       """Reply with a short summary of the latest open issues."""

&#x20;       issues = await self.\_fetch\_open\_issues()



&#x20;       if not issues:

&#x20;           await message.respond(f"There are no open issues in {self.repo}. 🎉")

&#x20;           return



&#x20;       lines = \[f"Here are the latest open issues in {self.repo}:"]

&#x20;       lines += \[

&#x20;           f"- #{issue\['number']}: {issue\['title']} ({issue\['html\_url']})"

&#x20;           for issue in issues

&#x20;       ]

&#x20;       await message.respond("\\n".join(lines))

```

