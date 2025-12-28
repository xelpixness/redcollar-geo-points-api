from django.urls import path
from .views import GeoPointCreateView, PointMessageCreateView

urlpatterns = [
    path("points/", GeoPointCreateView.as_view(), name="point-create"),
    path("points/messages/", PointMessageCreateView.as_view(), name="message-create"),
]
