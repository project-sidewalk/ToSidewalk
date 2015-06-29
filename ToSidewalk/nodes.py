from latlng import LatLng
import json
import numpy as np
import math
import logging as log
from types import *

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
        self.parent_nodes = None
        self.confirmed = False

        assert type(self.id) is StringType
        return

    def __str__(self):
        return "Node object, id: " + str(self.id) + ", latlng: " + str(self.location())

    def angle_to(self, node):
        y_node, x_node = node.location()
        y_self, x_self = self.location()
        return math.atan2(y_node - y_self, x_node - x_self)

    def append_sidewalk_node(self, way_id, node):
        self.sidewalk_nodes.setdefault(way_id, []).append(node)

    def append_way(self, wid):
        if wid not in self.way_ids:
            self.way_ids.append(wid)

    def belongs_to(self):
        return self.parent_nodes

    def export(self):
        if self.parent_nodes and self.parent_nodes.parent_network:
            geojson = {}
            geojson['type'] = "FeatureCollection"
            geojson['features'] = []
            for way_id in self.way_ids:
                way = self.parent_nodes.parent_network.ways.get(way_id)
                geojson['features'].append(way.get_geojson_features())
            return json.dumps(geojson)

    def get_adjacent_nodes(self):
        """
        A list of Node objects that are adjacent to this Node object (self)
        :return: A list of nodes
        """
        parent_nodes = self.belongs_to()
        network = parent_nodes.belongs_to()
        return network.get_adjacent_nodes(self)

    def get_way_ids(self):
        return self.way_ids

    def get_shared_way_ids(self, other):
        """
        Other could be either a list of way ids, or a Node object
        """
        if type(other) == list:
            return list(set(self.way_ids) & set(other))
        else:
            return list(set(self.way_ids) & set(other.get_way_ids()))

    def get_sidewalk_nodes(self, wid):
        return self.sidewalk_nodes[wid]

    def has_sidewalk_nodes(self):
        return len(self.sidewalk_nodes) > 0

    def is_intersection(self):
        return len(self.get_adjacent_nodes()) >= self.min_intersection_cardinality
        # return len(self.get_way_ids()) >= self.min_intersection_cardinality

    def remove_way_id(self, wid):
        if wid in self.way_ids:
            self.way_ids.remove(wid)
        return

    def vector(self):
        return np.array(self.location())

    def vector_to(self, node, normalize=False):
        vec = np.array(node.location()) - np.array(self.location())
        if normalize and np.linalg.norm(vec) != 0:
            vec /= np.linalg.norm(vec)
        return vec


class Nodes(object):
    def __init__(self):
        self.nodes = {}
        self.crosswalk_node_ids = []
        self.parent_network = None
        return

    def add(self, node):
        """
        Add a Node object to self
        :param node: A Node object
        """
        node.parent_nodes = self
        self.nodes[node.id] = node

    def belongs_to(self):
        """
        Returns a parent network
        :return: A parent Network object
        """
        return self.parent_network

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
        Remove a node from self.nodes
        http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
        :param nid:
        :return:
        """
        del self.nodes[nid]

    def update(self, nid, new_node):
        self.nodes[nid] = new_node
        return

def print_intersections(nodes):
    for node in nodes.get_list():
        if node.is_intersection():
            location = node.latlng.location(radian=False)
            log.debug(str(location[0]) + "," + str(location[1]))
    return
