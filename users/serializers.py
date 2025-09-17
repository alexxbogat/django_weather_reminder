from rest_framework import serializers

from users.models import User, Subscription
from weather.serializers import CitySerializer


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class SubscriptionSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['city', 'email_push', 'webhook_url', 'period_push', 'created_at', 'updated_at']
        read_only_fields = ['city', 'created_at', 'updated_at']
