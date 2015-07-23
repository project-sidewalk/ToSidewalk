import numpy as np
import os
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, Point
from sqlalchemy.exc import IntegrityError

import db
from StreetTables import *
from ToSidewalk.ToSidewalk import parse


def split_streets(filename):
    """
    Reads in an OSM file, splits the ways, and writes the processed osm file

    :param filename:
    :return:
    """
    street_network = parse(filename)
    street_network.split_streets()
    street_network.update_node_cardinality()
    street_network.merge_nodes()
    street_network.nodes.clean()
    street_network.clean_street_segmentation()
    osm = street_network.export(format="osm")

    with open("../../output/SmallMap_04_streets.osm", "wb") as f:
        f.write(osm)


def insert(filename):
    """
    Insert streets
    Example: http://geoalchemy-2.readthedocs.org/en/latest/core_tutorial.html

    :return:
    """
    database = db.DB('../../.settings')
    street_network = parse(filename)

    street_edge_table = StreetEdgeTable().__table__
    street_edge_parent_edge_table = StreetEdgeParentEdgeTable().__table__
    street_edge_street_node_table = StreetEdgeStreetNodeTable().__table__
    street_node_table = StreetNodeTable().__table__


    # Using transaction from sqlalchemy
    # http://docs.sqlalchemy.org/en/rel_0_9/core/connections.html#using-transactions
    connection = database.engine.connect()
    with connection.begin() as trans:
        # Insert nodes
        for node in street_network.get_nodes():
            try:
                street_node_id = int(node.id)
                geom = from_shape(Point(node.lng, node.lat), srid=4326)
                ins = street_node_table.insert().values(street_node_id=street_node_id, geom=geom, lat=node.lat, lng=node.lng)
                connection.execute(ins)
            except IntegrityError:
                # The node already exists
                continue


        # Insert streets
        for street in street_network.get_ways():
            # Insert a street
            coordinates = street_network.get_coordinates(street, lnglat=True)
            geom = from_shape(LineString(coordinates), srid=4326)
            street_id = int(street.id)
            x1 = coordinates[0][0]
            y1 = coordinates[0][1]
            x2 = coordinates[1][0]
            y2 = coordinates[1][1]
            street_type = street.type
            source = int(street.nids[0])
            target = int(street.nids[-1])
            ins = street_edge_table.insert().values(street_edge_id=street_id, geom=geom, x1=x1, y1=y1,
                                                    x2=x2, y2=y2, way_type=street_type, source=source,
                                                    target=target, deleted=False)
            connection.execute(ins)

            # Insert parent edges if there are any
            parents = street.get_original_ways()
            for parent_way_id in parents:
                parent_edge_id = int(parent_way_id)
                street_edge_id = int(street.id)
                ins = street_edge_parent_edge_table.insert().values(street_edge_id=street_edge_id, parent_edge_id=parent_edge_id)
                connection.execute(ins)


            # Insert edge-node relationship
            for node_id in street.get_node_ids():
                street_edge_id = int(street.id)
                street_node_id = int(node_id)
                ins = street_edge_street_node_table.insert().values(street_edge_id=street_edge_id, street_node_id=street_node_id)
                connection.execute(ins)

        trans.commit()


def init_assignment_count():
    database = db.DB('../../.settings')
    assignment_count_table = StreetEdgeAssignmentCountTable.__table__

    session = database.session
    query = session.query(StreetEdgeTable.street_edge_id, StreetEdgeAssignmentCountTable.assignment_count, StreetEdgeAssignmentCountTable.completion_count).\
        outerjoin(StreetEdgeAssignmentCountTable).\
        filter(StreetEdgeAssignmentCountTable.assignment_count is not None)

    connection = database.engine.connect()
    with connection.begin() as trans:
        for item in query:
            street_edge_id = item[0]
            ins = assignment_count_table.insert().values(street_edge_id=street_edge_id, assignment_count=0, completion_count=0)
            connection.execute(ins)

        trans.commit()


if __name__ == "__main__":
    print("StreetController.py")
    filename = os.path.relpath("../../output", os.path.dirname(__file__)) + "/SmallMap_04_streets.osm"
    # insert(filename)
    # split_streets("../../resources/SmallMap_04.osm")
    init_assignment_count()