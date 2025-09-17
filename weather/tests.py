from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import User
from weather.models import City, WeatherRecord


class CityModelTest(TestCase):
    def test_create_city(self):
        """Test that a City object can be created with correct attributes."""
        city = City.objects.create(name="Test", country="TE", lat=50.45, lon=100.10)
        self.assertEqual(city.name, "Test")
        self.assertEqual(city.country, "TE")
        self.assertEqual(city.lat, 50.45)
        self.assertEqual(city.lon, 100.10)


class WeatherRecordTest(TestCase):
    def test_record_weather(self):
        """Test that a WeatherRecord object can be created and linked to a City."""
        city = City.objects.create(name="Test", country="TE", lat=50.45, lon=100.10)
        weatherrecord = WeatherRecord.objects.create(
            city=city,
            temperature=50.45,
            feels_like=50.75,
            humidity=4,
            wind_speed=10.75,
            pressure=100.7,
        )
        self.assertEqual(weatherrecord.city.name, "Test")
        self.assertEqual(weatherrecord.temperature, 50.45)
        self.assertEqual(weatherrecord.humidity, 4)
        self.assertEqual(weatherrecord.pressure, 100.7)
        self.assertTrue(weatherrecord.recorded_at)


class CityViewSetTest(APITestCase):
    def setUp(self):
        City.objects.create(name="Kyiv", country="UA", lat=50.45, lon=30.523)
        City.objects.create(name="Lviv", country="UA", lat=49.84, lon=24.03)

    def test_list_cities(self):
        """Test that the CityViewSet returns a list of all cities."""
        url = reverse('city-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


class CityWeatherByNameViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='IvanTest',
            email='ivan@testovich.com',
            password='Bt41BBT103'
        )
        token_url = reverse('token_obtain_pair')
        response = self.client.post(token_url, {
            "username": "IvanTest",
            "password": "Bt41BBT103"
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.city = City.objects.create(name="Kyiv", country="UA", lat=50.45, lon=30.523)
        self.weather = WeatherRecord.objects.create(
            city=self.city,
            temperature=25.0,
            feels_like=26.5,
            humidity=50,
            wind_speed=5.0,
            pressure=1012.0,
        )

    def test_get_weather(self):
        """Test that the CityWeatherByNameView returns correct weather data for a city."""
        url = reverse('city-weather-by-name', kwargs={"city_name": "Kyiv", "country_code": "UA"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["temperature"], 25.0)
        self.assertEqual(response.data["humidity"], 50)
        self.assertEqual(response.data["wind_speed"], 5.0)
