from django.urls import path
from .views import (
    GeoPointCreateView,
    PointMessageCreateView,
    GeoPointSearchView,
    PointMessageSearchView,
)

urlpatterns = [
    path("points/", GeoPointCreateView.as_view(), name="point-create"),
    path("points/messages/", PointMessageCreateView.as_view(), name="message-create"),
    path("points/search/", GeoPointSearchView.as_view(), name="point-search"),
    path(
        "points/messages/search/",
        PointMessageSearchView.as_view(),
        name="message-search",
    ),
]
