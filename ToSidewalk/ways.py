import json
import math
import numpy as np
from shapely.geometry import Polygon, LineString, Point
from utilities import latlng_offset_size, window
from types import *

class Way(object):
    def __init__(self, wid=None, nids=[], type=None):
        if wid is None:
            self.id = str(id(self))
        else:
            self.id = str(wid)
        self.nids = list(nids)
        self.type = type
        self.user = 'test'
        self.parent_ways = None

        assert len(self.nids) > 1

    def belongs_to(self):
        """
        Returns a parent Ways object
        :return:
        """
        return self.parent_ways

    def export(self):
        """
        A utility method to export the data as a geojson dump
        :return: A geojson data in a string format.
        """
        if self.parent_ways and self.parent_ways.parent_network:
            geojson = dict()
            geojson['type'] = "FeatureCollection"
            geojson['features'] = []
            feature = self.get_geojson_features()
            geojson['features'].append(feature)
            return json.dumps(geojson)

    def get_geojson_features(self):
        """
        A utilitie method to export the data as a geojson dump
        :return: A dictionary of geojson features
        """
        feature = dict()
        feature['properties'] = {
            'type': self.type,
            'id': self.id,
            'user': self.user,
            "stroke-width": 2,
            "stroke-opacity": 1,
            'stroke': '#e93f3f'
        }
        feature['type'] = 'Feature'
        feature['id'] = 'way/%s' % (self.id)

        coordinates = []
        for nid in self.nids:
            node = self.parent_ways.parent_network.nodes.get(nid)
            coordinates.append([node.lng, node.lat])
        feature['geometry'] = {
            'type': 'LineString',
            'coordinates': coordinates
        }
        return feature

    def get_node_ids(self):
        """
        Get a list of node ids
        :return: A list of node ids
        """
        return self.nids

    def get_nodes(self):
        """
        Get nodes
        :return:
        """
        ways = self.belongs_to()
        network = ways.belongs_to()
        node_ids = self.get_node_ids()
        return [network.get_node(nid) for nid in node_ids]

    def get_shared_node_ids(self, other):
        """
        Get node ids that are shared between two Way objects. other could be either
        a list of node ids or a Way object.
        :param other: A list of node ids or a Way object
        :return: A list of node ids
        """
        if type(other) == list:
            return list(set(self.nids) & set(other))
        else:
            return list(set(self.nids) & set(other.get_node_ids()))

    def insert_node(self, insert_index, nid_to_insert):
        """
        Insert a node id into nids
        :param insert_index:
        :param nid_to_insert:
        """
        self.nids.insert(insert_index, nid_to_insert)

    def remove_node(self, nid_to_remove):
        """
        Remove a node from the data structure
        http://stackoverflow.com/questions/2793324/is-there-a-simple-way-to-delete-a-list-element-by-value-in-python
        :param nid_to_remove: A node id
        """
        self.nids = [nid for nid in self.nids if nid != nid_to_remove]

    def swap_nodes(self, nid_from, nid_to):
        """
        Swap a node that forms the way with another node
        :param nid_from: A node id
        :param nid_to: A node id
        """
        index_from = self.nids.index(nid_from)
        self.nids[index_from] = nid_to

    def angle(self):
        """
        Get an angle formed by a vector from the first node to the last one.
        :return:
        """
        ways = self.belongs_to()
        network = ways.belongs_to()
        start_node = network.get_node(self.nids[0])
        end_node = network.get_node(self.nids[-1])
        vector = start_node.vector_to(end_node, normalize=True)
        angle = math.degrees(math.atan2(vector[0], vector[1]))
        return angle

    def polygon(self, distance_to_sidewalk=15):
        """
        Get a polygon
        :param distance_to_sidewalk:
        :return:
        """
        ways = self.belongs_to()
        network = ways.belongs_to()
        start_node = network.get_node(self.nids[0])
        end_node = network.get_node(self.nids[-1])
        vector = start_node.vector_to(end_node, normalize=True)
        perpendicular = np.array([vector[1], - vector[0]])
        distance = latlng_offset_size(start_node.lat, vector=perpendicular, distance=distance_to_sidewalk)
        p1 = start_node.vector() + perpendicular * distance
        p2 = end_node.vector() + perpendicular * distance
        p3 = end_node.vector() - perpendicular * distance
        p4 = start_node.vector() - perpendicular * distance

        poly = Polygon([p1, p2, p3, p4])
        return poly

    def is_parallel_to(self, other, threshold=10.):
        """
        Check if this way is parallel to another one
        :param other: A Way object or a way id
        :return:
        """
        if type(other) == StringType:
            streets = self.belongs_to()
            other = streets.get(other)

        poly1 = self.polygon()
        poly2 = other.polygon()
        angle1 = self.angle()
        angle2 = other.angle()
        angle_diff = (angle1 - angle2 + 360) % 360
        angle_diff = min(angle_diff, 360 - angle_diff)
        return (angle_diff < threshold or angle_diff > 180 - threshold) and poly1.intersects(poly2)

    def on_same_street(self, other):
        """
        Is on the same street
        :param other:
        :return:
        """
        ways = self.belongs_to()
        network = ways.belongs_to()
        base_node0 = network.get_node(self.nids[0])
        base_node1 = network.get_node(other.nids[-1])
        base_vector = base_node0.vector_to(base_node1, normalize=True)

        def cmp_with_projection(n1, n2):
            dot_product1 = np.dot(n1.vector(), base_vector)
            dot_product2 = np.dot(n2.vector(), base_vector)
            if dot_product1 < dot_product2:
                return -1
            elif dot_product2 < dot_product1:
                return 1
            else:
                return 0

        # Sort the nodes in the second street
        street_2_nodes = [network.get_node(nid) for nid in other.nids]
        sorted_street2_nodes = sorted(street_2_nodes, cmp=cmp_with_projection)
        if street_2_nodes[0].id != sorted_street2_nodes[0].id:
            other.nids = list(reversed(other.nids))

        if self.nids[0] == other.nids[-1] or self.nids[-1] == other.nids[0]:
            return True

        # Check if they are on the same street or not.
        all_nodes = [network.get_node(nid) for nid in self.nids] + [network.get_node(nid) for nid in other.nids]
        all_nodes = sorted(all_nodes, cmp=cmp_with_projection)
        all_nids = [node.id for node in all_nodes]

        if all_nids[0] == all_nids[1]:
            # Two ways share the first node, then forks
            return False
        elif all_nids[-1] == all_nids[-2]:
            # Two ways share the last node, then forks
            return False

        all_nids_street_indices = [0 if nid in self.nids else 1 for nid in all_nids]
        all_nids_street_switch = [idx_pair[0] != idx_pair[1] for idx_pair in window(all_nids_street_indices, 2)]

        # Check if there is any parallel region between two ways
        if sum(all_nids_street_switch) == 1:
            return True
        else:
            return False

    def merge(self, other):
        """
        Merge two ways
        :param other:
        :return:
        """
        network = self.belongs_to().belongs_to()
        from network import Network
        import itertools
        temp_network = Network()
        my_nodes = self.get_nodes()
        other_nodes = other.get_nodes()
        temp_network.add_nodes(my_nodes)
        temp_network.add_nodes(other_nodes)
        base_vector = my_nodes[0].vector_to(my_nodes[-1], normalize=True)

        def cmp_with_projection(n1, n2):
            dot_product1 = np.dot(n1.vector(), base_vector)
            dot_product2 = np.dot(n2.vector(), base_vector)
            if dot_product1 < dot_product2:
                return -1
            elif dot_product2 < dot_product1:
                return 1
            else:
                return 0

        my_ways = [temp_network.create_street(None, [pair[0].id, pair[1].id]) for pair in window(my_nodes, 2)]
        other_ways = [temp_network.create_street(None, [pair[0].id, pair[1].id]) for i, pair in enumerate(window(other_nodes, 2))]

        # Find intersecting segments
        intersecting_pairs = []
        non_intersecting_pairs = []
        for pair in itertools.product(my_ways, other_ways):
            poly1 = pair[0].polygon()
            poly2 = pair[1].polygon()
            if poly1.intersects(poly2):
                intersecting_pairs.append(pair)
            else:
                non_intersecting_pairs.append(pair)

        # Join connected segments of ways following Anthony's code

        my_ways_to_join, other_ways_to_join = zip(*intersecting_pairs)

        new_nodes = []
        my_nodes_to_join = []
        for way in set(my_ways_to_join):
            my_nodes_to_join.append(way.get_nodes()[0])
        my_nodes_to_join.append(way.get_nodes()[1])
        my_nodes_to_join = sorted(list(set(my_nodes_to_join)), cmp=cmp_with_projection)

        other_nodes_to_join = []
        for way in set(other_ways_to_join):
            other_nodes_to_join.append(way.get_nodes()[0])
        other_nodes_to_join.append(way.get_nodes()[1])
        other_nodes_to_join = sorted(list(set(other_nodes_to_join)), cmp=cmp_with_projection)

        lat_origin = (my_nodes_to_join[0].lat + other_nodes_to_join[0].lat) / 2
        lng_origin = (my_nodes_to_join[0].lng + other_nodes_to_join[0].lng) / 2
        from nodes import Node
        origin = Node(None, lat_origin, lng_origin)

        new_nodes = my_nodes_to_join + other_nodes_to_join
        new_nodes = sorted(new_nodes, cmp=cmp_with_projection)
        new_node_ids = []
        for node in new_nodes:
            v = origin.vector_to(node)
            d = np.dot(v, base_vector)
            new_lat, new_lng = origin.vector() + base_vector * d
            node = network.create_node(None, new_lat, new_lng)
            new_node_ids.append(node.id)
        network.create_street(None, new_node_ids)


class Ways(object):
    def __init__(self):
        self.ways = {}
        self.intersection_node_ids = []
        self.parent_network = None

    def __eq__(self, other):
        return id(self) == id(other)

    def add(self, way):
        """
        Add a Way object
        :param way: A Way object
        """
        way.parent_ways = self
        self.ways[way.id] = way

    def belongs_to(self):
        """
        Return a parent network
        :return: A Network object
        """
        return self.parent_network

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

    def getdirection(self):
        startnode=self.parent_ways.parent_network.nodes.get(self.get_node_ids()[0])
        endnode=self.parent_ways.parent_network.nodes.get(self.get_node_ids()[-1])
        startlat=startnode.lat
        endlat = endnode.lat

        if startlat>endlat:
            return 1
        else:
            return -1

    def set_oneway_tag(self, oneway_tag):
        self.oneway = oneway_tag

    def set_ref_tag(self, ref_tag):
        self.ref = ref_tag

    def get_oneway_tag(self):
        return self.oneway

    def get_ref_tag(self):
        return self.ref

    def append_sidewalk_id(self, way_id):
        self.sidewalk_ids.append(way_id)
        return self

    def get_sidewalk_ids(self):
        return self.sidewalk_ids

    def get_length(self):
        start_node = self.parent_ways.parent_network.nodes.get(self.get_node_ids()[0])
        end_node = self.parent_ways.parent_network.nodes.get(self.get_node_ids()[-1])
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

