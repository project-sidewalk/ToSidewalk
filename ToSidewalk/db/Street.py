from sqlalchemy import Column, Integer, String, Float, Boolean, TIMESTAMP
from geoalchemy2 import Geometry

import db


class StreetEdgeTable(db.Base):
    """
    Mapping to the street_edge table.
    """
    __tablename__ = "street_edge"
    street_edge_id = Column(Integer, primary_key=True, name="street_edge_id")
    geom = Column(Geometry("LineString", srid=4326), name="geom")
    x1 = Column(Float, name="x1")
    y1 = Column(Float, name="y1")
    x2 = Column(Float, name="x2")
    y2 = Column(Float, name="y2")
    way_type = Column(String, name="way_type")
    source = Column(Integer, name="source")
    target = Column(Integer, name="target")
    deleted = Column(Boolean, name="deleted")
    timestamp = Column(TIMESTAMP, name="timestamp")


class StreetEdgeParentEdgeTable(db.Base):
    """
    Mapping to the street_edge_parent_edge table.
    """
    __tablename__ = "street_edge_parent_edge"
    street_edge_id = Column(Integer, primary_key=True, name="street_edge_id")
    parent_edge_id = Column(Integer, name="parent_edge_id")


class StreetEdgeStreetNodeTable(db.Base):
    """
    Mapping to the street_edge_street_node table.
    """
    __tablename__ = "street_edge_street_node"
    street_edge_id = Column(Integer, primary_key=True, name="street_edge_id")
    street_node_id = Column(Integer, name="street_node_id")


class StreetNodeTable(db.Base):
    """
    Mapping to the street_node table.
    """
    __tablename__ = "street_node_table"
    street_edge_id = Column(Integer, primary_key=True, name="street_node_id")
    geom = Column(Geometry("Point", srid=4326), name="geom")
    lat = Column(Float, name="lat")
    lng = Column(Float, name="lng")


if __name__ == "__main__":
    database = db.DB("../../.settings")
    session = database.session
    query = session.query(StreetEdgeTable).filter_by(deleted=False)
    for item in query:
        print item.street_edge_id, item.x1, item.y1
