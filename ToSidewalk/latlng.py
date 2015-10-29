import numpy as np
from math import radians, cos, sin, asin, sqrt, atan2
from shapely.geometry import Point


class LatLng(Point):
    def __init__(self, lat, lng):
        super(LatLng, self).__init__(lng, lat)
        self.lat = float(lat)
        self.lng = float(lng)

    def __eq__(self, other):
        return self.lat == other.lat and self.lng == other.lng

    def __str__(self):
        return str(self.lat) + "," + str(self.lng)

    def angle_to(self, latlng):
        """
        Get an agnle from this LatLng to another LatLng

        :param node: A node object
        """
        y_node, x_node = latlng.lat, latlng.lng
        y_self, x_self = self.lat, self.lng
        return atan2(y_node - y_self, x_node - x_self)

    def distance_in_meters(self, latlng):
        """
        Get a distance from this object's coordinate to
        another latlng coordinate in meters

        :param latlng: A LatLng object
        :return: Distance in meters
        """
        return self.distance_to(latlng)

    def distance_to(self, latlng):
        """
        Deprecated. This is called by distance_in_meters
        """
        try:
            return haversine(radians(self.lng), radians(self.lat), radians(latlng.lng), radians(latlng.lat))
        except AttributeError:
            raise

    def vector(self):
        """
        Get a Numpy array representation of a latlng coordinate

        :return: A latlng coordinate in a 2-d Numpy array
        """
        return np.array([self.lat, self.lng])

    def vector_to(self, latlng, normalize=False):
        """
        Get a vector from the latlng coordinate of this latlng to another latlng.

        :param latlng: The target LatLng object.
        :param normalize: Boolean.
        :return: A vector in a 2-d Numpy array
        """
        vec = np.array([self.lat, self.lng]) - np.array([self.lat, self.lng])
        if normalize and np.linalg.norm(vec) != 0:
            vec /= np.linalg.norm(vec)
        return vec


class LngLat(LatLng):
    def __init__(self, lng, lat):
        super(LngLat, self).__init__(lat, lng)


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal radians)
    http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points

    :param lon1: Longitude of the first point
    :param lat1: Latitude of the first point
    :param lon2: Longitude of the second point
    :param lat2: Latitude of the second point
    :return: A distance in meters
    """
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Radius of earth in kilometers. Use 3956 for miles
    return c * r
