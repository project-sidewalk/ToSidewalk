from sqlalchemy import Column, Integer, String, Float, Boolean, TIMESTAMP, BIGINT
from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

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

    # http://docs.sqlalchemy.org/en/rel_1_0/orm/basic_relationships.html
    street_edge_assignment_count = relationship("StreetEdgeAssignmentCountTable", uselist=False, backref="street_edge")


class StreetEdgeParentEdgeTable(db.Base):
    """
    Mapping to the street_edge_parent_edge table.
    """
    __tablename__ = "street_edge_parent_edge"
    street_edge_parent_edge_id = Column(Integer, primary_key=True, name="street_edge_parent_edge_id")
    street_edge_id = Column(BIGINT, ForeignKey('street_edge.street_edge_id'), name="street_edge_id")
    parent_edge_id = Column(BIGINT, ForeignKey('street_edge.street_edge_id'), name="parent_edge_id")


class StreetEdgeStreetNodeTable(db.Base):
    """
    Mapping to the street_edge_street_node table.
    """
    __tablename__ = "street_edge_street_node"
    street_edge_street_node_id = Column(Integer, primary_key=True, name="street_edge_street_node_id")
    street_edge_id = Column(BIGINT, ForeignKey('street_edge.street_edge_id'), name="street_edge_id")
    street_node_id = Column(BIGINT, ForeignKey('street_node.street_node_id'), name="street_node_id")


class StreetNodeTable(db.Base):
    """
    Mapping to the street_node table.
    """
    __tablename__ = "street_node"
    street_edge_id = Column(Integer, primary_key=True, name="street_node_id")
    geom = Column(Geometry("Point", srid=4326), name="geom")
    lat = Column(Float, name="lat")
    lng = Column(Float, name="lng")


class StreetEdgeAssignmentCountTable(db.Base):
    """
    Mapping to the street_edge_assignment_count
    """
    __tablename__ = "street_edge_assignment_count"
    street_edge_assignment_count_id = Column(Integer, primary_key=True, name="street_edge_assignment_count_id")
    street_edge_id = Column(Integer, ForeignKey('street_edge.street_edge_id'), name="street_edge_id")
    assignment_count = Column(Integer, name="assignment_count")
    completion_count = Column(Integer, name="completion_count")


if __name__ == "__main__":
    database = db.DB("../../.settings")
    session = database.session
    query = session.query(StreetEdgeTable).filter_by(deleted=False)
    for item in query:
        print item.street_edge_id, item.x1, item.y1
