from latlng import LatLng
import json
import numpy as np
import math
import logging as log
from types import *
from shapely.geometry import Polygon, LineString, Point
from utilities import latlng_offset_size, window

class Node(LatLng):
    def __init__(self, nid=None, lat=None, lng=None):
        # self.latlng = latlng  # Note: Would it be cleaner to inherit LatLng?
        super(Node, self).__init__(lat, lng)

        if nid is None:
            self.id = str(id(self))
        else:
            self.id = str(nid)

        self.way_ids = []
        self.sidewalk_nodes = {}
        self.min_intersection_cardinality = 2
        self.crosswalk_distance = 0.00010
        self.confirmed = False
        self.made_from = []  # A list of nodes that this node is made from

        self._parent_nodes = None  # Parent Nodes data structure

        assert type(self.id) is StringType
        return

    def __str__(self):
        return "Node object, id: " + str(self.id) + ", latlng: " + str(self.location())

    def angle_to(self, node):
        """TBD

        :param node: A node object
        """
        y_node, x_node = node.location()
        y_self, x_self = self.location()
        return math.atan2(y_node - y_self, x_node - x_self)

    def append_sidewalk_node(self, way_id, node):
        """TBD

        :param way_id: TBD
        :param ndoe: TBD
        """
        self.sidewalk_nodes.setdefault(way_id, []).append(node)

    def append_way(self, wid):
        """
        Add a way id to the list that keeps track of
        which ways are connected to the node

        :param wid: Way id
        :return:
        """
        if wid not in self.way_ids:
            self.way_ids.append(wid)

    def belongs_to(self):
        """TBD"""
        return self._parent_nodes

    def export(self):
        """
        Export this node's information in Geojson format.
        """
        if self._parent_nodes and self._parent_nodes._parent_network:
            geojson = {}
            geojson['type'] = "FeatureCollection"
            geojson['features'] = []
            for way_id in self.way_ids:
                way = self._parent_nodes._parent_network.ways.get(way_id)
                geojson['features'].append(way.get_geojson_features())
            return json.dumps(geojson)

    def get_adjacent_nodes(self):
        """
        Return a list of Node objects that are adjacent to this Node object (self)

        :return: A list of nodes
        """
        network = _parent_nodes.belongs_to()
        return network.get_adjacent_nodes(self)

    def get_way_ids(self):
        """ Return a list of way_ids that are connected to this node.

        :return: A list of way ids
        """
        return self.way_ids

    def get_shared_way_ids(self, other):
        """
        Other could be a Node object or a list of way ids

        :param other: A Node object or a list of way ids
        :return: A list of way ids that are shared between this node and other
        """
        if type(other) == list:
            return list(set(self.way_ids) & set(other))
        else:
            return list(set(self.way_ids) & set(other.get_way_ids()))

    def get_sidewalk_nodes(self, wid):
        """ Return sidewalk nodes

        :param wid: A way id
        :return: A list of node objects
        """
        if wid in self.sidewalk_nodes:
            return self.sidewalk_nodes[wid]
        else:
            return None

    def has_sidewalk_nodes(self):
        """ Check if this node has sidewalk nodes

        :return: Boolean
        """
        return len(self.sidewalk_nodes) > 0

    def is_intersection(self):
        """
        Check if this node is an intersection or not

        :return: Boolean
        """
        # adj_nodes = self.get_adjacent_nodes()
        # return len(adj_nodes) >= self.min_intersection_cardinality
        way_ids = self.get_way_ids()
        return len(way_ids) >= self.min_intersection_cardinality

    def remove_way_id(self, wid):
        """
        Remove a way id from the list that keeps track of what ways
        are connected to this node

        :param wid: A way id
        :return: return the way id of the deleted Way object
        """
        if wid in self.way_ids:
            self.way_ids.remove(wid)
            return wid
        return None

    def vector(self):
        """ Get a Numpy array representation of a latlng coordinate

        :return: A latlng coordinate in a 2-d Numpy array
        """
        return np.array(self.location())

    def vector_to(self, node, normalize=False):
        """ Get a vector from the latlng coordinate of this node to
        another node.

        :param node: The target Node object.
        :param normalize: Boolean.
        :return: A vector in a 2-d Numpy array
        """
        vec = np.array(node.location()) - np.array(self.location())
        if normalize and np.linalg.norm(vec) != 0:
            vec /= np.linalg.norm(vec)
        return vec


class Nodes(object):
    def __init__(self):
        self.nodes = {}
        self.crosswalk_node_ids = []
        self._parent_network = None
        return

    def add(self, node):
        """
        Add a Node object to self

        :param node: A Node object
        """
        node._parent_nodes = self
        self.nodes[node.id] = node

    def belongs_to(self):
        """
        Returns a parent network

        :return: A parent Network object
        """
        return self._parent_network

    def clean(self):
        """
        Remove all the nodes from the data structure if they are not connected to any ways
        """
        nodes = self.get_list()
        for node in nodes:
            if len(node.get_way_ids()) == 0:
                self.remove(node.id)

    def create_polygon(self, node1, node2, r=15.):
        """
        Create a rectangular polygon from two nodes passed

        :param nid1: A node id
        :param nid2: Another node id
        :return: A Shapely polygon (rectangle)
        """
        if type(node1) == StringType:
            node1 = self.get(node1)
            node2 = self.get(node2)

        # start_node = network.get_node(self.nids[0])
        # end_node = network.get_node(self.nids[-1])
        vector = node1.vector_to(node2, normalize=True)
        perpendicular = np.array([vector[1], - vector[0]])
        distance = latlng_offset_size(node1.lat, vector=perpendicular, distance=r)
        p1 = node1.vector() + perpendicular * distance
        p2 = node2.vector() + perpendicular * distance
        p3 = node2.vector() - perpendicular * distance
        p4 = node1.vector() - perpendicular * distance

        poly = Polygon([p1, p2, p3, p4])
        return poly

    def get(self, nid):
        """
        Get a Node object

        :param nid: A node id
        :return: A Node object
        """
        if nid in self.nodes:
            return self.nodes[nid]
        else:
            return None

    def get_intersection_nodes(self):
        """
        Get a list of Node objects, in which each node is an intersection node.

        :return: A list of Node objects
        """
        return [self.nodes[nid] for nid in self.nodes if self.nodes[nid].is_intersection()]

    def get_list(self):
        """
        Get a list of node objects

        :return: A list of Node objects
        """
        return self.nodes.values()

    def remove(self, nid):
        """
        Remove a node from the data structure
        http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary

        :param nid: A node id
        """
        del self.nodes[nid]

    def update(self, nid, new_node):
        """TBD

        :param nid:
        :param new_node:
        """
        self.nodes[nid] = new_node
        return

def print_intersections(nodes):
    for node in nodes.get_list():
        if node.is_intersection():
            location = node.latlng.location(radian=False)
            log.debug(str(location[0]) + "," + str(location[1]))
    return
