import numpy as np
import logging as log
from types import *
from shapely.geometry import Polygon, LineString, Point
from utilities import latlng_offset_size, window


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
