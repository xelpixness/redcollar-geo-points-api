from rest_framework import serializers
from .models import GeoPoint, PointMessage


class GeoPointSerializer(serializers.ModelSerializer):
    """Serializer for geographic points with GeoJSON validation"""

    coordinates = serializers.JSONField()

    def validate_coordinates(self, value):
        """
        Validate GeoJSON Point format according to RFC 7946
        Expected: {"type": "Point", "coordinates": [longitude, latitude]}
        """
        # 1. Check it's a dict
        if not isinstance(value, dict):
            raise serializers.ValidationError("Coordinates must be a JSON object")

        # 2. Check required fields
        if "type" not in value:
            raise serializers.ValidationError("Missing 'type' field in GeoJSON")
        if "coordinates" not in value:
            raise serializers.ValidationError("Missing 'coordinates' field in GeoJSON")

        # 3. Check type is 'Point'
        if value["type"] != "Point":
            raise serializers.ValidationError("GeoJSON type must be 'Point'")

        # 4. Check coordinates is a list of 2 numbers
        coords = value["coordinates"]
        if not isinstance(coords, list):
            raise serializers.ValidationError("Coordinates must be an array")

        if len(coords) != 2:
            raise serializers.ValidationError(
                "Coordinates array must contain exactly 2 values: [longitude, latitude]"
            )

        lon, lat = coords

        # 5. Check both are numbers
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise serializers.ValidationError("Longitude and latitude must be numbers")

        # 6. Check valid ranges
        if not (-180 <= lon <= 180):
            raise serializers.ValidationError(
                "Longitude must be between -180 and 180 degrees"
            )

        if not (-90 <= lat <= 90):
            raise serializers.ValidationError(
                "Latitude must be between -90 and 90 degrees"
            )

        return value

    class Meta:
        model = GeoPoint
        fields = [
            "id",
            "name",
            "description",
            "coordinates",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class PointMessageSerializer(serializers.ModelSerializer):
    """Serializer for point messages"""

    point = serializers.PrimaryKeyRelatedField(
        queryset=GeoPoint.objects.all(),
        error_messages={
            "does_not_exist": "Point does not exist. Please provide a valid point ID.",
            "incorrect_type": "Point ID must be an integer.",
        },
    )

    class Meta:
        model = PointMessage
        fields = ["id", "point", "user", "text", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
