# Stocks Portfolio

We will create a skill that will allow opsdroid to store a portfolio of stocks and return each with the current market price and info of it.

This example will use [YFinace](https://github.com/ranaroussi/yfinance) to get the information of the stocks and [SQLite3](https://www.sqlite.org/index.html) to keep our portfolio when we close the bot.

*If you need help or if you are unsure about something join our* [matrix channel](https://riot.im/app/#/room/#opsdroid-general:matrix.org) *and ask away! We are more than happy to help you.*

## Building the Skill

We are now ready to commence building our skill! First, you will need to create a folder for the stocks portfolio skill. Choose a location and name it stocks-portfolio.

```bash
mkdir /path/to/my/stocks-portfolio
```

Inside of the directory we will be making a `configuration.yaml` file which we will be using in the next section to config our skill.

### Configuration

Now, let's open `configuration.yaml` file and add our stocks portfolio skill to the skills section.

```yaml
skills:
  stock:
    path: /path/to/my/stocks-portfolio
```

### Imports and Classes Needed

Now that our skill has been configured in the `configuration.yaml` file, we will continue by creating the `__init__.py` file inside of our stocks-portfolio folder and start working on the skill!

The first thing we need to do is to import the `Skill` class and the `regex_matcher` from opsdroid. Then we will need to import `yfinance` and `sqlite3` modules. Your `__init__.py` file should look like this:

```python
import yfinance as yf
import sqlite3

from opsdroid.matchers import match_regex
from opsdroid.skill import Skill
```

