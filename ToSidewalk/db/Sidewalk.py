from sqlalchemy import Column, Integer, String, Float, Boolean, TIMESTAMP
from geoalchemy2 import Geometry
import db


class SidewalkEdgeTable(db.Base):
    """
    Mapping to the sidewalk_edge table.
    """
    __tablename__ = "sidewalk_edge"
    sidewalk_edge_id = Column(Integer, primary_key=True, name="sidewalk_edge_id")
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


if __name__ == "__main__":
    print("Sidewalk.py")