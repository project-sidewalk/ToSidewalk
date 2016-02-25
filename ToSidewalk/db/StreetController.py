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

def play():
    ids = map(lambda id: int(id), edge_ids.strip().split("\n"))
    database = db.DB('../../.settings')
    session = database.session

    for edge in session.query(StreetEdgeTable):
        if edge.street_edge_id in ids:
            edge.deleted = True
            # print edge.street_edge_id
    session.commit()


edge_ids = """
3
4
6
8
10
12
14
15
17
18
21
25
26
27
28
30
31
32
34
35
37
42
43
48
49
50
525
1036
3156
3158
3161
3162
3163
3164
3167
3168
3169
3171
3173
3174
3175
3176
3177
3178
3179
3180
3181
3182
3185
3187
3188
3189
3190
3195
3197
3198
3199
3200
3201
3202
3203
3206
3207
3208
3209
3210
3211
3213
3214
3215
3218
3219
3222
3224
3225
3226
3227
3228
3230
3231
3233
3253
3254
3292
3373
3377
3502
3539
3546
3738
3907
3929
3949
3968
4215
4284
4440
4522
4559
5850
5853
6439
6442
6899
6901
6906
6908
7032
7470
7491
7493
7495
7496
7497
7499
7500
7501
7503
7504
7505
7507
7508
7511
7512
7513
7514
7517
7518
7521
7523
7526
7527
7529
7533
7534
7535
7536
7538
7539
7540
7541
7542
15736
22691
22693
22695
22697
22699
22700
22701
22702
22703
22704
22705
22706
22707
22708
22713
22714
22715
22716
22719
22721
22722
22723
22724
22725
22726
22729
22730
22735
22736
22737
22738
22739
22741
22744
22781
22782
22783
22784
22797
22826
22831
22832
22886
23122
23129
23130
23336
23443
23444
23445
23446
23447
23448
23745
23746
23756
23757
23758
23759
23761
23762
23763
23764
23765
23766
23773
23774
23799
23840
24161
24162
24335
24337
24338
24339
24340
24341
24342
24343
24344
24864
25319
25320
25344
25345
25346
25347
25348
25536
25539
25777
26783
26798
27050
27051
27052
27065
27121
27122
27125
27126
27142
27067
27072
27082"""

if __name__ == "__main__":
    print("StreetController.py")
    play()