import ogr
import osr
import shapefile


def convert_spatial_reference_system(coordinates, source_epsg, target_epsg):
    """
    This method takes a list of (x, y) coordinates and project it from one spatial reference system
    to another (e.g., EPSG 102010 to EPSG 4326).

    References:
    * http://gis.stackexchange.com/questions/78838/how-to-convert-projected-coordinates-to-lat-lon-using-python
    * http://gis.stackexchange.com/questions/52500/is-there-any-online-tool-for-converting-coordinates-between-different-epsg

    :param coordinates: A list of (x, y) coordinates (e.g., [(x1, y1), (x2, y2), ...]
    :param source_epsg: A source EPSG spatial reference system (e.g., 102010)
    :param target_epsg: A target EPSG spatial refeerence system (e.g., 4326)
    :return:
    """
    source_spatial_reference = osr.SpatialReference()
    source_spatial_reference.ImportFromEPSG(source_epsg)
    target_spatial_reference = osr.SpatialReference()
    target_spatial_reference.ImportFromEPSG(target_epsg)
    coordinate_transformation = osr.CoordinateTransformation(source_spatial_reference, target_spatial_reference)

    transformed_coordinates = []
    for coordinate in coordinates:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(coordinate[0], coordinate[1])
        point.Transform(coordinate_transformation)
        transformed_coordinates.append((point.GetX(), point.GetY()))
    return transformed_coordinates


def shape2osm(filename, source_epsg=None, target_epsg=None):
    """
    """
    sf = shapefile.Reader(filename)
    shapes = zip(sf.shapes(), sf.records())
    for shape, record in shapes:
        if source_epsg and target_epsg:
            points = convert_spatial_reference_system(shape.points, source_epsg, target_epsg)
        else:
            points = shape.points

    # Todo. Export the data to OSM


if __name__ == "__main__":
    filename = "../resources/DC_IntersectedWithTheCityBoundary/DCLength.shp"
    shape2osm(filename, source_epsg=102010, target_epsg=4326)