from ToSidewalk.db.db import DB
from ToSidewalk.db.MissionTables import MissionTable
from ToSidewalk.db.RegionTable import RegionTable


def populate_missions(session):
    mission_types = {
        "initial-mission": {
            "id": "initial-mission",
            "levels": [1],
            "distances": [250],  # meters (m)
            "coverages": [None]
        },
        "distance-mission": {
            "id": "distance-mission",
            "levels": [1, 2, 3, 4, 5, 6, 7],
            "distances": [500, 1000, 2500, 5000, 10000, 15000, 20000],  # meters (m)
            "coverages": [None, None, None, None, None, None, None]
        },
        "area-coverage-mission": {
            "id": "area-coverage-mission",
            "levels": [1, 2, 3, 4],
            "distances": [None, None, None, None],
            "coverages": [25, 50, 75, 100]  # percentages (%)
        }
    }

    # Populate missions
    missions = []
    missions.append(MissionTable(label="initial-mission", level=1, distance=250))
    for record in RegionTable.list_region_of_type(session, "neighborhood"):
        for level, distance, coverage in zip(mission_types["distance-mission"]["levels"], mission_types["distance-mission"]["distances"], mission_types["distance-mission"]["coverages"]):
            mission = MissionTable(region_id=record.region_id, label="distance-mission", level=level, distance=distance, coverage=coverage)
            missions.append(mission)

        for level, distance, coverage in zip(mission_types["area-coverage-mission"]["levels"], mission_types["area-coverage-mission"]["distances"], mission_types["area-coverage-mission"]["coverages"]):
            mission = MissionTable(region_id=record.region_id, label="area-coverage-mission", level=level, distance=distance, coverage=coverage)
            missions.append(mission)
    MissionTable.add_missions(session, missions)


def compute_area_coverage_from_distance(session):
    """

    :param session:
    :return:
    """
    total_distance_by_region = {}

    distance_query = """SELECT SUM(ST_Length(ST_Transform(street_edge.geom, 26985))) FROM sidewalk.region
    INNER JOIN sidewalk.street_edge ON region.geom && street_edge.geom WHERE region.region_id = %s"""

    region_ids = set(map(lambda m: m.region_id, filter(lambda m: m.region_id is not None, MissionTable.list(session))))
    for region_id in region_ids:
        total_distance_by_region[region_id] = session.execute(distance_query % str(region_id)).fetchone()[0]

    # from pprint import pprint
    # pprint(total_distance_by_region)

    for mission in MissionTable.list_missions_with_label(session, "distance-mission"):
        total_distance = total_distance_by_region[mission.region_id]
        coverage = round(mission.distance / total_distance * 100, 2)

        mission.coverage = coverage
        if coverage >= 100:
            mission.deleted = True
    session.commit()


def compute_distance_from_area_coverage(session):
    total_distance_by_region = {}

    distance_query = """SELECT SUM(ST_Length(ST_Transform(street_edge.geom, 26985))) FROM sidewalk.region
    INNER JOIN sidewalk.street_edge ON region.geom && street_edge.geom WHERE region.region_id = %s"""

    region_ids = set(map(lambda m: m.region_id, filter(lambda m: m.region_id is not None, MissionTable.list(session))))
    for region_id in region_ids:
        total_distance_by_region[region_id] = session.execute(distance_query % str(region_id)).fetchone()[0]

    for mission in MissionTable.list_missions_with_label(session, "area-coverage-mission"):
        total_distance = total_distance_by_region[mission.region_id]
        distance = round(total_distance * mission.coverage / 100, 2)
        mission.distance = distance
    session.commit()

if __name__ == "__main__":
    print("MissionTables.py")
    database = DB("../../.settings")
    session = database.session
    # populate_missions(session)
    # compute_area_coverage_from_distance(session)
    # compute_distance_from_area_coverage(session)



