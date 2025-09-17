from django.urls import path, include
from rest_framework.routers import DefaultRouter

from weather.views import CityViewSet, CityWeatherByNameView

router = DefaultRouter()
router.register('cities', CityViewSet, basename='city')

urlpatterns = [
    path('', include(router.urls)),
    path("cities/<str:city_name>/<str:country_code>/weather/", CityWeatherByNameView.as_view(),
         name="city-weather-by-name"),
]
