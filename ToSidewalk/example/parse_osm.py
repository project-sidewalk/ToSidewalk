"""
This scripts read a osm file, parse street segments, and export the parsed data in osm format.
"""
from ToSidewalk.graph import *


def main(in_filename, out_filename):
    geometric_graph = parse_osm(in_filename)
    # geometric_graph = clean_edge_segmentation(geometric_graph)
    # geometric_graph = split_path(geometric_graph)
    # geometric_graph = remove_short_edges(geometric_graph)
    with open(out_filename, "wb") as f:
        f.write(geometric_graph.export(format="osm"))

if __name__ == "__main__":
    main("../../resources/DC_IntersectedWithTheCityBoundary/district-of-columbia-latest.osm",
         "../../output/dc-streets-from-district-of-columbia-latest.osm")
