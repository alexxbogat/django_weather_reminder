from unittest.mock import patch
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import User, Subscription
from users.tasks import send_weather_notification
from weather.models import City


class UserModelTest(TestCase):
    """Tests for the User model."""

    def test_create_user(self):
        """Test creating a user with a password."""
        user = User.objects.create_user(username='Test', email='test@test.com', password='Bt41stT123')
        self.assertEqual(user.username, 'Test')
        self.assertEqual(user.email, 'test@test.com')
        self.assertTrue(user.check_password('Bt41stT123'))


class SubscriptionModelTest(TestCase):
    """Tests for the Subscription model."""

    def test_subscription_user(self):
        """Test creating a subscription and scheduling the next send time."""
        user = User.objects.create_user(username='Ivan', email='ivan@test.com', password='Bt41stT123')
        city = City.objects.create(name="Kyiv", country="UA", lat=50.45, lon=30.523)
        sub = Subscription.objects.create(
            user=user,
            city=city,
            email_push=False,
            webhook_url='https://test.com',
            period_push=3
        )
        self.assertEqual(sub.user.username, "Ivan")
        self.assertEqual(sub.city.name, "Kyiv")
        self.assertFalse(sub.email_push)
        self.assertEqual(sub.webhook_url, "https://test.com")
        self.assertEqual(sub.period_push, 3)
        self.assertTrue(sub.created_at)
        self.assertTrue(sub.updated_at)
        self.assertIsNone(sub.next_send_at)

        sub.schedule_next()
        self.assertIsNotNone(sub.next_send_at)


class SubscriptionAPITest(APITestCase):
    """Integration tests for the Subscription API."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='IvanTest',
            email='ivan@testovich.com',
            password='Bt41BBT103'
        )
        self.city = City.objects.create(name="Kyiv", country="UA", lat=70.75, lon=38.503)
        token_url = reverse('token_obtain_pair')
        response = self.client.post(token_url, {
            "username": "IvanTest",
            "password": "Bt41BBT103"
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.sub_url = reverse(
            'city-weather-subscription',
            kwargs={'city_name': 'Kyiv', 'country_code': 'UA'}
        )

    @patch("users.views.send_weather_notification.delay")
    def test_create_subscription(self, mock_task):
        """User can create a subscription."""
        data = {"email_push": True, "period_push": 3, "webhook_url": "https://test.com"}
        response = self.client.post(self.sub_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["subscription"], True)

    def test_list_subscriptions(self):
        """User can retrieve a list of their subscriptions."""
        Subscription.objects.create(
            user=self.user,
            city=self.city,
            email_push=True,
            period_push=3,
            webhook_url="https://test.com"
        )
        list_url = reverse('subscription-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["webhook_url"], "https://test.com")

    @patch("users.views.send_weather_notification.delay")
    def test_update_subscription(self, mock_task):
        """User can update subscription settings."""
        Subscription.objects.create(
            user=self.user,
            city=self.city,
            email_push=True,
            period_push=3,
            webhook_url="https://test.com"
        )
        data = {"email_push": False, "period_push": 1}
        response = self.client.put(self.sub_url, data)
        self.assertEqual(response.data["subscription"], "Subscription updated")
        self.assertFalse(response.data["email_push"])

    def test_delete_subscription(self):
        """User can delete a subscription."""
        Subscription.objects.create(
            user=self.user,
            city=self.city,
            email_push=True,
            period_push=3,
            webhook_url="https://test.com"
        )
        response = self.client.delete(self.sub_url)
        self.assertEqual(response.data["subscription"], "Subscription removed")

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch("users.views.send_weather_notification.delay")
    def test_email_send(self, mock_task):
        """Test that an email notification is sent when a subscription with email_push=True is created."""
        data = {"email_push": True, "period_push": 3}
        response = self.client.post(self.sub_url, data)
        sub = Subscription.objects.filter(user=self.user).first()
        send_weather_notification.run(sub.id)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Kyiv", mail.outbox[0].subject)

    @patch("users.tasks.requests.post")
    @patch("users.views.send_weather_notification.delay")
    def test_webhook_send(self, mock_task, mock_post):
        """Test that webhook URL is stored and called when notification task is executed."""
        data = {
            "email_push": False,
            "period_push": 3,
            "webhook_url": "https://test.com"
        }
        response = self.client.post(self.sub_url, data)
        self.assertEqual(response.status_code, 200)

        sub = Subscription.objects.get(user=self.user, city=self.city)
        self.assertEqual(sub.webhook_url, "https://test.com")

        send_weather_notification.run(sub.id)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("json", kwargs)
        self.assertIn("temperature", kwargs["json"])
