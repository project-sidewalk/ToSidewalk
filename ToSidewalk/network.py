from xml.etree import cElementTree as ET
from shapely.geometry import Polygon, Point, LineString
import json
import logging as log
import math
import numpy as np

from nodes import Node, Nodes
from ways import Street, Streets
from utilities import window, area

from itertools import combinations
from heapq import heappush, heappop, heapify

class Network(object):
    def __init__(self, nodes, ways):
        self.nodes = nodes
        self.ways = ways

        self.ways.parent_network = self
        self.nodes.parent_network = self

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
        :param nodes:
        :return:
        """
        for node in nodes:
            self.add_node(node)

    def add_way(self, way):
        """
        Add a way to this network
        :param way: A Way object to add
        :return:
        """
        self.ways.add(way)
        for nid in way.nids:
            self.nodes.get(nid).way_ids.append(way.id)

    def add_ways(self, ways):
        """
        Add a list of ways to this network
        :param ways:
        :return:
        """
        for way in ways:
            self.add_way(way)

    def get_adjacent_nodes(self, node):
        """
        Get adjacent nodes for the passed node
        :param node:
        :return:
        """
        adj_nodes = []
        way_ids = node.get_way_ids()

        for way_id in way_ids:
            way = self.ways.get(way_id)
            # If the current intersection node is at the head of street.nids, then take the second node and push it
            # into adj_street_nodes. Otherwise, take the node that is second to the last in street.nids .
            if way.nids[0] == node.id:
                adj_nodes.append(self.nodes.get(way.nids[1]))
            else:
                adj_nodes.append(self.nodes.get(way.nids[-2]))

        return adj_nodes

    def parse_intersections(self):
        node_list = self.nodes.get_list()
        intersection_node_ids = [node.id for node in node_list if node.is_intersection()]
        self.ways.set_intersection_node_ids(intersection_node_ids)
        return

    def remove_node(self, nid):
        node = self.nodes.get(nid)
        for way_id in node.way_ids:
            self.ways.get(way_id).remove_node(nid)
        self.nodes.remove(nid)
        return

    def remove_way(self, way_id):
        """
        Remove a way object from this network
        :param way_id: A way id
        :return:
        """
        way = self.ways.get(way_id)
        for nid in way.get_node_ids():
            node = self.nodes.get(nid)
            node.remove_way_id(way_id)
            way_ids = node.get_way_ids()
            if len(way_ids) == 0:
                self.nodes.remove(nid)
        self.ways.remove(way_id)

    def swap_nodes(self, nid_from, nid_to):
        """
        Swap the node in all the ways
        :param nid_from:
        :param nid_to:
        :return:
        """
        node = self.nodes.get(nid_from)
        if node and node.way_ids:
            for way_id in node.way_ids:
                self.ways.get(way_id).swap_nodes(nid_from, nid_to)
            self.nodes.remove(nid_from)
        return

class OSM(Network):

    def __init__(self, nodes, ways, bounds):
        # self.nodes = nodes
        # self.ways = ways
        super(OSM, self).__init__(nodes, ways)

        if bounds:
            self.bounds = bounds

    def preprocess(self):
        """
        Preprocess and clean up the data
        :return:
        """
        parallel_segments = self.find_parallel_street_segments()
        self.merge_parallel_street_segments(parallel_segments)

        self.split_streets()
        self.update_ways()
        self.merge_nodes()

        # Clean up and so I can make a sidewalk network
        self.clean_street_segmentation()



        # Remove ways that have only a single node.
        for way in self.ways.get_list():
            if len(way.nids) < 2:
                self.remove_way(way.id)
        return

    def clean_street_segmentation(self):
        """
        Go through nodes and find ones that have two connected ways (nodes should have either one or more than two ways)
        """
        for node in self.nodes.get_list():
            if len(node.get_way_ids()) == 2:
                way_id_1, way_id_2 = node.get_way_ids()
                way_1 = self.ways.get(way_id_1)
                way_2 = self.ways.get(way_id_2)

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
                new_street = Street(None, combined_nids, "footway")
                self.add_way(new_street)
                self.remove_way(way_id_1)
                self.remove_way(way_id_2)

        return

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
            for way in self.ways.get_list():
                feature = {}
                feature['properties'] = {
                    'type': way.type,
                    'id': way.id,
                    'user': way.user,
                    'stroke': '#555555'
                }
                feature['type'] = 'Feature'
                feature['id'] = 'way/%s' % (way.id)

                coordinates = []
                for nid in way.nids:
                    node = self.nodes.get(nid)
                    coordinates.append([node.lng, node.lat])
                feature['geometry'] = {
                    'type': 'LineString',
                    'coordinates': coordinates
                }
                geojson['features'].append(feature)

            return json.dumps(geojson)

    def merge_nodes(self, distance_threshold=0.015):
        """
        Merge nodes that are close to intersection nodes. Then merge nodes that are
        close to each other.
        """
        for street in self.ways.get_list():
            # if len(street.nids) < 2:
            if len(street.nids) <= 2:
                # Skip. You should not merge two intersection nodes
                continue

            start = self.nodes.get(street.nids[0])
            end = self.nodes.get(street.nids[-1])

            # Merge the nodes around the beginning of the street
            for nid in street.nids[1:-1]:
                target = self.nodes.get(nid)
                distance = start.distance_to(target)
                if distance < distance_threshold:
                    self.remove_node(nid)
                else:
                    break

            if len(street.nids) <= 2:
                # Done, if you merged everything other than intersection nodes
                continue

            for nid in street.nids[-2:0:-1]:
                target = self.nodes.get(nid)
                distance = end.distance_to(target)
                if distance < distance_threshold:
                    self.remove_node(nid)
                else:
                    break

        return

    def find_parallel_street_segments(self):
        """
        This method finds parallel segments and returns a list of pair of way ids
        :return: A list of pair of parallel way ids
        """
        streets = self.ways.get_list()
        street_polygons = []
        distance_to_sidewalk = 0.00005

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
            poly.nids = set((start_node_id, end_node_id))
            street_polygons.append(poly)

        # Find pair of polygons that intersect each other.
        polygon_combinations = combinations(street_polygons, 2)
        # Create a list for storing parallel pairs
        parallel_pairs = []



        # Todo: change the variable name pair to pair_poly
        for pair in polygon_combinations: # pair[0] and pair[1] are polygons
            angle_diff = ((pair[0].angle - pair[1].angle) + 360.) % 180.
            if pair[0].intersects(pair[1]) and (angle_diff < 10. or angle_diff>170.):
                # If the polygon intersects, and they have a kind of similar angle, and they don't share a node,
                # then they should be merged together.
                parallel_pairs.append((street_polygons.index(pair[0]), street_polygons.index(pair[1])))


        filtered_parallel_pairs = []

        #Filter parallel_pairs and store in filtered_parallel_pairs
        for pair in parallel_pairs:
            street_pair = (streets[pair[0]], streets[pair[1]])
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
            filtered_parallel_pairs.append(pair)
        return [(streets[pair[0]].id, streets[pair[1]].id) for pair in filtered_parallel_pairs]

    def segment_parallel_streets(self, street_pair):
        """
        First find parts of the street pairs that you want to merge (you don't want to merge entire streets
        because, for example, one could be much longer than the other and it doesn't make sense to merge
        :param street_pair:
        :return:
        """
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

        all_nodes = [self.nodes.get(nid) for nid in street_pair[0].nids] + [self.nodes.get(nid) for nid in street_pair[1].nids]
        all_nodes = sorted(all_nodes, cmp=cmp_with_projection)
        all_nids = [node.id for node in all_nodes]

        # Condition in list comprehension
        # http://stackoverflow.com/questions/4260280/python-if-else-in-list-comprehension
        all_nids_street_indices = [0 if nid in street_pair[0].nids else 1 for nid in all_nids]
        all_nids_street_switch = [idx_pair[0] != idx_pair[1] for idx_pair in window(all_nids_street_indices, 2)]

        # Find the first occurence of an element in a list
        # http://stackoverflow.com/questions/9868653/find-first-list-item-that-matches-criteria
        begin_idx = all_nids_street_switch.index(next(x for x in all_nids_street_switch if x == True))

        # Find the last occurence of an element in a list
        # http://stackoverflow.com/questions/6890170/how-to-find-the-last-occurrence-of-an-item-in-a-python-list
        end_idx = (len(all_nids_street_switch) - 1) - all_nids_street_switch[::-1].index(next(x for x in all_nids_street_switch if x == True))

        overlapping_segment = all_nids[begin_idx:end_idx]

        begin_nid = all_nids[begin_idx]
        if begin_nid in street_pair[0].nids:
            street1_begin_nid = begin_nid
            street2_begin_nid = all_nids[begin_idx + 1]
        else:
            street1_begin_nid = all_nids[begin_idx + 1]
            street2_begin_nid = begin_nid
        street1_begin_idx = street_pair[0].nids.index(street1_begin_nid)
        street2_begin_idx = street_pair[1].nids.index(street2_begin_nid)

        end_nid = all_nids[end_idx]
        if end_nid in street_pair[0].nids:
            street1_end_nid = end_nid
            street2_end_nid = all_nids[end_idx + 1]
        else:
            street1_end_nid = all_nids[end_idx + 1]
            street2_end_nid = end_nid
        street1_end_idx = street_pair[0].nids.index(street1_end_nid)
        street2_end_idx = street_pair[1].nids.index(street2_end_nid)

        street1_segmentation = [street_pair[0].nids[:street1_begin_idx],
                                street_pair[0].nids[street1_begin_idx:street1_end_idx + 1],
                                street_pair[0].nids[street1_end_idx + 1:]]
        street2_segmentation = [street_pair[1].nids[:street2_begin_idx],
                                street_pair[1].nids[street2_begin_idx:street2_end_idx + 1],
                                street_pair[1].nids[street2_end_idx + 1:]]

        if street1_segmentation[0]:
            street1_segmentation[0].append(street1_segmentation[1][0])
        if street1_segmentation[2]:
            street1_segmentation[2].insert(0, street1_segmentation[1][-1])

        if street2_segmentation[0]:
            street2_segmentation[0].append(street2_segmentation[1][0])
        if street2_segmentation[2]:
            street2_segmentation[2].insert(0, street2_segmentation[1][-1])

        return overlapping_segment, street1_segmentation, street2_segmentation

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
            street_pair = (self.ways.get(pair[0]), self.ways.get(pair[1]))

            # First find parts of the street pairs that you want to merge (you don't want to merge entire streets
            # because, for example, one could be much longer than the other and it doesn't make sense to merge
            subset_nids, street1_segment, street2_segment = self.segment_parallel_streets((street_pair[0], street_pair[1]))
            if not subset_nids:
                continue

            # Get two parallel segments and the distance between them
            street1_node = self.nodes.get(street1_segment[1][0])
            street2_node = self.nodes.get(street2_segment[1][0])
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
            street1_nid = street1_segment[1][0]
            street2_nid = street2_segment[1][0]
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

                    new_node = Node(None, new_position[0], new_position[1])
                    self.add_node(new_node)
                    new_street_nids.append(new_node.id)
                except IndexError:
                    # Take care of the last node.
                    # Use the previous perpendicular vector but reverse the direction
                    node = self.nodes.get(nid)
                    new_position = node.location() - normal * distance
                    new_node = Node(None, new_position[0], new_position[1])
                    self.add_node(new_node)
                    new_street_nids.append(new_node.id)

            log.debug(pair)
            node_to[subset_nids[0]] = new_street_nids[0]
            node_to[subset_nids[-1]] = new_street_nids[-1]

            merged_street = Street(None, new_street_nids)
            merged_street.distance_to_sidewalk *= 2
            self.add_way(merged_street)
            self.simplify(merged_street.id, 0.1)
            streets_to_remove.append(street_pair[0].id)
            streets_to_remove.append(street_pair[1].id)

            # Create streets from the unmerged nodes.
            # Todo: I think this part of the code can be prettier
            if street1_segment[0] or street2_segment[0]:
                if street1_segment[0] and street2_segment[0]:
                    if street1_segment[0][0] == street2_segment[0][0]:
                        # The two segments street1 and street2 share a common node. Just connect one of them to the
                        # new merged street.
                        if subset_nids[0] in street1_segment[1]:
                            street1_segment[0][-1] = node_to[street1_segment[0][-1]]
                            s = Street(None, street1_segment[0])
                            self.add_way(s)
                        else:
                            street2_segment[0][-1] = node_to[street2_segment[0][-1]]
                            s = Street(None, street2_segment[0])
                            self.add_way(s)
                    else:
                        # Both street1_segment and street2_segment exist, but they do not share a common node
                        street1_segment[0][-1] = node_to[street1_segment[0][-1]]
                        s = Street(None, street1_segment[0])
                        self.add_way(s)
                        street2_segment[0][-1] = node_to[street2_segment[0][-1]]
                        s = Street(None, street2_segment[0])
                        self.add_way(s)
                elif street1_segment[0]:
                    # Only street1_segment exists
                    street1_segment[0][-1] = node_to[street1_segment[0][-1]]
                    s = Street(None, street1_segment[0])
                    self.add_way(s)
                else:
                    # Only street2_segment exists
                    street2_segment[0][-1] = node_to[street2_segment[0][-1]]
                    s = Street(None, street2_segment[0])
                    self.add_way(s)

            if street1_segment[2] or street2_segment[2]:
                if street1_segment[2] and street2_segment[2]:
                    if street1_segment[2][-1] == street2_segment[2][-1]:
                        # The two segments street1 and street2 share a common node. Just connect one of them to the
                        # new merged street.
                        if subset_nids[-1] in street1_segment[1]:
                            street1_segment[2][0] = node_to[subset_nids[-1]]
                            s = Street(None, street1_segment[2])
                            self.add_way(s)
                        else:
                            street2_segment[2][0] = node_to[subset_nids[-1]]
                            s = Street(None, street2_segment[2])
                            self.add_way(s)
                    else:
                        # Both street1_segment and street2_segment exist, but they do not share a common node
                        street1_segment[2][0] = node_to[subset_nids[-1]]
                        s = Street(None, street1_segment[2])
                        self.add_way(s)
                        street2_segment[2][0] = node_to[subset_nids[-1]]
                        s = Street(None, street2_segment[2])
                        self.add_way(s)
                elif street1_segment[2]:
                    # Only street1_segment exists
                    street1_segment[2][0] = node_to[subset_nids[-1]]
                    s = Street(None, street1_segment[2])
                    self.add_way(s)
                else:
                    # Only street2_segment exists
                    street2_segment[2][0] = node_to[subset_nids[-1]]
                    s = Street(None, street2_segment[2])
                    self.add_way(s)

        for street_id in set(streets_to_remove):
            self.remove_way(street_id)
        return

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
        class triangle(object):
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
            t = triangle(group[0], group[1], group[2])
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
        # new_streets = Streets()
        for way in self.ways.get_list():
            intersection_nids = [nid for nid in way.nids if self.nodes.get(nid).is_intersection()]
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
                        if idx != 0 and idx != len(way.nids):
                            new_nids = way.nids[prev_idx:idx + 1]
                            new_way = Street(None, new_nids, way.type)
                            # new_streets.add(new_way)
                            self.add_way(new_way)
                            prev_idx = idx
                    new_nids = way.nids[prev_idx:]
                    new_way = Street(None, new_nids, way.type)
                    # new_streets.add(new_way)
                    self.add_way(new_way)
                    self.remove_way(way.id)
        # self.ways = new_streets

        return

    def update_ways(self):
        # Update the way_ids
        for node in self.nodes.get_list():
            # Now the minimum number of ways connected has to be 3 for the node to be an intersection
            node.way_ids = []
            node.min_intersection_cardinality = 3
        for street in self.ways.get_list():
            for nid in street.nids:
                self.nodes.get(nid).append_way(street.id)


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

    # Parse nodes and ways. Only read the ways that have the tags specified in valid_highways
    streets = Streets()
    street_nodes = Nodes()
    street_network = OSM(street_nodes, streets, bounds)
    for node in nodes_tree:
        mynode = Node(node.get("id"), node.get("lat"), node.get("lon"))
        street_network.add_node(mynode)

    valid_highways = {'primary', 'secondary', 'tertiary', 'residential'}
    for way in ways_tree:
        highway_tag = way.find(".//tag[@k='highway']")
        if highway_tag is not None and highway_tag.get("v") in valid_highways:
            node_elements = filter(lambda elem: elem.tag == "nd", list(way))
            nids = [node.get("ref") for node in node_elements]

            # Sort the nodes by longitude.
            if street_nodes.get(nids[0]).lng > street_nodes.get(nids[-1]).lng:
                nids = nids[::-1]

            street = Street(way.get("id"), nids)
            street_network.add_way(street)

    return street_network


def parse_intersections(nodes, ways):
    node_list = nodes.get_list()
    intersection_node_ids = [node.id for node in node_list if node.is_intersection()]
    ways.set_intersection_node_ids(intersection_node_ids)
    return


if __name__ == "__main__":
    # filename = "../resources/SegmentedStreet_01.osm"
    filename = "../resources/ParallelLanes_01.osm"
    street_network = parse(filename)
    street_network.preprocess()
    street_network.parse_intersections()

    geojson = street_network.export(format='geojson')
    print geojson

