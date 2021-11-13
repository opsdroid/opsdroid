# Weather

우리는 opsdroid로 마을의 현재 날씨를 알려주는 기술을 만들 것입니다.

이 튜토리얼은 OpenWeatherMap API를 사용하여 도시에서 날씨 정보를 가져옵니다. 무료 버전의 API만 있으면 되므로 등록 후 API 메뉴에서 키를 가져오십시오.
[OpenWeatherMap](https://openweathermap.org)
[API](https://openweathermap.org/price)

*도움이 필요하거나 확실하지 않은 사항이 있으면 매트릭스 채널에 가입하여 문의해 주십시오! 우리는 당신을 도울 수 있다면 매우 기쁠 것입니다.* [matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org)

## Setting Up

튜토리얼에서 날씨 정보를 원하는 도시와 사용할 시스템(매트릭 또는 임페리얼)을 선택할 수 있습니다. 이러한 설정은 opsdroid의 configuration.yaml 파일에 지정됩니다.

우리의 __init_.py init 파일은 두 가지 기능을 포함합니다. 하나는 OpenWeatherMap API와 상호 작용하는 기능이고 하나는 opsdroid가 우리 도시의 날씨를 알려주는 데 사용할 기능입니다.

## Building the Skill

우리는 이제 기술을 연습할 준비가 되었습니다. 먼저 날씨 스킬을 위한 폴더를 만들어야 합니다. 위치를 선택하고 날씨 기술 이름을 지정하십시오.

```bash
mkdir /path/to/my/weather-skill
```

### Configuration

이제 opsdroid의 configuration.yaml 파일을 열고 날씨 기술을 스킬 섹션에 추가해 보겠습니다.

```yaml
skills:
  weather:
    city: <Your city, your country>     # For accuracy use {city},{country code}
    units: <metric/imperial>       # Choose metric/imperial
    api-key: <Your Api Key>
    # Developing the skill
    path: /path/to/my/weather-skill
    no-cache: true
```

_Note:모든 opsdroid 실행에 스킬을 설치하도록 하려면 no-cache를 true로 설정해야 합니다._

#### Weather Skill

이제 configuration.yaml 파일에 모든 구성 세부 정보가 설정되었으므로 날씨 스킬 폴더 안에 __init_py를 만들고 스킬 작업을 시작하겠습니다.
우리가 가장 먼저 해야 할 일은 opsdroid와 aiohttp 모듈에서 스킬 클래스와 regex_matcher를 가져오는 것입니다. __init_.py 파일은 다음과 같아야 합니다.:

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

import aiohttp
```

#### Get Weather Data

이제 OpenWeatherMap에서 날씨 데이터를 가져와야 합니다. 날씨 데이터를 얻기 위해 비동기 함수를 만들어 봅시다.
OpenWeatherMap의 현재 날씨 데이터 문서를 읽어보면, 우리가 사용해야 하는 API 끝부분이 http://api.openweathermap.org/data/2.5/weather?q= 이라는 것을 알 수 있을 것입니다.
[current weather data](https://openweathermap.org/current)

__init_.py 파일을 다음과 같이 만듭니다.:

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

import aiohttp

async def get_weather(config):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
```

다음 사항을 OpenWeatherMap에 전달해야 합니다.

- 도시
- 단위
- API 키
- 
이러한 세부 정보는 이미 opsdroid 구성에 있으므로 구성에서 가져올 수 있습니다.
기능을 다음과 같이 만드십시오.:

```python
async def get_weather(config):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
    parameters = "{}&units={}&appid={}".format(
        config['city'], config['units'], config['api-key'])
```
api_url과 파라미터에 가입하면 날씨 데이터를 얻는 데 필요한 전체 URL을 얻을 수 있습니다. 이제 aiohttp를 사용하여 세션을 시작하고 OpenWeatherMap에서 데이터를 가져올 것입니다.
이제 기능은 다음과 같아야 합니다.:

```python
async def get_weather(config):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
    parameters = "{}&units={}&appid={}".format(
        config['city'], config['units'], config['api-key'])

    async with aiohttp.ClientSession() as session:
        response = await session.get(api_url + parameters)
```

우리의 날씨 기능이 점점 좋아지고 있습니다. 이제 JSON 형식으로 응답을 반환해야 합니다. 다행히도 aiohttp는 그것을 꽤 쉽게 만들어 주므로, 우리가 해야 할 일은 우리의 반응에 .json()을 추가하는 것입니다.
기능을 다음과 같이 만드십시오.:

```python
async def get_weather(config):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
    parameters = "{}&units={}&appid={}".format(
        config['city'], config['units'], config['api-key'])

    async with aiohttp.ClientSession() as session:
        response = await session.get(api_url + parameters)
    return await response.json()
```

이제 get_weather 함수를 호출하면 aiohttp는 OpenWeatherMap API에서 모든 데이터를 가져와 파이썬 사전으로 우리에게 돌려줍니다.
response.json()은 다음과 같은 내용을 제공합니다.:

```json
{
     "coord":
         {
             "lon": -0.13,
             "lat": 51.51
         },
     "weather":
         [
             {
                 "id": 800,
                 "main": "Clear",
                 "description": "clear sky",
                 "icon": "01n"
             }
         ],
     "base": "stations",
     "main":
         {
             "temp": 3.37,
             "pressure": 1022,
             "humidity": 86,
             "temp_min": 2,
             "temp_max": 5
         },
     "visibility": 10000,
     "wind":
         {
             "speed": 2.1,
             "deg": 310
         },
     "clouds":
         {
             "all": 0
         },
     "dt": 1511076000,
     "sys":
         {
             "type": 1,
             "id": 5089,
             "message": 0.1668,
             "country": "GB",
             "sunrise": 1511076308,
             "sunset": 1511107601
         },
     "id": 2639545,
     "name": "London",
     "cod": 200
 }
```

이제 우리의 기능을 호출하면 날씨 데이터를 얻을 수 있을 것입니다. 다음 단계는 opsdroid가 현재의 날씨를 알려주도록 만드는 것입니다.

#### Tell the Weather

이 기술로 우리의 get_weather 기능을 호출한 다음 날씨 데이터를 통해 자세한 정보를 얻을 수 있습니다.
우리는 또한 우리가 선택한 매처(이 경우 regex)로 기술을 꾸며야 합니다.
__init_.py 파일을 다음과 같이 만듭니다.:

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

import aiohttp

async def get_weather(config):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
    parameters = "{}&units={}&appid={}".format(
        config['city'], config['units'], config['api-key'])

    async with aiohttp.ClientSession() as session:
        response = await session.get(api_url + parameters)
    return await response.json()


class WeatherSkill(Skill):

    @match_regex()
    async def tell_weather(self, message):
        pass
```

우리는 날씨를 알려주기 위해 무엇이 opsdroid를 실행시킬지 선택해야 합니다. How's the weather? 라고 입력할 때의 opsdroid 실행기를 만들어 봅시다.

```python
class WeatherSkill(Skill):

    @match_regex("How's the weather?")
    async def tell_weather(self, message):
        pass
```

이제 우리는 기술을 실행시킬 방법을 얻었으므로 날씨 데이터를 얻기 위해 get_weather 기능을 사용할 것입니다. 가독성을 위해 일부 날씨 데이터도 저장할 수 있는 변수를 만들 것입니다.
기능을 다음과 같이 만드십시오.:

```python
class WeatherSkill(Skill):

    @match_regex("How's the weather?")
    async def tell_weather(self, message):
        weather_data = await get_weather(self.config)
        temp = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        city = weather_data['name']
```

이제 남은 일은 opsdroid가 당신의 도시 기온을 나타내도록 만드는 것입니다. 우리는 message.respond()를 호출하여 그것을 할 수 있습니다.
tell_weather 기능을 다음과 같이 변경합니다.:

```python
class WeatherSkill(Skill):

    @match_regex("How's the weather?")
    async def tell_weather(self, message):
        weather_data = await get_weather(self.config)
        temp = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        city = weather_data['name']

        await message.respond("It's {} and {}% humidity in {}.".format(temp, humidity, city))
```

이제 여러분이 How's the weather를 opsdroid에 입력할 때마다 현재의 날씨를 알려줄 것입니다.
마지막으로, 우리는 개인적인 방법으로 get_weather 기능을 스킬 클래스로 이동시킬 수 있는데, 이것은 우리가 그 구성에 대해 논쟁할 것이 없게 할 것입니다. 이것은 우리에게 결과적으로 다음과 같은 기술으로 남을 것입니다.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

import aiohttp

class WeatherSkill(Skill):

    async def _get_weather(self):
        api_url = "http://api.openweathermap.org/data/2.5/weather?q="
        parameters = "{}&units={}&appid={}".format(
            self.config['city'], self.config['units'], self.config['api-key'])

        async with aiohttp.ClientSession() as session:
            response = await session.get(api_url + parameters)
        return await response.json()

    @match_regex("How's the weather?")
    async def tell_weather(self, message):
        weather_data = await self._get_weather()
        temp = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        city = weather_data['name']

        await message.respond("It's {} and {}% humidity in {}.".format(temp, humidity, city))
```
