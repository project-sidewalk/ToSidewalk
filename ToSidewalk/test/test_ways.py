import unittest
from ToSidewalk.ways import *
from ToSidewalk.nodes import *
from ToSidewalk.network import *

class TestWayMethods(unittest.TestCase):
    def test_constructor(self):
        """
        Test the constructor
        """
        nids = [1, 2, 3]
        way = Way(-1, nids)
        self.assertNotEqual(way.id, '0')

        way = Way(0, nids)
        self.assertEqual(way.id, '0')

        way = Way(0, nids)
        self.assertTrue(way.get_node_ids()[0], nids[0])
        self.assertTrue(way.get_node_ids()[1], nids[1])
        self.assertTrue(way.get_node_ids()[2], nids[2])

    def test_belongs_to(self):
        myway = Way(None, [1, 2])
        ways = Ways()
        ways.add(myway)
        self.assertEqual(myway.belongs_to(), ways)


class TestWaysMethods(unittest.TestCase):
    def test_belongs_to(self):
        ways = Ways()
        nodes = Nodes()
        network = Network(nodes, ways)
        self.assertEqual(ways.belongs_to(), network)


class TestSidewalkMethods(unittest.TestCase):
    def test_swap_nodes(self):
        # Todo
        pass

if __name__ == '__main__':
    unittest.main()
