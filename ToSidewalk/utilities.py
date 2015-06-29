from itertools import islice
import math
import numpy as np

from types import *

def area(p1, p2, p3):
    """
    Given three points (x1, y1), (x2, y2), (x3, y3), return the area of the triangle that is formed by the three points.
    :param p1: Point 1 (e.g., [x1, y1])
    :param p2: Point 2 (e.g., [x2, y2])
    :param p3: Point 3 (e.g., [x3, y3])
    :return: Area of a triangle
    """
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    area = np.cross(v1, v2) / 2
    return abs(area)

def latlng_offset(lat_origin, lng_origin, **kwargs):
    """
    Given an original coordinate (lat, lng) and displacement (dx, dy) in meters,
    return a new latlng coordinate.
    http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    :param lat_origin: Original latitude
    :param lng_origin: Original longitude
    :param kwargs: Can take:
        dx: Displacement along the x-axis in Cartesian coordinate
        dy: Displacement along the y-axis in Cartesian coordinate
        vector: A vector
        distance: A size of the vector
    :return: Returns a tuple of latlng position
    """

    if 'dx' in kwargs and 'dy' in kwargs:
        dx = kwargs['dx']
        dy = kwargs['dy']
    elif 'vector' in kwargs and 'distance' in kwargs:
        assert kwargs['vector'] is ListType
        v = np.array(kwargs['vector'])
        v /= np.linalg.norm(v)
        angle = math.atan2(v[1], v[0])
        dx = kwargs['distance'] * math.cos(angle)
        dy = kwargs['distance'] * math.sin(angle)
    dlat = float(dy) / 111111
    dlng = float(dx) / (111111 * math.cos(math.radians(lat_origin)))
    return lat_origin + dlat, lng_origin + dlng

def latlng_offset_size(lat_origin, lng_origin, **kwargs):
    """
    Given an coordinate (lat, lng) and displacement (dx, dy) in meters, return the size of offset in latlng
    :param lat_origin:
    :param lng_origin:
    :param kwargs:
    :return: Returns a size of the offset
    """
    if 'dx' in kwargs and 'dy' in kwargs:
        dx = kwargs['dx']
        dy = kwargs['dy']
    elif 'vector' in kwargs and 'distance' in kwargs:
        assert kwargs['vector'] is ListType
        v = np.array(kwargs['vector'])
        v /= np.linalg.norm(v)
        angle = math.atan2(v[1], v[0])
        dx = kwargs['distance'] * math.cos(angle)
        dy = kwargs['distance'] * math.sin(angle)
    dlat = float(dy) / 111111
    dlng = float(dx) / (111111 * math.cos(math.radians(lat_origin)))
    return math.sqrt(dlat * dlat + dlng * dlng)

def window(seq, n=2, padding=None):
    """
    Returns a sliding window (of width n) over data from the iterable
       s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...

    Itertools
    https://docs.python.org/2/library/itertools.html#recipes
    Helper sliding window iterater method
    See: http://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator-in-python

    :param seq: An iterable like a list
    :param n: A size of a window
    :param padding: Padding at the both ends of the iterable.
    """
    # it = iter(seq)
    if padding is not None:
        seq = [None for i in range(padding)] + list(seq) + [None for i in range(padding)]
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result
    return
