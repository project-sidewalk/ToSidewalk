from shapely.geometry import LineString


class Edge(LineString):
    def __init__(self, source, target):
        super(Edge, self).__init__([source, target])
        self.source = source
        self.target = target
        source.append_edge(self)
        target.append_edge(self)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, p):
        self._path = p
