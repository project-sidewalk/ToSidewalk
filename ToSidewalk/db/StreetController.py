import db
from Street import *
from ToSidewalk.ToSidewalk import parse

import pprint as pp

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





if __name__ == "__main__":
    pass