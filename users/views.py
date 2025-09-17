from django.core.exceptions import ValidationError
from rest_framework import viewsets, permissions, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User, Subscription
from users.serializers import UserSerializer, RegisterSerializer, SubscriptionSerializer
from users.tasks import send_weather_notification
from weather.models import City
from weather.services import find_city


class RegisterView(generics.CreateAPIView):
    """API endpoint that allows new users to register."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows viewing users."""
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing user subscriptions."""
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).order_by('id')


class SubscriptionCityView(APIView):
    """API endpoint for managing subscriptions for a specific city."""

    def get_city(self, city_name: str, country_code: str) -> City | None:
        """
        Retrieves a City instance by name and country code. If not found locally, fetches data from external service.

        Args:
            city_name (str): The name of the city.
            country_code (str): The ISO country code.

        Returns:
            City or None: Returns a City instance if found, otherwise None.
        """
        city = City.objects.filter(name=city_name, country=country_code).first()
        if not city:
            city_data = find_city(city_name, country_code)
            city = City.objects.filter(name=city_data["name"], country=city_data["country"]).first()
        return city

    def get_subscription(self, user: User, city: City) -> Subscription | None:
        """
        Retrieves a Subscription instance for a given user and city.

        Args:
            user (User): The user instance.
            city (City): The city instance.

        Returns:
            Subscription or None: Returns the subscription if it exists, otherwise None.
        """
        return Subscription.objects.filter(user=user, city=city).first()

    def post(self, request, city_name: str, country_code: str) -> Response:
        """
        Creates a new subscription for the authenticated user.

        Args:
            request: DRF request object.
            city_name (str): The name of the city to subscribe to.
            country_code (str): The country code of the city.
        """
        try:
            city = self.get_city(city_name, country_code)
        except ValidationError as e:
            return Response({"error": str(e)}, status=404)

        serializer = SubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscription = Subscription.objects.create(
            user=request.user,
            city=city,
            email_push=serializer.validated_data.get("email_push", True),
            webhook_url=serializer.validated_data.get("webhook_url", None),
            period_push=serializer.validated_data.get("period_push", 12),
        )

        subscription.schedule_next()
        send_weather_notification.delay(subscription.id)

        return Response({
            'user': request.user.username,
            'email': request.user.email,
            'subscription': True,
            'city': city.name,
            'country': city.country,
            'email_push': subscription.email_push,
            'webhook_url': subscription.webhook_url,
            'period_push': subscription.period_push,
        })

    def delete(self, request, city_name: str, country_code: str) -> Response:
        """
        Deletes the subscription for the authenticated user for a specific city.

        Args:
            request: DRF request object.
            city_name (str): Name of the city.
            country_code (str): Country code of the city.
        """
        try:
            city = self.get_city(city_name, country_code)
        except ValidationError as e:
            return Response({"error": str(e)}, status=404)

        subscription = self.get_subscription(request.user, city)
        if not subscription:
            return Response({"error": "Subscription not found"}, status=404)
        subscription.delete()

        return Response({
            'user': request.user.username,
            'email': request.user.email,
            'subscription': 'Subscription removed',
            'city': city.name,
            'country': city.country,
        })

    def put(self, request, city_name: str, country_code: str) -> Response:
        """
        Updates the subscription settings for the authenticated user for a specific city.

        Args:
            request: DRF request object.
            city_name (str): Name of the city.
            country_code (str): Country code of the city.
        """
        try:
            city = self.get_city(city_name, country_code)
        except ValidationError as e:
            return Response({"error": str(e)}, status=404)

        serializer = SubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscription = self.get_subscription(request.user, city)
        if not subscription:
            return Response({"error": "Subscription not found"}, status=404)
        subscription.email_push = serializer.validated_data.get("email_push", True)
        subscription.webhook_url = serializer.validated_data.get("webhook_url", None)
        subscription.period_push = serializer.validated_data.get("period_push", 12)
        subscription.save()

        subscription.schedule_next()
        send_weather_notification.delay(subscription.id)

        return Response({
            'user': request.user.username,
            'email': request.user.email,
            'subscription': 'Subscription updated',
            'city': city.name,
            'country': city.country,
            'email_push': subscription.email_push,
            'period_push': subscription.period_push,
        })
