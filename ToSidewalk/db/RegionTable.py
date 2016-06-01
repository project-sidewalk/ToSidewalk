from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, MetaData, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

import db
import fiona
import shapefile

meta = MetaData(schema="sidewalk")
Base = declarative_base(metadata=meta)


class RegionPropertyTable(Base):
    __tablename__ = "region_property"
    region_property_id = Column(Integer, primary_key=True, name="region_property_id")
    region_id = Column(Integer, name="region_id")
    key = Column(String, name="key")
    value = Column(String, name="value")

    def __repr__(self):
        return "RegionProperty(region_property_id=%s, region_id=%s, key=%s, value=%s)" % (self.region_property_id, self.region_id, self.key, self.value)

    @classmethod
    def add_region_property(cls, session, region_property):
        session.add(region_property)
        session.commit()

    @classmethod
    def add_region_properties(cls, session, region_properties):
        for region_property in region_properties:
            session.add(region_property)
        session.commit()


class RegionTypeTable(Base):
    __tablename__ = "region_type"
    region_type_id = Column(Integer, primary_key=True, name="region_type_id")
    region_type = Column(String, name="region_type")

    def __repr__(self):
        return "RegionType(region_type_id=%s, region_type=%s)" % (self.region_type_id, self.region_type)

    @classmethod
    def list(cls, session):
        """
        List records of region types

        :param session:
        :return:
        """
        return [record for record in session.query(cls)]


class RegionTable(Base):
    """
    Mapping to the street_edge table.
    """
    __tablename__ = "region"
    __table_args__ = {'schema': 'sidewalk'}

    region_id = Column(Integer, primary_key=True, name="region_id")
    region_type_id = Column(Integer, ForeignKey('region_type.region_type_id'), name="region_type_id")
    description = Column(String, name="description")
    data_source = Column(String, name="data_source")
    geom = Column(Geometry("Polygon", srid=4326), name="geom")

    def __repr__(self):
        return "Region(region_id=%s, region_type_id=%s, description=%s, data_source=%s, geom=%s)" % \
               (self.region_id, self.region_type_id, self.description, self.data_source, self.geom)

    @classmethod
    def list(cls, session):
        query = session.query(cls)
        return [record for record in query]

    @classmethod
    def list_region_of_type(cls, session, type):
        region_type = session.query(RegionTypeTable).filter_by(region_type=type).first()
        return [record for record in session.query(cls).filter_by(region_type_id=region_type.region_type_id).order_by(cls.region_id)]

    @classmethod
    def add_region(cls, session, region):
        session.add(region)
        session.commit()

    @classmethod
    def add_regions(cls, session, regions):
        for region in regions:
            session.add(region)
        session.commit()


def import_dc_neighborhood(session):
    #
    # sf = shapefile.Reader(resource_file_dir)
    # shapes = sf.shapes()
    # Insert data

    # http://gis.stackexchange.com/questions/70591/creating-shapely-multipolygons-from-shape-file-multipolygons
    from shapely.geometry import shape
    from geoalchemy2.shape import from_shape

    regions = []
    resource_file_dir = "../../resources/Census_Tracts__2010/Census_Tracts__2010.shp"
    region_type_id = 2  # "neighborhood"
    data_source = "http://opendata.dc.gov/datasets/6969dd63c5cb4d6aa32f15effb8311f3_8"
    with fiona.open(resource_file_dir) as shp:
        for feature in shp:
            polygon = shape(feature["geometry"])
            wkb_element = from_shape(polygon, srid=4326)
            description = feature["properties"]["TRACT"]
            region = RegionTable(region_type_id=region_type_id, description=description, data_source=data_source, geom=wkb_element)
            regions.append(region)

    RegionTable.add_regions(session, regions)


def import_neighborhood_names(session):
    region_names = []
    with fiona.open("../../resources/tract_centroid/tract_centroid_with_name.shp") as shp:

        for feature in shp:
            region_id = int(feature['properties']['region_id'])
            neighborhood_name = feature['properties']['tract_cent']
            region_property = RegionPropertyTable(region_id=region_id, key="Neighborhood Name", value=neighborhood_name)
            region_names.append(region_property)

    RegionPropertyTable.add_region_properties(session, region_names)


if __name__ == "__main__":
    database = db.DB("../../.settings")
    session = database.session

    # import_dc_neighborhood(session)
    # import_neighborhood_names(session)

    # regions = RegionTable.list_region_of_type(session, "neighborhood")


