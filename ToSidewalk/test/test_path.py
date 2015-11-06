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

    def test_merge(self):
        nodes = [Node(i, i, 0) for i in range(10)]
        edges = [Edge(source, target) for source, target in window(nodes, 2)]
        path = Path(0, edges)

        e1 = edges[1]
        e2 = edges[2]

        new_edge = path.merge_edges(edges[1], edges[2])
        self.assertFalse(e1 in nodes[1].edges)
        self.assertFalse(e2 in nodes[2].edges)

        self.assertTrue(path == new_edge.path)

if __name__ == '__main__':
    unittest.main()
