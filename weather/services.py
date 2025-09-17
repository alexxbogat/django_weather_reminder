import os
import requests
from django.core.exceptions import ValidationError

from dotenv import load_dotenv

from weather.models import City, WeatherRecord

load_dotenv()

API_KEY = os.getenv('API_KEY')


def find_city(city_name: str, country_code: str) -> dict:
    """
    Find a city by name and country code using the OpenWeatherMap Geocoding API.

    Args:
        city_name (str): Name of the city.
        country_code (str): ISO country code.

    Returns:
        dict | None: City information containing name, country, latitude, and longitude
        if the request is successful. Otherwise, None.
    """
    url = f'http://api.openweathermap.org/geo/1.0/direct?q={city_name},{country_code}&limit=1&appid={API_KEY}'
    res = requests.get(url)
    if res.status_code != 200:
        raise ValidationError({"error": "Weather service error", "details": res.text})
    data = res.json()
    if not data:
        raise ValidationError({"error": "City not found", "details": f"City: {city_name}, Country code: {country_code}"})
    city_data = data[0]
    City.objects.update_or_create(
        name=city_data["name"],
        country=city_data["country"],
        defaults={
            "lat": city_data["lat"],
            "lon": city_data["lon"]
        }
    )
    return city_data


def weather_city(city: City) -> dict | None:
    """
    Retrieve the latest weather data for a given city using the OpenWeatherMap API.

    Args:
        city (City): The city instance for which to retrieve weather.

    Returns:
        dict | None: Dictionary containing city name, temperature, feels-like temperature,
        humidity, wind speed, and pressure if successful. Otherwise, None.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={city.lat}&lon={city.lon}&units=metric&appid={API_KEY}"
    res = requests.get(url)
    if res.status_code != 200:
        raise ValidationError({"error": "Weather service error", "details": res.text})

    data = res.json()
    if not data:
        raise ValidationError({"error": "Weather not found", "details": f"{city}"})
    temperature = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    pressure = data["main"]["pressure"]

    result = {
        'city': f"{city.name}, {city.country}",
        'temperature': temperature,
        'feels_like': feels_like,
        'humidity': humidity,
        'wind_speed': wind_speed,
        'pressure': pressure
    }

    WeatherRecord.objects.update_or_create(
        city=city,
        defaults={
            "temperature": temperature,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "pressure": pressure,
        }
    )
    return result
