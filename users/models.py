import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser

from weather.models import City


class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)


class Subscription(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='subscriptions')
    city = models.ForeignKey(to=City, on_delete=models.CASCADE, related_name='subscriptions')
    email_push = models.BooleanField(default=True)
    webhook_url = models.URLField(blank=True, null=True)
    next_send_at = models.DateTimeField(null=True, blank=True)
    period_push = models.PositiveSmallIntegerField(default=12)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def schedule_next(self):
        utc_tz = datetime.timezone.utc
        self.next_send_at = datetime.datetime.now(utc_tz) + datetime.timedelta(hours=self.period_push)
        self.save()

    class Meta:
        unique_together = ('user', 'city')
