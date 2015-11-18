from sqlalchemy import Column, Integer, String, Float, Boolean, TIMESTAMP, BIGINT
from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, MetaData
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

import db
meta = MetaData(schema="sidewalk")
Base = declarative_base(metadata=meta)


class RegionTypeTable(Base):
    __tablename__ = "region_type"
    region_type_id = Column(Integer, primary_key=True, name="region_type_id")
    region_type = Column(String, name="region_type")


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

if __name__ == "__main__":
    pass