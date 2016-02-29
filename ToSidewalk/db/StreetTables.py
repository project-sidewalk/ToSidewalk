from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Column, Integer, String, Float, Boolean, TIMESTAMP, BIGINT
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, backref
from ToSidewalk.ToSidewalk import parse

import db
import os
import sys

from logging import debug, DEBUG, basicConfig
basicConfig(stream=sys.stderr, level=DEBUG)


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
    street_node_id = Column(Integer, primary_key=True, name="street_node_id")
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


def groupby(mylist, splitter):
    """
    A utility function to split and group a list
    :param mylist:
    :param splitter:
    :return:
    """
    ret, curr = [], []

    for item in mylist:
        curr.append(item)
        if item in splitter:
            ret.append(curr)
            curr = [item]
    ret.append(curr)
    ret = filter(lambda x: len(x) > 1, ret)
    return ret


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
    query = session.query(StreetEdgeTable.street_edge_id, StreetEdgeAssignmentCountTable.assignment_count,
                          StreetEdgeAssignmentCountTable.completion_count).\
        outerjoin(StreetEdgeAssignmentCountTable).\
        filter(StreetEdgeAssignmentCountTable.assignment_count is not None)

    connection = database.engine.connect()
    with connection.begin() as trans:
        for item in query:
            street_edge_id = item[0]
            ins = assignment_count_table.insert().values(street_edge_id=street_edge_id,
                                                         assignment_count=0, completion_count=0)
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


def sanitize_edge_id(graph):
    for path in graph.get_paths():
        print path


def insert_dc_street_records():
    filename = os.path.relpath("../../output", os.path.dirname(__file__)) + "/"
    filename += "dc-streets-from-district-of-columbia-trunk.osm"

    database = db.DB('../../.settings')
    street_graph = get_street_graph(database="", osm_filename=filename)
    sanitize_edge_id(street_graph)
    insert_streets(street_graph)
    return


if __name__ == "__main__":
    import pprint as pp
    from geoalchemy2.shape import from_shape
    from shapely.geometry import LineString, Point
    database = db.DB("../../.settings")
    session = database.session

    street_edge_table = StreetEdgeTable().__table__
    street_edge_parent_edge_table = StreetEdgeParentEdgeTable().__table__
    street_edge_street_node_table = StreetEdgeStreetNodeTable().__table__
    street_node_table = StreetNodeTable().__table__

    connection = database.engine.connect()
    with connection.begin() as trans:
        # Todo. Split trunk streets
        split_points = {}
        edges = session.query(StreetEdgeTable).filter_by(way_type='trunk').all()

        for edge in edges:
            edge_node_links = session.query(StreetEdgeStreetNodeTable).filter_by(street_edge_id=edge.street_edge_id)
            for link in edge_node_links:
                linked_nodes = list(session.query(StreetEdgeStreetNodeTable).filter_by(street_node_id=link.street_node_id))
                if 1 < len(linked_nodes):
                    # Find intersections
                    split_points.setdefault(edge, []).append(link.street_node_id)

        # last_edge = session.query(StreetEdgeTable).order_by(StreetEdgeTable.street_edge_id.desc()).first()
        # last_row_id = last_edge.street_edge_id
        for edge in split_points:
            print edge
            edge_node_links = session.query(StreetEdgeStreetNodeTable).filter_by(street_edge_id=edge.street_edge_id)
            edge_node_ids = [link.street_node_id for link in edge_node_links]
            splitter = split_points[edge]
            grouped = groupby(edge_node_ids, splitter)
            if len(grouped) > 1:
                print edge
            #     for node_ids in grouped:
            #
            #         # Insert a new edge
            #         node_records = [session.query(StreetNodeTable).filter_by(street_node_id=node_id).one() for node_id in node_ids]
            #         coordinates = [(node_record.lng, node_record.lat) for node_record in node_records]
            #         geom = from_shape(LineString(coordinates), srid=4326)
            #         street_id = int(edge.street_edge_id)
            #         x1 = coordinates[0][0]
            #         y1 = coordinates[0][1]
            #         x2 = coordinates[-1][0]
            #         y2 = coordinates[-1][1]
            #         street_type = edge.way_type
            #         source = int(node_records[0].street_node_id)
            #         target = int(node_records[-1].street_node_id)
            #
            #         new_street_edge_id = last_row_id + 1
            #         last_row_id += 1
            #
            #         ins = street_edge_table.insert().values(street_edge_id=new_street_edge_id, geom=geom, x1=x1, y1=y1, x2=x2, y2=y2,
            #                                                 way_type=street_type, source=source, target=target, deleted=False)
            #         connection.execute(ins)
            #
            #
            #         # Insert child-edge/parent-edge relationship
            #         for node_id in map(lambda node: node.street_node_id, node_records):
            #             street_node_id = int(node_id)
            #             ins = street_edge_street_node_table.insert().values(street_edge_id=new_street_edge_id, street_node_id=street_node_id)
            #             connection.execute(ins)
            #
            #         # Insert street-edge/street_node relationship
            #         ins = street_edge_parent_edge_table.insert().values(street_edge_id=new_street_edge_id, parent_edge_id=edge.street_edge_id)
            #         connection.execute(ins)
            #     # pp.pprint(node_ids)

            # edge.deleted = True