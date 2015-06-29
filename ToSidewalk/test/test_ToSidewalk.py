import unittest
import random
from ToSidewalk.ways import *
from ToSidewalk.ToSidewalk import *

class TestToSidewalkMethods(unittest.TestCase):
    def test_sort_nodes(self):
        """
        """
        center = "38.988152,-76.941595"
        center = map(float, center.split(","))
        center_node = Node('0', center[0], center[1])

        latlngs = """
38.988927,-76.940528
38.989269,-76.941408
38.988239,-76.942878
38.987172,-76.942540
38.987105,-76.941494
38.987906,-76.940222
        """

        latlngs = latlngs.strip().split('\n')
        latlngs = [map(float, latlng.split(',')) for latlng in latlngs]

        nodes1 = [Node(str(i), latlng[0], latlng[1]) for i, latlng in enumerate(latlngs)]
        nodes2 = [Node(str(i), latlng[0], latlng[1]) for i, latlng in enumerate(latlngs)]

        random.shuffle(nodes1)
        nodes1 = sort_nodes(center_node, nodes1)

        for node1, node2 in zip(nodes1, nodes2):
            self.assertTrue(node1.lat == node2.lat)
            self.assertTrue(node1.lng == node2.lng)

    def test_make_crosswalk_node(self):
        clat, clng = 0, 0
        lat1, lng1 = 0, 1
        lat2, lng2 = 1, 0
        cnode = Node('0', clat, clng)
        node1 = Node('1', lat1, lng1)
        node2 = Node('2', lat2, lng2)

        rlat, rlng = cnode.crosswalk_distance / math.sqrt(2), cnode.crosswalk_distance / math.sqrt(2)
        node = make_crosswalk_node(cnode, node1, node2)
        self.assertEqual(rlat, node.lat)
        self.assertEqual(rlng, node.lng)

        clat, clng = 0, 0
        lat1, lng1 = 0, 1
        lat2, lng2 = 1, 0
        lat3, lng3 = 0, -1
        lat4, lng4 = -1, 0
        cnode = Node('0', clat, clng)
        node1 = Node('1', lat1, lng1)
        node2 = Node('2', lat2, lng2)
        node3 = Node('3', lat3, lng3)
        node4 = Node('4', lat4, lng4)

        # Parameter Error:
        # http://stackoverflow.com/questions/256222/which-exception-should-i-raise-on-bad-illegal-argument-combinations-in-python
        adjacent_nodes = [node1, node2]
        self.assertRaises(ValueError, make_crosswalk_nodes, cnode, adjacent_nodes)
        adjacent_nodes = [node1, node2, node3]
        self.assertRaises(ValueError, make_crosswalk_nodes, cnode, adjacent_nodes)

        # Opposite of assertRaises
        # http://stackoverflow.com/questions/4319825/python-unittest-opposite-of-assertraises
        try:
            adjacent_nodes = [node1, node2, node3, node4]
            make_crosswalk_nodes(cnode, adjacent_nodes)
        except ValueError:
            self.fail("make_crosswalk_nodes() failed unexpectedly")

    def test_make_crosswalks(self):
        filename = "../../resources/SmallMap_01.osm"
        street_network = parse(filename)
        street_network.preprocess()
        street_network.parse_intersections()
        sidewalk_network = make_sidewalks(street_network)
        make_crosswalks(street_network, sidewalk_network)

    def test_connect_crosswalk_nodes(self):
        node_0 = Node(0, 0, 0)
        node_1 = Node(1, 0, 0.001)
        node_2 = Node(2, 0.001, 0)
        node_3 = Node(3, 0, -0.001)
        node_4 = Node(4, -0.001, 0)
        street_1 = Street(1, [node_0.id, node_1.id])
        street_2 = Street(2, [node_0.id, node_2.id])
        street_3 = Street(3, [node_0.id, node_3.id])
        street_4 = Street(4, [node_0.id, node_4.id])

        nodes = Nodes()
        streets = Streets()
        street_network = OSM(nodes, streets, None)
        street_network.add_nodes([node_0, node_1, node_2, node_3, node_4])
        street_network.add_ways([street_1, street_2, street_3, street_4])

        # street_network.preprocess()
        street_network.parse_intersections()
        sidewalk_network = make_sidewalks(street_network)

        c_node_1 = Node('c1', 0.0001, 0.0001)
        c_node_1.parents = (node_0, node_1, node_2)
        # c_node_1.way_ids = [node_1.way_ids[0], node_2.way_ids[0]]
        c_node_2 = Node('c2', 0.0001, -0.0001)
        c_node_2.parents = (node_0, node_2, node_3)
        # c_node_2.way_ids = [node_2.way_ids[0], node_3.way_ids[0]]
        c_node_3 = Node('c3', -0.0001, -0.0001)
        c_node_3.parents = (node_0, node_3, node_4)
        # c_node_3.way_ids = (node_3.way_ids[0], node_4.way_ids[0])
        c_node_4 = Node('c4', -0.0001, 0.0001)
        c_node_4.parents = (node_0, node_4, node_1)
        # c_node_4.way_ids = (node_4.way_ids[0], node_1.way_ids[0])
        sidewalk_network.add_nodes([c_node_1, c_node_2, c_node_3, c_node_4])

        crosswalk = Sidewalk('c', ['c1', 'c2', 'c3', 'c4', 'c1'])
        sidewalk_network.add_way(crosswalk)

        connect_crosswalk_nodes(sidewalk_network, crosswalk.nids)

        for street in streets.get_list():
            # Sidewalks should not cross
            sidewalk_ids = street.get_sidewalk_ids()
            s1 = sidewalk_network.ways.get(sidewalk_ids[0])
            s2 = sidewalk_network.ways.get(sidewalk_ids[1])
            s1_n1, s1_n2 = sidewalk_network.nodes.get(s1.nids[0]), sidewalk_network.nodes.get(s1.nids[-1])
            s2_n1, s2_n2 = sidewalk_network.nodes.get(s2.nids[0]), sidewalk_network.nodes.get(s2.nids[-1])
            s1_n1_p = np.array([s1_n1.lat, s1_n1.lng, 1.])
            s1_n2_p = np.array([s1_n2.lat, s1_n2.lng, 1.])

            s2_n1_p = np.array([s2_n1.lat, s2_n1.lng, 1.])
            s2_n2_p = np.array([s2_n2.lat, s2_n2.lng, 1.])

            l1 = np.cross(s1_n1_p, s1_n2_p)
            l1 /= l1[2]
            l2 = np.cross(s2_n1_p, s2_n2_p)
            l2 /= l2[2]

            intersection = np.cross(l1, l2)
            intersection /= intersection[2]
            lng_min = min([s1_n1.lng,
                          s1_n2.lng,
                          s2_n1.lng,
                          s1_n2.lng])
            lng_max = max([s1_n1.lng,
                          s1_n2.lng,
                          s2_n1.lng,
                          s1_n2.lng])
            lat_min = min([s1_n1.lat,
                          s1_n2.lat,
                          s2_n1.lat,
                          s1_n2.lat])
            lat_max = max([s1_n1.lat,
                          s1_n2.lat,
                          s2_n1.lat,
                          s1_n2.lat])
            does_cross = intersection[0] > lat_min and intersection[0] < lat_max and intersection[1] > lng_min and intersection[1] < lng_max

            self.assertFalse(does_cross)  # should not cross

    def test_main(self):
        filenames = [
            "../../resources/Simple4WayIntersection_01.osm",
            "../../resources/Simple4WayIntersection_02.osm",
            "../../resources/TShapeIntersection_01.osm",
            "../../resources/TShapeIntersection_02.osm",
            "../../resources/SegmentedStreet_01.osm",
            "../../resources/ComplexIntersection_01.osm",
            "../../resources/SmallMap_01.osm",
            "../../resources/SmallMap_02.osm",
            "../../resources/ParallelLanes_01.osm"
        ]
        for filename in filenames:
            log.debug(filename)
            street_network = parse(filename)
            street_network.preprocess()
            street_network.parse_intersections()
            log.debug(main(street_network))

if __name__ == '__main__':
    unittest.main()
