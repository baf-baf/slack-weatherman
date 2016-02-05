__author__ = 'Vitalii Zavoloka, https://github.com/baf-baf'

import pywapi   # https://code.google.com/archive/p/python-weather-api/
import string
import re       # regular expressions
import datetime
import requests
import json
import pprint   # for debug

class PyWeatherman:

    def __init__(self, params, slackToken):
        self.params = params
        self.slackToken = slackToken
        self.message = ''
        self.morningGreetings = "Good morning team !\n"
        self.eveningGreetings = "Good evening team !\n"
        self.getWeather()


    def getWeather(self):
        weatherFullStr = ''
        for k in self.params:

            weatherApiResponse = pywapi.get_weather_from_weather_com(self.params[k]['id'])
            weatherFullStr += "\n"  + self.params[k]['city'] + \
                              " : " + self.handleWeatherResponse(weatherApiResponse)

        self.message = weatherFullStr


    def handleWeatherResponse(self, response):

        weather = string.lower(response['current_conditions']['text'])
        weatherText = self.parseWeatherText(weather)

        temperature = response['current_conditions']['temperature']         # Celsius
        feelsTemperature = response['current_conditions']['feels_like']     # Celsius
        temperatureText = temperature + "C"
        if temperature != feelsTemperature:
            temperatureText += ", but feels like " + feelsTemperature + "C"

        humidity = response['current_conditions']['humidity']               # Percentage
        humidityText = "Humidity : " + humidity + "%"

        windSpeed = response['current_conditions']['wind']['speed']         # Km/H
        windText = response['current_conditions']['wind']['text']
        windFullText = "Wind : " + windText + " " + windSpeed + "Km/H"

        lastUpdate = response['current_conditions']['last_updated']

        weatherStr = weatherText  + " | " + temperatureText + " | " + \
                     humidityText + " | " + windFullText + " ( Last update : " + lastUpdate + " )"

        return weatherStr


    def debugVariable(self, variable):

        pp = pprint.PrettyPrinter()
        pp.pprint(variable)

    def parseWeatherText(self, text):

        # Weather text examples :
        #   Mostly Cloudy, Clouds, Mist, Sunny, Rain, Snow,
        #   Partly Cloudy, Mostly Cloudy, Mostly Sunny,
        #   Snow/Rain, Snow to Rain, Light Rain, Showers/Wind
        #   PM Showers, AM Clouds/PM Sun, Snow Showers
        # Slack icon examples :
        #   :sunny:, :mostly_sunny:, :partly_sunny:, :barely_sunny:, :partly_sunny_rain:
        #   :cloud:, :rain_cloud:, :thunder_cloud_and_rain:, :lightning:, :snow_cloud:
        # Correspondences :
        #   Default : :mostly_sunny:
        #   Sunny -> :sunny: | Cloudy, Mist  -> :cloud:
        #   Mostly Sunny, Partly Cloudy  -> :mostly_sunny: |  Partly Sunny, Mostly Cloudy -> :partly_sunny:
        #   Showers, Rain, Rain Showers -> :rain_cloud: | Light Rain, Sun & Rain -> :partly_sunny_rain:
        #   Storm~ , Lighting -> :lightning: | Storm~ & Rain~, Lightning & Rain, Lightning & Storm~ -> :thunder_cloud_and_rain:
        #   Snow, Snow Showers -> :snow_cloud:

        weatehrText = text
        weatherIcon = ":mostly_sunny:"

        reSunny = re.search( r'sun', weatehrText, re.M | re.I)
        if reSunny:
            weatherIcon = ":sunny:"

        reCloudyMist = re.search( r'cloudy|mist|fog', weatehrText, re.M | re.I)
        if reCloudyMist:
            weatherIcon = ":cloud:"

        reMsPc = re.search( r'mostly sunny|partly cloudy', weatehrText, re.M | re.I)
        if reMsPc:
            weatherIcon = ":mostly_sunny:"

        rePsMc = re.search( r'partly sunny|mostly cloudy', weatehrText, re.M | re.I)
        if rePsMc:
            weatherIcon = ":partly_sunny:"

        reShowersRain = re.search( r'shower|rain|rain shower', weatehrText, re.M | re.I)
        if reShowersRain:
            weatherIcon = ":rain_cloud:"

        reLightRain = re.search( r'(light rain)|(sun.+rain|rain.+sun)', weatehrText, re.M | re.I)
        if reLightRain:
            weatherIcon = ":partly_sunny_rain:"

        reStorms = re.search( r'(storm)|(storm.+)|(lighting)', weatehrText, re.M | re.I)
        if reStorms:
            weatherIcon = ":lightning:"

        reStormRain = re.search( r'(storm.+rain)|(rain.+storm)', weatehrText, re.M | re.I)
        reRainLighting = re.search( r'(lighting.+rain)|(rain.+lighting)', weatehrText, re.M | re.I)
        reStormLighting = re.search( r'(lighting.+storm)|(storm.+lighting)', weatehrText, re.M | re.I)
        reStormShowers = re.search( r'(storm.+shower)|(shower.+storm)', weatehrText, re.M | re.I)
        reShowersLighting = re.search( r'(lighting.+shower)|(shower.+lighting)', weatehrText, re.M | re.I)

        if reStormRain or reRainLighting or reStormLighting or reStormShowers or reShowersLighting:
            weatherIcon = ":thunder_cloud_and_rain:"

        reSnow = re.search( r'snow', weatehrText, re.M | re.I)
        if reSnow:
            weatherIcon = ":snow_cloud:"

        return weatherIcon + " " + weatehrText

    def sendRequest(self):

        currentHour = datetime.datetime.now().hour
        greetings = "Hello team !\n"
        if currentHour < 12:
            greetings = self.morningGreetings
        elif currentHour > 17:
            greetings = self.eveningGreetings

        #factOfTheDay = self.getFunFactOfTheDay()
        factOfTheDay = ''
        self.message = greetings + factOfTheDay + self.message

        payload = {
                "channel"   : self.slackToken['channel'],
                "username"  : "Cat - Weatherman",
                "text"      : self.message,
                "icon_emoji": ":smiley_cat:"
        }
        message = {'payload' : json.dumps(payload)}
        requests.post(self.slackToken['hook_token'], data=message)

    # unused for now
    def getFunFactOfTheDay(self):

        currentDateTime = datetime.datetime.now()
        date = currentDateTime.strftime("%d")
        month = currentDateTime.strftime("%m")

        response = requests.get("https://numbersapi.p.mashape.com/" + month + \
                                "/" + date + "/date?fragment=false&json=true",
                               headers={
                                # "X-Mashape-Key": "",
                                 "Accept": "text/plain"
                               }
        )
        jsonResponse = json.loads(response.text)
        message = "\nFact fo the day (" + date + "/" + month + "/" + str(jsonResponse['year']) + "): " + \
                  jsonResponse['text'] + "\n"
        return message

# ---------------------------------------------------------------------------------------------

weatherman = PyWeatherman(
    {   # Dictionary which contains "ID : City" pairs
        0: {'id': 'UPXX0106:1:UP', 'city': 'Kremenchuk'},   # Ukraine
        1: {'id': 'UPXX0014:1:UP', 'city': 'Kharkiv'},      # Ukraine
        2: {'id': 'GMXX0051:1:GM', 'city': 'Hannover'},     # Germany
    },
    {  # Slack data
        'hook_token': '',            # https://####
        'channel'   : '#general'
    }
)
weatherman.sendRequest()








