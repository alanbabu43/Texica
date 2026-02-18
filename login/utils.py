from decimal import Decimal
import math

# Fare calculation utility

# Base fares and per km rates for different vehicle types
FARE_CONFIG = {
    'auto': {
        'base_fare': Decimal('30.00'),
        'per_km': Decimal('12.00'),
        'min_fare': Decimal('30.00'),
    },
    'sedan': {
        'base_fare': Decimal('50.00'),
        'per_km': Decimal('15.00'),
        'min_fare': Decimal('50.00'),
    },
    'suv': {
        'base_fare': Decimal('80.00'),
        'per_km': Decimal('20.00'),
        'min_fare': Decimal('80.00'),
    },
    'luxury': {
        'base_fare': Decimal('150.00'),
        'per_km': Decimal('30.00'),
        'min_fare': Decimal('150.00'),
    },
}


def calculate_fare(distance, vehicle_type):
    """
    Calculate fare based on distance and vehicle type
    
    Args:
        distance: Distance in kilometers (float or Decimal)
        vehicle_type: Type of vehicle ('auto', 'sedan', 'suv', 'luxury')
    
    Returns:
        Decimal: Calculated fare
    """
    if vehicle_type not in FARE_CONFIG:
        vehicle_type = 'sedan'  # Default to sedan
    
    config = FARE_CONFIG[vehicle_type]
    distance = Decimal(str(distance))
    
    # Calculate fare: base fare + (distance * per km rate)
    fare = config['base_fare'] + (distance * config['per_km'])
    
    # Ensure minimum fare
    fare = max(fare, config['min_fare'])
    
    # Round to 2 decimal places
    return fare.quantize(Decimal('0.01'))


def estimate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula
    
    Args:
        lat1, lon1: Pickup coordinates
        lat2, lon2: Dropoff coordinates
    
    Returns:
        float: Distance in kilometers
    """
    # Convert to float if Decimal
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return round(distance, 2)


def generate_transaction_id(booking_id):
    """
    Generate a unique transaction ID
    
    Args:
        booking_id: Booking ID
    
    Returns:
        str: Transaction ID
    """
    import uuid
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8].upper()
    
    return f"TXN{booking_id}{timestamp}{unique_id}"
