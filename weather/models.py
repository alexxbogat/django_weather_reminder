from django.db import models


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    lat = models.DecimalField(max_digits=8, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        unique_together = ('name', 'country')

    def __str__(self):
        return f"{self.name}, {self.country}"


class WeatherRecord(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='weather_records')
    temperature = models.FloatField()
    feels_like = models.FloatField()
    humidity = models.PositiveIntegerField()
    wind_speed = models.FloatField()
    pressure = models.FloatField()
    recorded_at = models.DateTimeField(auto_now=True)
