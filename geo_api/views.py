from rest_framework import generics, permissions
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json

from .models import GeoPoint, PointMessage
from .serializers import GeoPointSerializer, PointMessageSerializer
from .utils import haversine_distance


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


class GeoPointSearchView(APIView):
    """
    View for searching points within radius (GET /api/points/search/)
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # 1. Get query params from request
        latitude = request.query_params.get("latitude")
        longitude = request.query_params.get("longitude")
        radius = request.query_params.get("radius")

        # 2. Check that all params are present
        if not latitude or not longitude or not radius:
            return Response(
                {
                    "error": "Missing required parameters",
                    "required": ["latitude", "longitude", "radius (km)"],
                    "example": "/api/points/search/?latitude=55.7558&longitude=37.6173&radius=10",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Try to convert params to floats
        try:
            center_lat = float(latitude)
            center_lon = float(longitude)
            radius_km = float(radius)
        except ValueError:
            return Response(
                {"error": "Parameters must be valid numbers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Check that coordinates are valid
        if not (-90 <= center_lat <= 90):
            return Response(
                {"error": "Latitude must be between -90 and 90 degrees"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-180 <= center_lon <= 180):
            return Response(
                {"error": "Longitude must be between -180 and 180 degrees"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 5. Check radius is positive
        if radius_km <= 0:
            return Response(
                {"error": "Radius must be a positive number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 6. Search for points
        points_in_radius = []

        for point in GeoPoint.objects.all():
            try:
                point_coords = point.coordinates
                if isinstance(point_coords, str):
                    point_coords = json.loads(point_coords)

                point_lon, point_lat = point_coords["coordinates"]

                distance = haversine_distance(
                    center_lat, center_lon, point_lat, point_lon
                )

                # If distance is within radius, add to results
                if distance <= radius_km:
                    points_in_radius.append(
                        {
                            "id": point.id,
                            "name": point.name,
                            "description": point.description,
                            "distance_km": round(distance, 2),
                            "coordinates": point_coords,
                            "created_by": point.created_by.username,
                        }
                    )

            except (KeyError, ValueError, json.JSONDecodeError):
                # Skip points with invalid coordinates
                continue

        # 7. Return results
        return Response(
            {
                "search_center": {"latitude": center_lat, "longitude": center_lon},
                "radius_km": radius_km,
                "points_found": len(points_in_radius),
                "points": points_in_radius,
            }
        )


class PointMessageSearchView(APIView):
    """
    Search messages within radius of a point (GET /api/points/messages/search/)
    Returns messages whose associated points are within given radius
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # 1. Get query parameters
        latitude = request.query_params.get("latitude")
        longitude = request.query_params.get("longitude")
        radius = request.query_params.get("radius")

        # 2. Validate parameters
        if not all([latitude, longitude, radius]):
            return Response(
                {
                    "error": "Missing required parameters",
                    "required": ["latitude", "longitude", "radius (km)"],
                    "example": "/api/points/messages/search/?latitude=55.7558&longitude=37.6173&radius=10",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Try to convert params to floats
        try:
            center_lat = float(latitude)
            center_lon = float(longitude)
            radius_km = float(radius)
        except ValueError:
            return Response(
                {"error": "Parameters must be valid numbers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Check that coordinates are valid
        if not (-90 <= center_lat <= 90):
            return Response(
                {"error": "Latitude must be between -90 and 90 degrees"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-180 <= center_lon <= 180):
            return Response(
                {"error": "Longitude must be between -180 and 180 degrees"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 5. Check radius is positive
        if radius_km <= 0:
            return Response(
                {"error": "Radius must be a positive number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 6. Search for messages
        messages_in_radius = []

        for message in PointMessage.objects.select_related("point", "user").all():
            try:
                # Get point coordinates
                point_coords = message.point.coordinates
                if isinstance(point_coords, str):
                    point_coords = json.loads(point_coords)

                # GeoJSON: [longitude, latitude]
                point_lon, point_lat = point_coords["coordinates"]

                # Calculate distance from search center to point
                distance = haversine_distance(
                    center_lat, center_lon, point_lat, point_lon
                )

                # If point is within radius, include the message
                if distance <= radius_km:
                    messages_in_radius.append(
                        {
                            "id": message.id,
                            "text": message.text,
                            "created_at": message.created_at,
                            "distance_km": round(distance, 2),
                            "point": {
                                "id": message.point.id,
                                "name": message.point.name,
                                "coordinates": point_coords,
                            },
                            "user": {
                                "id": message.user.id,
                                "username": message.user.username,
                            },
                        }
                    )

            except (KeyError, ValueError, json.JSONDecodeError):
                # Skip messages with invalid point coordinates
                continue

        # 7. Return results
        return Response(
            {
                "search_center": {"latitude": center_lat, "longitude": center_lon},
                "radius_km": radius_km,
                "messages_found": len(messages_in_radius),
                "messages": messages_in_radius,
            }
        )
