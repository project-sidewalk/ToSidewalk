import math
import numpy as np
import os
from shapely.geometry import LineString, Polygon
from utilities import latlng_offset_size


class Edge(LineString):
    unique_id_counter = 0

    def __init__(self, source, target, eid=None):
        if os.name == 'posix':
            # Need this because Shapely 1.3 for OS X has different constructor for LineString.
            super(Edge, self).__init__([(source.lng, source.lat), (target.lng, target.lat)])
        else:
            super(Edge, self).__init__([source, target])

        self.source = source
        self.target = target
        source.append_edge(self)
        target.append_edge(self)
        if eid:
            self._id = eid
        else:
            self._id = self.get_uid()

    def copy(self):
        return Edge(self.source, self.target)

    @staticmethod
    def angle(edge1, edge2):
        """
        Angle between two edges that are connected to each other

        :param edge1:
        :param edge2:
        :return:
        """
        assert edge1 != edge2
        assert Edge.connected(edge1, edge2)

        # vec_edge1 = edge1.vector(normalize=True)
        # vec_edge2 = edge2.vector(normalize=True)
        if edge1.source == edge2.source or edge1.target == edge2.target:
            vec_edge1 = edge1.vector(normalize=True)
            vec_edge2 = edge2.vector(normalize=True)
        else:
            vec_edge1 = edge1.vector(normalize=True)
            vec_edge2 = edge2.target.vector_to(edge2.source, normalize=True)

        cosine = np.dot(vec_edge1, vec_edge2)
        return math.acos(cosine)

    @staticmethod
    def connected(edge1, edge2):
        """
        Check if two edges are connected
        :param edge1:
        :param edge2:
        :return:
        """
        return len({edge1.source, edge1.target, edge2.source, edge2.target}) == 3  # One and only one shared node

    @staticmethod
    def parallel(edge1, edge2, angle_threshold=10.):
        """
        Assess if two edges are parallel or not.

        :param edge1:
        :param edge2:
        :param angle_threshold: Angle in degrees
        :return:
        """
        assert edge1 != edge2

        vec_edge1 = edge1.vector(normalize=True)
        vec_edge2 = edge2.vector(normalize=True)

        cosine = np.dot(vec_edge1, vec_edge2)
        cosine_threshold = math.cos(math.radians(angle_threshold))
        return abs(cosine) > abs(cosine_threshold)

    @staticmethod
    def same_path(edge1, edge2):
        """
        Assess if two edges belong to a same path
        :param edge1:
        :param edge2:
        :return:
        """
        assert hasattr(edge1, 'path') and hasattr(edge2, 'path')
        return edge1.path == edge2.path

    @staticmethod
    def overlap(edge1, edge2, distance=15., relative=False):
        """
        Return the area overlap between two edges after expanding them.
        :param edge1:
        :param edge2:
        :param distance:
        :param relative:
        :return:
        """
        poly1 = edge1.expand(distance)
        poly2 = edge2.expand(distance)
        intersection_area = poly1.intersection(poly2).area

        if relative:
            return max(intersection_area / poly1.area, intersection_area / poly2.area)
        else:
            return intersection_area

    def expand(self, distance=15.):
        """
        Return a polygon after expanding this polygon
        :param edge1:
        :param distance:
        :return:
        """
        vector = self.vector(normalize=True)
        perpendicular = np.array([vector[1], -vector[0]])
        d = latlng_offset_size(self.source.lat, vector=perpendicular, distance=distance)

        p1 = self.source.vector() + perpendicular * distance
        p2 = self.target.vector() + perpendicular * distance
        p3 = self.target.vector() - perpendicular * distance
        p4 = self.source.vector() - perpendicular * distance

        return Polygon([p1, p2, p3, p4])

    def vector(self, normalize=False):
        """
        Return a vector from the source node to the target node
        :param normalize:
        :return:
        """
        return self.source.vector_to(self.target, normalize=normalize)

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
        return (self.__class__, (self.source, self.target, self.id))

    # def __eq__(self, other):
    #     sup_eq = super(Edge, self).__eq__(self, other)
    #     return sup_eq and id(self) == id(other)

if __name__ == "__main__":
    from node import Node
    source = Node(0, 0., 0.)
    target = Node(1, 10., 10.)
    edge = Edge(source, target)

    import pickle
    p = pickle.dumps(edge)
    edge = pickle.loads(p)
    print edge