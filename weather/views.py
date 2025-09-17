from datetime import datetime, timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from weather.models import City, WeatherRecord
from weather.serializers import CitySerializer
from weather.services import find_city, weather_city

WEATHER_CACHE_SECONDS = 600


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    """A read-only viewset for listing all available cities."""
    queryset = City.objects.all().order_by('name')
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]


class CityWeatherByNameView(APIView):
    """An API view to get the latest weather information for a city by its name and country code."""

    def get(self, request, city_name: str, country_code: str):
        """
        Retrieve the latest weather for a city.

        Args:
            request: The HTTP request object.
            city_name (str): Name of the city.
            country_code (str): ISO country code.
        """
        city = City.objects.filter(name__iexact=city_name, country__iexact=country_code).first()
        if not city:
            city_data = find_city(city_name, country_code)
            city = City.objects.filter(name=city_data["name"], country=city_data["country"]).first()

        weather = WeatherRecord.objects.filter(city=city).first()
        now_dt = datetime.now(timezone.utc)
        if weather and (now_dt - weather.recorded_at).total_seconds() < WEATHER_CACHE_SECONDS:
            return Response({
                "city": f"{city.name}, {city.country}",
                "temperature": weather.temperature,
                "feels_like": weather.feels_like,
                "humidity": weather.humidity,
                "wind_speed": weather.wind_speed,
                "pressure": weather.pressure,
            })
        result = weather_city(city)
        return Response(result)
