import numpy as np
from node import Node
from edge import Edge
from path import Path
from utilities import window
from types import *

import sys
from logging import debug, DEBUG, basicConfig
basicConfig(stream=sys.stderr, level=DEBUG)


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
            self._bounds = [np.min(lat), np.min(lng), np.max(lat), np.max(lng)]
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

    def add_node(self, node):
        """
        Add an existing node object to this graph
        :param node:
        :return:
        """
        if int(node.id) not in self.nodes:
            self.nodes[int(node.id)] = node

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

    def add_path(self, path):
        """
        Add an existing path object to this graph
        :param path:
        :return:
        """
        if path.id not in self.paths:
            self.paths[path.id] = path

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
            if len(node.edges) == 0 and int(node.id) in self.nodes:
                del self.nodes[int(node.id)]

        del self.paths[path_id]

    def split_path(self, path, node):
        """
        Split the path at node
        :return:
        """
        assert len(node.edges) > 2  # it should be an intersection node

        nodes = path.get_nodes()

        if nodes[0] == node or nodes[-1] == node:
            # Return if this is at the end of this path
            return

        idx = nodes.index(node)
        edges1 = path.edges[:idx]
        edges2 = path.edges[idx:]

        path1 = self.create_path(edges=edges1)
        path2 = self.create_path(edges=edges2)
        Path.copy_properties(path, path1)
        Path.copy_properties(path, path2)
        del self.paths[path.id]

    def subgraph(self, bounds, remove=False):
        """
        Extract a subgraph that is in the area bounded by the boudning box (minlat, minlng, maxlat, maxlng)

        :param bounds: (minlat, minlng, maxlat, maxlng)
        :return:
        """
        from shapely.geometry import Polygon
        coords = ((bounds[1], bounds[0]),
                  (bounds[3], bounds[0]),
                  (bounds[3], bounds[2]),
                  (bounds[1], bounds[2]),
                  (bounds[1], bounds[0]))
        bounding_box = Polygon(coords)
        nodes = self.get_nodes()

        # Get all the paths to extract
        paths = []
        for node in nodes:
            if bounding_box.contains(node):
                paths += node.paths
        paths = set(paths)

        if not paths:
            return

        nodes = []
        for path in paths:
            nodes += path.get_nodes()
        nodes = set(nodes)

        new_graph = GeometricGraph()
        for node in nodes:
            new_graph.add_node(node)

        for path in paths:
            new_graph.add_path(path)
            if remove:
                self.remove_path(path.id)

        return new_graph

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
            m.plot(x, y, color="#000000", marker='o', linestyle='-', linewidth=2, alpha=.5)

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
        elif format == "osm":
            header_string = """<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6">"""
            bounding_box_string = """<bounds minlat="%s" minlon="%s" maxlat="%s" maxlon="%s"/>""" % tuple(map(str, self.bounds))

            node_to_node_element = lambda n: """<node id="%s" lat="%s" lon="%s" osm_id="%s"/>""" % (str(n.id), str(n.lat), str(n.lng), str(n.osm_id))
            nodes_string = "\n".join(map(node_to_node_element, self.get_nodes()))

            ways_string_list = []
            node_to_nd_element = lambda n: """  <nd ref="%s"/>""" % str(n.id)
            osm_id_to_tag_element = lambda tag: """  <tag k="osm_id" v="%s"/>""" % str(tag)
            for path in self.get_paths():
                ways_string_list.append("<way id=\"%s\">" % str(path.id))
                ways_string_list += map(node_to_nd_element, path.get_nodes())
                ways_string_list += map(osm_id_to_tag_element, path.osm_ids)
                ways_string_list.append("</way>")
            ways_string = "\n".join(ways_string_list)
            osm_string = "\n".join((header_string, bounding_box_string, nodes_string, ways_string, "</osm>"))
            return osm_string
        else:
            raise ValueError("format should be either 'geojson' or 'osm'")


def parse_osm(filename, valid_highways={'primary', 'secondary', 'tertiary', 'residential'}):
    """
    Parse an OSM file
    """
    debug("Opening the file: %s" % filename)

    from xml.etree import cElementTree as ET
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

    debug("Started parsing the file...")
    geometric_graph = GeometricGraph()
    geometric_graph.bounds = bounds

    osm_id_to_node_id = {}
    for node in nodes_tree:
        try:
            n = geometric_graph.create_node(x=float(node.get("lon")), y=float(node.get("lat")))
            if node.get("osm_id"):
                n.osm_id = int(node.get("osm_id"))
            else:
                n.osm_id = int(node.get("id"))
            assert n.osm_id != None

            osm_id_to_node_id[n.osm_id] = int(n.id)

            for tag in node.findall('tag'):
                n.tags.append(tag)
        except AssertionError:
            raise

    # Parse ways
    for way in ways_tree:
        highway_tag = way.find(".//tag[@k='highway']")
        if highway_tag is not None and highway_tag.get("v") in valid_highways:
            node_elements = filter(lambda elem: elem.tag == "nd", list(way))
            nodes = [geometric_graph.get_node(osm_id_to_node_id[int(element.get("ref"))]) for element in node_elements]
            path = geometric_graph.create_path(nodes=nodes)
            path.way_type = highway_tag.get('v')
            path.osm_ids.append(int(way.get("id")))
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
    debug("Size of the graph. N_path=%s" % str(len(paths)))
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

        if len(new_edges) > 1 and new_edges[-1].get_length(in_meters=True) < distance_threshold:
            edge_1 = new_edges.pop()
            edge_2 = new_edges.pop()
            new_edge = path.merge_edges(edge_1, edge_2)
            new_edges.append(new_edge)

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
    debug("Started cleaning edge segmentation...")
    queue = graph.get_paths()
    while queue:
        path = queue.pop(0)
        nodes = path.get_nodes()
        for node in [nodes[0], nodes[-1]]:
            if len(node.edges) == 2:
                # Fix the segmentation by merging the two paths. Get the two path, sort the
                # edges, and concatenate.
                path1, path2 = node.edges[0].path, node.edges[1].path
                if path1 == path2:
                    continue

                try:
                    new_path = graph.merge_path(path1, path2)
                except AssertionError, e:
                    debug(e)
                    debug(path1)
                    debug(path2)
                    raise

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
            graph.split_path(path, node)
    return graph


def split_graph(graph, rows, columns, remove=False, pool=None):
    """
    This method splits the graph into row x col sub graphs


    :param rows: a number of rows
    :param columns: a number of columns
    :return:
    """
    dlat = (graph.bounds[2] - graph.bounds[0]) / rows
    dlng = (graph.bounds[3] - graph.bounds[1]) / columns

    from itertools import product
    rows_columns = product(range(rows), range(columns))

    to_bound = lambda row_column: (graph.bounds[0] + row_column[0] * dlat, graph.bounds[1] + row_column[1] * dlng,
                             graph.bounds[0] + (row_column[0] + 1) * dlat, graph.bounds[1] + (row_column[1] + 1) * dlng)
    to_subgraph = lambda bound: graph.subgraph(bound, remove=remove)
    bounds = map(to_bound, rows_columns)

    debug("Start splitting the graph...")
    return map(to_subgraph, bounds)




def merge_graph(graph1, graph2):
    """
    Merge two graphs.

    Todo. This is not really safe... Imagine two graphs sharing same nodes but those nodes
    have differnt memory signatures. If you look up an edge and see what nodes are connected to them,
    those nodes may not be in the graph (well, technically they are, but those nodes are pointing
    to other nodes in the graph data structure...)

    :param graph1:
    :param graph2:
    :return:
    """
    debug("Start merging the graphs...")
    for node in graph2.get_nodes():
        graph1.add_node(node)

    for path in graph2.get_paths():
        graph1.add_path(path)

    return graph1


def merge_parallel_edges(graph, distance_threshold=15):
    pass


def make_sidewalks(street_graph, distance_to_sidewalk=15):
    """
    Make a new graph with new sidewalk edges and sidewalk nodes from the passed graph of streets.
    For each street in the street_graph like:
    Street:     *------*------*------*

    Create two sidewalks like:
    Sidewalk 1: +------+------+------+
    Street:     *------*------*------*
    Sidewalk 2: +------+------+------+

    Todo: Move this function to ToSidewalk.py

    :param graph:
    :return:
    """
    import numpy as np
    from utilities import latlng_offset_size

    sidewalk_graph = GeometricGraph()

    # Create sidewalks
    for path in street_graph.get_paths():
        sidewalk_nodes_1 = []
        sidewalk_nodes_2 = []

        # Create sidewalk nodes
        # First make new sidewalk nodes on each side of each street node. Use three consecutive
        # nodes to calculate the correct angle to place the sidewalk nodes.
        for prev_node, curr_node, next_node in window(path.get_nodes(), 3, padding=1):
            if not prev_node:
                vec_prev = curr_node.vector() - curr_node.vector_to(next_node)  # v is a vec of (lat, lng)
                prev_node = Node(-1, vec_prev[0], vec_prev[1])  # a temporary node to calculate vec_curr_to_sidewalk
            elif not next_node:
                vec_next = curr_node.vector() - curr_node.vector_to(prev_node)
                next_node = Node(-1, vec_next[0], vec_next[1])

            # Calculate the angle from the current node to the sidewalk nodes.
            vec_curr_to_prev = curr_node.vector_to(prev_node, normalize=True)
            vec_curr_to_next = curr_node.vector_to(next_node, normalize=True)
            vec_curr_to_sidewalk = vec_curr_to_prev + vec_curr_to_next

            # vec_curr_to_sidewalk is 0 if you are using temporary node for prev_node or next_node. Take care of it.
            # Then normalize the vector.
            if np.linalg.norm(vec_curr_to_sidewalk) < 1e-10:
                vec_curr_to_sidewalk = np.array([vec_curr_to_next[1], -vec_curr_to_next[0]])
            vec_curr_to_sidewalk /= np.linalg.norm(vec_curr_to_sidewalk)

            # Create two sidewalk nodes next to the current node
            d = latlng_offset_size(curr_node.lat, vector=vec_curr_to_sidewalk, distance=distance_to_sidewalk)
            latlng_1 = np.array([curr_node.lat, curr_node.lng]) + vec_curr_to_sidewalk * d
            latlng_2 = np.array([curr_node.lat, curr_node.lng]) - vec_curr_to_sidewalk * d
            sidewalk_node_1 = sidewalk_graph.create_node(float(latlng_1[1]), float(latlng_1[0]))
            sidewalk_node_2 = sidewalk_graph.create_node(float(latlng_2[1]), float(latlng_2[0]))
            sidewalk_node_1.parents = [prev_node, curr_node, next_node]
            sidewalk_node_2.parents = [prev_node, curr_node, next_node]

            # Figure out which side you want to put each node
            vec_curr_to_sidewalk_node_1 = curr_node.vector_to(sidewalk_node_1)
            if np.cross(vec_curr_to_next, vec_curr_to_sidewalk_node_1) > 0:
                sidewalk_nodes_1.append(sidewalk_node_1)
                sidewalk_nodes_2.append(sidewalk_node_2)
            else:
                sidewalk_nodes_2.append(sidewalk_node_1)
                sidewalk_nodes_1.append(sidewalk_node_2)

        sidewalk_graph.create_path(nodes=sidewalk_nodes_1)
        sidewalk_graph.create_path(nodes=sidewalk_nodes_2)

    # Create crosswalks
    intersection_nodes = [node for node in street_graph.get_nodes() if node.is_intersection()]
    for node in intersection_nodes:
        print "%s,%s" % (node.lat, node.lng)

    return sidewalk_graph


def main():
    debug("Start...")
    filename = "../resources/SmallMap_03.osm"
    geometric_graph = parse_osm(filename)
    geometric_graph = clean_edge_segmentation(geometric_graph)
    geometric_graph = split_path(geometric_graph)
    geometric_graph = remove_short_edges(geometric_graph)

    sidewalk_graph = make_sidewalks(geometric_graph)
    sidewalk_graph.visualize()


if __name__ == "__main__":
    main()
