import unittest
from ToSidewalk.node import Node
from ToSidewalk.edge import Edge
from ToSidewalk.path import Path
from ToSidewalk.utilities import window


class TestPathMethods(unittest.TestCase):
    def test_get_nodes(self):
        nodes = [Node(i, i, 0) for i in range(10)]

        from random import shuffle
        shuffle(nodes)
        edges = [Edge(source, target) for source, target in window(nodes, 2)]
        path = Path(0, edges)

        for n1, n2 in zip(map(lambda e: e.source, path.edges), path.get_nodes()[:-1]):
            self.assertEqual(n1, n2)

if __name__ == '__main__':
    unittest.main()
