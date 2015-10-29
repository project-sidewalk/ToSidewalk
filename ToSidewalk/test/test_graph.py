import unittest

from ToSidewalk.graph import GeometricGraph


class TestGeometricGraphMethods(unittest.TestCase):

    def setUp(self):
        self.graph = GeometricGraph()

    def test_remove_node(self):
        node = self.graph.create_node(0, 0)
        self.graph.remove_node(node.id)
        self.assertEqual(len(self.graph.nodes.values()), 0)

    def test_get_adjacent_nodes(self):
        n0 = self.graph.create_node(0, 0)
        n1 = self.graph.create_node(1, 0)
        n2 = self.graph.create_node(0, 1)
        n3 = self.graph.create_node(-1, 0)
        n4 = self.graph.create_node(0, -1)

        p1 = self.graph.create_path([n0, n1])
        p2 = self.graph.create_path([n0, n2])
        p3 = self.graph.create_path([n0, n3])
        p4 = self.graph.create_path([n0, n4])

        self.assertEqual(len(self.graph.get_adjacent_nodes(n0)), 4)


    def test_remove_node(self):
        nodes =[self.graph.create_node(i, i * 10, i) for i in range(5)]
        path = self.graph.create_path(nodes, 0)

        self.graph.remove_node(2)

        self.assertEqual(len(path.edges), 3)
        self.assertEqual(path.edges[1].xy[0][0], 1.)
        self.assertEqual(path.edges[1].xy[0][1], 3.)
        self.assertEqual(path.edges[1].xy[1][0], 10.)
        self.assertEqual(path.edges[1].xy[1][1], 30.)



if __name__ == '__main__':
    unittest.main()
