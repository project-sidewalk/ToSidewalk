from latlng import LatLng
import json
import numpy as np
import random
from types import *


class Node(LatLng):
    def __init__(self, nid=None, lat=None, lng=None):
        # self.latlng = latlng  # Note: Would it be cleaner to inherit LatLng?
        super(Node, self).__init__(lat, lng)

        if type(nid) is IntType and nid > 0x7fffffff:
            nid = random.randint(0, 0x7fffffff)  # Generate a random unsigned integer.

        if nid is None:
            ri = random.randint(0, 0x7fffffff)  # Generate a random positive integer.
            self.id = str(ri)
        else:
            self.id = str(nid)

        self.edges = []

        self.user = "ProjectSidewalk"
        self.way_ids = []
        self.sidewalk_nodes = {}
        self.min_intersection_cardinality = 2
        self.crosswalk_distance = 0.00011
        self.confirmed = False
        self.made_from = []  # A list of nodes that this node is made from

        self._parent_nodes = None  # Parent Nodes data structure

        assert type(self.id) is StringType
        return

    def __str__(self):
        return str(self.id) + ": " + str(self.lat) + str(self.lng)

    def append_edge(self, edge):
        """
        Append an edge to a list of edges.

        :param edge: An Edge object
        """
        self.edges.append(edge)


    def get_edges(self):
        return self.edges

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
            len_before = len(self.way_ids)
            self.way_ids.append(wid)
            len_after = len(self.way_ids)
            assert len_before + 1 == len_after

    def append_ways(self, way_ids):
        """

        :param way_ids:
        :return:
        """
        for wid in way_ids:
            self.append_way(wid)

    def belongs_to(self):
        """TBD"""
        return self._parent_nodes

    def export(self, format="geojson"):

        """
        Export this node's information in Geojson format.
        """
        if self._parent_nodes and self._parent_nodes._parent_network:
            if format=="geojson":
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
        network = self._parent_nodes.belongs_to()
        return network.get_adjacent_nodes(self)

    def get_geojson_features(self):
        """
        A utilitie method to export the data as a geojson dump
        :return: A dictionary of geojson features
        """
        feature = dict()
        feature['properties'] = {
            'node_id': self.id,
            'lat': self.lat,
            'lng': self.lng,
            'way_ids': str(self.way_ids)
        }
        feature['type'] = 'Feature'
        feature['node_id'] = '%s' % (self.id)

        feature['geometry'] = {
            'type': 'Point',
            'coordinates': [self.lng, self.lat]
        }
        return feature

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