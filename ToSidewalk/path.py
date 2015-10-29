from edge import Edge


class Path(object):
    def __init__(self, id, edges):
        self.id = id
        self.edges = edges
        for edge in self.edges:
            edge.path = self

    @property
    def edges(self):
        return self._edges

    @edges.setter
    def edges(self, edges):
        self._edges = edges

    def get_nodes(self):
        """
        Returns all the nodes in this path in topologically ordered manner

        :return:
        """
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

    def _remove_edge(self, edge):
        """
        This method should be called from
        :param edge:
        :return:
        """
        edge.source.edges.remove(edge)
        edge.target.edges.remove(edge)
        self.edges.remove(edge)

    def remove_node(self, node):
        """
        This method removes a node from a path. This method should be called from GeometricGraph's method only.

        :param node:
        :return:
        """
        assert len(self.edges) > 1

        nodes = self.get_nodes()
        if node == nodes[0]:
            self._remove_edge(self.edges[0])
        elif node == nodes[-1]:
            self._remove_edge(self.edges[-1])
        else:
            idx = nodes.index(node)
            new_edge = Edge(nodes[idx - 1], nodes[idx + 1])
            new_edge.path = self
            new_edges = self.edges[:idx - 1] + [new_edge] + self.edges[idx + 1:]
            self._remove_edge(self.edges[idx])
            self.edges = new_edges
