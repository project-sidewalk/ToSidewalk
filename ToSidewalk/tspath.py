from types import *
from edge import Edge
from shapely.geometry import MultiLineString, mapping


class TSPath(object):
    def __init__(self, id, edges):
        self.id = id
        self.edges = edges
        for edge in self.edges:
            edge.path = self

        self.way_type = None
        self.tags = []

    @staticmethod
    def copy_properties(path1, path2):
        """
        Copy non-geometric properties of path1 to path2
        :param path1:
        :param path2:
        :return:
        """
        path2.way_type = path1.way_type
        path2.tags = list(path1.tags)
        path2.osm_ids = list(path1.osm_ids)

    @property
    def edges(self):
        return self._edges

    @property
    def osm_ids(self):
        if not hasattr(self, '_osm_ids'):
            self._osm_ids = []
        return self._osm_ids

    @property
    def multi_line_string(self):
        return MultiLineString(self.edges)

    @property
    def geojson_feature(self):
        feature = dict()
        feature['type'] = 'Feature'
        feature['id'] = '%s' % (self.id)
        feature['properties'] = {}
        feature['geometry'] = mapping(self.multi_line_string)
        return feature

    @edges.setter
    def edges(self, edges):
        self._edges = edges

    @osm_ids.setter
    def osm_ids(self, ids):
        assert type(ids) == ListType
        self._osm_ids = ids

    def remove_edge(self, edge):
        """
        This method should be called from
        :param edge:
        :return:
        """
        edge.source.edges.remove(edge)
        edge.target.edges.remove(edge)
        self.edges.remove(edge)

    def get_nodes(self):
        """
        Returns all the nodes in this path in topologically ordered manner

        :return:
        """
        assert len(self.edges) > 0
        if len(self.edges) == 1:
            return [self.edges[0].source, self.edges[0].target]
        else:
            second_node = list({self.edges[0].source, self.edges[0].target} & {self.edges[1].source, self.edges[1].target})[0]
            if self.edges[0].target == second_node:
                nodes = [self.edges[0].source, self.edges[0].target]
            else:
                nodes = [self.edges[0].target, self.edges[0].source]

            for edge in self.edges[1:]:
                if nodes[-1] == edge.source:
                    nodes.append(edge.target)
                else:
                    nodes.append(edge.source)
            return nodes

    def merge_edges(self, edge1, edge2):
        """
        Merge two edges in this path
        :param edge1:
        :param edge2:
        :return:
        """
        assert len(self.edges) > 1
        assert edge1 in self.edges
        assert edge2 in self.edges
        assert edge1 != edge2

        if {edge1.source, edge1.target} == {edge2.source, edge2.target}:
            new_edge = Edge(edge1.source, edge1.target)
        else:
            num_shared_nodes = len({edge1.source, edge1.target} & {edge2.source, edge2.target})
            assert num_shared_nodes == 1 or num_shared_nodes == 2

            shared_node = list({edge1.source, edge1.target} & {edge2.source, edge2.target})[0]
            if edge1.source == shared_node:
                node1 = edge1.target
            else:
                node1 = edge1.source
            if edge2.source == shared_node:
                node2 = edge2.target
            else:
                node2 = edge2.source
            new_edge = Edge(node1, node2)

        new_edge.path = self
        self.edges.insert(self.edges.index(edge1), new_edge)

        # Clean up
        edge1.source.remove_edge(edge1)
        edge1.target.remove_edge(edge1)
        edge2.source.remove_edge(edge2)
        edge2.target.remove_edge(edge2)
        edge1.path = None
        edge2.path = None

        self.edges.remove(edge1)
        self.edges.remove(edge2)
        return new_edge

    def remove_node(self, node):
        """
        This method removes a node from a path. This method should be called from GeometricGraph's method only.

        :param node:
        :return:
        """
        assert len(self.edges) > 1

        nodes = self.get_nodes()
        if node == nodes[0]:
            self.remove_edge(self.edges[0])
        elif node == nodes[-1]:
            self.remove_edge(self.edges[-1])
        else:
            idx = nodes.index(node)
            new_edge = Edge(nodes[idx - 1], nodes[idx + 1])
            new_edge.path = self
            new_edges = self.edges[:idx - 1] + [new_edge] + self.edges[idx + 1:]
            self.remove_edge(self.edges[idx])
            self.edges = new_edges

    def to_string(self):
        """
        Returns a st

        :return:
        """
        return_string = ""
        for node in self.get_nodes():
            return_string += "%s,%s\n" % (node.lat, node.lng)
        return return_string

    def split_edges(self, edge_index):
        assert edge_index >= 0 or edge_index < len(self.edges)
        return self.edges[:edge_index], self.edges[edge_index + 1:]

    def __reduce__(self):
        return (self.__class__, (self.id, self.edges))