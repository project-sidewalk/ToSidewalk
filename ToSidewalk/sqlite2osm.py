import sqlite3
from collections import namedtuple

NodeRecord = namedtuple("NodeRecord", ["way_id", "node_id", "way_pos", "lat", "lon"])


def node_record_to_element(record):
    return """<node id="%s" lat="%s" lon="%s"/>""" % (str(record.node_id), str(record.lat), str(record.lon))


def sqlite2osm(filename):
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()

    # XML header
    header_string = """<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6">"""

    # Bound element
    bounding_box_query = """SELECT MIN(nodes.lat), MIN(nodes.lon), MAX(nodes.lat), MAX(nodes.lon) FROM baltimore_streets AS street
INNER JOIN ways_nodes ON ways_nodes.way_id == street.id
INNER JOIN nodes ON nodes.id == ways_nodes.node_id"""
    cursor.execute(bounding_box_query)
    bounding_box_string = """<bounds minlat="%s" minlon="%s" maxlat="%s" maxlon="%s"/>""" % tuple(map(str, cursor.fetchone()))

    # Node and Way elements
    query = '''SELECT ways_nodes.way_id, ways_nodes.node_id, ways_nodes.way_pos, nodes.lat, nodes.lon FROM baltimore_streets AS street
INNER JOIN ways_nodes ON ways_nodes.way_id == street.id
INNER JOIN nodes ON nodes.id == ways_nodes.node_id'''

    cursor.execute(query)
    # Remove duplicates and create a text dump
    # http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
    seen_ids = set()
    seen_ids_add = seen_ids.add
    nodes = [record for record in map(NodeRecord._make, cursor.fetchall()) if not (record.node_id in seen_ids or seen_ids_add(record.node_id))]
    nodes_string = "\n".join(map(node_record_to_element, nodes))

    ways_string = ""
    prev_id = -1
    cursor.execute(query)
    for record in map(NodeRecord._make, cursor.fetchall()):
        if prev_id != record.way_id:
            prev_id = record.way_id
            ways_string += """</way>\n<way id="%s">\n""" % str(record.way_id)
        ways_string += """  <nd ref="%s"\>\n""" % str(record.node_id)

    ways_string += "</way>"
    ways_string = ways_string[7:]  # Remove the redundant </way> at the beginning

    osm_string = "\n".join((header_string, bounding_box_string, nodes_string, ways_string, "</osm>"))
    connection.close()
    return osm_string

if __name__ == "__main__":
    filename = "M:\public\sidewalk-files\openstreetmap\Baltimore Streets\maryland-latest.osm\maryland-latest.osm.db"
    with open("../output/BaltimoreStreets.osm", "wb") as of:
        of.write(sqlite2osm(filename))