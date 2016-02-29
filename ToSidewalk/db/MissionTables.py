from sqlalchemy import Column, Integer, String
import db


class MissionTable(db.Base):
    """
    Mapping to the sidewalk_edge table.
    """
    __tablename__ = "mission"
    mission_id = Column(Integer, primary_key=True, name="mission_id")
    region_id = Column(Integer, name="region_id")
    mission = Column(String, name="mission")
    level = Column(Integer, name="level")
    description = Column(String, name="description")

if __name__ == "__main__":
    print("MissionTables.py")