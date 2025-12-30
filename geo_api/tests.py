from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
import json
from rest_framework import status
from rest_framework.test import APIClient
from .models import GeoPoint, PointMessage
from .serializers import GeoPointSerializer, PointMessageSerializer

# ---------------- 🍰🍰🍰 POST /api/points/ 🍰🍰🍰 ------------------


class GeoPointCreateTests(TestCase):
    """Tests for GeoPoint creation endpoint"""

    def setUp(self):
        """Setup test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.valid_data = {
            "name": "Test Point",
            "description": "Test Description",
            "coordinates": {
                "type": "Point",
                "coordinates": [37.6173, 55.7558],  # Москва
            },
        }

    def test_create_point_with_valid_data(self):
        """Test creating a point with valid data"""
        url = reverse("point-create")
        response = self.client.post(
            url, data=json.dumps(self.valid_data), content_type="application/json"
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check database
        self.assertEqual(GeoPoint.objects.count(), 1)

        point = GeoPoint.objects.first()
        self.assertEqual(point.name, self.valid_data["name"])
        self.assertEqual(point.created_by, self.user)

    def test_create_point_unauthenticated(self):
        """Test that unauthenticated user cannot create points"""
        client = APIClient()  # New unauthenticated client
        url = reverse("point-create")

        response = client.post(
            url, data=json.dumps(self.valid_data), content_type="application/json"
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
        self.assertEqual(GeoPoint.objects.count(), 0)


# ---------------- 🍰🍰🍰 POST /api/points/messages/ 🍰🍰🍰 ------------------


class PointMessageCreateTests(TestCase):
    """Tests for PointMessage creation endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.point = GeoPoint.objects.create(
            name="Test Point",
            description="Test",
            coordinates='{"type": "Point", "coordinates": [0, 0]}',
            created_by=self.user,
        )

    def test_create_message_for_existing_point(self):
        """Test creating a message for existing point"""
        url = reverse("message-create")
        data = {"point": self.point.id, "text": "Test message"}

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PointMessage.objects.count(), 1)

        message = PointMessage.objects.first()
        self.assertEqual(message.text, data["text"])
        self.assertEqual(message.user, self.user)

    def test_create_message_empty_text(self):
        """Test creating a message with empty text should fail"""
        url = reverse("message-create")
        data = {"point": self.point.id, "text": ""}  # Empty text!

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("text", response.data)

    def test_create_point_without_name(self):
        """Test creating a point without name should fail"""
        url = reverse("point-create")
        invalid_data = {
            # No name!
            "coordinates": {"type": "Point", "coordinates": [0, 0]}
        }

        response = self.client.post(
            url, data=json.dumps(invalid_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_point_with_long_name(self):
        """Test creating a point with name longer than 255 chars should fail"""
        url = reverse("point-create")
        invalid_data = {
            "name": "A" * 256,  # 256 chars > 255 limit
            "coordinates": {"type": "Point", "coordinates": [0, 0]},
        }

        response = self.client.post(
            url, data=json.dumps(invalid_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_message_unauthenticated(self):
        """Test that unauthenticated user cannot create messages"""
        client = APIClient()  # Unauthenticated client
        url = reverse("message-create")
        data = {"point": self.point.id, "text": "Test message"}

        response = client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
        self.assertEqual(PointMessage.objects.count(), 0)


# ---------------- 🍰🍰🍰 GET /api/points/search/ 🍰🍰🍰 ------------------


class GeoPointSearchTests(TestCase):
    """Tests for GeoPoint search within radius"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        # Make sure we have some points
        self.point_moscow = GeoPoint.objects.create(
            name="Moscow Kremlin",
            description="Test",
            coordinates='{"type": "Point", "coordinates": [37.6173, 55.7558]}',
            created_by=self.user,
        )

        self.point_spb = GeoPoint.objects.create(
            name="St. Petersburg",
            description="Test",
            coordinates='{"type": "Point", "coordinates": [30.3141, 59.9398]}',
            created_by=self.user,
        )

        # Point nearby Moscow
        self.point_zelenograd = GeoPoint.objects.create(
            name="Zelenograd",
            description="Test",
            coordinates='{"type": "Point", "coordinates": [37.1818, 55.9825]}',
            created_by=self.user,
        )

    def test_search_with_all_parameters(self):
        """Test search with all required parameters"""
        url = reverse("point-search")
        response = self.client.get(
            url, {"latitude": 55.7558, "longitude": 37.6173, "radius": 5}  # 5 km
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("points", response.data)
        self.assertIn("radius_km", response.data)
        self.assertEqual(response.data["radius_km"], 5)

    def test_search_finds_nearby_points(self):
        """Test that search finds points within radius"""
        url = reverse("point-search")

        response = self.client.get(
            url, {"latitude": 55.7558, "longitude": 37.6173, "radius": 50}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should find both Moscow and Zelenograd
        points_found = response.data["points_found"]
        point_names = [p["name"] for p in response.data["points"]]

        self.assertEqual(points_found, 2)
        self.assertIn("Moscow Kremlin", point_names)
        self.assertIn("Zelenograd", point_names)
        self.assertNotIn("St. Petersburg", point_names)  # Outside radius

    def test_search_non_numeric_parameters(self):
        """Test search with non-numeric parameters"""
        url = reverse("point-search")

        # latitude not a number
        response = self.client.get(
            url, {"latitude": "not-a-number", "longitude": 37.6173, "radius": 10}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("valid numbers", response.data["error"])

    def test_search_missing_parameters(self):
        """Test search without required parameters"""
        url = reverse("point-search")

        # Missing parameters
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Missing", response.data["error"])

    def test_search_invalid_latitude(self):
        """Test search with invalid latitude"""
        url = reverse("point-search")

        response = self.client.get(
            url, {"latitude": 200, "longitude": 37.6173, "radius": 10}  # Wrong latitude
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Latitude", response.data["error"])

    def test_search_invalid_longitude(self):
        """Test search with invalid longitude"""
        url = reverse("point-search")

        response = self.client.get(
            url,
            {"latitude": 55.7558, "longitude": 200, "radius": 10},  # Wrong longitude
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Longitude", response.data["error"])

    def test_search_negative_radius(self):
        """Test search with negative radius"""
        url = reverse("point-search")

        response = self.client.get(
            url,
            {
                "latitude": 55.7558,
                "longitude": 37.6173,
                "radius": -10,  # Negative radius
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("positive", response.data["error"].lower())

    def test_search_unauthenticated(self):
        """Test that search requires authentication"""
        client = APIClient()  # No authentication
        url = reverse("point-search")

        response = client.get(
            url, {"latitude": 55.7558, "longitude": 37.6173, "radius": 10}
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )


# ------------- 🍰🍰🍰 GET /api/points/messages/search/... 🍰🍰🍰 ---------------


class PointMessageSearchTests(TestCase):
    """Tests for PointMessage search within radius"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        # Make sure we have some points
        self.point_moscow = GeoPoint.objects.create(
            name="Moscow Point",
            description="Test",
            coordinates='{"type": "Point", "coordinates": [37.6173, 55.7558]}',
            created_by=self.user,
        )

        self.point_zelenograd = GeoPoint.objects.create(
            name="Zelenograd Point",
            description="Test",
            coordinates='{"type": "Point", "coordinates": [37.1818, 55.9825]}',
            created_by=self.user,
        )

        self.point_spb = GeoPoint.objects.create(
            name="SPB Point",
            description="Test",
            coordinates='{"type": "Point", "coordinates": [30.3141, 59.9398]}',
            created_by=self.user,
        )

        # Create some messages
        self.message_moscow = PointMessage.objects.create(
            point=self.point_moscow, user=self.user, text="Message in Moscow"
        )

        self.message_zelenograd = PointMessage.objects.create(
            point=self.point_zelenograd, user=self.user, text="Message in Zelenograd"
        )

        self.message_spb = PointMessage.objects.create(
            point=self.point_spb, user=self.user, text="Message in SPB"
        )

    def test_search_messages_with_valid_parameters(self):
        """Test message search with all required parameters"""
        url = reverse("message-search")
        response = self.client.get(
            url, {"latitude": 55.7558, "longitude": 37.6173, "radius": 5}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("messages", response.data)
        self.assertEqual(response.data["radius_km"], 5)

    def test_search_messages_finds_within_radius(self):
        """Test that search finds messages whose points are within radius"""
        url = reverse("message-search")

        response = self.client.get(
            url, {"latitude": 55.7558, "longitude": 37.6173, "radius": 40}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should find both messages Moscow and Zelenograd
        messages_found = response.data["messages_found"]
        message_texts = [m["text"] for m in response.data["messages"]]

        self.assertEqual(messages_found, 2)
        self.assertIn("Message in Moscow", message_texts)
        self.assertIn("Message in Zelenograd", message_texts)
        self.assertNotIn("Message in SPB", message_texts)  # Not within radius

    def test_search_messages_non_numeric_parameters(self):
        """Test message search with non-numeric parameters"""
        url = reverse("message-search")

        # latitude not a number
        response = self.client.get(
            url, {"latitude": "invalid", "longitude": 37.6173, "radius": 10}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("valid numbers", response.data["error"])

    def test_search_messages_missing_parameters(self):
        """Test message search without required parameters"""
        url = reverse("message-search")

        response = self.client.get(url)  # No parameters

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_search_messages_invalid_latitude(self):
        """Test message search with invalid coordinates"""
        url = reverse("message-search")

        response = self.client.get(
            url, {"latitude": 200, "longitude": 37.6173, "radius": 10}  # Wrong latitude
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Latitude", response.data["error"])

    def test_search_messages_invalid_longitude(self):
        """Test search with invalid longitude"""
        url = reverse("message-search")

        response = self.client.get(
            url,
            {"latitude": 55.7558, "longitude": 200, "radius": 10},  # Wrong longitude
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Longitude", response.data["error"])

    def test_search_messages_negative_radius(self):
        """Test message search with negative radius"""
        url = reverse("message-search")

        response = self.client.get(
            url, {"latitude": 55.7558, "longitude": 37.6173, "radius": -10}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_search_messages_unauthenticated(self):
        """Test that message search requires authentication"""
        client = APIClient()  # No authentication
        url = reverse("message-search")

        response = client.get(
            url, {"latitude": 55.7558, "longitude": 37.6173, "radius": 10}
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_search_returns_message_structure(self):
        """Test that search returns correct message structure"""
        url = reverse("message-search")

        response = self.client.get(
            url, {"latitude": 55.7558, "longitude": 37.6173, "radius": 5}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if response.data["messages_found"] > 0:
            message = response.data["messages"][0]

            # Проверяем структуру ответа
            self.assertIn("id", message)
            self.assertIn("text", message)
            self.assertIn("created_at", message)
            self.assertIn("distance_km", message)
            self.assertIn("point", message)
            self.assertIn("user", message)

            # Проверяем структуру точки
            self.assertIn("id", message["point"])
            self.assertIn("name", message["point"])
            self.assertIn("coordinates", message["point"])

            # Проверяем структуру пользователя
            self.assertIn("id", message["user"])
            self.assertIn("username", message["user"])


# ------------------ 🍰🍰🍰 MODELS (__str__) 🍰🍰🍰 ------------------


class ModelsTests(TestCase):
    """Tests for model methods (__str__, etc.)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.point = GeoPoint.objects.create(
            name="Test Location",
            description="Test description",
            coordinates='{"type": "Point", "coordinates": [0, 0]}',
            created_by=self.user,
        )

    def test_geopoint_str(self):
        """Test GeoPoint __str__ method"""
        self.assertEqual(str(self.point), "Test Location")

    def test_pointmessage_str(self):
        """Test PointMessage __str__ method"""
        message = PointMessage.objects.create(
            point=self.point, user=self.user, text="Test message text"
        )

        expected = f"Message by {self.user.username} for {self.point.name}"
        self.assertEqual(str(message), expected)


# ------------------ 🍰🍰🍰 SERIALIZERS 🍰🍰🍰 ------------------


class GeoPointSerializerTests(TestCase):
    """Tests for GeoPointSerializer validation"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_valid_coordinates(self):
        """Test valid GeoJSON coordinates"""

        valid_data = {
            "name": "Test Point",
            "description": "Test description",
            "coordinates": {
                "type": "Point",
                "coordinates": [37.6173, 55.7558],  # Valid coordinates
            },
        }

        serializer = GeoPointSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_coordinates_not_dict(self):
        """Test coordinates that are not a dictionary"""

        invalid_data = {
            "name": "Test",
            "coordinates": "not a dict",  # String instead of dict
        }

        serializer = GeoPointSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)
        self.assertIn("JSON object", str(serializer.errors["coordinates"]))

    def test_missing_type_field(self):
        """Test GeoJSON missing 'type' field"""
        from .serializers import GeoPointSerializer

        invalid_data = {
            "name": "Test",
            "coordinates": {"coordinates": [10, 20]},  # Missing 'type'
        }

        serializer = GeoPointSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)

    def test_missing_coordinates_field(self):
        """Test GeoJSON missing 'coordinates' field"""
        invalid_data = {
            "name": "Test",
            "coordinates": {"type": "Point"},  # Missing 'coordinates'
        }

        serializer = GeoPointSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)
        self.assertIn(
            "Missing 'coordinates' field", str(serializer.errors["coordinates"])
        )

    def test_wrong_geojson_type(self):
        """Test GeoJSON with wrong type (not 'Point')"""

        invalid_data = {
            "name": "Test",
            "coordinates": {
                "type": "Polygon",  # Wrong type
                "coordinates": [[[0, 0], [1, 1]]],
            },
        }

        serializer = GeoPointSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)
        self.assertIn("Point", str(serializer.errors["coordinates"]))

    def test_coordinates_not_array(self):
        """Test coordinates field is not an array"""

        invalid_data = {
            "name": "Test",
            "coordinates": {
                "type": "Point",
                "coordinates": "not an array",  # String instead of array
            },
        }

        serializer = GeoPointSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)
        self.assertIn("array", str(serializer.errors["coordinates"]))

    def test_coordinates_wrong_length(self):
        """Test coordinates array with wrong number of elements"""

        invalid_data = {
            "name": "Test",
            "coordinates": {"type": "Point", "coordinates": [10]},  # Only one element
        }

        serializer = GeoPointSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)
        self.assertIn("exactly 2 values", str(serializer.errors["coordinates"]))

    def test_coordinates_not_numbers(self):
        """Test coordinates that are not numbers"""
        test_cases = [
            {
                "coordinates": {
                    "type": "Point",
                    "coordinates": ["not-a-number", 50],  # lon is string
                }
            },
            {
                "coordinates": {
                    "type": "Point",
                    "coordinates": [50, "not-a-number"],  # lat is string
                }
            },
            {
                "coordinates": {
                    "type": "Point",
                    "coordinates": [None, 50],  # lon is None
                }
            },
            {"coordinates": {"type": "Point", "coordinates": [50, []]}},  # lat is list
        ]

        for data in test_cases:
            full_data = {"name": "Test Point", **data}
            serializer = GeoPointSerializer(data=full_data)
            self.assertFalse(serializer.is_valid(), f"Should fail for {data}")
            self.assertIn("coordinates", serializer.errors)
            self.assertIn("must be numbers", str(serializer.errors["coordinates"]))

    def test_invalid_longitude(self):
        """Test longitude out of range"""

        invalid_data = {
            "name": "Test",
            "coordinates": {
                "type": "Point",
                "coordinates": [200, 50],  # Longitude > 180
            },
        }

        serializer = GeoPointSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)
        self.assertIn("between -180 and 180", str(serializer.errors["coordinates"]))

    def test_invalid_latitude(self):
        """Test latitude out of range"""

        invalid_data = {
            "name": "Test",
            "coordinates": {"type": "Point", "coordinates": [50, 100]},  # Latitude > 90
        }

        serializer = GeoPointSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)
        self.assertIn("between -90 and 90", str(serializer.errors["coordinates"]))


class PointMessageSerializerTests(TestCase):
    """Tests for PointMessageSerializer validation"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.point = GeoPoint.objects.create(
            name="Test Point",
            description="Test",
            coordinates='{"type": "Point", "coordinates": [0, 0]}',
            created_by=self.user,
        )

    def test_valid_message(self):
        """Test creating a valid message"""

        valid_data = {"point": self.point.id, "text": "Test message"}

        serializer = PointMessageSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_nonexistent_point(self):
        """Test message for non-existent point"""

        invalid_data = {"point": 99999, "text": "Test message"}  # Non-existent ID

        serializer = PointMessageSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("point", serializer.errors)
        self.assertIn("Point does not exist", str(serializer.errors["point"]))

    def test_invalid_point_type(self):
        """Test point field with wrong type (not integer)"""

        invalid_data = {
            "point": "not-an-integer",  # String instead of integer
            "text": "Test message",
        }

        serializer = PointMessageSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("point", serializer.errors)
        self.assertIn("integer", str(serializer.errors["point"]))
