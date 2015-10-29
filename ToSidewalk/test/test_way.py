import unittest
from ToSidewalk.node import *
from ToSidewalk.edge import *
from ToSidewalk.path import *
from ToSidewalk.utilities import window


class TestPathMethods(unittest.TestCase):

    def test_distance(self):
        nodes1 = [Node(x, lat=0, lng=x) for x in range(10)]
        nodes2 = [Node(x, lat=1, lng=x) for x in range(10)]
        edges1 = [Edge(source, target) for source, target in window(nodes1, 2)]
        edges2 = [Edge(source, target) for source, target in window(nodes2, 2)]
        path1 = Path(0, edges1)
        path2 = Path(1, edges2)

        self.assertEqual(path1.distance(path2), 1)

    def test_edges(self):
        nodes1 = [Node(x, lat=0, lng=x) for x in range(10)]

        edges1 = [Edge(source, target) for source, target in window(nodes1, 2)]
        path = Path(0, edges1)

        for e1, e2 in zip(path.edges, edges1):
            self.assertEqual(e1, e2)

if __name__ == '__main__':
    unittest.main()
