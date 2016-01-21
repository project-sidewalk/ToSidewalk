from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, MetaData
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

import db
meta = MetaData(schema="sidewalk")
Base = declarative_base(metadata=meta)


class AuditTaskInteractionTable(Base):
    """
    Mapping to the street_edge table.
    """
    __tablename__ = "audit_task_interaction"
    __table_args__ = {'schema': 'sidewalk'}

    audit_task_interaction_id = Column(Integer, primary_key=True, name="audit_task_interaction_id")
    audit_task_id = Column(Integer, name="audit_task_id")
    action = Column(String, name="action")
    gsv_panorama_id = Column(String, name="gsv_panorama_id")
    lat = Column(Float, name="lat")
    lng = Column(Float, name="lng")
    heading = Column(Float, name="heading")
    pitch = Column(Float, name="pitch")
    zoom = Column(Integer, name="zoom")
    note = Column(String, name="note")
    timestamp = Column(TIMESTAMP, name="timestamp")
    temporary_label_id = Column(Integer, name="temporary_label_id")

if __name__ == "__main__":
    from itertools import groupby
    from pandas import Series
    database = db.DB("../../.settings")
    session = database.session
    query = session.query(AuditTaskInteractionTable)  # .filter(AuditTaskInteractionTable.action="TaskStart")
    records = [(record.audit_task_id, record.action, record.timestamp) for record in query]
    records = sorted(records, key=lambda x: (x[0], x[2]))

    times = []
    for key, values in groupby(records, lambda x: x[0]):
        l = list(values)
        times.append((l[-1][2] - l[0][2]).seconds)

    print(sum(times))
    print(Series(times).describe())
