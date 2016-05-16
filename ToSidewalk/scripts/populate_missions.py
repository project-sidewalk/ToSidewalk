from ToSidewalk.db.db import DB
from ToSidewalk.db.MissionTables import MissionTable
from ToSidewalk.db.RegionTable import RegionTable

from pint import UnitRegistry
ureg = UnitRegistry()


def populate_missions(session, mission_label):
    """
    Populate the mission
    :param session:
    :return:
    """
    # Populate missions
    missions = []

    if mission_label == "initial-mission":
        missions.append(MissionTable(label="initial-mission", level=1, distance=304.8, distance_ft=1000, distance_mi=0.189394))
    elif mission_label == "distance-mission":
        # Get total distance in the neighborhood. Create mission for every 1 mile
        step_size = 1  # 1 mile
        neighborhood_distance_query = """SELECT SUM(ST_Length(ST_Transform(street_edge.geom, 26985))) FROM sidewalk.region
INNER JOIN sidewalk.street_edge ON ST_Intersects(region.geom, street_edge.geom) WHERE region.region_id = %s"""

        for record in RegionTable.list_region_of_type(session, "neighborhood"):
            neighborhood_total_distance_m = float(session.execute(neighborhood_distance_query % str(record.region_id)).fetchone()[0]) * ureg.meter
            neighborhood_total_distance_mi = neighborhood_total_distance_m.to(ureg.mile)
            distances = [2000 * ureg.feet, 4000 * ureg.feet] + [dist * ureg.mile for dist in range(1, int(neighborhood_total_distance_mi.magnitude), step_size)]

            for level, distance in enumerate(distances, 1):
                distance_m = distance.to(ureg.meter)
                distance_ft = distance.to(ureg.foot)
                distance_mi = distance.to(ureg.mile)
                coverage = (distance_m / neighborhood_total_distance_m).magnitude
                mission = MissionTable(region_id=record.region_id, label=mission_label, level=level,
                                       distance=distance_m.magnitude, distance_ft=distance_ft.magnitude,
                                       distance_mi=distance_mi.magnitude, coverage=coverage)
                missions.append(mission)

    elif mission_label == "area-coverage-mission":
        neighborhood_distance_query = """SELECT SUM(ST_Length(ST_Transform(street_edge.geom, 26985))) FROM sidewalk.region
INNER JOIN sidewalk.street_edge ON ST_Intersects(region.geom, street_edge.geom) WHERE region.region_id = %s"""

        for record in RegionTable.list_region_of_type(session, "neighborhood"):
            neighborhood_total_distance_m = float(session.execute(neighborhood_distance_query % str(record.region_id)).fetchone()[0]) * ureg.meter

            coverage_levels = [0.25, 0.5, 0.75, 1.0]

            for level, coverage in enumerate(coverage_levels, 1):
                distance_m = neighborhood_total_distance_m * coverage
                distance_ft = distance_m.to(ureg.foot)
                distance_mi = distance_m.to(ureg.mile)
                mission = MissionTable(region_id=record.region_id, label=mission_label, level=level,
                                       distance=distance_m.magnitude, distance_ft=distance_ft.magnitude,
                                       distance_mi=distance_mi.magnitude, coverage=coverage)
                missions.append(mission)

    if missions:
        MissionTable.add_missions(session, missions)


def compute_area_coverage_from_distance(session):
    """

    :param session:
    :return:
    """
    total_distance_by_region = {}

    distance_query = """SELECT SUM(ST_Length(ST_Transform(street_edge.geom, 26985))) FROM sidewalk.region
INNER JOIN sidewalk.street_edge ON ST_Intersects(region.geom, street_edge.geom) WHERE region.region_id = %s"""

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
INNER JOIN sidewalk.street_edge ON ST_Intersects(region.geom, street_edge.geom) WHERE region.region_id = %s"""

    region_ids = set(map(lambda m: m.region_id, filter(lambda m: m.region_id is not None, MissionTable.list(session))))
    for region_id in region_ids:
        total_distance_by_region[region_id] = session.execute(distance_query % str(region_id)).fetchone()[0]

    for mission in MissionTable.list_missions_with_label(session, "area-coverage-mission"):
        total_distance = total_distance_by_region[mission.region_id]
        distance = round(total_distance * mission.coverage / 100, 2)
        mission.distance = distance
    session.commit()


if __name__ == "__main__":
    print("populate_missions.py")
    database = DB("../../.settings")
    session = database.session
    # populate_missions(session, "area-coverage-mission")
    # compute_area_coverage_from_distance(session)
    # compute_distance_from_area_coverage(session)



