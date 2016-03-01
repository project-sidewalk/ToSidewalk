from ToSidewalk.db.db import DB
from ToSidewalk.db.MissionTables import MissionTable
from ToSidewalk.db.RegionTable import RegionTable


def populate_missions(session):
    mission_types = {
        "initial-mission": {
            "id": "initial-mission",
            "levels": [1]
        },
        "neighborhood-coverage-challenge": {
            "id": "neighborhood-coverage-challenge",
            "levels": [1, 2, 3]
        },
        "distance-challenge": {
            "id": "distance-challenge",
            "levels": [0.5, 1, 2.5, 5, 10, 15, 20]  # km
        },
        "area-coverage-challenge": {
            "id": "area-coverage-challenge",
            "levels": [25, 50, 75, 100]  # %
        }
    }

    # Populate missions
    missions = []
    missions.append(MissionTable(mission="initial-mission", level=1))
    missions.append(MissionTable(mission="neighborhood-coverage-challenge", level=1))
    missions.append(MissionTable(mission="neighborhood-coverage-challenge", level=2))
    missions.append(MissionTable(mission="neighborhood-coverage-challenge", level=3))
    for record in RegionTable.list_region_of_type(session, "neighborhood"):
        for level in mission_types["distance-challenge"]["levels"]:
            mission = MissionTable(region_id=record.region_id, mission="distance-challenge", level=level)
            missions.append(mission)

        for level in mission_types["area-coverage-challenge"]["levels"]:
            mission = MissionTable(region_id=record.region_id, mission="area-coverage-challenge", level=level)
            missions.append(mission)
    MissionTable.add_missions(session, missions)


if __name__ == "__main__":
    print("MissionTables.py")
    database = DB("../../.settings")
    session = database.session
    populate_missions(session)


