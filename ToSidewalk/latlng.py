from math import radians, cos, sin, asin, sqrt

class LatLng(object):
    def __init__(self, lat, lng, node_id=None):
        self.lat = float(lat)
        self.lng = float(lng)
        return

    def __eq__(self, other):
        return self.lat == other.lat and self.lng == other.lng

    def distance_to(self, latlng):
        return haversine(radians(self.lng), radians(self.lat), radians(latlng.lng), radians(latlng.lat))

    def location(self):
        return self.lat, self.lng

    def __str__(self):
        return str(self.lat) + "," + str(self.lng)

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal radians)

    http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    """
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r
