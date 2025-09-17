from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, RegisterView, SubscriptionViewSet, SubscriptionCityView

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register(r'subscription', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path("cities/<str:city_name>/<str:country_code>/weather/subscription/", SubscriptionCityView.as_view(),
         name="city-weather-subscription"),
]
