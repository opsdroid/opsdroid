# Stocks Portfolio

우리는 opsdroid가 특정 주식의 정보를 반환할 수 있는 기술을 만들 것입니다. 그것은 또한 주식 포트폴리오를 저장할 수 있고 각각에 대한 현재 시세와 정보를 가지고 수익률을 올릴 수 있을 것입니다.
이 예시는 YFinace를 사용하여 주식의 정보를 얻고 SQLite3를 사용하여 봇을 닫을 때 포트폴리오를 유지합니다.
[YFinace](https://github.com/ranaroussi/yfinance)
[SQLite3](https://www.sqlite.org/index.html)

*도움이 필요하거나 확실하지 않은 사항이 있으면 매트릭스 채널에 가입하여 문의해 주세요! 우리는 당신을 도울 수 있다면 매우 기쁠 것입니다.* [matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org)

## Building the Skill

이제 기술 개발을 시작할 준비가 되었습니다! 먼저, 주식 포트폴리오 스킬을 위한 폴더를 만들어야 합니다. 위치를 선택하고 이름을 stocks-portfolio로 지정합니다.

```bash
mkdir /path/to/my/stocks-portfolio
```

디렉토리 내부에 configuration.yaml 파일을 만들 것이며, 다음 섹션에서 이 파일을 사용하여 스킬을 구성할 것입니다.

### Configuration
이제 configuration.yaml 파일을 열고 스킬 섹션에 주식 포트폴리오 스킬을 추가해 보겠습니다.

```yaml
skills:
  stock:
    path: /path/to/my/stocks-portfolio
```

### Imports and Classes Needed

이제 우리의 기술이 Configuration.yaml 파일에 구성되었으므로, 우리는 계속 우리의 stocks-portfolio 폴더 안에 __init_py 파일을 만들고 스킬 작업을 시작할 것입니다!

우리가 가장 먼저 해야 할 일은 opsdroid에서 스킬 클래스와 regex 매처를 가져오는 것입니다. 그러면 yfinance와 sqlite3 모듈을 가져와야 할 것입니다. __init_.py 파일은 다음과 같아야 합니다.:

```python
import yfinance as yf
import sqlite3

from opsdroid.matchers import match_regex
from opsdroid.skill import Skill
```

### Connecting to SQLite3 

다음 단계는 __init_.py 파일을 SQLite 데이터베이스에 연결하는 것입니다. __init_.py 파일은 다음과 같아야 합니다.:

```python
import yfinance as yf
import sqlite3

from opsdroid.matchers import match_regex
from opsdroid.skill import Skill

conn = sqlite3.connect('/path/to/my/database')
c = conn.cursor()
```

### Receiving Input

이제 봇이 받을 내용을 수집해야 합니다. 먼저 스킬 클래스를 상속하는 클래스를 만들어 보겠습니다. 내부에서는 @match_regex인 특수 opsdroid 함수를 사용할 것입니다. 이 함수는 메시지를 보내고 메시지 옆에 사용할 입력(.*)을 수집하기 위해 @match_regex(r"Stock: (.*)") 과 같이 사용합니다. 그런 다음 message.regex.group(1)을 사용하여 액세스할 것입니다. 이제 봇에서 수신한 내용을 할당할 수 있습니다.
StockSkill 클래스는 다음과 같아야 합니다.:

```python
class StockSkill(Skill):

    @match_regex(r"Stock: (.*)")
    async def search_info_stock(self, message):
        stock_name = message.regex.group(1)
```

### Getting the Data

이제 재미있는 파트입니다! YFinance 모듈을 사용하여 주식에 대한 데이터를 가져오고 모듈은 주식의 기호를 가져와서 정보를 반환할 것입니다. 자세한 내용은 설명서를 참조하십시오.[documentation](https://github.com/ranaroussi/yfinance)
StockSkill 클래스를 다음과 같이 만듭니다.:

```python
class StockSkill(Skill):

    @match_regex(r"Stock: (.*)")
    async def search_info_stock(self, message):
        stock_name = message.regex.group(1)
        stock = yf.Ticker(stock_name) 
```
이제 stock은 주식 기호를 입력할 때 YFinance로부터 받는 것입니다.

### Using the Data

데이터를 가져와 변수에 할당한 후 데이터를 사용할 수 있습니다! 이제 커넥터에 정보를 반환할 수 있습니다. 정보 속성을 사용하지만 다른 속성에 관심이 있는 경우 해당 문서를 사용할 수 있습니다.
YFinance 모듈의 데이터는 JSON으로 반환됩니다. 여기 있습니다.:

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

우리는 ['longName'], ['regularMarketOpen'], ['longBusinessSummary'] 를 원합니다. 이제 우리는 봇이 데이터를 전송하기를 원하므로 await message.respond()를 사용할 것입니다. 다음과 같이 보여야 합니다.:

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

축하합니다! 이제 주식의 이름, 가격 및 정보를 알려주는 봇을 만들었습니다. Stock: <symbol-of-stock> 으로 이것을 할 수 있습니다. 봇의 기본 부분이 완성되면 포트폴리오/절약 섹션을 만들 수 있습니다.

### Saving and Adding to the Portfolio

#### Creating the Table

우리는 이제 이전에 연결했던 SQLite3 데이터베이스 파일을 사용하고 c.execute('''CREATE TABLE stocks (symbol text)''') 를 수행하여 테이블을 추가해야 합니다. 이 명령을 방금 만든 것과 유사한 함수로 실행할 것입니다. 또한 새 표를 만들 때 데이터베이스를 재설정해야 합니다. 다음과 같은 모양이어야 합니다.:

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
테이블과 데이터베이스 파일을 사용하여 다음 섹션을 준비했습니다!

#### Adding to the Portfolio

이제 우리는 주식 기호를 데이터베이스에 삽입하는 또 다른 기능을 만들 것입니다. c.execute("SELECT * FROM stocks")를 통해 데이터베이스에서 정보를 가져오고 c.execute("INSERT INTO stocks VALUES (?)", (params,)) 을 통해 입력할 것입니다. 매개 변수는 주식 이름/기호와 동일합니다. 다음과 같이 보여야 합니다.:

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

여기서 문제는 봇이 동일한 주식의 복제를 데이터베이스에 허용한다는 것입니다. 우리는 루프에 대한 몇 가지 방법으로 이 문제를 해결할 것입니다. 최종 결과는 다음과 같습니다.:

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

이제 쉬운 부분은 데이터베이스에 추가된 스톡을 나열하는 것입니다. 우리는 c.execute("SELECT * FROM stocks")로 데이터베이스에 추가한 것과 동일한 방식으로 데이터베이스에서 데이터를 가져오게 됩니다. 데이터를 사용하여 데이터베이스의 모든 내용을 루프로 살펴볼 수 있습니다. 다음과 같은 모양이어야 합니다.:

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

그러나 문제가 있습니다. 사용자가 데이터베이스에 아무것도 없이 스톡 목록을 요청하면 오류가 발생합니다. 데이터베이스의 행 len이 0인지 확인하여 이 문제를 해결할 수 있습니다. 다음과 같이 보여야 합니다.:

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

이제 주식에 대한 특정 정보를 추가, 나열하고 찾을 수 있습니다. 축하합니다! 당신의 opsdroid 여정에 행운을 빌어요! 최종 코드는 다음과 같습니다.:

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
