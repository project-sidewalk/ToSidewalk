from sqlalchemy import Column, Integer, String, Float, Boolean
import db


class MissionTable(db.Base):
    __tablename__ = "mission"
    __table_args__ = {'schema': 'sidewalk'}
    mission_id = Column(Integer, primary_key=True, name="mission_id", autoincrement=True)
    region_id = Column(Integer, name="region_id")
    mission = Column(String, name="mission")
    level = Column(Float, name="level")
    # description = Column(String, name="description")
    deleted = Column(Boolean, name="deleted", default=False)

    def __repr__(self):
        return "Mission(mission_id=%s, region_id=%s, mission=%s, level=%s, description=%s)" % \
               (self.mission_id, self.region_id, self.mission, self.level, self.description)

    @classmethod
    def list(cls, session):
        """
        Returns a list of records in the mission table

        :param session:
        :return:
        """
        query = session.query(cls)
        return [record for record in query]

    @classmethod
    def add_mission(cls, session, mission):
        """
        Add a record of a new mission to the table
        E.g., MissionTable.add_mission(session, MissionTable(region_id=None, mission="Test", level=1, description="Test"))

        :param session:
        :param mission:
        :return:
        """
        session.add(mission)
        session.commit()

    @classmethod
    def add_missions(cls, session, missions):
        """
        Add a group of new missions to the table.

        :param session:
        :param missions:
        :return:
        """
        for mission in missions:
            session.add(mission)
        session.commit()


if __name__ == "__main__":
    print("MissionTables.py")
    database = db.DB("../../.settings")
    session = database.session

    for mission in MissionTable.list(session):
        print mission
