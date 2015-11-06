import unittest
import math
from ToSidewalk.latlng import *


class TestLatLngMethods(unittest.TestCase):

    def test_angle_to(self):
        self.assertAlmostEqual(LatLng(0, 0).angle_to(LatLng(1, 1)), math.atan2(1, 1))

    def test_distance(self):
        self.assertAlmostEqual(LatLng(0, 0).distance(LatLng(1, 1)), math.sqrt(2))

    def test_haversine(self):
        """
        Haversine ground truth is from:
        http://andrew.hedges.name/experiments/haversine/
        """
        latlng1 = [38.898556, -77.037852]
        latlng2 = [38.897147, -77.043934]
        latlng1 = [math.radians(x) for x in latlng1]
        latlng2 = [math.radians(x) for x in latlng2]

        distance = 549
        error = abs(distance - haversine(latlng1[1], latlng1[0], latlng2[1], latlng2[0]))
        self.assertTrue(error < 1)  # Error should be below 1m

        latlng1 = [38.900665, -76.983008]
        latlng2 = [38.9007234, -76.98197]
        latlng1 = [math.radians(x) for x in latlng1]
        latlng2 = [math.radians(x) for x in latlng2]
        distance = 90

        error = abs(distance - haversine(latlng1[1], latlng1[0], latlng2[1], latlng2[0]))
        self.assertTrue(error < 1)  # Error should be below 1m

    def test_equal(self):
        latlng1 = [38.898556, -77.037852]
        latlng2 = [38.897147, -77.043934]
        latlng3 = [38.898556, -77.037852]
        latlng1 = [math.radians(x) for x in latlng1]
        latlng2 = [math.radians(x) for x in latlng2]
        latlng3 = [math.radians(x) for x in latlng3]

        coord1 = LatLng(latlng1[0], latlng1[1])
        coord2 = LatLng(latlng2[0], latlng2[1])
        coord3 = LatLng(latlng3[0], latlng3[1])
        self.assertFalse(coord1 == coord2)
        self.assertTrue(coord1 == coord3)

    def test_vector_to(self):
        latlng1 = [38.898556, -77.037852]
        latlng2 = [38.897147, -77.043934]
        latlng3 = [38.898556, -77.037852]
        coord1 = LatLng(latlng1[0], latlng1[1])
        coord2 = LatLng(latlng2[0], latlng2[1])
        coord3 = LatLng(latlng3[0], latlng3[1])

        self.assertTrue(np.array_equal(coord1.vector_to(coord2), np.array(latlng2) - np.array(latlng1)))
        self.assertFalse(np.array_equal(coord1.vector_to(coord3), np.array(latlng2) - np.array(latlng1)))

if __name__ == '__main__':
    unittest.main()
