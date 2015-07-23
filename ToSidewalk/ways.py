import json
import math
import numpy as np
import itertools
import logging as log
import random
from shapely.geometry import Polygon, LineString, Point
from utilities import latlng_offset_size, window
from types import *
from nodes import Node

class Way(object):
    def __init__(self, wid=None, nids=[], way_type=None):
        self._original_ways = []
        if type(wid) is IntType and wid > 0x7fffffff:
            self._original_ways.append(str(wid))
            wid = random.randint(0, 0x7fffffff)  # Generate a random unsigned integer.

        if wid is None:
            ri = random.randint(0, 0x7fffffff)  # Generate a random unsigned integer.
            self.id = str(ri)
        else:
            self.id = str(wid)
        self.nids = list(nids)
        self.type = way_type
        self.user = 'ProjectSidewalk'
        self._parent_ways = None

        self._tags = []

        assert len(self.nids) > 1

    def add_tag(self, tag):
        """
        Appends a tag into self._tags
        :param tag: An osm tag
        :return:
        """
        self._tags.append(tag)

    def get_tags(self):
        """
        Returns a list of tags
        :return:
        """
        return self._tags

    def add_original_way(self, way):
        """
        This method adds a way id to _original_ways to keep track of from which
        ways from OSM this way was created.

        :param way: A way id or a Way object
        """
        if isinstance(way, Way):
            way = way.id

        if way not in self._original_ways:
            self._original_ways.append(way)

    def add_original_ways(self, ways):
        """

        :param ways:
        :return:
        """
        for way in ways:
            self.add_original_way(way)

    def belongs_to(self):
        """
        Returns a parent Ways object
        :return: A Ways object
        """
        return self._parent_ways

    def export(self):
        """
        A utility method to export the data as a geojson dump
        :return: A geojson data in a string format.
        """
        if self._parent_ways and self._parent_ways._parent_network:
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
        coordinates = []
        ways = self.belongs_to()
        network = ways.belongs_to()

        start = network.get_node(self.nids[0])
        end = network.get_node(self.nids[-1])

        feature = dict()
        feature['properties'] = {
            'way_type': self.type,
            'way_id': self.id,
            'user': self.user,
            'osm_ways': self._original_ways,
            'source': start.id,
            'target': end.id,
            'cost': 1.0,
            'reverse_cost': 1.0,
            'x1': start.lng,
            'y1': start.lat,
            'x2': end.lng,
            'y2': end.lat,
            'node_ids': self.nids
        }
        feature['type'] = 'Feature'
        feature['id'] = '%s' % (self.id)

        for nid in self.nids:
            node = network.get_node(nid)
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

    def get_original_ways(self):
        """
        Returns original_ways

        :return: A list of way ids
        """
        return self._original_ways

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
        Use Network.remove_node!

        Remove a node from nid (a list of node ids)
        http://stackoverflow.com/questions/2793324/is-there-a-simple-way-to-delete-a-list-element-by-value-in-python
        :param nid_to_remove: A node id
        """
        if isinstance(nid_to_remove, Node):
            nid_to_remove = nid_to_remove.id


        self.nids = [nid for nid in self.nids if nid != nid_to_remove]
        #
        # temp_ways = self.belongs_to()
        # if temp_ways:
        #     temp_network = temp_ways.belongs_to()
        #     if temp_network:
        #         node = temp_network.get_node(nid_to_remove)
        #         node.remove_way_id(self.id)
        #
        #         # if len(node.get_way_ids()) < 1:
        #         #     temp_network.remove_node(node)
        #
        #         if len(self.nids) < 2:
        #             temp_network.remove_way(self)

    def swap_nodes(self, node_from, node_to):

        """
        Swap a node that forms the way with another node. The new node inherits previous node's way_ids

        :param nid_from: A node id or a Node object
        :param nid_to: A node id or a Node object
         """
        network = self.belongs_to().belongs_to()
        if type(node_from) == StringType:
            node_from = network.get_node(node_from)
        if type(node_to) == StringType:
            node_to = network.get_node(node_to)

        try:
            index_from = self.nids.index(node_from.id)
            if node_to.id in self.nids:
                self.remove_node(node_from.id)  # remove node id if node_to.id already exists
            else:
                self.nids[index_from] = node_to.id
        except AttributeError:
            print node_from, node_to
            log.debug("Way.swap_nodes(): Debug")
        #except ValueError:
        #    return
        for way_id in node_from.way_ids:
            node_to.append_way(way_id)

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
        ways = self.belongs_to()
        network = ways.belongs_to()
        my_nodes = self.get_nodes()
        other_nodes = other.get_nodes()

        # Create a base vector that defines the direction of a parallel line
        v1 = my_nodes[0].vector_to(my_nodes[-1], normalize=True)
        v2 = other_nodes[0].vector_to(other_nodes[-1], normalize=True)
        base_vector = v1 + v2
        base_vector /= np.linalg.norm(base_vector)

        def cmp_with_projection(n1, n2):
            dot_product1 = np.dot(n1.vector(), base_vector)
            dot_product2 = np.dot(n2.vector(), base_vector)
            if dot_product1 < dot_product2:
                return -1
            elif dot_product2 < dot_product1:
                return 1
            else:
                return 0

        # Chop this way and the way to merge into pieces of smaller ways to find what regions of
        # those ways you want to merge together
        my_ways = [Street(None, [pair[0].id, pair[1].id]) for pair in window(my_nodes, 2)]
        other_ways = [Street(None, [pair[0].id, pair[1].id]) for pair in window(other_nodes, 2)]

        # Find intersecting regions. Create all the combinations between pieces of streets
        # in my_ways and other_ways using itertools.product. Check if polygons formed by each pair
        # intersect to each other. If they do, count them as intersecting pairs.
        intersecting_pairs = []
        non_intersecting_pairs = []
        for pair in itertools.product(my_ways, other_ways):
            way1 = pair[0]
            way2 = pair[1]
            node1_1 = network.get_node(way1.nids[0])
            node1_2 = network.get_node(way1.nids[-1])
            node2_1 = network.get_node(way2.nids[0])
            node2_2 = network.get_node(way2.nids[-1])

            poly1 = network.nodes.create_polygon(node1_1, node1_2)
            poly2 = network.nodes.create_polygon(node2_1, node2_2)

            if poly1.intersects(poly2):
                intersecting_pairs.append(pair)
            else:
                non_intersecting_pairs.append(pair)

        # Join pieces of streets that you want to intersect
        try:
            my_ways_to_join, other_ways_to_join = zip(*intersecting_pairs)
        except ValueError:
            assert len(intersecting_pairs) == 0
            return

        my_node_ids_to_join = []
        for way in set(my_ways_to_join):
            my_node_ids_to_join.append(way.get_node_ids()[0])
        my_node_ids_to_join.append(way.get_node_ids()[1])
        my_nodes_to_join = [network.get_node(nid) for nid in my_node_ids_to_join]
        my_nodes_to_join = sorted(list(set(my_nodes_to_join)), cmp=cmp_with_projection)

        other_node_ids_to_join = []
        for way in set(other_ways_to_join):
            other_node_ids_to_join.append(way.get_node_ids()[0])
        other_node_ids_to_join.append(way.get_node_ids()[1])
        other_nodes_to_join = [network.get_node(nid) for nid in other_node_ids_to_join]
        other_nodes_to_join = sorted(list(set(other_nodes_to_join)), cmp=cmp_with_projection)

        # Define a origin. The nodes that constitute the merged way will be created at locations
        # relative to this origin.
        lat_origin = (my_nodes_to_join[0].lat + other_nodes_to_join[0].lat) / 2
        lng_origin = (my_nodes_to_join[0].lng + other_nodes_to_join[0].lng) / 2
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

        # print non_intersecting_pairs


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

