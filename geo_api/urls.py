from django.urls import path
from .views import GeoPointCreateView, PointMessageCreateView, GeoPointSearchView

urlpatterns = [
    path("points/", GeoPointCreateView.as_view(), name="point-create"),
    path("points/messages/", PointMessageCreateView.as_view(), name="message-create"),
    path("points/search/", GeoPointSearchView.as_view(), name="point-search"),
]
