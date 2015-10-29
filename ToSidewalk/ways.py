import math
import numpy as np
from way import Way


class Ways(object):
    def __init__(self):
        self.ways = {}
        self.intersection_node_ids = []
        self._parent_network = None

    def __eq__(self, other):
        return id(self) == id(other)

    def add(self, way):
        """
        Add a Way object
        :param way: A Way object
        """
        way._parent_ways = self
        self.ways[way.id] = way

    def belongs_to(self):
        """
        Return a parent network
        :return: A Network object
        """
        return self._parent_network

    def get(self, wid):
        """
        Search and return a Way object by its id
        :param wid: A way id
        :return: A Way object
        """
        if wid in self.ways:
            return self.ways[wid]
        else:
            return None

    def get_list(self):
        """
        Get a list of all Way objects in the data structure
        :return: A list of Way objects
        """
        return self.ways.values()

    def has(self, wid):
        """
        Checks if the way id exists
        :param wid: A way id
        :return: Boolean
        """
        return wid in self.ways

    def remove(self, wid):
        """
        Remove a way from the data structure
        http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
        :param wid: A way id
        """
        del self.ways[wid]

    def set_intersection_node_ids(self, nids):
        self.intersection_node_ids = nids

# Notes on inheritance
# http://stackoverflow.com/questions/576169/understanding-python-super-with-init-methods
class Street(Way):
    def __init__(self, wid=None, nids=[], type=None):
        super(Street, self).__init__(wid, nids, type)
        self.sidewalk_ids = []  # Keep track of which sidewalks were generated from this way
        self.distance_to_sidewalk = 0.00008
        self.oneway = 'undefined'
        self.ref = 'undefined'
        self.hough = []
        # Maintain a list of neighboring streets, populated during merge
        self.neighbors = []
    def __hash__(self):
        start_nid = self.get_node_ids()[0]
        end_nid = self.get_node_ids()[-1]
        return hash((start_nid, end_nid))
    def add_neighbor(self, new_neighbor):
        self.neighbors.append(new_neighbor)
    def get_neighbors(self):
        return self.neighbors
    def get_start_latitude(self):
        start_node = self.get_nodes()[0]
        return start_node.lat
    def get_start_longitude(self):
        start_node = self.get_nodes()[0]
        return start_node.lng
    def get_end_latitude(self):
        end_node = self.get_nodes()[-1]
        return end_node.lat
    def get_end_longitude(self):
        end_node = self.get_nodes()[-1]
        return end_node.lng
    def get_hough_point(self):

        start_lat = self.get_start_latitude()
        start_long = self.get_start_longitude()
        end_lat = self.get_end_latitude()
        end_long = self.get_end_longitude()


        # Recenter the origin
        start_lat -= 38.9
        start_long += 76.988
        end_lat -= 38.9
        end_long += 76.988
        # Calculate what m and b are in slope-intercept form
        x1 = start_lat
        y1 = start_long
        x2 = end_lat
        y2 = end_long
        x0 = 0
        y0 = 0
        try:
            r = abs((y2 - y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1)/math.sqrt((y2-y1)**2 + (x2 - x1)**2)
        except ZeroDivisionError:
            r=100000
        dx = x2 - x1
        dy = y2 - y1
        rads = math.atan2(-dy,dx)
        rads %= 2 * math.pi
        degs = math.radians((math.degrees(rads) + 90) % 360)


        hough = [r, degs]
        self.hough = hough

        return hough

    def getdirection(self):
        """
        Get a direction of the street
        :return:
        """
        ways = self.belongs_to()
        network = ways.belongs_to()
        startnode = network.get_node(self.get_node_ids()[0])
        endnode = network.get_node(self.get_node_ids()[-1])
        startlat = startnode.lat
        endlat = endnode.lat

        if startlat > endlat:
            return 1
        else:
            return -1

    def set_oneway_tag(self, oneway_tag):

        """
        This method sets the oneway property of the Way object to "yes" or "no".

        :param str oneway_tag: One-way tag. Either "yes" or "no"
        """
        self.oneway = oneway_tag

    def set_ref_tag(self, ref_tag):
        """
        This method sets the reference property of the Way object.

        :param str ref_tag: Reference tag. A string refering to a reference way/node/relation.
        """
        self.ref = ref_tag

    def get_oneway_tag(self):
        """
        This method returns the oneway property

        :return: 
        """

        return self.oneway

    def get_ref_tag(self):
        """TBD"""
        return self.ref

    def append_sidewalk_id(self, way_id):
        """TBD"""
        self.sidewalk_ids.append(way_id)
        return self

    def get_sidewalk_ids(self):
        """TBD"""
        return self.sidewalk_ids

    def get_length(self):

        """TBD"""
        ways = self.belongs_to()
        network = ways.belongs_to()
        start_node = network.get_node(self.get_node_ids()[0])
        end_node = network.get_node(self.get_node_ids()[-1])

        vec = np.array(start_node.location()) - np.array(end_node.location())
        length = abs(vec[0] - vec[-1])
        return length

class Streets(Ways):
    def __init__(self):
        super(Streets, self).__init__()

class Sidewalk(Way):
    def __init__(self, wid=None, nids=[], type=None):
        super(Sidewalk, self).__init__(wid, nids, type)

    def set_street_id(self, street_id):
        """
        Set the parent street id
        :param street_id: A street id
        """
        self.street_id = street_id

class Sidewalks(Ways):
    def __init__(self):
        super(Sidewalks, self).__init__()
        self.street_id = None

