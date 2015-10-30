import unittest

from ToSidewalk.graph import GeometricGraph


class TestGeometricGraphMethods(unittest.TestCase):

    def setUp(self):
        self.graph = GeometricGraph()

    def test_remove_node(self):
        node = self.graph.create_node(0., 0.)
        self.graph.remove_node(node.id)
        self.assertEqual(len(self.graph.nodes.values()), 0.)

    def test_get_adjacent_nodes(self):
        n0 = self.graph.create_node(0., 0.)
        n1 = self.graph.create_node(1., 0.)
        n2 = self.graph.create_node(0., 1.)
        n3 = self.graph.create_node(-1., 0.)
        n4 = self.graph.create_node(0., -1.)

        p1 = self.graph.create_path(nodes=[n0, n1])
        p2 = self.graph.create_path(nodes=[n0, n2])
        p3 = self.graph.create_path(nodes=[n0, n3])
        p4 = self.graph.create_path(nodes=[n0, n4])

        self.assertEqual(len(self.graph.get_adjacent_nodes(n0)), 4)

    def test_get_degrees(self):
        n0 = self.graph.create_node(0., 0.)
        n1 = self.graph.create_node(1., 0.)
        n2 = self.graph.create_node(0., 1.)
        n3 = self.graph.create_node(-1., 0.)
        n4 = self.graph.create_node(0., -1.)

        p1 = self.graph.create_path(nodes=[n0, n1])
        p2 = self.graph.create_path(nodes=[n0, n2])
        p3 = self.graph.create_path(nodes=[n0, n3])
        p4 = self.graph.create_path(nodes=[n0, n4])

        self.assertEqual(self.graph.get_degrees()[0][0], 4)

    def test_remove_node(self):
        nodes =[self.graph.create_node(float(i), float(i) * 10) for i in range(5)]
        path = self.graph.create_path(nodes=nodes)

        self.graph.remove_node(2)

        self.assertEqual(len(path.edges), 3)
        self.assertEqual(path.edges[1].xy[0][0], 1.)
        self.assertEqual(path.edges[1].xy[0][1], 3.)
        self.assertEqual(path.edges[1].xy[1][0], 10.)
        self.assertEqual(path.edges[1].xy[1][1], 30.)

    def test_remove_path(self):
        nodes1 = [self.graph.create_node(float(i), 0.) for i in range(5)]
        nodes2 = [self.graph.create_node(float(i), 1.) for i in range(2)] + [nodes1[2]]
        path1 = self.graph.create_path(nodes=nodes1)
        path2 = self.graph.create_path(nodes=nodes2)

        node = nodes1[2]
        self.assertEqual(len(node.edges), 3)
        self.graph.remove_path(path1.id)
        self.assertEqual(len(node.edges), 1)

if __name__ == '__main__':
    unittest.main()
