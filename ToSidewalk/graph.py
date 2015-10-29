from node import Node
from edge import Edge
from path import Path
from utilities import window
from types import *


class GeometricGraph(object):
    def __init__(self):
        self.nodes = {}
        self.paths = {}
        self.node_id_counter = 0
        self.path_id_counter = 0

    @property
    def nodes(self):
        return self._nodes

    @property
    def paths(self):
        return self._paths

    @nodes.setter
    def nodes(self, n):
        self._nodes = n

    @paths.setter
    def paths(self, p):
        self._paths = p

    def create_node(self, x, y, id=None):
        """
        This method creates a new node.

        :param lng:
        :param lat:
        :param id:
        :return:
        """
        if not id:
            id = self.node_id_counter
            self.node_id_counter += 1

        assert type(x) == FloatType
        assert type(y) == FloatType
        assert type(id) == IntType or type(id) == LongType
        self.nodes[id] = Node(id, y, x)
        return self.nodes[id]

    def create_path(self, nodes, id=None):
        """
        This method creates a new path.

        :param nodes:
        :param id:
        :return:
        """
        if not id:
            id = self.path_id_counter
            self.path_id_counter += 1
        edges = [Edge(source, target) for source, target in window(nodes, 2)]
        self.paths[id] = Path(id, edges)
        return self.paths[id]

    def get_node(self, node_id):
        """
        This method returns a node object with a given id.

        :param node_id:
        :return:
        """
        return self.nodes[node_id]

    def get_path(self, path_id):
        """
        This method returns a path object with a given id.

        :param path_id:
        :return:
        """
        return self.paths[path_id]

    def get_adjacent_nodes(self, node):
        """
        This method returns a set of nodes that are connected to the given node.

        :param node:
        :return:
        """
        nodes = []
        for edge in node.edges:
            if node == edge.source:
                nodes.append(edge.target)
            else:
                nodes.append(edge.source)
        return nodes

    def remove_node(self, node_id):
        """
        Remove a node from the graph

        :param node_id: Node id
        """
        node = self.get_node(node_id)
        connected_edges = node.edges
        connected_paths = set(map(lambda e: e.path, connected_edges))
        for path in connected_paths:
            if len(path.edges) == 1:
                self.remove_path(path)
            else:
                path.remove_node(node)

        if node_id in self.nodes:
            del self.nodes[node_id]

    def remove_path(self, path_id):
        """
        Remove a path
        :param path_id:
        :return:
        """
        path = self.get_path(path_id)
        edges = path.edges
        nodes = path.get_nodes()
        for edge in edges:
            edge.source.edges.remove(edge)
            edge.target.edges.remove(edge)

        for node in nodes:
            if len(node.edges) == 0:
                del self.nodes[int(node.id)]

        del self.paths[path_id]


def parse_osm(filename):
    """
    Parse an OSM file
    """
    from xml.etree import cElementTree as ET
    import logging as log
    with open(filename, "rb") as osm:
        # Find element
        # http://stackoverflow.com/questions/222375/elementtree-xpath-select-element-based-on-attribute
        tree = ET.parse(osm)
        nodes_tree = tree.findall(".//node")
        ways_tree = tree.findall(".//way")
        bounds_elem = tree.find(".//bounds")
        bounds = [bounds_elem.get("minlat"), bounds_elem.get("minlon"), bounds_elem.get("maxlat"), bounds_elem.get("maxlon")]

    log.debug("Start parsing the file: %s" % filename)
    geometric_graph = GeometricGraph()

    valid_highways = {'primary', 'secondary', 'tertiary', 'residential'}
    for node in nodes_tree:
        try:
            geometric_graph.create_node(x=float(node.get("lon")), y=float(node.get("lat")), id=int(node.get("id")))
        except AssertionError as e:
            print "Assertion Error"

    # Parse ways
    for way in ways_tree:
        highway_tag = way.find(".//tag[@k='highway']")
        if highway_tag is not None and highway_tag.get("v") in valid_highways:
            node_elements = filter(lambda elem: elem.tag == "nd", list(way))
            nodes = [geometric_graph.get_node(int(element.get("ref"))) for element in node_elements]
            path = geometric_graph.create_path(nodes, int(way.get("id")))
            path.way_type = highway_tag.get('v')
            for tag in way.findall('tag'):
                if tag.attrib['k'] != "highway":
                    path.tags.append(tag.attrib)

    return geometric_graph


if __name__ == "__main__":
    filename = "../resources/SmallMap_04.osm"
    geometric_graph = parse_osm(filename)