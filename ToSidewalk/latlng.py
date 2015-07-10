from math import radians, cos, sin, asin, sqrt

class LatLng(object):
    def __init__(self, lat, lng, node_id=None):
        self.lat = float(lat)
        self.lng = float(lng)
        return

    def __eq__(self, other):
        return self.lat == other.lat and self.lng == other.lng

    def __str__(self):
        return str(self.lat) + "," + str(self.lng)

    def distance_to(self, latlng):

        """Get a distance from this object's coordinate to
        another latlng coordinate in meters

        :param latlng: A LatLng object
        :return: Distance in meters
        """
        try:
            return haversine(radians(self.lng), radians(self.lat), radians(latlng.lng), radians(latlng.lat))
        except AttributeError:
            raise


    def location(self):
        """Returns a tuple of latlng

        :return: A tuple (lat, lng)
        """
        return self.lat, self.lng

def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance between two points
    on the earth (specified in decimal radians)
    http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    :param lon1: Longitude of the first point
    :param lat1: Latitude of the first point
    :param lon2: Longitude of the second point
    :param lat2: Latitude of the second point
    :return: A distance in meters
    """
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Radius of earth in kilometers. Use 3956 for miles
    return c * r
