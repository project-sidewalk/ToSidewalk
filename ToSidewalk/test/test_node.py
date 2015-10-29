import unittest
from ToSidewalk.node import *
from ToSidewalk.edge import *


class TestNodeMethods(unittest.TestCase):
    def test_get_edges(self):
        node1 = Node(0, 0, 0)
        node2 = Node(1, 1, 0)
        edge1 = Edge(node1, node2)

        self.assertIn(edge1, node1.edges)
        self.assertIn(edge1, node2.edges)

if __name__ == '__main__':
    unittest.main()
