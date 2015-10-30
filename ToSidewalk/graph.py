import numpy as np
from node import Node
from edge import Edge
from path import Path
from utilities import window
from types import *


class GeometricGraph(object):
    def __init__(self):
        self.nodes = {}
        self.paths = {}
        self.node_id_counter = 0
        self.path_id_counter = 0
        self.bounds = None

    @property
    def bounds(self):
        if not self._bounds:
            latlngs = np.array(map(lambda node: (node.lat, node.lng), self.get_nodes()))
            lat, lng = latlngs.T[0], latlngs.T[1]
            self._bounds = [np.min(lat), np.min(lng), np.max(lat).np.max(lng)]
        return self._bounds

    @property
    def nodes(self):
        return self._nodes

    @property
    def paths(self):
        return self._paths

    @bounds.setter
    def bounds(self, b):
        self._bounds = b

    @nodes.setter
    def nodes(self, n):
        self._nodes = n

    @paths.setter
    def paths(self, p):
        self._paths = p

    def create_node(self, x, y, id=None):
        """
        This method creates a new node.

        :param lng:
        :param lat:
        :param id:
        :return:
        """
        if not id:
            id = self.node_id_counter
            self.node_id_counter += 1

        assert type(x) == FloatType
        assert type(y) == FloatType
        assert type(id) == IntType or type(id) == LongType
        self.nodes[id] = Node(id, y, x)
        return self.nodes[id]

    def create_path(self, **kwargs):
        """
        This method creates a new path.

        :param nodes:
        :param id:
        :return:
        """
        if "id" not in kwargs:
            id = self.path_id_counter
            self.path_id_counter += 1
        else:
            id = kwargs["id"]

        if "nodes" in kwargs:
            edges = [Edge(source, target) for source, target in window(kwargs["nodes"], 2)]
        elif "edges" in kwargs:
            edges = kwargs["edges"]
        else:
            raise ValueError("nodes or edges have to be provided")
        self.paths[id] = Path(id=id, edges=edges)
        return self.paths[id]

    def get_node(self, node_id):
        """
        This method returns a node object with a given id.

        :param node_id:
        :return:
        """
        return self.nodes[node_id]

    def get_nodes(self):
        """
        This method returns all the nodes in this graph

        :return: A list of nodes
        """
        return [node for node in self.nodes.values()]

    def get_path(self, path_id):
        """
        This method returns a path object with a given id.

        :param path_id:
        :return:
        """
        return self.paths[path_id]

    def get_paths(self):
        """
        This method returns a list of paths
        :return:
        """
        return self.paths.values()

    def get_adjacent_nodes(self, node):
        """
        This method returns a set of nodes that are connected to the given node.

        :param node:
        :return:
        """
        nodes = []
        for edge in node.edges:
            if node == edge.source:
                nodes.append(edge.target)
            else:
                nodes.append(edge.source)
        return nodes

    def get_degrees(self):
        """
        This method returns a list of tuple that contains (degree, node), where degree is a number of connected
        edges.

        :return: A list of (degree, node)
        """
        return [(len(node.edges), node) for node in self.nodes.values()]

    def merge_path(self, path1, path2):
        """
        Merge two paths into one.

        :param path1:
        :param path2:
        :return:
        """
        assert path1 != path2

        nodes1, nodes2 = path1.get_nodes(), path2.get_nodes()
        if nodes1[0] ==nodes2[0]:
            path1.edges = path1.edges[::-1]
        elif nodes1[-1] == nodes2[-1]:
            path2.edges = path2.edges[::-1]
        elif nodes1[0] == nodes2[-1]:
            _path1 = path2
            path2 = path1
            path1 = _path1

        new_edges = path1.edges + path2.edges
        new_path = self.create_path(edges=new_edges)
        new_path.osm_ids = path1.osm_ids + path2.osm_ids
        new_path.way_type = path1.way_type
        new_path.tags = path1.tags + path2.tags

        del self.paths[path1.id]
        del self.paths[path2.id]
        return new_path

    def remove_node(self, node_id):
        """
        Remove a node from the graph

        :param node_id: Node id
        """
        node = self.get_node(node_id)
        connected_edges = node.edges
        connected_paths = set(map(lambda e: e.path, connected_edges))
        for path in connected_paths:
            if len(path.edges) == 1:
                self.remove_path(path)
            else:
                path.remove_node(node)

        if node_id in self.nodes:
            del self.nodes[node_id]

    def remove_path(self, path_id):
        """
        Remove a path
        :param path_id:
        :return:
        """
        path = self.get_path(path_id)
        edges = path.edges
        nodes = path.get_nodes()
        for edge in edges:
            edge.source.edges.remove(edge)
            edge.target.edges.remove(edge)

        for node in nodes:
            if len(node.edges) == 0:
                del self.nodes[int(node.id)]

        del self.paths[path_id]

    def visualize(self):
        """
        Visuzalise the edges

        References:
        * http://stackoverflow.com/questions/11603537/plot-multiple-lines-in-python-basemap
        """
        from mpl_toolkits.basemap import Basemap
        import matplotlib.pyplot as plt
        import numpy as np

        m = Basemap(projection='mill', llcrnrlat=self.bounds[0], urcrnrlat=self.bounds[2],
                    llcrnrlon=self.bounds[1], urcrnrlon=self.bounds[3], resolution='c')

        m.drawcoastlines()
        m.drawcountries()
        m.drawstates()
        m.fillcontinents(color='#EEEEEE', lake_color='#FFFFFF')
        m.drawmapboundary(fill_color='#FFFFFF')

        # Plotting segments
        for path in self.get_paths():
            latlngs = np.array(map(lambda node: (node.lat, node.lng), path.get_nodes()))
            x, y = m(latlngs.T[1], latlngs.T[0])
            m.plot(x, y, color="#000000", linestyle='-', linewidth=2, alpha=.5)

        plt.title('Segment plotting')
        plt.show()

    def export(self, format="geojson"):
        """
        Todo
        """
        if format == "geojson":
            import json
            geojson = {}
            geojson['type'] = "FeatureCollection"
            geojson['features'] = []

            for path in self.get_paths():
                geojson['features'].append(path.geojson_feature)

            return json.dumps(geojson)


def parse_osm(filename):
    """
    Parse an OSM file
    """
    from xml.etree import cElementTree as ET
    import logging as log
    with open(filename, "rb") as osm:
        # Find element
        # http://stackoverflow.com/questions/222375/elementtree-xpath-select-element-based-on-attribute
        tree = ET.parse(osm)
        nodes_tree = tree.findall(".//node")
        ways_tree = tree.findall(".//way")
        bounds_elem = tree.find(".//bounds")
        padding = 5e-2
        bounds = [float(bounds_elem.get("minlat")) - padding,
                  float(bounds_elem.get("minlon")) - padding,
                  float(bounds_elem.get("maxlat")) + padding,
                  float(bounds_elem.get("maxlon")) + padding]

    log.debug("Start parsing the file: %s" % filename)
    geometric_graph = GeometricGraph()
    geometric_graph.bounds = bounds

    valid_highways = {'primary', 'secondary', 'tertiary', 'residential'}
    for node in nodes_tree:
        try:
            geometric_graph.create_node(x=float(node.get("lon")), y=float(node.get("lat")), id=int(node.get("id")))
        except AssertionError as e:
            print "Assertion Error"

    # Parse ways
    for way in ways_tree:
        highway_tag = way.find(".//tag[@k='highway']")
        if highway_tag is not None and highway_tag.get("v") in valid_highways:
            node_elements = filter(lambda elem: elem.tag == "nd", list(way))
            nodes = [geometric_graph.get_node(int(element.get("ref"))) for element in node_elements]
            path = geometric_graph.create_path(nodes=nodes, id=int(way.get("id")))
            path.way_type = highway_tag.get('v')
            path.osm_ids.append(path.id)
            for tag in way.findall('tag'):
                if tag.attrib['k'] != "highway":
                    path.tags.append(tag.attrib)

    return geometric_graph


def remove_short_edges(graph, distance_threshold=15):
    """
    Remove short edges.

    :param graph:
    :return:
    """
    paths = graph.get_paths()
    for path in paths:
        if len(path.edges) < 2:
            continue

        edges = list(path.edges)
        new_edges = []

        while edges:
            edge = edges.pop(0)
            if edge.get_length(in_meters=True) < distance_threshold and len(edges) > 0:
                other = edges.pop(0)
                new_edge = path.merge_edges(edge, other)
                edges.insert(0, new_edge)
            else:
                new_edges.append(edge)

        path.edges = new_edges

    return graph


def clean_edge_segmentation(graph):
    """
    Go through nodes and find ones that have two connected paths. Merge the two paths.
    I don't want segmentation in a path.

    Segmented path: *------*-------*------*=======*=======*

    :param graph:
    :return:
    """
    queue = graph.get_paths()
    while queue:
        path = queue.pop(0)
        nodes = path.get_nodes()
        for node in [nodes[0], nodes[-1]]:
            if len(node.edges) == 2:
                # Fix the segmentation by merging the two paths. Get the two path, sort the
                # edges, and concatenate.
                path1, path2 = node.edges[0].path, node.edges[1].path
                new_path = graph.merge_path(path1, path2)

                if path1 in queue:
                    queue.remove(path1)
                if path2 in queue:
                    queue.remove(path2)

                queue.append(new_path)

    return graph


def split_path(graph):
    """
    This method splits the each path at intersection
    :param graph:
    :return:
    """
    intersection_nodes = filter(lambda node: node.is_intersection(), graph.get_nodes())
    for node in intersection_nodes:
        for path in node.paths:
            path.split(node)
    return graph


def merge_parallel_edges(graph, distance_threshold=15):
    pass

if __name__ == "__main__":
    filename = "../resources/SmallMap_04.osm"
    geometric_graph = parse_osm(filename)
    geometric_graph = clean_edge_segmentation(geometric_graph)
    geometric_graph = split_path(geometric_graph)
    geometric_graph = remove_short_edges(geometric_graph)
    print geometric_graph.export()
