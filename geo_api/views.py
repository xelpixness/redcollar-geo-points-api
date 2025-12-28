from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .models import GeoPoint, PointMessage
from .serializers import GeoPointSerializer, PointMessageSerializer


class GeoPointCreateView(generics.CreateAPIView):
    """
    View for creating geographic points (POST /api/points/)
    """

    queryset = GeoPoint.objects.all()
    serializer_class = GeoPointSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Automatically set created_by as current user
        """
        serializer.save(created_by=self.request.user)


class PointMessageCreateView(generics.CreateAPIView):
    """
    View for creating messages attached to geographic points
        (POST /api/points/messages/)
    """

    queryset = PointMessage.objects.all()
    serializer_class = PointMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Automatically set user as current user
        """
        serializer.save(user=self.request.user)
