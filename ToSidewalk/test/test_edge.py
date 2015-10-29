import unittest
from ToSidewalk.edge import *
from ToSidewalk.node import *


class TestEdgeMethods(unittest.TestCase):

    def test_distance(self):
        node1 = Node(0, 0, 0)
        node2 = Node(1, 1, 0)
        node3 = Node(2, 0, 1)
        node4 = Node(3, 1, 1)
        edge1 = Edge(node1, node2)
        edge2 = Edge(node3, node4)

        self.assertEqual(edge1.distance(edge2), 1.)

if __name__ == '__main__':
    unittest.main()
