from rest_framework import serializers
from weather.models import City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'country', 'lat', 'lon']
