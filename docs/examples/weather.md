# Weather

We will create a skill, that will make opsdroid tell us the current weather in a town.

This tutorial will use the  [OpenWeatherMap](https://openweathermap.org) API to get the weather information from a city. We will only need the free version of the API, so register and get your key from the [API](https://openweathermap.org/price) menu.

*If you need help or if you are unsure about something join our* [matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org) *and ask away! We are more than happy to help you.*

## Setting Up

In the tutorial, you can choose the city that you want the weather information about and which system to use (metric or imperial). These settings will be specified in our opsdroid `configuration.yaml` file.

Our `__init__.py` init file will contain two functions, one that interacts with the OpenWeatherMap API and one that opsdroid will use to tell us the weather in our city.

## Building the Skill

We are ready to start working on our skills. First, you need to create a folder for the weather skill. Choose a location and name it weather-skill.

```bash
mkdir /path/to/my/weather-skill
```

### Configuration

Now, let's open opsdroid `configuration.yaml` file and add our weather skill to the skills section.

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

_Note: We will need to set `no-cache` to true, in order to tell opsdroid to install the skill on every opsdroid run._

#### Weather Skill

Now that our skill has all the configuration details set up in the `configuration.yaml` file, let's create the `__init__.py` inside our `weather-skill` folder and start working on the skill.

The first thing we need to do is to import the `Skill` class and the `regex_matcher` from opsdroid and the `aiohttp` module. Your `__init__.py` file should look like this:

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

import aiohttp
```

#### Get Weather Data

Now we need to get the weather data from OpenWeatherMap. Let's create an asynchronous function to get the weather data.

If you read the [current weather data](https://openweathermap.org/current) documentation from OpenWeatherMap, you will see that the API endpoint that we need to use is `http://api.openweathermap.org/data/2.5/weather?q=`

Make your `__init__.py` file look like this:

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

import aiohttp

async def get_weather(config):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
```

We will need to pass the following things to OpenWeatherMap:

- City
- Units
- API-key

Since these details are already in our opsdroid `configuration.yaml` we can get them from the config.

Make your function look like this:

```python
async def get_weather(config):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
    parameters = "{}&units={}&appid={}".format(
        config['city'], config['units'], config['api-key'])
```

If we join `api_url` and `parameters`  we get the full URL that we need to get our weather data. We will now use `aiohttp` to start a session and get the data from OpenWeatherMap.

Your function should look like this now:

```python
async def get_weather(config):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
    parameters = "{}&units={}&appid={}".format(
        config['city'], config['units'], config['api-key'])

    async with aiohttp.ClientSession() as session:
        response = await session.get(api_url + parameters)
```

Our `get_weather` function is starting to look good. What's left to do is returning our response in a JSON format. Luckily `aiohttp` makes that quite easy for us, all we need to do is add `.json()` to our response.

Make our function to look like this:

```python
async def get_weather(config):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
    parameters = "{}&units={}&appid={}".format(
        config['city'], config['units'], config['api-key'])

    async with aiohttp.ClientSession() as session:
        response = await session.get(api_url + parameters)
    return await response.json()
```

Now when we call our `get_weather` function, `aiohttp` will get all the data from the OpenWeatherMap API and return it to us as a Python dictionary.

`response.json()` will give us something that looks like this:

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

Now if we call our function we will be able to get our weather data. The next step is to make opsdroid tell us the current weather.

#### Tell the Weather

This skill will call our `get_weather` function and then get the details from our weather data.

We also need to decorate the skill with our chosen matcher (regex in this case).

Make your `__init__.py` file look like this:

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

We need to chose what should trigger opsdroid to tell us the weather. Let's make opsdroid trigger when we type `How's the weather?`.

```python
class WeatherSkill(Skill):

    @match_regex("How's the weather?")
    async def tell_weather(self, message):
        pass
```

Now that we have a way to trigger the skill we will use our `get_weather` function to get the weather data. For the sake of readability, we will create some variables to hold some of the weather data as well.

Make your function look like this:

```python
class WeatherSkill(Skill):

    @match_regex("How's the weather?")
    async def tell_weather(self, message):
        weather_data = await get_weather(self.config)
        temp = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        city = weather_data['name']
```

What's left to do is to make opsdroid say the temperature in your city. We can do that by calling `message.respond()`

Change `tell_weather` function to the following:

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

Now every time you type `How's the weather` opsdroid will tell you the current weather.

Finally we could move our `get_weather` function into the skill class as a private method, which would allow us to not have to pass the config through as an argument. This would leave us with a final skill that looks like this.

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
