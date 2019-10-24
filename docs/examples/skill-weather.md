# opsdroid skill-weather

A skill for [opsdroid](https://github.com/opsdroid/opsdroid) to tell you the current weather.
Opsdroid will tell you what's forecasted for today, how many degrees and percentage of humidity.

## Creating skills

Skills are designed to be simpler than other modules to ensure that it is easy to get started.

To create a skill you need to at minimum create a single python file in your repository with the  `__init__.py`  name. For example the skill  `hello`  has a single file called  `__init__.py`.

##  Configuration
```yaml
 skills:
	    name: weather
	    # Required
	    city: London,UK # For accuracy use {city},{country code} 
	    unit: metric # Choose metric/imperial
	    api-key: 6fut9e098d8g90g
```

## Writing the skill
```python

    from opsdroid.matchers import match_regex
    

	import aiohttp
	

	async def get_weather(config):

		base_url = "http://api.openweathermap.org/data/2.5/"

		api_url = "weather?q={}&units={}&appid={}".format(

		config['city'], config['unit'], config['api-key'])
		

		async with aiohttp.ClientSession() as session:

			response = await session.get(base_url + api_url)

		return await response.json()
		

	@match_regex(r'(?:how|what)(?:\'s|s| is) the weather', case_sensitive=False)

	async def tell_weather(opsdroid, config, message):
	

		weather = await get_weather(config)

		temp = weather['main']['temp']

		humidity = weather['main']['humidity']

		city = weather['name']

		status = weather['weather'][0]['description'].title()
		

		await message.respond("It's currently {} degrees, {}% humidity in {} and {} is forecasted "

				"for today".format(temp, humidity, city, status))


	@match_regex(r'is it (?:cold|hot|warm|nice outside)', case_sensitive=False)

		async def cold_outside(opsdroid, config, message):

		weather = await get_weather(config)

		temp = weather['main']['temp']
		

		if temp < 10 or config['unit'] == 'imperial' and temp < 50:

			await message.respond("It's pretty cold today! It's currently "

			"{} degrees outside".format(temp))

		elif 10 < temp < 19 or 50 < temp < 60:

			await message.respond("I think it's better if you take a "

			"jacket with you today. It's currently "

			"{} degrees outside".format(temp))

		elif 19 < temp < 23 or 65 < temp < 75:

			await message.respond("It's not too bad actually, it's currently "

			"{} degrees outside".format(temp))

		elif temp > 23 or temp > 75:

			await message.respond("It's pretty hot today, it's currently "

			"{} degrees outside".format(temp))
```
## Demonstrating
Now every time you type `How's the weather`  or `What's the weather`opsdroid will tell you the current weather.