import unittest
from ToSidewalk.network import *
from ToSidewalk.nodes import *
from ToSidewalk.ways import *


class TestNetworkMethods(unittest.TestCase):

    def test_get_adjacent_nodes(self):
        """
        Test
        """
        streets = Streets()
        nodes = Nodes()
        network = Network(nodes, streets)
        n0 = Node(0, 0, 0)
        n1 = Node(1, 0, 1)
        n2 = Node(2, 1, 0)
        n3 = Node(3, 0, -1)
        network.add_nodes([n0, n1, n2, n3])
        s1 = Street(1, [n0.id, n1.id])
        s2_1 = Street('2_1', [n0.id, n2.id])
        s2_2 = Street('2_2', [n0.id, n2.id])

        network.add_ways([s1, s2_1, s2_2])

        adj = network.get_adjacent_nodes(n0)
        self.assertEqual(len(adj), 2)

        s3 = Street('3', [n0.id, n3.id])
        network.add_way(s3)
        adj = network.get_adjacent_nodes(n0)
        self.assertEqual(len(adj), 3)

    def test_segment_parallel_streets(self):
        """
        Test segment parallel streets
        """
        segment1_coordinates = [(float(i + 1), float(i)) for i in range(0, 7)]
        segment2_coordinates = [(float(i + 1), float(i)) for i in range(0, 7)]

        nodes = Nodes()
        segment1_nodes = [Node('s1_' + str(i), coord[1], coord[0]) for i, coord in enumerate(segment1_coordinates)]
        segment2_nodes = [Node('s2_' + str(i), coord[1], coord[0]) for i, coord in enumerate(segment2_coordinates)]
        # answer_segment_nodes = [Node(None, LatLng(coord[1], coord[0])) for coord in answer_segment_coordinates]

        for node in segment1_nodes:
            nodes.add(node)
        for node in segment2_nodes:
            nodes.add(node)

        segment1_node_ids = [node.id for node in segment1_nodes]
        segment2_node_ids = [node.id for node in segment2_nodes]
        # answer_segment_node_ids = [node.id for node in answer_segment_nodes]

        street1 = Street(1, segment1_node_ids)
        street2 = Street(2, segment2_node_ids)
        # answer_street = Street(None, answer_segment_node_ids)

        streets = Streets()
        streets.add(street1)
        streets.add(street2)

        network = OSM(nodes, streets, None)

        overlap, segments1, segments2 = network.segment_parallel_streets([street1, street2])

        self.assertEqual(segments1[0], [])
        self.assertEqual(segments1[2], [])
        self.assertListEqual(segments1[1], segment1_node_ids)
        self.assertEqual(segments2[0], [])
        self.assertEqual(segments2[2], [])
        self.assertListEqual(segments2[1], segment2_node_ids)

    def test_segment_parallel_streets2(self):
        """
        Test segment parallel streets
        """
        segment1_coordinates = [(float(i + 1), float(i)) for i in range(2, 10)]
        segment2_coordinates = [(float(i + 1), float(i)) for i in range(0, 7)]
        answer_segment_coordinates = [(float(2 * i + 1) / 2, float(2 * i + 1) / 2) for i in range(0, 7)]

        nodes = Nodes()
        segment1_nodes = [Node('s1_' + str(i), coord[1], coord[0]) for i, coord in enumerate(segment1_coordinates)]
        segment2_nodes = [Node('s2_' + str(i), coord[1], coord[0]) for i, coord in enumerate(segment2_coordinates)]
        # answer_segment_nodes = [Node(None, LatLng(coord[1], coord[0])) for coord in answer_segment_coordinates]

        for node in segment1_nodes:
            nodes.add(node)
        for node in segment2_nodes:
            nodes.add(node)

        segment1_node_ids = [node.id for node in segment1_nodes]
        segment2_node_ids = [node.id for node in segment2_nodes]
        # answer_segment_node_ids = [node.id for node in answer_segment_nodes]

        street1 = Street(1, segment1_node_ids)
        street2 = Street(2, segment2_node_ids)
        # answer_street = Street(None, answer_segment_node_ids)

        streets = Streets()
        streets.add(street1)
        streets.add(street2)

        network = OSM(nodes, streets, None)

        overlap, segments1, segments2 = network.segment_parallel_streets([street1, street2])

        self.assertEqual(segments1[0], [])
        self.assertEqual(segments1[2], segment1_node_ids[-3:])
        self.assertListEqual(segments1[1], segment1_node_ids[:-2])
        self.assertEqual(segments2[0], segment2_node_ids[:2])
        self.assertEqual(segments2[2], [])
        self.assertListEqual(segments2[1], segment2_node_ids[1:])

    def test_merge_parallel_street_segments(self):
        """
        Test the constructor
        """
        segment1_coordinates = [(float(i + 1), float(i)) for i in range(0, 7)]
        segment2_coordinates = [(float(i + 1), float(i)) for i in range(0, 7)]
        answer_segment_coordinates = [(float(2 * i + 1) / 2, float(2 * i + 1) / 2) for i in range(0, 7)]

        nodes = Nodes()
        segment1_nodes = [Node(None, coord[1], coord[0]) for coord in segment1_coordinates]
        segment2_nodes = [Node(None, coord[1], coord[0]) for coord in segment2_coordinates]
        answer_segment_nodes = [Node(None, coord[1], coord[0]) for coord in answer_segment_coordinates]

        for node in segment1_nodes:
            nodes.add(node)
        for node in segment2_nodes:
            nodes.add(node)

        segment1_node_ids = [node.id for node in segment1_nodes]
        segment2_node_ids = [node.id for node in segment2_nodes]
        answer_segment_node_ids = [node.id for node in answer_segment_nodes]

        street1 = Street(1, segment1_node_ids)
        street2 = Street(2, segment2_node_ids)
        answer_street = Street(None, answer_segment_node_ids)

        streets = Streets()
        streets.add(street1)
        streets.add(street2)

        network = OSM(nodes, streets, None)

        merged_segment = network.merge_parallel_street_segments([(street1.id, street2.id)])

        # self.assertEqual(answer_segment_coordinates[0], merged_segment[0])

    def test_merge_parallel_street_segments2(self):
        filename = "../../resources/ParallelLanes_03.osm"

        street_network = parse(filename)
        street_network.split_streets()
        parallel_segments = street_network.find_parallel_street_segments()
        street_network.merge_parallel_street_segments(parallel_segments)
        return

    def test_simplify(self):
        segment1_coordinates = [
            (0., 2.),
            (3., 0.),
            (6., 1.),
            (9., 0.),
            (12., 0.5),
            (15., 2.)
        ]

        nodes = Nodes()
        segment1_nodes = [Node('s1_' + str(i), coord[1], coord[0]) for i, coord in enumerate(segment1_coordinates)]
        for node in segment1_nodes:
            nodes.add(node)

        segment1_node_ids = [node.id for node in segment1_nodes]
        street1 = Street(1, segment1_node_ids)
        streets = Streets()
        streets.add(street1)

        network = OSM(nodes, streets, None)
        network.simplify(street1.id)

    def test_parse(self):
        filename = "../../resources/SmallMap_01.osm"
        street_network = parse(filename)
        # Todo: Write a test to see the parsing worked


    def test_split_streets(self):
        filename = "../../resources/SmallMap_01.osm"
        street_network = parse(filename)
        street_network.preprocess()
        # Todo: Write a better test...

    def test_swap_nodes(self):
        node1 = Node(1, 1, 1)
        node2 = Node(2, 2, 2)
        node3 = Node(3, 3, 3)
        nodes = Nodes()
        ways = Ways()
        network = Network(nodes, ways)
        network.add_node(node1)
        network.add_node(node2)
        network.add_node(node3)

        way1 = Way(None, [node1.id, node2.id])
        way2 = Way(None, [node1.id, node3.id])
        network.add_way(way1)
        network.add_way(way2)

        self.assertEqual(node1.id, way1.nids[0])
        self.assertEqual(node1.id, way2.nids[0])

        network.swap_nodes(node1.id, node3.id)
        self.assertEqual(node3.id, way1.nids[0])
        self.assertEqual(node3.id, way2.nids[0])

    def test_remove_node(self):
        node1 = Node(1, 1, 0)
        node2 = Node(2, 2, -3)
        node3 = Node(3, 2, 3)
        node4 = Node(4, 4, -3)
        node5 = Node(5, 4, 3)
        node6 = Node(6, 6, 0)

        nodes = Nodes()
        ways = Ways()
        network = Network(nodes, ways)
        network.add_node(node1)
        network.add_node(node2)
        network.add_node(node3)
        network.add_node(node4)
        network.add_node(node5)
        network.add_node(node6)

        way1 = Way(None, [node1.id, node2.id, node4.id, node6.id])
        way2 = Way(None, [node1.id, node3.id, node5.id, node6.id])
        network.add_way(way1)
        network.add_way(way2)

        self.assertEqual(len(way1.nids), 4)
        self.assertEqual(len(way2.nids), 4)

        # Delete a node
        network.remove_node(node2.id)
        self.assertEqual(len(way1.nids), 3)
        self.assertEqual(len(way2.nids), 4)

        # When a node that is shared between ways are deleted
        network.remove_node(node6.id)
        self.assertEqual(len(way1.nids), 2)
        self.assertEqual(len(way2.nids), 3)

    def test_export(self):
        node0 = Node(0, 0, 0)
        node1 = Node(1, 0, 1)
        node2 = Node(2, 1, 0)
        node3 = Node(3, 0, -1)
        node4 = Node(4, -1, 0)
        way1 = Way(1, (node0.id, node1.id))
        way2 = Way(2, (node0.id, node2.id))
        way3 = Way(3, (node0.id, node3.id))
        way4 = Way(4, (node0.id, node4.id))

        nodes = Nodes()
        ways = Ways()
        network = OSM(nodes, ways, None)
        network.add_nodes([node0, node1, node2, node3, node4])
        network.add_ways([way1, way2, way3, way4])

        mygeojson = network.export()
        string = """{"type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 0.0]]}, "type": "Feature", "properties": {"stroke": "#555555", "type": null, "id": "1", "user": "test"}, "id": "way/1"}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [-1.0, 0.0]]}, "type": "Feature", "properties": {"stroke": "#555555", "type": null, "id": "3", "user": "test"}, "id": "way/3"}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [0.0, 1.0]]}, "type": "Feature", "properties": {"stroke": "#555555", "type": null, "id": "2", "user": "test"}, "id": "way/2"}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [0.0, -1.0]]}, "type": "Feature", "properties": {"stroke": "#555555", "type": null, "id": "4", "user": "test"}, "id": "way/4"}]}"""
        self.assertEqual(mygeojson, string)


if __name__ == '__main__':
    unittest.main()


