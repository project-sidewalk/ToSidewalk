from RegionTable import *
import shapefile


def import_dc_neighborhood():
    database = db.DB("../../.settings")
    region_table = RegionTable.__table__
    session = database.session
    connection = database.engine.connect()

    resource_file_dir = "../../resources/DCNeighborhood/Neighborhood_Composition/Neighborhood_Composition.shp"
    sf = shapefile.Reader(resource_file_dir)
    shapes = sf.shapes()

    # Insert data
    region_type_id = 2  # "neighborhood"
    data_source = "http://opendata.dc.gov/datasets/a0225495cda9411db0373a1db40a64d5_21"
    with connection.begin() as transaction:
        for i, shape in enumerate(shapes):
            polygon_string = "POLYGON((" + ",".join(["%f %f" % (coord[0], coord[1]) for coord in shape.points]) + \
                             ",%f %f" % (shape.points[0][0], shape.points[0][1]) + "))"
            ins = region_table.insert().values(region_id=i,
                                               region_type_id=region_type_id,
                                               description="DC Neighborhood Composition",
                                               data_source=data_source,
                                               geom=polygon_string)
            connection.execute(ins)
        transaction.commit()


    # session = database.session
    # query = session.query(RegionTypeTable)
    # for item in query:
    #     print item.region_type_id, item.region_type
#
# SELECT * FROM region
# WHERE (region_id = 85 OR region_id = 73 OR region_id = 105 OR region_id = 97)

if __name__ == "__main__":
    import_dc_neighborhood()
