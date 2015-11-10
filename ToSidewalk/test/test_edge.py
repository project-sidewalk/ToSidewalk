import unittest
from ToSidewalk.edge import Edge
from ToSidewalk.node import Node
from ToSidewalk.path import Path


class TestEdgeMethods(unittest.TestCase):

    def test_distance(self):
        node1 = Node(0, 0, 0)
        node2 = Node(1, 1, 0)
        node3 = Node(2, 0, 1)
        node4 = Node(3, 1, 1)
        edge1 = Edge(node1, node2)
        edge2 = Edge(node3, node4)

        self.assertEqual(edge1.distance(edge2), 1.)

    def test_same_path(self):
        node1 = Node(0, 0, 0)
        node2 = Node(1, 1, 0)
        node3 = Node(2, 0, 1)
        node4 = Node(3, 1, 1)
        edge1 = Edge(node1, node2)
        edge2 = Edge(node2, node4)
        edge3 = Edge(node1, node3)
        edge4 = Edge(node3, node4)
        path1 = Path(0, [edge1, edge2])
        path2 = Path(1, [edge3, edge4])

        self.assertTrue(Edge.same_path(edge1, edge2))
        self.assertFalse(Edge.same_path(edge1, edge3))

    def test_parallel(self):
        node1 = Node(0, 0, 0)
        node2 = Node(1, 1, 0)
        node3 = Node(2, 0, 1)
        node4 = Node(3, 1, 1)
        edge1 = Edge(node1, node2)
        edge2 = Edge(node2, node4)
        edge3 = Edge(node1, node3)
        edge4 = Edge(node3, node4)

        self.assertFalse(Edge.parallel(edge1, edge2))
        self.assertTrue(Edge.parallel(edge1, edge4))

    def test_connected(self):
        node1 = Node(0, 0, 0)
        node2 = Node(1, 1, 0)
        node3 = Node(2, 0, 1)
        node4 = Node(3, 1, 1)
        edge1 = Edge(node1, node2)
        edge2 = Edge(node1, node4)
        edge3 = Edge(node3, node4)
        # edge2 = Edge(node2, node4)
        # edge3 = Edge(node1, node3)
        # edge4 = Edge(node3, node4)

        self.assertTrue(Edge.connected(edge1, edge2))
        self.assertFalse(Edge.connected(edge1, edge3))


    def test_angle(self):
        import math
        node1 = Node(0, 0, 0)
        node2 = Node(1, 1, 0)
        node3 = Node(2, 0, 1)
        node4 = Node(3, 1, 1)
        edge1 = Edge(node1, node2)
        edge2 = Edge(node1, node4)
        edge3 = Edge(node4, node1)

        self.assertAlmostEqual(45., math.degrees(Edge.angle(edge1, edge2)))
        self.assertAlmostEqual(45., math.degrees(Edge.angle(edge1, edge3)))
if __name__ == '__main__':
    unittest.main()
