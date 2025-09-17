import datetime
import requests

from celery import shared_task
from contextlib import contextmanager
from django.core.mail import send_mail
from django.core.cache import cache

from users.models import Subscription
from weather.services import weather_city

LOCK_EXPIRE = 60


@contextmanager
def task_lock(lock_id, expire=LOCK_EXPIRE):
    acquired = cache.add(lock_id, True, expire)
    try:
        yield acquired
    finally:
        if acquired:
            cache.delete(lock_id)


@shared_task
def send_weather_notification(subscription_id):
    """
    Sends a weather notification to the user for a specific subscription.

    Args:
        subscription_id (int): The ID of the Subscription object.
    """
    lock_id = f"sublock-{subscription_id}"

    with task_lock(lock_id) as acquired:
        if not acquired:
            return None
        subscription = Subscription.objects.get(id=subscription_id)
        city = subscription.city
        user = subscription.user

        weather = weather_city(city)
        if not weather:
            return None

        if subscription.email_push:
            send_mail(
                subject=f"Weather in: {city.name}",
                message=f"Hello {user.username},\nCurrent weather in: {city.name}:\nTemperature: {weather['temperature']}°C\nFeels like: {weather['feels_like']}\nHumidity: {weather['humidity']}%",
                from_email=None,
                recipient_list=[user.email],
            )

        if hasattr(subscription, 'webhook_url') and subscription.webhook_url:
            requests.post(subscription.webhook_url, json=weather)
        subscription.schedule_next()


@shared_task
def check_due_subscriptions():
    """Checks all subscriptions that are due for notification and triggers their tasks."""
    utc_tz = datetime.timezone.utc
    now = datetime.datetime.now(utc_tz)
    due_subs = Subscription.objects.filter(next_send_at__lte=now)

    for sub in due_subs:
        send_weather_notification.delay(sub.id)
