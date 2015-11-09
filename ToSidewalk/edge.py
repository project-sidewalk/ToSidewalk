import os
from shapely.geometry import LineString


class Edge(LineString):
    unique_id_counter = 0

    def __init__(self, source, target):
        if os.name == 'posix':
            # Need this because Shapely 1.3 for OS X has different constructor for LineString.
            super(Edge, self).__init__([(source.lng, source.lat), (target.lng, target.lat)])
        else:
            super(Edge, self).__init__([source, target])

        self.source = source
        self.target = target
        source.append_edge(self)
        target.append_edge(self)
        self._id = self.get_uid()

    @classmethod
    def get_uid(cls):
        cls.unique_id_counter += 1
        return cls.unique_id_counter

    @property
    def id(self):
        return self._id

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, p):
        self._path = p

    def get_length(self, in_meters=False):
        if in_meters:
            return self.source.distance_in_meters(self.target)
        else:
            return self.length

    def __reduce__(self):
        return (self.__class__, (self.source, self.target))

if __name__ == "__main__":
    from node import Node
    source = Node(0, 0., 0.)
    target = Node(1, 10., 10.)
    edge = Edge(source, target)

    import pickle
    p = pickle.dumps(edge)
    edge = pickle.loads(p)
    print edge