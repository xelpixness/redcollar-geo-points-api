from django.db import models
from django.contrib.auth.models import User
from djgeojson.fields import PointField


# Create your models here.
class GeoPoint(models.Model):
    """Model for geographic points on map"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    coordinates = PointField()
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_points"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PointMessage(models.Model):
    """Model for messages attached to geographic points"""

    point = models.ForeignKey(
        GeoPoint, on_delete=models.CASCADE, related_name="messages"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="point_messages"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.user.username} for {self.point.name}"
