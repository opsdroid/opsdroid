# Stocks Portfolio

We will create a skill that will allow opsdroid to return info on specific stocks. It will also be able to store a portfolio of stocks and return each with the current market price and information about them.

This example will use [YFinace](https://github.com/ranaroussi/yfinance) to get the information of the stocks and [SQLite3](https://www.sqlite.org/index.html) to keep our portfolio when we close the bot.

*If you need help or if you are unsure about something join our* [matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org) *and ask away! We are more than happy to help you.*

## Building the Skill

We are now ready to commence building our skill! First, you will need to create a folder for the stock portfolio skill. Choose a location and name it stocks-portfolio.

```bash
mkdir /path/to/my/stocks-portfolio
```

Inside of the directory, we will be making a `configuration.yaml` file which we will be using in the next section to config our skill.

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

### Connecting to SQLite3 

Our next step is to connect our `__init__.py` file to a SQLite database. Your `__init__.py` file should look something like this now:

```python
import yfinance as yf
import sqlite3

from opsdroid.matchers import match_regex
from opsdroid.skill import Skill

conn = sqlite3.connect('/path/to/my/database')
c = conn.cursor()
```

### Receiving Input

Now we have to collect what the bot will receive and we will be doing this by first creating a class that inherits the Skill class.
Inside we will be using the special opsdroid function which is `@match_regex`.
This function will send the message, and to collect the input we will be using `(.*)` beside the message, like this `@match_regex(r"Stock: (.*)")`. We will then be accessing it with `message.regex.group(1)`.
We can now assign what we received from the bot. 

The `StockSkill` class should look something like this:

```python
class StockSkill(Skill):

    @match_regex(r"Stock: (.*)")
    async def search_info_stock(self, message):
        stock_name = message.regex.group(1)
```

### Getting the Data

Now the fun part! We will be using the YFinance module to get the data for the stocks, the module will take the stock's symbol and return the info. You can read the [documentation](https://github.com/ranaroussi/yfinance) for more info. 

Make your `StockSkill` class look something like this:

```python
class StockSkill(Skill):

    @match_regex(r"Stock: (.*)")
    async def search_info_stock(self, message):
        stock_name = message.regex.group(1)
        stock = yf.Ticker(stock_name) 
```
Now `stock` is what we receive from YFinance when we input a stock's symbol.

### Using the Data

After getting the data and assigning it to a variable, we can start using it! We can now return the info to the connector. We will be using the info property, but if you are interested in the different properties, you can use their [documentation](https://github.com/ranaroussi/yfinance).

The data from the YFinance module is returned back as JSON. Here it is:

```json
{
   "zip":"94103",
   "sector":"Technology",
   "fullTimeEmployees":3719,
   "longBusinessSummary":"Unity Software Inc. operates a real-time 3D development platform. Its platform provides software solutions to create, run, and monetize interactive, real-time 2D and 3D content for mobile phones, tablets, PCs, consoles, and augmented and virtual reality devices. The company offers its solutions directly through its online store and field sales operations in North America, Denmark, Finland, the United Kingdom, Germany, Japan, China, Singapore, and South Korea, as well as indirectly through independent distributors and resellers worldwide. The company was founded in 2004 and is 
headquartered in San Francisco, California.",
   "city":"San Francisco",
   "phone":"415-539-3162",
   "state":"CA",
   "country":"United States",
   "companyOfficers":[
      
   ],
   "website":"http://www.unity.com",
   "maxAge":1,
   "address1":"30 3rd Street",
   "industry":"Software—Application",
   "previousClose":154.18,
   "regularMarketOpen":152.33,
   "twoHundredDayAverage":123.33359,
   "trailingAnnualDividendYield":"None",
   "payoutRatio":0,
   "volume24Hr":"None",
   "regularMarketDayHigh":156.92,
   "navPrice":"None",
   "averageDailyVolume10Day":1915112,
   "totalAssets":"None",
   "regularMarketPreviousClose":154.18,
   "fiftyDayAverage":151.33788,
   "trailingAnnualDividendRate":"None",
   "open":152.33,
   "toCurrency":"None",
   "averageVolume10days":1915112,
   "expireDate":"None",
   "yield":"None",
   "algorithm":"None",
   "dividendRate":"None",
   "exDividendDate":"None",
   "beta":"None",
   "circulatingSupply":"None",
   "startDate":"None",
   "regularMarketDayLow":147.61,
   "priceHint":2,
   "currency":"USD",
   "regularMarketVolume":1362006,
   "lastMarket":"None",
   "maxSupply":"None",
   "openInterest":"None",
   "marketCap":40567812096,
   "volumeAllCurrencies":"None",
   "strikePrice":"None",
   "averageVolume":2200304,
   "priceToSalesTrailing12Months":57.123283,
   "dayLow":147.61,
   "ask":152,
   "ytdReturn":"None",
   "askSize":800,
   "volume":1362006,
   "fiftyTwoWeekHigh":174.94,
   "forwardPE":"None",
   "fromCurrency":"None",
   "fiveYearAvgDividendYield":"None",
   "fiftyTwoWeekLow":65.11,
   "bid":148,
   "tradeable":false,
   "dividendYield":"None",
   "bidSize":1800,
   "dayHigh":156.92,
   "exchange":"NYQ",
   "shortName":"Unity Software Inc.",
   "longName":"Unity Software Inc.",
   "exchangeTimezoneName":"America/New_York",
   "exchangeTimezoneShortName":"EST",
   "isEsgPopulated":false,
   "gmtOffSetMilliseconds":"-18000000",
   "quoteType":"EQUITY",
   "symbol":"U",
   "messageBoardId":"finmb_241908542",
   "market":"us_market",
   "annualHoldingsTurnover":"None",
   "enterpriseToRevenue":54.824,
   "beta3Year":"None",
   "profitMargins":-0.35116002,
   "enterpriseToEbitda":-213.991,
   "52WeekChange":1.1919534,
   "morningStarRiskRating":"None",
   "forwardEps":"None",
   "revenueQuarterlyGrowth":"None",
   "sharesOutstanding":270776992,
   "fundInceptionDate":"None",
   "annualReportExpenseRatio":"None",
   "bookValue":"None",
   "sharesShort":6390454,
   "sharesPercentSharesOut":0.023599999,
   "fundFamily":"None",
   "lastFiscalYearEnd":1577750400,
   "heldPercentInstitutions":0.61965,
   "netIncomeToCommon":-317163008,
   "trailingEps":"None",
   "lastDividendValue":"None",
   "SandP52WeekChange":0.14322305,
   "priceToBook":"None",
   "heldPercentInsiders":0.16246,
   "nextFiscalYearEnd":1640908800,
   "mostRecentQuarter":1601424000,
   "shortRatio":3.2,
   "sharesShortPreviousMonthDate":1607990400,
   "floatShares":120820703,
   "enterpriseValue":38934634496,
   "threeYearAverageReturn":"None",
   "lastSplitDate":"None",
   "lastSplitFactor":"None",
   "legalType":"None",
   "lastDividendDate":"None",
   "morningStarOverallRating":"None",
   "earningsQuarterlyGrowth":"None",
   "dateShortInterest":1610668800,
   "pegRatio":-15.31,
   "lastCapGain":"None",
   "shortPercentOfFloat":0.048600003,
   "sharesShortPriorMonth":5086368,
   "impliedSharesOutstanding":"None",
   "category":"None",
   "fiveYearAverageReturn":"None",
   "regularMarketPrice":152.33,
   "logo_url":"https://logo.clearbit.com/unity.com"
}
```

We want the `['longName']`, `['regularMarketOpen']` and `['longBusinessSummary']`. Now we want the bot to send the data, so we will be using `await message.respond()`. Here is what it should look like:

```python
class StockSkill(Skill):

    @match_regex(r"Stock: (.*)")
    async def search_info_stock(self, message):
        stock_name = message.regex.group(1)
        stock = yf.Ticker(stock_name)
        await message.respond(f"Name: {stock.info['longName']}")
        await message.respond(f"Current Price: {stock.info['regularMarketOpen']} {stock.info['currency']}")
        await message.respond(f"About: {stock.info['longBusinessSummary']}")
```

Congratulations! You have now made a bot that can tell you the name, price and info on a stock. You can do this with `Stock: <symbol-of-stock>`. With the basic part of the bot finished we can make the portfolio/saving section.

### Saving and Adding to the Portfolio

#### Creating the Table

We now have to use the SQLite3 database file that we had connected to earlier and add a table to it by doing `c.execute('''CREATE TABLE stocks (symbol text)''')`. We will be executing this command in a function similar to the one we had just made. We also want it to reset the database when making a new table. It should look something like this:

```python
@match_regex(r"Reset Portfolio")
    async def new_table(self, message):
        try:
            c.execute('''DROP TABLE IF EXISTS stocks''')
            c.execute('''CREATE TABLE stocks
                (symbol text)''')
        except:
            await message.respond('Portfolio Creation Failed')
```

With our table and database file we are set for the next section!

#### Adding to the Portfolio

Now we will be making another function which will be responsible for inserting the stock symbols into the database. We will get the info from the database with `c.execute("SELECT * FROM stocks")` and we will inserting it with `c.execute("INSERT INTO stocks VALUES (?)", (params,))`, params will equal our stock name/symbol. Here is what it should look like:

```python
@match_regex(r"Add Stock: (.*)")
    async def add_stock(self, message):
        stock_name = message.regex.group(1)
        params = (stock_name)
        
        c.execute("SELECT * FROM stocks")
        rows = c.fetchall()
        
        c.execute("INSERT INTO stocks VALUES (?)", (params,))
        conn.commit()
        
        await message.respond(f'Stock "{stock_name}" Added to Portfolio')
```

The problem here is that the bot will allow duplicates of the same stock into the database. We will be solving this problem with some for loops. Here is what it should look like in the end:

```python
@match_regex(r"Add Stock: (.*)")
    async def add_stock(self, message):
        stock_name = message.regex.group(1)
        params = (stock_name)
        c.execute("SELECT * FROM stocks")
        rows = c.fetchall()

        dupe_name = []

        for row in rows:
            dupe_name.append(row[0])

        if stock_name in dupe_name:
            await message.respond(f"Duplicate of {stock_name}")

        else:
            c.execute("INSERT INTO stocks VALUES (?)", (params,))
            conn.commit()
            await message.respond(f'Stock "{stock_name}" Added to Portfolio')
```

#### Listing the Portfolio

Now the easy part, which is listing the stocks that have been added to the database. We will be doing this by getting the data from the database the same as how we did for the adding to the database which is `c.execute("SELECT * FROM stocks")`. With the data we can use a for loop to go through all the things in the database. It should look something like this:

```python
@match_regex(r"List Stocks")
    async def list_info_stock(self, message):
        c.execute("SELECT * FROM stocks")
        rows = c.fetchall()

        for row in rows:
            stock = yf.Ticker(row[0])
            await message.respond(f"Name: {stock.info['longName']}")
            await message.respond(f"Price: {stock.info['regularMarketOpen']} {stock.info['currency']}")
            await message.respond(f"About: {stock.info['longBusinessSummary']}")
```

However we have a problem, if the user asks to `List Stocks` without anything in the database it will return an error. We can fix this by checking if the len of rows in the database is equal to 0. Here is what it should look like:

```python
@match_regex(r"List Stocks")
    async def list_info_stock(self, message):
        c.execute("SELECT * FROM stocks")
        rows = c.fetchall()
        
        if len(rows) == 0:
            await message.respond('No Stocks Added, Please Use Command "Add Stock:"')
            
        for row in rows:
            stock = yf.Ticker(row[0])
            await message.respond(f"Name: {stock.info['longName']}")
            await message.respond(f"Price: {stock.info['regularMarketOpen']} {stock.info['currency']}")
            await message.respond(f"About: {stock.info['longBusinessSummary']}")
```

Now you can add, list and find specific info about stocks. Congratulations! Good luck with your opsdroid journey! Here is what the final code should look like:

```python
import yfinance as yf
import sqlite3

from opsdroid.matchers import match_regex
from opsdroid.skill import Skill

conn = sqlite3.connect('stock_data.db')
c = conn.cursor()


class StockSkill(Skill):

    @match_regex(r"Stock: (.*)")
    async def search_info_stock(self, message):
        stock_name = message.regex.group(1)
        stock = yf.Ticker(stock_name)
        await message.respond(f"Name: {stock.info['longName']}")
        await message.respond(f"Current Price: {stock.info['regularMarketOpen']} {stock.info['currency']}")
        await message.respond(f"About: {stock.info['longBusinessSummary']}")

    @match_regex(r"Add Stock: (.*)")
    async def add_stock(self, message):
        stock_name = message.regex.group(1)
        params = (stock_name)
        c.execute("SELECT * FROM stocks")
        rows = c.fetchall()

        dupe_name = []

        for row in rows:
            dupe_name.append(row[0])

        if stock_name in dupe_name:
            await message.respond(f"Duplicate of {stock_name}")

        else:
            c.execute("INSERT INTO stocks VALUES (?)", (params,))
            conn.commit()
            await message.respond(f'Stock "{stock_name}" Added to Portfolio')

    @match_regex(r"List Stocks")
    async def list_info_stock(self, message):
        c.execute("SELECT * FROM stocks")
        rows = c.fetchall()
        if len(rows) == 0:
            await message.respond('No Stocks Added, Please Use Command "Add Stock:"')
        for row in rows:
            stock = yf.Ticker(row[0])
            await message.respond(f"Name: {stock.info['longName']}")
            await message.respond(f"Price: {stock.info['regularMarketOpen']} {stock.info['currency']}")
            await message.respond(f"About: {stock.info['longBusinessSummary']}")

    @match_regex(r"Reset Portfolio")
    async def new_table(self, message):
        try:
            file = open("stock_data.db", "w")
            file.close()
            c.execute('''CREATE TABLE stocks
                (symbol text)''')
            await message.respond('New Portfolio Created')
        except:
            await message.respond('Portfolio Creation Failed')
```
