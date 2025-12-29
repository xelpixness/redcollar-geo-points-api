import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points on Earth
    using Haversine formula (in kilometers)

    Formula:
    a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
    c = 2 ⋅ atan2(√a, √(1−a))
    d = R ⋅ c

    where:
    φ = latitude in radians
    λ = longitude in radians
    R = Earth's radius (6371 km)
    """
    # Earth radius in kilometers
    R = 6371.0

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in kilometers
    distance = R * c

    return distance
