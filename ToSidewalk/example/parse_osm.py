from ToSidewalk.graph import *


def main(filename):
    geometric_graph = parse_osm(filename)
    geometric_graph = clean_edge_segmentation(geometric_graph)
    geometric_graph = split_path(geometric_graph)
    geometric_graph = remove_short_edges(geometric_graph)
    with open("../../output/output.osm", "wb") as f:
        f.write(geometric_graph.export(format="osm"))

if __name__ == "__main__":
    main("../../resources/SmallMap_04.osm")