import os
import sys
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, Point
from sqlalchemy.exc import IntegrityError

from logging import debug, DEBUG, basicConfig
basicConfig(stream=sys.stderr, level=DEBUG)

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


def insert_streets(street_network):
    """
    Insert streets
    Example: http://geoalchemy-2.readthedocs.org/en/latest/core_tutorial.html

    :return:
    """
    database = db.DB('../../.settings')

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
                continue  # Continue if the node already exists

        # Insert streets
        for street in street_network.get_paths():
            # Insert a street
            nodes = street.get_nodes()
            coordinates = map(lambda node: (node.lng, node.lat), nodes)
            geom = from_shape(LineString(coordinates), srid=4326)
            street_id = int(street.id)
            x1 = coordinates[0][0]
            y1 = coordinates[0][1]
            x2 = coordinates[-1][0]
            y2 = coordinates[-1][1]
            street_type = street.way_type
            source = int(nodes[0].id)
            target = int(nodes[-1].id)
            ins = street_edge_table.insert().values(street_edge_id=street_id, geom=geom, x1=x1, y1=y1,
                                                    x2=x2, y2=y2, way_type=street_type, source=source,
                                                    target=target, deleted=False)
            connection.execute(ins)

            # Insert parent edges if there are any
            parents = street.osm_ids
            for parent_way_id in parents:
                parent_edge_id = int(parent_way_id)
                street_edge_id = int(street.id)
                ins = street_edge_parent_edge_table.insert().values(street_edge_id=street_edge_id, parent_edge_id=parent_edge_id)
                connection.execute(ins)

            # Insert edge-node relationship
            for node_id in map(lambda node: node.id, nodes):
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


def get_street_graph(**kwargs):
    """
    Parse a osm file and retrieve streets. Return a graph.

    :param kwargs:
    :return:
    """
    assert 'database' in kwargs
    assert 'osm_filename' in kwargs
    osm_filename = kwargs['osm_filename']

    from ToSidewalk.graph import *
    geometric_graph = parse_osm(osm_filename)
    geometric_graph = remove_dangling_nodes(geometric_graph)
    geometric_graph = clean_edge_segmentation(geometric_graph)
    geometric_graph = split_path(geometric_graph)
    geometric_graph = remove_short_edges(geometric_graph)
    return geometric_graph



def insert_dc_street_records():
    filename = os.path.relpath("../../resources", os.path.dirname(__file__)) + "/"
    filename += "DC_IntersectedWithTheCityBoundary/district-of-columbia-latest.osm"

    database = db.DB('../../.settings')
    street_graph = get_street_graph(database=database, osm_filename=filename)
    insert_streets(street_graph)

if __name__ == "__main__":
    print("StreetController.py")
    init_assignment_count()

    # split_streets("../../resources/SmallMap_04.osm")
    # init_assignment_count()