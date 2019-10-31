**OPSDROID WEATHER Skill**
REQUIREMENTS :
You need an api-key from https://openweathermap.org/api


CONFIGURATION :

skills:
Example-----
  - name: weather
    # Required
    city: London,UK    # For accuracy use {city},{country code}          
    unit: metric       # Choose metric/imperial
    api-key: 6fut9e098d8g90g


USAGE :

weather
Opsdroid will tell you what's forecasted for today, how many degrees and percentage of humidity.

user: how's the weather outside

opsdroid: It's currently 18.63 degrees, 60% humidity in London and Clouds is forecasted for today

Note: You can also use the command what's the weather.

