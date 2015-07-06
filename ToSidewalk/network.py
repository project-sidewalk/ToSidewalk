from xml.etree import cElementTree as ET
from shapely.geometry import Polygon, Point, LineString
from datetime import datetime
from types import StringType
from itertools import combinations
from heapq import heappush, heappop, heapify

import json
import logging as log
import math
import numpy as np


from nodes import Node, Nodes
from ways import Street, Streets, Ways
from utilities import window, area, foot, points_to_line


class Network(object):
    def __init__(self, nodes=None, ways=None):
        if nodes is None:
            self.nodes = Nodes()
        else:
            self.nodes = nodes

        if ways is None:
            self.ways = Ways()
        else:
            self.ways = ways

        self.ways._parent_network = self
        self.nodes._parent_network = self

        self.bounds = [100000.0, 100000.0, -100000.0, -100000.0]  # min lat, min lng, max lat, and max lng

        # Initialize the bounding box
        for node in self.nodes.get_list():
            # lat, lng = node.latlng.location(radian=False)
            self.bounds[0] = min(node.lat, self.bounds[0])
            self.bounds[2] = max(node.lat, self.bounds[2])
            self.bounds[1] = min(node.lng, self.bounds[1])
            self.bounds[3] = max(node.lng, self.bounds[3])

    def add_node(self, node):
        """
        Add a node to this network

        :param node: A Node object to add
        :return:
        """
        self.nodes.add(node)

    def add_nodes(self, nodes):
        """
        Add a list of nodes to this network

        :param nodes: A list of Node objects
        """
        for node in nodes:
            self.add_node(node)

    def add_way(self, way):
        """
        Add a Way object into this network

        :param way: A Way object to add
        """
        self.ways.add(way)
        for nid in way.nids:
            # self.nodes.get(nid).way_ids.append(way.id)
            node = self.get_node(nid)
            node.append_way(way.id)

    def add_ways(self, ways):
        """
        Add a list of Way objects to this network

        :param ways: A list of way objects
        """
        for way in ways:
            self.add_way(way)

    def create_node(self, node_id, lat, lng):
        """
        Create a new node and add it to the network

        :param node_id: A node id
        :param lat: Latitude
        :param lng: Longitude
        :return: The new Node object
        """
        node = Node(node_id, lat, lng)
        self.add_node(node)
        return node

    def create_street(self, street_id, nids, type=None):
        """
        Create a new street and add it to the network

        :param street_id: A street id
        :param nids: A list of node ids
        :param type: A street type
        :return: A new Street object
        """
        street = Street(street_id, nids, type)
        for nid in nids:
            node = self.get_node(nid)
            node.append_way(street.id)

        self.add_way(street)
        return street

    def get_adjacent_nodes(self, node):
        """
        Get adjacent nodes for the passed node

        :param node: A node object
        :return: A list of Node objects that are adjacent to the passed Node object
        """
        adj_nodes = []
        way_ids = node.get_way_ids()

        for way_id in way_ids:
            try:
                way = self.get_way(way_id)

                # If the current intersection node is at the head of street.nids, then take the second node and push it
                # into adj_street_nodes. Otherwise, take the node that is second to the last in street.nids .
                if way.nids[0] == node.id:
                    adj_nodes.append(self.nodes.get(way.nids[1]))
                else:
                    adj_nodes.append(self.nodes.get(way.nids[-2]))
            except AttributeError:
                log.exception("Way does not exist. way_id=%s" % way_id)
                continue

        return list(set(adj_nodes))

    def get_node(self, node_id):
        """
        Get a Node object

        :param node_id: A node id
        :return: A Node object
        """
        return self.nodes.get(node_id)

    def get_nodes(self):
        """
        Get all the Node objects

        :return: A list of Node objects
        """
        return self.nodes.get_list()

    def get_way(self, way_id):
        """
        Get a Way object

        :param way_id: A way id
        :return: A Way object
        """
        return self.ways.get(way_id)

    def get_ways(self):
        """
        Get all the way objects

        :return: A list of all the ways in the network
        """
        return self.ways.get_list()

    def parse_intersections(self):
        """
        TBD
        """
        node_list = self.nodes.get_list()
        intersection_node_ids = [node.id for node in node_list if node.is_intersection()]
        self.ways.set_intersection_node_ids(intersection_node_ids)

    def remove_node(self, nid):
        """
        Remove a node from the network.

        :param nid: A node id
        """
        if isinstance(nid, Node):
            nid = nid.id

        node = self.nodes.get(nid)
        for way_id in node.get_way_ids():
            way = self.ways.get(way_id)

            len_before = len(way.nids)
            way.remove_node(nid)
            len_after = len(way.nids)
            # try:
            #     assert len_after == len_before - 1
            #     assert len_after >= 2
            # except AssertionError:
            #     raise

        self.nodes.remove(nid)

    def remove_way(self, way_id):
        """
        Remove a way object from this network

        :param way_id: A way id
        :return:
        """
        way = self.get_way(way_id)
        if way:
            for nid in way.get_node_ids():

                node = self.get_node(nid)
                if node:
                    len_way_ids_before = len(node.get_way_ids())
                    node.remove_way_id(way_id)
                    len_way_ids_after = len(node.get_way_ids())
                    # try:
                    #     assert len_way_ids_before - 1 == len_way_ids_after
                    # except AssertionError:
                    #     print len_way_ids_before, len_way_ids_after
                    #     raise

                    way_ids = node.get_way_ids()
                    # Delete the node if it is no longer associated with any ways
                    if len(way_ids) == 0:
                        self.remove_node(nid)

                        assert nid not in self.nodes.nodes.keys()

            self.ways.remove(way_id)
            assert way_id not in self.ways.ways.keys()

    def join_ways(self, way_id_1, way_id_2):
        """
        Join two ways together to form a single way. Intended for use when a single long street is divided
        into multiple ways, which can cause issues with merging.

        :param way_id_1: ID of first way to merge. Must be passed as a string.
        :param way_id_2: ID of second way to merge. Must be passed as a string.
        :return:
        """
        # Take all nodes from way 2 and add them to way 1
        log.debug("Attempting to join ways " + way_id_1 + " and " + way_id_2 + " for merging.")
        try:
            way2 = self.ways.get(way_id_2)
            for nid in way2.get_node_ids():
                # This is a node we're going to add to way 1
                node = self.nodes.get(nid)
                # Associate the node with way 1 and disassociate it with way 2

                node.append_way(way_id_1)
                node.remove_way_id(way_id_2)
            # Remove way 2
            self.remove_way(way_id_2)
            # self.ways.remove(way_id_2)
        except KeyError:
            log.exception("Join failed, skipping...")
            raise

    def swap_nodes(self, node_from, node_to):
        """
        Swap the node in all the ways

        :param nid_from:
        :param nid_to:
        :return:
        """
        # node = self.nodes.get(nid_from)
        if type(node_from) == StringType and type(node_to) == StringType:
            node_from = self.get_node(node_from)
            node_to = self.get_node(node_to)

        if node_from and node_from.way_ids:
            for way_id in node_from.way_ids:
                way = self.get_way(way_id)
                way.swap_nodes(node_from, node_to)
                # self.ways.get(way_id).swap_nodes(nid_from, nid_to)
            # self.nodes.remove(nid_from)
            self.remove_node(node_from.id)
        return

    def vector(self, nid_from, nid_to, normalize=False):
        """
        Get a vector from one node to another

        :param nid_from: A source node id
        :param nid_to: A target node id
        :return: A vector (2D np.array)
        """
        node_from = self.get_node(nid_from)
        node_to = self.get_node(nid_to)
        return node_from.vector_to(node_to, normalize)


class OSM(Network):
    @staticmethod
    def create_network(type="street-network", bounding_box=None):
        """
        Create a network

        :param type: Network type
        :param bounding_box: A bounding box
        :return: A Network object
        """
        nodes = Nodes()

        if type == "street-network":
            ways = Streets()
        else:
            ways = Ways()
        return OSM(nodes, ways, bounding_box)

    def __init__(self, nodes, ways, bounds):
        # self.nodes = nodes
        # self.ways = ways
        super(OSM, self).__init__(nodes, ways)

        if bounds:
            self.bounds = bounds

    def clean(self):
        """
        Clean up dangling nodes that are not connected to any ways
        :return:
        """
        self.nodes.clean()

    def clean_street_segmentation(self):
        """
        Go through nodes and find ones that have two connected ways
        (nodes should have either one or more than two ways)
        """
        for node in self.nodes.get_list():
            try:
                if len(node.get_way_ids()) == 2:
                    way_id_1, way_id_2 = node.get_way_ids()
                    way_1 = self.get_way(way_id_1)
                    way_2 = self.get_way(way_id_2)

                    # Given that the streets are split, node's index in each way's nids (a list of node ids) should
                    # either be 0 or else.
                    if way_1.nids.index(node.id) == 0 and way_2.nids.index(node.id) == 0:
                        combined_nids = way_1.nids[:0:-1] + way_2.nids
                    elif way_1.nids.index(node.id) != 0 and way_2.nids.index(node.id) == 0:
                        combined_nids = way_1.nids[:-1] + way_2.nids
                    elif way_1.nids.index(node.id) == 0 and way_2.nids.index(node.id) != 0:
                        combined_nids = way_2.nids[:-1] + way_1.nids
                    else:
                        combined_nids = way_1.nids + way_2.nids[1::-1]

                    # Create a new way from way_1 and way_2. Then remove the two ways from self.way
                    new_street = self.create_street(None, combined_nids)
                    new_street.add_original_way(way_1)
                    new_street.add_original_way(way_2)
                    self.remove_way(way_id_1)
                    self.remove_way(way_id_2)
            except Exception as e:
                log.exception("Something went wrong while cleaning street segmentation, so skipping...")
                raise

    def export(self, format="geojson"):
        """
        Export the node and way data.
        Todo: Implement geojson format for export.
        """
        if format == 'osm':
            header = """
<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
<bounds minlat="%s" minlon="%s" maxlat="%s" maxlon="%s" />
""" % (str(self.bounds[0]), str(self.bounds[1]), str(self.bounds[2]), str(self.bounds[3]))

            footer = "</osm>"
            node_list = []
            for node in self.nodes.get_list():
                lat, lng = node.latlng.location(radian=False)
                node_str = """<node id="%s" visible="true" user="test" lat="%s" lon="%s" />""" % (str(node.id), str(lat), str(lng))
                node_list.append(node_str)

            way_list = []
            for way in self.ways.get_list():
                way_str = """<way id="%s" visible="true" user="test">""" % (str(way.id))
                way_list.append(way_str)
                for nid in way.get_node_ids():
                    nid_str = """<nd ref="%s" />""" % (str(nid))
                    way_list.append(nid_str)

                if way.type is not None:
                    tag = """<tag k="%s" v="%s" />""" % ("highway", way.type)
                    if way.type == "footway":
                        # How to tag sidewalks in OpenStreetMap
                        # https://help.openstreetmap.org/questions/1236/should-i-map-sidewalks
                        # http://wiki.openstreetmap.org/wiki/Tag:footway%3Dsidewalk
                        tag = """<tag k="%s" v="%s" />""" % ("footway", "sidewalk")
                    way_list.append(tag)
                way_list.append("</way>")

            osm = header + "\n".join(node_list) + "\n" + "\n".join(way_list) + "\n" + footer

            return osm
        else:
            # Mapbox GeoJson format
            # https://github.com/mapbox/simplestyle-spec/tree/master/1.1.0
            geojson = {}
            geojson['type'] = "FeatureCollection"
            geojson['features'] = []

            # Add ways
            for way in self.get_ways():
                feature = way.get_geojson_features()
                geojson['features'].append(feature)

            # Add nodes
            for node in self.get_nodes():
                feature = node.get_geojson_features()
                geojson['features'].append(feature)
            return json.dumps(geojson)

    def find_parallel_street_segments(self):
        """
        This method finds parallel segments and returns a list of pair of way ids
        :return: A list of pair of parallel way ids
        """
        streets = self.ways.get_list()
        street_polygons = []
        # Threshold for merging - increasing this will merge parallel ways that are further apart.
        distance_to_sidewalk = 0.00003

        for street in streets:
            start_node_id = street.get_node_ids()[0]
            end_node_id = street.get_node_ids()[-1]
            start_node = self.nodes.get(start_node_id)
            end_node = self.nodes.get(end_node_id)

            vector = start_node.vector_to(end_node, normalize=True)
            perpendicular = np.array([vector[1], - vector[0]]) * distance_to_sidewalk
            p1 = start_node.vector() + perpendicular
            p2 = end_node.vector() + perpendicular
            p3 = end_node.vector() - perpendicular
            p4 = start_node.vector() - perpendicular

            poly = Polygon([p1, p2, p3, p4])
            poly.angle = math.degrees(math.atan2(vector[0], vector[1]))
            poly.nids = [start_node_id, end_node_id]
            street_polygons.append(poly)

        # Find pair of polygons that intersect each other.
        polygon_combinations = combinations(street_polygons, 2)
        # Create a list for storing parallel pairs
        parallel_pairs = []
        # All possible pairs are stored for debugging purposes
        for pair_poly in polygon_combinations:
            # pair_poly[0] and pair_poly[1] are polygons
            # Add the pair to the list of all possible pairs for debug, but limit size to 50
            # Get node id of street being checked
            # street1 = streets[street_polygons.index(pair_poly[0])]
            # street2 = streets[street_polygons.index(pair_poly[1])]
            angle_diff = ((pair_poly[0].angle - pair_poly[1].angle) + 360.) % 180.
            if pair_poly[0].intersects(pair_poly[1]) and (angle_diff < 10. or angle_diff > 170.):
                # If the polygon intersects, and they have a kind of similar angle, and they don't share a node,
                # then they should be merged together.
                parallel_pairs.append((street_polygons.index(pair_poly[0]), street_polygons.index(pair_poly[1])))
        filtered_parallel_pairs = []

        # Filter parallel_pairs and store in filtered_parallel_pairs
        for pair in parallel_pairs:
            street_pair = (streets[pair[0]], streets[pair[1]])
            # street1 = streets[pair[0]]
            # street2 = streets[pair[1]]
            shared_nids = set(street_pair[0].nids) & set(street_pair[1].nids)

            # Find the adjacent nodes for the shared node
            if len(shared_nids) > 0:
                # Two paths merges at one node
                shared_nid = list(shared_nids)[0]
                shared_node = self.nodes.get(shared_nid)
                idx1 = street_pair[0].nids.index(shared_nid)
                idx2 = street_pair[1].nids.index(shared_nid)

                # Nodes are sorted by longitude (x-axis), so two paths should merge at the left-most node or the
                # right most node.
                if idx1 == 0 and idx2 == 0:
                    # The case where shared node is at the left-end
                    adj_nid1 = street_pair[0].nids[1]
                    adj_nid2 = street_pair[1].nids[1]
                else:
                    # The case where sahred node is at the right-end
                    adj_nid1 = street_pair[0].nids[-2]
                    adj_nid2 = street_pair[1].nids[-2]

                adj_node1 = self.nodes.get(adj_nid1)
                adj_node2 = self.nodes.get(adj_nid2)
                angle_to_node1 = math.degrees(shared_node.angle_to(adj_node1))
                angle_to_node2 = math.degrees(shared_node.angle_to(adj_node2))
                if abs(abs(angle_to_node1)-abs(angle_to_node2)) > 90:
                    # Paths are connected but they are not parallel lines
                    continue
                if(pair[0] == pair[1]):
                    # Don't merge two ways that are the same
                    continue
            filtered_parallel_pairs.append(pair)
        return [(streets[pair[0]].id, streets[pair[1]].id) for pair in filtered_parallel_pairs]

    def get_distance(self, way):
        """ Get a distance of the passed way

        :param way: A way object
        :return: A distance in meters
        """
        node1 = self.get_node(way.nids[0])
        node2 = self.get_node(way.nids[-1])
        try:
            assert node1 is not None
            assert node2 is not None
            distance = node1.distance_to(node2)
        except AssertionError:
            log.debug("Network.get_distance(): Debug")
        return distance

    def join_connected_ways(self, segments_to_merge):
        """
        This methods searches through the pairs of way ids that need to be merged, and checks to see if there
        are any ways that appear in multiple pairs. A way that appears in multiple pairs is likely a long
        way that needs to be merged with several short ways that run alongside it. The merge method will fail
        in this case, so as a workaround this method will join the short ways together into a single way to
        allow the merge method to work properly.

        :param segments_to_merge: List of pairs of ways that need to be merged. This likely comes from
        find_parallel_pairs().
        :return: A new list of pairs of ways to merge. Note: A new list is necessary because once ways are joined,
        some of the way IDs in the original list will no longer be valid.
        """

        # This list will contain the first way in each pair
        ways_to_merge_1 = []
        # This list will contain the second way in each pair
        ways_to_merge_2 = []
        # Add the ways IDs to the above lists
        for pair in segments_to_merge:
            ways_to_merge_1.append(int(pair[0]))  # KH: Way id?
            ways_to_merge_2.append(int(pair[1]))
            # See if ways share a node
        # Combine the two above lists
        all_ways_to_merge = ways_to_merge_1 + ways_to_merge_2
        # Using the combined list, create a set of ways that appear multiple times. These are the
        # long ways for which multiple short ways need to be merged into.
        ways_appearing_multiple_times = set([x for x in all_ways_to_merge if all_ways_to_merge.count(x) > 1])
        # Once ways are joined, some way IDs will no longer exist. We need to keep track of which way IDs have
        # been removed.
        removed_ways = []

        # For each long way, get the IDs of all the short ways that need to be merged with the long way
        for way in ways_appearing_multiple_times:
            # Store the IDs of the short ways in a list
            short_ways_to_join = []
            # Search for the ID of the long way in the two list 1, and store the associated short way (from list 2)
            # in short_ways_to_join
            for i, j in enumerate(ways_to_merge_1):
                if j == way:
                    short_ways_to_join.append(ways_to_merge_2[i])
            # Repeat the other way around, for cases where the ID of the long way is in list 2 and the ID of the
            # short way is in list 1.
            for i, j in enumerate(ways_to_merge_2):
                if j == way:
                    short_ways_to_join.append(ways_to_merge_1[i])
            # Go through the list of short ways that need to be joined and join them in pairs.
            for short_way in short_ways_to_join:
                # Don't join the first way with the first way
                if short_way != short_ways_to_join[0]:
                    # Make sure we only join ways that are going in the same direction
                    try:
                        way1 = self.ways.get(str(short_ways_to_join[0]))
                        way2 = self.ways.get(str(short_way))

                        if way1 is None or way2 is None:
                            continue

                        if way1.getdirection() == way2.getdirection():
                            self.join_ways(str(short_ways_to_join[0]), str(short_way))
                            # Keep track of way IDs that are no longer valid
                            removed_ways.append(short_way)
                    except KeyError:
                        log.exception("This should no longer happen")
                        raise
                    except AttributeError:
                        log.exception("way 1 or way 2 is None")
                        assert way1 is None or way2 is None  # Due to prior deletion
                        raise
        # Build new list of pairs to merge, excluding pairs with IDs that are no longer valid

        new_segments_to_merge = []
        for pair in segments_to_merge:
            # If the pair contains an ID that is no longer valid, don't add it to the new list of pairs.
            if int(pair[0]) in removed_ways or int(pair[1]) in removed_ways:
                pass
            else:
                new_segments_to_merge.append(pair)
        return new_segments_to_merge

    def merge_nodes(self, distance_threshold=15):
        """
        Remove nodes that are close to intersection nodes. Then merge nodes that are
        close to each other.
        """
        for street in self.get_ways():
            # if len(street.nids) < 2:
            if len(street.get_node_ids()) <= 2:
                # Skip. You should not merge two intersection nodes
                continue

            start = self.get_node(street.nids[0])
            end = self.get_node(street.nids[-1])

            # Merge the nodes around the beginning of the street
            for nid in street.get_node_ids()[1:-1]:
                target = self.get_node(nid)
                distance = start.distance_to(target)
                if distance < distance_threshold:
                    self.remove_node(nid)
                else:
                    break

            if len(street.get_node_ids()) <= 2:
                # Continue if you merged everything other than intersection nodes
                continue

            # merge the nodes that are around the end of the street
            for nid in street.get_node_ids()[-2:0:-1]:
                target = self.get_node(nid)
                distance = end.distance_to(target)
                if distance < distance_threshold:
                    self.remove_node(nid)
                else:
                    break

            # Merge nodes in between if necessary...
            while True:
                nids = street.get_node_ids()[1:-1]
                do_break = True
                for nid1, nid2 in window(nids, 2):
                    node1 = self.get_node(nid1)
                    node2 = self.get_node(nid2)
                    if node1.distance_to(node2) < distance_threshold:
                        new_node = self.create_node(None, (node1.lat + node2.lat) / 2, (node1.lng + node2.lng) / 2)

                        way_ids = node1.get_way_ids() + node2.get_way_ids()
                        new_node.append_ways(way_ids)

                        idx = street.nids.index(node1.id)
                        street.insert_node(idx, new_node.id)
                        try:
                            street.remove_node(node1)
                            street.remove_node(node2)
                        except AttributeError:
                            print street
                            raise
                        do_break = False
                        break
                if do_break:
                    break

    def merge_parallel_street_segments(self, parallel_pairs):
        """
        Note: Maybe I don't even have to merge any path (which breaks the original street network data structure.
        Instead, I can mark ways that have parallel neighbors not make sidewalks on both sides...

        :param parallel_pairs: pairs of street_ids.
        Todo: This method needs to be optimized using some spatial data structure (e.g., r*-tree) and other metadata..
        # Expand streets into rectangles, then find intersections between them.
        # http://gis.stackexchange.com/questions/90055/how-to-find-if-two-polygons-intersect-in-python
        """
        streets_to_remove = []

        # Merge parallel pairs
        for pair in parallel_pairs:
            #####
            try:
                street_pair = (self.ways.get(pair[0]), self.ways.get(pair[1]))

                # First find parts of the street pairs that you want to merge (you don't want to merge entire streets
                # because, for example, one could be much longer than the other and it doesn't make sense to merge
                # subset_nids is the overlapping segment
                subset_nids, street1_segment, street2_segment = self.segment_parallel_streets((street_pair[0], street_pair[1]))

                # If there is no overlapping segment, skip this merge
                if not subset_nids:
                    continue

                # Get two parallel segments and the distance between them
                try:
                    street1_node = self.nodes.get(street1_segment[1][0])
                    street2_node = self.nodes.get(street2_segment[1][0])
                except IndexError:
                    log.exception("Warning! Segment to merge was empty for one or both streets, so skipping this merge...")
                    continue
                street1_end_node = self.nodes.get(street1_segment[1][-1])
                street2_end_node = self.nodes.get(street2_segment[1][-1])

                LS_street1 = LineString((street1_node.location(), street1_end_node.location()))
                LS_street2 = LineString((street2_node.location(), street2_end_node.location()))
                distance = LS_street1.distance(LS_street2) / 2

                # Merge streets
                node_to = {}
                new_street_nids = []
                street1_idx = 0
                street2_idx = 0
                # First node of middle segment
                street1_nid = street1_segment[1][0]  # First node of the middle segment of street 1
                street2_nid = street2_segment[1][0]  # First node of the middle segment of street 2
                for nid in subset_nids:
                    try:
                        if nid == street1_nid:
                            street1_idx += 1
                            street1_nid = street1_segment[1][street1_idx]

                            node = self.nodes.get(nid)
                            opposite_node_1 = self.nodes.get(street2_nid)
                            opposite_node_2_nid = street2_segment[1][street2_idx + 1]
                            opposite_node_2 = self.nodes.get(opposite_node_2_nid)

                        else:
                            street2_idx += 1
                            street2_nid = self.ways.get(pair[1]).nids[street2_idx]

                            node = self.nodes.get(nid)
                            opposite_node_1 = self.nodes.get(street1_nid)
                            opposite_node_2_nid = street1_segment[1][street1_idx + 1]
                            opposite_node_2 = self.nodes.get(opposite_node_2_nid)

                        v = opposite_node_1.vector_to(opposite_node_2, normalize=True)
                        v2 = opposite_node_1.vector_to(node, normalize=True)
                        if np.cross(v, v2) > 0:
                            normal = np.array([v[1], v[0]])
                        else:
                            normal = np.array([- v[1], v[0]])
                        new_position = node.location() + normal * distance

                        new_node = self.create_node(None, new_position[0], new_position[1])
                        new_street_nids.append(new_node.id)
                    except IndexError:
                        # Take care of the last node.
                        # Use the previous perpendicular vector but reverse the direction
                        node = self.nodes.get(nid)
                        new_position = node.location() - normal * distance
                        # new_node = Node(None, new_position[0], new_position[1])
                        # self.add_node(new_node)

                        new_node = self.create_node(None, new_position[0], new_position[1])
                        new_street_nids.append(new_node.id)

                # log.debug(pair)
                # node_to[subset_nids[0]] = new_street_nids[0]
                # node_to[subset_nids[-1]] = new_street_nids[-1]

                merged_street = self.create_street(None, new_street_nids)
                merged_street.distance_to_sidewalk *= 2

                # self.simplify(merged_street.id, 0.1)
                streets_to_remove.append(street_pair[0].id)
                streets_to_remove.append(street_pair[1].id)

                # Create streets from the unmerged nodes.
                # Todo for KH: I think this part of the code can be prettier
                # if street1_segment[0] or street2_segment[0]:
                #     if street1_segment[0] and street2_segment[0]:
                #         if street1_segment[0][0] == street2_segment[0][0]:
                #             # The two segments street1 and street2 share a common node. Just connect one of them to the
                #             # new merged street.
                #             if subset_nids[0] in street1_segment[1]:
                #                 street1_segment[0][-1] = node_to[street1_segment[0][-1]]
                #                 self.create_street(None, street1_segment[0])
                #             else:
                #                 street2_segment[0][-1] = node_to[street2_segment[0][-1]]
                #                 self.create_street(None, street2_segment[0])
                #         else:
                #             # Both street1_segment and street2_segment exist, but they do not share a common node
                #             street1_segment[0][-1] = node_to[street1_segment[0][-1]]
                #             street2_segment[0][-1] = node_to[street2_segment[0][-1]]
                #             try:
                #                 self.create_street(None, street1_segment[0])
                #                 self.create_street(None, street2_segment[0])
                #             except KeyError:
                #                 print("Debug")
                #
                #     elif street1_segment[0]:
                #         # Only street1_segment exists
                #         try:
                #
                #             street1_segment[0][-1] = node_to[street1_segment[0][-1]]
                #         except KeyError:
                #             print "Debug"
                #         self.create_street(None, street1_segment[0])
                #     else:
                #         # Only street2_segment exists
                #         try:
                #             street2_segment[0][-1] = node_to[street2_segment[0][-1]]
                #             # Todo: Bug: Sometimes the node_to dictionary does not contain street2_segment[0][-1] causing error. Use the wilson.osm
                #             self.create_street(None, street2_segment[0])
                #         except KeyError:
                #             print("Debug")

        #         if street1_segment[2] or street2_segment[2]:
        #             if street1_segment[2] and street2_segment[2]:
        #                 if street1_segment[2][-1] == street2_segment[2][-1]:
        #                     # The two segments street1 and street2 share a common node. Just connect one of them to the
        #                     # new merged street.
        #                     if subset_nids[-1] in street1_segment[1]:
        #                         street1_segment[2][0] = node_to[subset_nids[-1]]
        #                         self.create_street(None, street1_segment[2])
        #                     else:
        #                         street2_segment[2][0] = node_to[subset_nids[-1]]
        #                         self.create_street(None, street2_segment[2])
        #                 else:
        #                     # Both street1_segment and street2_segment exist, but they do not share a common node
        #                     street1_segment[2][0] = node_to[subset_nids[-1]]
        #                     street2_segment[2][0] = node_to[subset_nids[-1]]
        #                     self.create_street(None, street1_segment[2])
        #                     self.create_street(None, street2_segment[2])
        #             elif street1_segment[2]:
        #                 # Only street1_segment exists
        #                 street1_segment[2][0] = node_to[subset_nids[-1]]
        #                 self.create_street(None, street1_segment[2])
        #             else:
        #                 # Only street2_segment exists
        #                 street2_segment[2][0] = node_to[subset_nids[-1]]
        #                 self.create_street(None, street2_segment[2])
        #
            except Exception as e:
                log.exception("Something went wrong while merging street segment, so skipping...")
                continue
            ######
        # for street_id in set(streets_to_remove):
        #     for nid in self.ways.get(street_id).nids:
        #         node = self.nodes.get(nid)
        #         for parent in node.way_ids:
        #             if not parent in streets_to_remove:
        #                 # FIXME Add the node to the way we're about to add
        #                 pass
        #     self.remove_way(street_id)
        return

    def merge_parallel_street_segments2(self):
        ways_to_remove = []
        streets = self.ways.get_list()
        street_combinations = combinations(streets, 2)

        segments_to_merge = []
        for street1, street2 in street_combinations:
            if self.parallel(street1, street2) and not street1.on_same_street(street2):
                street1.merge(street2)
                segments_to_merge.append((street1.id, street2.id))
                ways_to_remove.append(street1.id)
                ways_to_remove.append(street2.id)

        for way_id in set(ways_to_remove):
            self.remove_way(way_id)
            self.join_connected_ways(segments_to_merge)

    def merge_parallel_street_segments3(self, threshold=0.5):
        """
        My freaking third attempt to merge parallel segemnts.
        :param threshold:
        :return:
        """
        log.debug("Start merging the streets.")
        streets = self.get_ways()
        while True:
            streets = sorted(streets, key=lambda x: self.get_node(x.nids[0]).lat)
            do_break = True
            for street1 in streets:
                overlap_list = []  # store tuples of (index, area_overlap pair)
                for street2 in streets:
                    if street1 == street2 or set(street1.nids) == set(street2.nids):
                        continue

                    # If street1 and street2 overlaps, calculate the overlap value (divided by poly area)
                    # and store it into overlap list
                    if self.parallel(street1, street2) and not street1.on_same_street(street2):
                        street1_nodes = street1.get_nodes()
                        street2_nodes = street2.get_nodes()
                        node1_1, node1_2 = street1_nodes[0], street1_nodes[-1]
                        node2_1, node2_2 = street2_nodes[0], street2_nodes[-1]
                        poly1 = self.nodes.create_polygon(node1_1, node1_2)
                        poly2 = self.nodes.create_polygon(node2_1, node2_2)
                        area_intersection = poly1.intersection(poly2).area
                        my_area = max(area_intersection / poly1.area, area_intersection / poly2.area)
                        overlap_list.append((my_area, street2))

                # Merge the streets that have the largest overlap (that has overlap over 0.5)
                # and remove unnecessary streets
                overlap_list.sort(key=lambda x: - x[0])
                if overlap_list and overlap_list[0][0] > threshold:
                    street2 = overlap_list[0][1]
                    merged_nodes_list = self.merge_streets(street1, street2)

                    # Add the new nodes into this network
                    flattened = []
                    for nodes in merged_nodes_list:
                        flattened += nodes
                    flattened = list(set(flattened))
                    self.add_nodes(flattened)

                    # Create streets from the new nodes
                    new_streets = []
                    for nodes in merged_nodes_list:
                        new_node_ids = [node.id for node in nodes]
                        new_street = self.create_street(None, new_node_ids)
                        new_street.add_original_ways(street1.get_original_ways())
                        new_street.add_original_ways(street2.get_original_ways())
                        new_streets.append(new_street)

                    streets.remove(street1)
                    streets.remove(street2)

                    self.remove_way(street1.id)
                    self.remove_way(street2.id)
                    for new_street in new_streets:
                        streets.append(new_street)

                    do_break = False
            if do_break:
                break

    def merge_streets(self, street1, street2):
        """
        Merge two streets. You should pass two parallel segments.

        :param street1: A Street object
        :param street2: Anotehr Street object
        :return: A list of lists of nodes
        """
        # Create a base vector that defines the direction of a parallel line
        nodes1 = [self.get_node(nid) for nid in street1.get_node_ids()]
        nodes2 = [self.get_node(nid) for nid in street2.get_node_ids()]
        v1 = nodes1[0].vector_to(nodes1[-1], normalize=True)
        v2 = nodes2[0].vector_to(nodes2[-1], normalize=True)

        if np.dot(v1, v2) < 0:
            v2 = - v2
        base_vector = v1 + v2
        base_vector /= np.linalg.norm(base_vector)

        # Create a node that serves as an origin. First take an average coordinate of nodes in each ways.
        # Then take average of the two average coordinates that I've just calculated.
        lat_origin1, lng_origin1, lat_origin2, lng_origin2 = 0, 0, 0, 0
        for node in nodes1:
            lat_origin1 += node.lat
            lng_origin1 += node.lng
        lat_origin1 /= len(nodes1)
        lng_origin1 /= len(nodes1)
        for node in nodes2:
            lat_origin2 += node.lat
            lng_origin2 += node.lng
        lat_origin2 /= len(nodes2)
        lng_origin2 /= len(nodes2)

        lat_origin, lng_origin = (lat_origin1 + lat_origin2) / 2, (lng_origin1 + lng_origin2) / 2
        origin = Node(None, lat_origin, lng_origin)

        # Merge two ways. It will find a segment between the two segments that are passed to this method.
        # Segment the merged nodes into couple of lists of nodes.
        new_nodes = []
        for node in set(nodes1 + nodes2):
            vec = origin.vector_to(node)
            d = np.dot(base_vector, vec)
            lat_new, lng_new = origin.vector() + d * base_vector
            node_new = self.create_node(node.id, lat_new, lng_new)
            # node_new = Node(node.id, lat_new, lng_new)
            node_new.made_from.append(node)
            node_new.append_ways(node.get_way_ids())
            new_nodes.append(node_new)

        def cmp_with_projection(n1, n2):
            dot_product1 = np.dot(n1.vector(), base_vector)
            dot_product2 = np.dot(n2.vector(), base_vector)
            if dot_product1 < dot_product2:
                return -1
            elif dot_product2 < dot_product1:
                return 1
            else:
                return 0

        new_nodes = sorted(new_nodes, cmp=cmp_with_projection)
        new_nids = [node.id for node in new_nodes]
        indices = [new_nids.index(nid) for nid in [street1.nids[0], street1.nids[-1], street2.nids[0], street2.nids[-1]]]
        indices = sorted(list(set(indices)))

        # Segmenting nodes into couple of sets
        ret = []
        if len(indices) == 4:
            ret.append(new_nodes[:indices[1] + 1])
            ret.append(new_nodes[indices[1]:indices[2] + 1])
            ret.append(new_nodes[indices[2]:])
        elif len(indices) == 3:
            ret.append(new_nodes[:indices[1] + 1])
            ret.append(new_nodes[indices[1]:])
        else:
            assert len(indices) == 2
            ret.append(new_nodes)

        return ret

    def parallel(self, way1, way2, threshold=10.):
        """
        Checks if two ways are parallel to each other
        :param way1:
        :param way2:
        :return:
        """
        if type(way1) == StringType:
            way1 = self.get_way(way1)
            way2 = self.get_way(way2)

        node1_1 = self.get_node(way1.nids[0])
        node1_2 = self.get_node(way1.nids[-1])
        node2_1 = self.get_node(way2.nids[0])
        node2_2 = self.get_node(way2.nids[-1])

        if node1_1 is None or node1_2 is None or node2_1 is None or node2_2 is None:
            return False

        # Check if the way is cyclic
        if node1_1 == node1_2:
            node1_2 = self.get_node(way1.nids[-2])
        elif node2_1 == node2_2:
            node2_2 = self.get_node(way2.nids[-2])

        # Not sure why this happens... I'll need to check. Todo
        if node1_1 == node1_2:
            return False
        if node2_1 == node2_2:
            return False
        assert node1_1 != node1_2
        assert node2_1 != node2_2
        # Create polygons and get angles of ways
        poly1 = self.nodes.create_polygon(node1_1, node1_2)
        poly2 = self.nodes.create_polygon(node2_1, node2_2)

        angle1 = way1.angle()
        angle2 = way2.angle()
        angle_diff = (angle1 - angle2 + 360) % 360
        angle_diff = min(angle_diff, 360 - angle_diff)
        is_parallel = angle_diff < threshold or angle_diff > 180 - threshold
        try:
            does_intersect = poly1.intersects(poly2)
        except ValueError:
            raise
        return is_parallel and does_intersect

    def preprocess(self):
        """
        Preprocess and clean up the data

        """
        # print("Finding parallel street segments" + str(datetime.now()))
        # # parallel_segments = self.find_parallel_street_segments()
        # print("Finished finding parallel street segments" + str(datetime.now()))
        # # parallel_segments_filtered = self.join_connected_ways(parallel_segments)
        # print("Begin merging parallel street segments" + str(datetime.now()))
        # self.merge_parallel_street_segments(parallel_segments_filtered)

        self.split_streets()
        self.update_node_cardinality()
        self.merge_nodes()
        self.clean_street_segmentation()
        self.merge_parallel_street_segments3()

        # Clean up
        self.remove_short_segments()  # remove short segments
        self.merge_nodes()

        for node in self.get_nodes():
            node.way_ids = []
        for way in self.ways.get_list():
            if len(way.nids) < 2:
                self.remove_way(way.id)
            else:
                for nid in way.get_node_ids():
                    node = self.get_node(nid)
                    node.append_way(way.id)
        self.nodes.clean()  # Remove nodes that are not connected to anything.
        self.clean_street_segmentation()

    def remove_short_segments(self, distance_threshold=15):
        """
        Remove very short segments that have length below the passed threshold. This method assumes that there are no
        intersection nodes except for the two nodes at the both ends.

        :param distance_threshold: A ditance threshold in meters.
        """
        for way in self.get_ways():
            d = self.get_distance(way)

            if d < distance_threshold:
                node1 = self.get_node(way.nids[0])
                node2 = self.get_node(way.nids[-1])
                new_node = self.create_node(None, (node1.lat + node2.lat) / 2, (node1.lng + node2.lng) / 2)
                assert new_node.id in self.nodes.nodes

                # Go through all the ways that are connected to node1 (and node 2), then switch node1's nid with
                # the new node's nid.
                way_ids = set(node1.get_way_ids() + node2.get_way_ids())
                for way_id in way_ids:
                    if way_id != way.id:
                        temp_way = self.get_way(way_id)
                        if not temp_way:
                            continue

                        try:
                            # two nodes that I'm deleting are in this way as well. Not sure why this happens
                            assert (node1.id in temp_way.nids) != (node2.id in temp_way.nids)
                        except AssertionError:
                            # log.debug("Debug")
                            pass

                        if node1.id in temp_way.nids:
                            temp_way.swap_nodes(node1.id, new_node.id)
                        if node2.id in temp_way.nids:
                            temp_way.swap_nodes(node2.id, new_node.id)
                        new_node.append_way(way_id)

                node1.remove_way_id(way.id)
                node2.remove_way_id(way.id)
                self.remove_way(way.id)

    def segment_parallel_streets(self, street_pair):
        """
        First find parts of the street pairs that you want to merge (you don't want to merge entire streets
        because, for example, one could be much longer than the other and it doesn't make sense to merge
        :param street_pair: A pair of street ids or street objects
        :return: A set of three lists; overlapping_segment, street1_segmentation, street2_segmentation
        """

        if type(street_pair[0]) == StringType:
            street_pair = [self.get_way(street_pair[0]), self.get_way(street_pair[1])]

        # Take the two points from street_pair[0], and use it as a base vector.
        # Project all the points along the base vector and sort them.
        base_node0 = self.nodes.get(street_pair[0].nids[0])
        base_node1 = self.nodes.get(street_pair[0].nids[-1])
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

        # check if the nodes in the second street is in the right order
        street_2_nodes = [self.nodes.get(nid) for nid in street_pair[1].nids]
        sorted_street2_nodes = sorted(street_2_nodes, cmp=cmp_with_projection)
        if street_2_nodes[0].id != sorted_street2_nodes[0].id:
            street_pair[1].nids = list(reversed(street_pair[1].nids))

        # Get all the nodes in both streets and store them in a list
        all_nodes = [self.nodes.get(nid) for nid in street_pair[0].nids] + [self.nodes.get(nid) for nid in street_pair[1].nids]
        # Sort the nodes in the list by longitude
        all_nodes = sorted(all_nodes, cmp=cmp_with_projection)
        # Store the node IDs in another list
        all_nids = [node.id for node in all_nodes]

        # Condition in list comprehension
        # http://stackoverflow.com/questions/4260280/python-if-else-in-list-comprehension
        all_nids_street_indices = [0 if nid in street_pair[0].nids else 1 for nid in all_nids]

        # Return if they are not actually parallel


        all_nids_street_switch = [idx_pair[0] != idx_pair[1] for idx_pair in window(all_nids_street_indices, 2)]

        if all_nids[0] == all_nids[1]:
            # The case where the first node of each segments are same

            # Find the first occurrence of True in the list
            end_idx = len(all_nids_street_switch) - 1 - all_nids_street_switch[::-1].index(True)
            # end_idx = all_nids_street_switch.index(True)
            overlapping_segment = all_nids[1:end_idx + 1]

            street1_nid = all_nids[end_idx]
            if street1_nid in street_pair[0].nids:
                # A node from street1 comes first

                street2_nid = all_nids[end_idx + 1]
                street1_nid_idx = street_pair[0].nids.index(street1_nid)
                street2_nid_idx = street_pair[1].nids.index(street2_nid)

                street2_node2_nid = street_pair[1].nids[street2_nid_idx - 1]
                street2_node2 = self.get_node(street2_node2_nid)
                street2_node1 = self.get_node(street2_nid)
                street1_node = self.get_node(street1_nid)
                line = points_to_line((street2_node1.lng, street2_node1.lat), (street2_node2.lng, street2_node2.lat))
                foot_lng, foot_lat = foot(street1_node.lng, street1_node.lat, line[0], line[1], line[2])
                foot_node = self.create_node(None, foot_lat, foot_lng)
                street_pair[1].insert_node(street2_nid_idx, foot_node.id)
            else:
                # A node from street2 comes first
                street1_nid = all_nids[end_idx + 1]
                street2_nid = all_nids[end_idx]
                street1_nid_idx = street_pair[0].nids.index(street1_nid)
                street2_nid_idx = street_pair[1].nids.index(street2_nid)

                street1_node2_nid = street_pair[0].nids[street1_nid_idx - 1]
                street1_node2 = self.get_node(street1_node2_nid)
                street1_node1 = self.get_node(street1_nid)
                street2_node = self.get_node(street2_nid)
                line = points_to_line((street1_node1.lng, street1_node1.lat), (street1_node2.lng, street1_node2.lat))
                foot_lng, foot_lat = foot(street2_node.lng, street2_node.lat, line[0], line[1], line[2])
                foot_node = self.create_node(None, foot_lat, foot_lng)
                street_pair[0].insert_node(street1_nid_idx, foot_node.id)

            overlapping_segment.append(foot_node.id)
            street1_segmentation = [[],
                                    street_pair[0].nids[:street1_nid_idx + 1],
                                    street_pair[0].nids[street1_nid_idx + 1:]]
            # Street 2 is also divided into three segments - beginning segment, overlapping segment, and end segment
            street2_segmentation = [[],
                                    street_pair[1].nids[:street2_nid_idx + 1],
                                    street_pair[1].nids[street2_nid_idx + 1:]]

            if len(street1_segmentation[2]) > 0:
                street1_segmentation[2].insert(0, street1_segmentation[1][-1])
            if len(street2_segmentation[2]) > 0:
                street2_segmentation[2].insert(0, street2_segmentation[1][-1])
            return overlapping_segment, street1_segmentation, street2_segmentation
        elif all_nids[-1] == all_nids[-2]:
            # The case where the last node of each segments are same
            # Find the first occurrence of True in the list
            begin_idx = all_nids_street_switch.index(True)

            # end_idx = all_nids_street_switch.index(True)
            overlapping_segment = all_nids[begin_idx + 1:-1]

            street1_nid = all_nids[begin_idx]
            if street1_nid in street_pair[0].nids:
                # A node from street1 comes first

                street2_nid = all_nids[begin_idx + 1]
                street1_nid_idx = street_pair[0].nids.index(street1_nid)
                street2_nid_idx = street_pair[1].nids.index(street2_nid)

                street1_node2_nid = street_pair[0].nids[street1_nid_idx - 1]
                street1_node2 = self.get_node(street1_node2_nid)
                street1_node1 = self.get_node(street1_nid)
                street2_node = self.get_node(street2_nid)
                line = points_to_line((street1_node1.lng, street1_node1.lat), (street1_node2.lng, street1_node2.lat))
                foot_lng, foot_lat = foot(street2_node.lng, street2_node.lat, line[0], line[1], line[2])
                foot_node = self.create_node(None, foot_lat, foot_lng)
                street_pair[0].insert_node(street1_nid_idx + 1, foot_node.id)

                street1_nid_idx += 1
            else:
                # A node from street2 comes first
                street1_nid = all_nids[begin_idx + 1]
                street2_nid = all_nids[begin_idx]
                street1_nid_idx = street_pair[0].nids.index(street1_nid)
                street2_nid_idx = street_pair[1].nids.index(street2_nid)

                street2_node2_nid = street_pair[1].nids[street2_nid_idx - 1]
                street2_node2 = self.get_node(street2_node2_nid)
                street2_node1 = self.get_node(street2_nid)
                street1_node = self.get_node(street1_nid)
                line = points_to_line((street2_node1.lng, street2_node1.lat), (street2_node2.lng, street2_node2.lat))
                foot_lng, foot_lat = foot(street1_node.lng, street1_node.lat, line[0], line[1], line[2])
                foot_node = self.create_node(None, foot_lat, foot_lng)
                street_pair[1].insert_node(street2_nid_idx + 1, foot_node.id)
                street2_nid_idx += 1

            overlapping_segment.insert(0, foot_node.id)

            street1_segmentation = [street_pair[0].nids[:street1_nid_idx],
                                    street_pair[0].nids[street1_nid_idx:],
                                    []]
            # Street 2 is also divided into three segments - beginning segment, overlapping segment, and end segment
            street2_segmentation = [street_pair[1].nids[:street2_nid_idx],
                                    street_pair[1].nids[street2_nid_idx:],
                                    []]

            if len(street1_segmentation[0]) > 0:
                street1_segmentation[0].append(street1_segmentation[1][0])
            if len(street2_segmentation[0]) > 0:
                street2_segmentation[0].append(street2_segmentation[1][0])
            return overlapping_segment, street1_segmentation, street2_segmentation
        else:
            # Other cases (i.e., segments do not intersect)

            # Find the first occurrence of True in the list
            begin_idx = all_nids_street_switch.index(True)

            # Find the last occurrence of True in the list
            end_idx = len(all_nids_street_switch) - 1 - all_nids_street_switch[::-1].index(True)

            overlapping_segment = all_nids[begin_idx + 1:end_idx + 1]

            begin_nid = all_nids[begin_idx]
            if begin_nid in street_pair[0].nids:
                street1_begin_nid = begin_nid
                street2_begin_nid = all_nids[begin_idx + 1]
            else:
                street1_begin_nid = all_nids[begin_idx + 1]
                street2_begin_nid = begin_nid
            street1_begin_idx = street_pair[0].nids.index(street1_begin_nid)
            street2_begin_idx = street_pair[1].nids.index(street2_begin_nid)

            # Create a foot from a first node to the segment on the other side
            if begin_nid in street_pair[1].nids:
                begin_node = self.get_node(begin_nid)
                street2_node_2 = self.get_node(street2_begin_nid)
                street2_node_1_nid = street_pair[1].nids[street2_begin_idx - 1]
                street2_node_1 = self.get_node(street2_node_1_nid)
                line = points_to_line((street2_node_1.lng, street2_node_1.lat), (street2_node_2.lng, street2_node_2.lat))
                foot_lng, foot_lat = foot(begin_node.lng, begin_node.lat, line[0], line[1], line[2])
                foot_node = self.create_node(None, foot_lat, foot_lng)
                street_pair[1].insert_node(street2_begin_idx + 1, foot_node.id)
                street2_begin_idx += 1
            else:
                begin_node = self.get_node(begin_nid)
                street1_node_2 = self.get_node(street2_begin_nid)
                street1_node_1_nid = street_pair[0].nids[street1_begin_idx - 1]
                street1_node_1 = self.get_node(street1_node_1_nid)
                line = points_to_line((street1_node_1.lng, street1_node_1.lat), (street1_node_2.lng, street1_node_2.lat))
                foot_lng, foot_lat = foot(begin_node.lng, begin_node.lat, line[0], line[1], line[2])
                foot_node = self.create_node(None, foot_lat, foot_lng)
                street_pair[0].insert_node(street1_begin_idx, foot_node.id)
                street1_begin_idx += 1
            overlapping_segment.insert(0, foot_node.id)

            end_nid = all_nids[end_idx]
            if end_nid in street_pair[0].nids:
                street1_end_nid = end_nid
                street2_end_nid = all_nids[end_idx + 1]
            else:
                street1_end_nid = all_nids[end_idx + 1]
                street2_end_nid = end_nid
            street1_end_idx = street_pair[0].nids.index(street1_end_nid)
            street2_end_idx = street_pair[1].nids.index(street2_end_nid)

            # Create a foot from the last node to the segment on the other side
            if end_nid in street_pair[0].nids:
                end_node = self.get_node(end_nid)
                street2_node_2 = self.get_node(street2_end_nid)
                street2_node_1_nid = street_pair[1].nids[street2_end_idx - 1]
                street2_node_1 = self.get_node(street2_node_1_nid)
                line = points_to_line((street2_node_1.lng, street2_node_1.lat), (street2_node_2.lng, street2_node_2.lat))
                foot_lng, foot_lat = foot(end_node.lng, end_node.lat, line[0], line[1], line[2])
                foot_node = self.create_node(None, foot_lat, foot_lng)
                street_pair[1].insert_node(street2_end_idx, foot_node.id)
                # street2_end_idx -= 2
            else:
                end_node = self.get_node(end_nid)
                street1_node_2 = self.get_node(street2_end_nid)
                street1_node_1_nid = street_pair[0].nids[street1_end_idx - 1]
                street1_node_1 = self.get_node(street1_node_1_nid)
                line = points_to_line((street1_node_1.lng, street1_node_1.lat), (street1_node_2.lng, street1_node_2.lat))
                foot_lng, foot_lat = foot(end_node.lng, end_node.lat, line[0], line[1], line[2])
                foot_node = self.create_node(None, foot_lat, foot_lng)
                street_pair[0].insert_node(street1_end_idx, foot_node.id)
                # street1_end_idx -= 2
            overlapping_segment.append(foot_node.id)

            # Street 1 is divided into three segments - beginning segment, overlapping segment, and end segment
            street1_segmentation = [street_pair[0].nids[:street1_begin_idx],
                                    street_pair[0].nids[street1_begin_idx:street1_end_idx + 1],
                                    street_pair[0].nids[street1_end_idx + 1:]]
            # Street 2 is also divided into three segments - beginning segment, overlapping segment, and end segment
            street2_segmentation = [street_pair[1].nids[:street2_begin_idx],
                                    street_pair[1].nids[street2_begin_idx:street2_end_idx + 1],
                                    street_pair[1].nids[street2_end_idx + 1:]]

            # If street 1 has a beginning segment...
            if street1_segmentation[0]:
                street1_segmentation[0].append(street1_segmentation[1][0])
            # If street 1 has an ending segment...
            if street1_segmentation[2]:
                street1_segmentation[2].insert(0, street1_segmentation[1][-1])
            # If street 2 has a beginning segment...
            if street2_segmentation[0]:
                try:
                    street2_segmentation[0].append(street2_segmentation[1][0])
                except IndexError:
                    log.debug("Network.segment_parallel_streets: Debug")
                # if street2_segmentation[1]:
                #     street2_segmentation[0].append(street2_segmentation[1][0])
                # elif street2_segmentation[2]:
                #     street2_segmentation[0].append(street2_segmentation[2][0])
            # If street 2 has an ending segment...
            if street2_segmentation[2]:
                try:
                    street2_segmentation[2].insert(0, street2_segmentation[1][-1])
                except IndexError:
                    log.debug("Network.segment_parallel_streets: Debug")
                # if street2_segmentation[1]:
                #     street2_segmentation[2].insert(0, street2_segmentation[1][-1])
                # elif street2_segmentation[0]:
                #     street2_segmentation[2].insert(0, street2_segmentation[0][-1])

            return overlapping_segment, street1_segmentation, street2_segmentation

    def simplify(self, way_id, threshold=0.5):
        """
        Need a line simplification. Visvalingam?

        http://bost.ocks.org/mike/simplify/
        https://hydra.hull.ac.uk/assets/hull:8343/content
        """
        nodes = [self.nodes.get(nid) for nid in self.ways.get(way_id).get_node_ids()]
        latlngs = [node.location() for node in nodes]
        groups = list(window(range(len(latlngs)), 3))

        # Python heap
        # http://stackoverflow.com/questions/12749622/creating-a-heap-in-python
        # http://stackoverflow.com/questions/3954530/how-to-make-heapq-evaluate-the-heap-off-of-a-specific-attribute
        class Triangle(object):
            def __init__(self, prev_idx, idx, next_idx):
                self.idx = idx
                self.prev_idx = idx - 1
                self.next_idx = idx + 1
                self.area = area(latlngs[self.prev_idx], latlngs[self.idx], latlngs[self.next_idx])

            def update_area(self):
                self.area = area(latlngs[self.prev_idx], latlngs[self.idx], latlngs[self.next_idx])

            def __cmp__(self, other):
                if self.area < other.area:
                    return -1
                elif self.area == other.area:
                    return 0
                else:
                    return 1

            def _str__(self):
                return str(self.idx) + " area=" + str(self.area)

        dict = {}
        heap = []
        for i, group in enumerate(groups):
            t = Triangle(group[0], group[1], group[2])
            dict[group[1]] = t
            heappush(heap, t)

        while float(len(heap) + 2) / len(latlngs) > threshold:
            try:
                t = heappop(heap)
                if (t.idx + 1) in dict:
                    dict[t.idx + 1].prev_idx = t.prev_idx
                    dict[t.idx + 1].update_area()
                if (t.idx - 1) in dict:
                    dict[t.idx - 1].next_idx = t.next_idx
                    dict[t.idx - 1].update_area()
                heapify(heap)
            except IndexError:
                break

        l = [t.idx for t in heap]
        l.sort()
        new_nids = [nodes[0].id]
        for idx in l:
            new_nids.append(nodes[idx].id)
        new_nids.append(nodes[-1].id)
        self.ways.get(way_id).nids = new_nids

        return

    def split_streets(self):
        """
        Split ways into segments at intersections
        """

        for way in self.get_ways():
            intersection_nids = []
            for node in way.get_nodes():
                try:
                    if node.is_intersection():
                        intersection_nids.append(node.id)
                except AttributeError:
                    raise
            intersection_indices = [way.nids.index(nid) for nid in intersection_nids]
            if len(intersection_indices) > 0:
                # Do not split streets if (i) there is only one intersection node and it is the on the either end of the
                # street, or (ii) there are only two nodes and both of them are on the edge of the street.
                # Otherwise split the street!
                if len(intersection_indices) == 1 and (intersection_indices[0] == 0 or intersection_indices[0] == len(way.nids) - 1):
                    continue
                elif len(intersection_indices) == 2 and (intersection_indices[0] == 0 and intersection_indices[1] == len(way.nids) - 1):
                    continue
                elif len(intersection_indices) == 2 and (intersection_indices[1] == 0 and intersection_indices[0] == len(way.nids) - 1):
                    continue
                else:
                    prev_idx = 0
                    for idx in intersection_indices:
                        if idx != 0 and idx != len(way.nids) - 1:
                            new_nids = way.nids[prev_idx:idx + 1]
                            street = self.create_street(None, new_nids)
                            street.add_original_way(way)
                            prev_idx = idx
                    new_nids = way.nids[prev_idx:]
                    street = self.create_street(None, new_nids)
                    street.add_original_way(way)
                    self.remove_way(way.id)

    def update_node_cardinality(self):
        """
        Update the nodes' minimum intersection cardinality.
        """
        for node in self.nodes.get_list():
            # Now the minimum number of ways connected has to be 3 for the node to be an intersection
            node.min_intersection_cardinality = 3

    def update_node_way_connection(self):
        """
        Go through each way and update which nodes belongs to this way
        """
        for street in self.get_ways():
            for nid in street.get_node_ids():
                node = self.get_node(nid)
                if node:
                    node.append_way(street.id)


def parse(filename):
    """
    Parse a OSM file
    """
    with open(filename, "rb") as osm:
        # Find element
        # http://stackoverflow.com/questions/222375/elementtree-xpath-select-element-based-on-attribute
        tree = ET.parse(osm)

        nodes_tree = tree.findall(".//node")
        ways_tree = tree.findall(".//way")
        bounds_elem = tree.find(".//bounds")
        bounds = [bounds_elem.get("minlat"), bounds_elem.get("minlon"), bounds_elem.get("maxlat"), bounds_elem.get("maxlon")]

    log.debug("Start parsing the file: %s" % filename)
    # Parse nodes and ways. Only read the ways that have the tags specified in valid_highways
    streets = Streets()
    street_nodes = Nodes()
    street_network = OSM(street_nodes, streets, bounds)
    for node in nodes_tree:
        # mynode = Node(node.get("id"), node.get("lat"), node.get("lon"))
        # street_network.add_node(mynode)
        street_network.create_node(node.get("id"), node.get("lat"), node.get("lon"))

    valid_highways = {'primary', 'secondary', 'tertiary', 'residential'}
    for way in ways_tree:
        highway_tag = way.find(".//tag[@k='highway']")
        oneway_tag = way.find(".//tag[@k='oneway']")
        ref_tag = way.find(".//tag[@k='ref']")
        if highway_tag is not None and highway_tag.get("v") in valid_highways:
            node_elements = filter(lambda elem: elem.tag == "nd", list(way))
            nids = [node.get("ref") for node in node_elements]

            # Sort the nodes by longitude.
            if street_nodes.get(nids[0]).lng > street_nodes.get(nids[-1]).lng:
                nids = nids[::-1]

            street = street_network.create_street(way.get("id"), nids)
            if oneway_tag is not None:
                street.set_oneway_tag('yes')
            else:
                street.set_oneway_tag('no')
            street.set_ref_tag(ref_tag)



    return street_network


def parse_intersections(nodes, ways):
    node_list = nodes.get_list()
    intersection_node_ids = [node.id for node in node_list if node.is_intersection()]
    ways.set_intersection_node_ids(intersection_node_ids)
    return


if __name__ == "__main__":
    # filename = "../resources/SegmentedStreet_01.osm"
    filename = "../resources/ParallelLanes_01.osm"
    print("Beginning parse..." + str(datetime.now()))

    street_network = parse(filename)
    print("Parse finished, beginning preprocess..." + str(datetime.now()))
    street_network.preprocess()
    print("Preprocess finished, beginning parse_intersections" + str(datetime.now()))
    street_network.parse_intersections()
    print("parse_intersections finished, beginning export" + str(datetime.now()))

    geojson = street_network.export(format='geojson')
    print("Export finished" + str(datetime.now()))
    #print geojson
