import unittest
from ToSidewalk.shape2osm import convert_spatial_reference_system


class TestLatLngMethods(unittest.TestCase):

    def test_convert_spatial_reference_system(self):
        """
        Haversine ground truth is from:
        http://andrew.hedges.name/experiments/haversine/
        """
        source_epsg = 102010
        target_epsg = 4326
        coordinates_102010 = [(1544425.2172204019, 39141.495243635756),
                              (1544473.3024991949, 39207.373681605626)]

        # converted the above coordinates using http://cs2cs.mygeodata.eu/
        coordinates_4326 = [(-76.9386616, 38.8891714),
                            (-76.9379174, 38.8896617)]

        output_coordinates = convert_spatial_reference_system(coordinates_102010, source_epsg, target_epsg)
        self.assertAlmostEqual(coordinates_4326[0][0], output_coordinates[0][0])
        self.assertAlmostEqual(coordinates_4326[0][1], output_coordinates[0][1])
        self.assertAlmostEqual(coordinates_4326[1][0], output_coordinates[1][0])
        self.assertAlmostEqual(coordinates_4326[1][1], output_coordinates[1][1])


if __name__ == '__main__':
    unittest.main()
