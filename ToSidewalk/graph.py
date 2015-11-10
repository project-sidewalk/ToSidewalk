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

        for edge in edges:
            edge.path = self.paths[id]

        return self.paths[id]

    def get_node(self, node_id):
        """
        This method returns a node object with a given id.

        :param node_id:
        :return:
        """
        assert node_id in self.nodes
        return self.nodes[node_id]

    def get_nodes(self):
        """
        This method returns all the nodes in this graph

        :return: A list of nodes
        """
        return [node for node in self.nodes.values()]

    def get_edges(self):
        """
        This method returns a set of edges
        :return:
        """
        paths = self.get_paths()
        edges = []
        for path in paths:
            edges += path.edges
        return set(edges)

    def get_path(self, path_id):
        """
        This method returns a path object with a given id.

        :param path_id:
        :return:
        """
        assert path_id in self.paths
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
        assert node.id in self.nodes

        nodes = []
        for edge in node.edges:
            if node == edge.source:
                nodes.append(edge.target)
            else:
                nodes.append(edge.source)

        assert len(nodes) > 0
        return nodes

    def get_degrees(self):
        """
        This method returns a list of tuple that contains (degree, node), where degree is a number of connected
        edges.

        :return: A list of (degree, node)
        """
        return [(len(node.edges), node) for node in self.nodes.values()]

    @staticmethod
    def get_connected_paths(node):
        """
        This method returns a set of paths that are connected to the given node

        :param node:
        :return: A set of path objects
        """
        return {edge.path for edge in node.edges}

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


    def merge_edges(self, edge1, edge2):
        """
        Return a new edge after merging the two passed edge. This method does not delete the original edges.
        :param edge1:
        :param edge2:
        :return: A list of edges and a table that maps the old nodes to new nodes.
        """
        # assert Edge.parallel(edge1, edge2)
        old_to_new, new_to_old = {}, {}

        if Edge.connected(edge1, edge2):
            # If one node is shared between two edges, the method should return two new edges that are connected
            base_node = {edge1.source, edge1.target} & {edge2.source, edge2.target}
            assert len(base_node) == 1  # One and only one shared node
            target_nodes = {edge1.source, edge1.target, edge2.source, edge2.target} - base_node
            assert len(target_nodes) == 2  # Two nodes other than the shared nodes

            target_nodes = list(target_nodes)
            base_node = list(base_node)[0]
            tmp_lat, tmp_lng = (target_nodes[1].lat + target_nodes[0].lat) / 2, (target_nodes[1].lng + target_nodes[0].lng) / 2
            tmp_node = Node(-1, tmp_lat, tmp_lng)
            base_vector = base_node.vector_to(tmp_node, normalize=True)

            # Create new nodes
            items = []  # (distance along the base vec, node)
            for target_node in target_nodes:
                vec_base_to_target = base_node.vector_to(target_node)
                d_base_to_new_node = np.dot(vec_base_to_target, base_vector)
                new_node_latlng = base_node.vector() + d_base_to_new_node * base_vector
                new_node = self.create_node(float(new_node_latlng[1]), float(new_node_latlng[0]))
                items.append((d_base_to_new_node, new_node))
            items.sort(key=lambda item: item[0])
            new_nodes = map(lambda item: item[1], items)
            assert len(new_nodes) == 2
            new_edge = Edge(source=base_node, target=new_nodes[0])
            for node in target_nodes:
                old_to_new[node] = new_nodes[0]
            old_to_new[base_node] = base_node
            return new_edge, old_to_new
        else:
            # Take the average coordinate of the four nodes connected to the edges to get a base node coord.
            edge_nodes = {edge1.source, edge1.target, edge2.source, edge2.target}
            latlngs = [np.array([node.lat, node.lng]) for node in edge_nodes]
            base_latlng = np.sum(latlngs, axis=0) / len(latlngs)
            base_node = Node(-1, base_latlng[0], base_latlng[1])

            v1 = edge1.vector(normalize=True)
            v2 = edge2.vector(normalize=True)
            if np.dot(v1, v2) < 0:
                v2 = -v2
            base_vector = (v1 + v2) / np.linalg.norm(v1 + v2)

            items = []
            for edge_node in edge_nodes:
                vec_base_to_edge_node = base_node.vector_to(edge_node)
                d_base_to_new_node = np.dot(vec_base_to_edge_node, base_vector)
                new_node_latlng = base_node.vector() + d_base_to_new_node * base_vector
                new_node = self.create_node(float(new_node_latlng[1]), float(new_node_latlng[0]))
                items.append((d_base_to_new_node, new_node))
                old_to_new[edge_node] = new_node
                new_to_old[new_node] = edge_node
            items.sort(key=lambda item: item[0])
            new_nodes = map(lambda item: item[1], items)
            assert len(new_nodes) == 4
            new_edge = Edge(source=new_nodes[1], target=new_nodes[2])
            old_to_new[new_to_old[new_nodes[0]]] = new_nodes[1]
            old_to_new[new_to_old[new_nodes[3]]] = new_nodes[2]

            return new_edge, old_to_new

    def swap_path_node(self, path, swap_from, swap_to):
        """
        Swap the source node in the path to target
        :param path:
        :param source:
        :param target:
        :return:
        """
        nodes = path.get_nodes()
        assert swap_from in nodes
        idx = nodes.index(swap_from)
        if idx == 0:
            # Remove the first edge and swap with a new one
            old_edge = path.edges[0]
            if old_edge.source == swap_from:
                new_edge = Edge(source=swap_to, target=old_edge.target)
            else:
                new_edge = Edge(source=old_edge.source, target=swap_to)
            new_edge.path = path
            path.remove_edge(old_edge)
            path.edges.insert(0, new_edge)
        elif idx == len(nodes) - 1:
            # Remove the last edge and swap with a new one
            old_edge = path.edges[-1]
            if old_edge.source == swap_from:
                new_edge = Edge(source=swap_to, target=old_edge.target)
            else:
                new_edge = Edge(source=old_edge.source, target=swap_to)
            new_edge.path = path
            path.remove_edge(old_edge)
            path.edges.append(new_edge)
        else:
            old_edge_1 = path.edges[idx - 1]
            old_edge_2 = path.edges[idx]
            for e_idx, old_edge in [(idx - 1, old_edge_1), (idx, old_edge_2)]:
                if old_edge.source == swap_from:
                    new_edge = Edge(source=swap_to, target=old_edge.target)
                else:
                    new_edge = Edge(source=old_edge.source, target=swap_to)
                new_edge.path = path
                path.remove_edge(old_edge)
                path.edges.insert(e_idx, new_edge)

    def swap_edge_node(self, edge, node_from, node_to):
        """
        Swap a node
        :param edge:
        :param node_from:
        :param node_to:
        :return:
        """
        assert hasattr(edge, 'path')
        assert edge in edge.path.edges
        if node_from == node_to:
            return edge

        path = edge.path
        if edge.source == node_from:
            new_edge = Edge(source=node_to, target=edge.target)
        else:
            new_edge = Edge(source=edge.source, target=node_to)
        new_edge.path = path
        idx = path.edges.index(edge)
        path.remove_edge(edge)
        path.edges.insert(idx, new_edge)
        return new_edge

    def swap_edge(self, edge, nodes_from, nodes_to):
        """

        :param nodes_from:
        :param nodes_to:
        :return:
        """
        assert len(nodes_from) == 2
        assert len(nodes_to) == 2
        assert edge in edge.path.edges
        assert len(edge.path.edges) == 1
        if edge.source == nodes_from[0]:
            new_edge = Edge(source=nodes_to[0], target=nodes_to[1])
        else:
            new_edge = Edge(source=nodes_to[1], target=nodes_to[0])
        path = edge.path
        new_edge.path = path
        path.remove_edge(edge)
        path.edges.append(new_edge)

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

    def visualize(self, padding=0.001):
        """
        Visuzalise the edges

        References:
        * http://stackoverflow.com/questions/11603537/plot-multiple-lines-in-python-basemap
        """
        from mpl_toolkits.basemap import Basemap
        import matplotlib.pyplot as plt
        import numpy as np

        m = Basemap(projection='mill', llcrnrlat=self.bounds[0] - padding, urcrnrlat=self.bounds[2] + padding,
                    llcrnrlon=self.bounds[1] - padding, urcrnrlon=self.bounds[3] + padding, resolution='c')

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


def merge_parallel_edges(graph, overlap_threshold=.3, angle_threshold=10.):
    import math
    import rtree
    debug("Merge parallel edges...")

    rtree_index = rtree.index.Index()
    edges = graph.get_edges()
    edge_to_original_edge_table = {}
    for edge in edges:
        rtree_index.insert(edge.id, edge.bounds, edge)
        edge_to_original_edge_table[edge.id] = edge

    while edges:
        current_edge = edges.pop()

        # Caution! The parent path information of each edge is lost when retrieved from rtree. This is because
        # pickle cannot serialize some properties (e.g., the reference to path object). So fix that.
        nearby_edges = list(rtree_index.nearest(current_edge.bounds, 5, objects='raw'))
        nearby_edges = map(lambda e: edge_to_original_edge_table[e.id],
                           filter(lambda e: e != current_edge, nearby_edges))

        # Check if two edges are parallel and do not belong to the same path.
        parallel_edges = []
        for nearby_edge in nearby_edges:
            try:
                if Edge.connected(current_edge, nearby_edge) and \
                        (math.degrees(Edge.angle(current_edge, nearby_edge)) < angle_threshold or
                         math.degrees(Edge.angle(current_edge, nearby_edge)) > 360. - angle_threshold):
                    parallel_edges.append((Edge.overlap(current_edge, nearby_edge, relative=True), current_edge, nearby_edge))
                elif Edge.parallel(current_edge, nearby_edge) and not Edge.same_path(current_edge, nearby_edge)\
                        and not Edge.connected(current_edge, nearby_edge):
                    parallel_edges.append((Edge.overlap(current_edge, nearby_edge, relative=True), current_edge, nearby_edge))
            except AssertionError:
                debug("Something went wrong")
                raise

        # Merge edges that have the greatest overlap
        parallel_edges.sort(key=lambda item: -item[0])
        edges_to_remove = set()
        if parallel_edges and parallel_edges[0][0] > overlap_threshold:
            edge1, edge2 = parallel_edges[0][1], parallel_edges[0][2]
            path1, path2 = edge1.path, edge2.path

            # Identify which edges will get affected
            affected = {edge for node in {edge1.source, edge1.target, edge2.source, edge2.target} for edge in node.edges}
            edges_to_remove = affected.copy()
            affected -= set(path1.edges)  # Exclude the edges in p1
            affected -= set(path2.edges)  # Exclude the edges in p2
            affected_paths = set()

            # Merge two edges and create a new path out of the edge.
            # Warning: This could cause edge segmentation. We'll take care of it below.
            new_edge, old_to_new = graph.merge_edges(edge1, edge2)
            new_path = graph.create_path(edges=[new_edge])
            affected_paths.add(new_path)

            # Keep edges (Create copies of edges so nodes won't get deleted when I delete paths.)
            edge_index_1 = path1.edges.index(edge1)
            edge_index_2 = path2.edges.index(edge2)
            edges_1_1, edges_1_2 = path1.split_edges(edge_index_1)
            edges_2_1, edges_2_2 = path2.split_edges(edge_index_2)
            edge_lists = [edges_1_1, edges_1_2, edges_2_1, edges_2_2]
            new_edge_lists = [[e.copy() for e in edges] for edges in edge_lists]
            new_edge_lists = filter(lambda e: e, new_edge_lists)  # remove empty lists

            # Remove old paths
            graph.remove_path(path1.id)
            graph.remove_path(path2.id)

            # Create new paths
            for new_edge_list in new_edge_lists:
                p = graph.create_path(edges=new_edge_list)
                affected_paths.add(p)
                node_to_swap = list(set(p.get_nodes()) & set(old_to_new.keys()))
                assert len(node_to_swap) == 1
                node_to_swap = node_to_swap[0]

                edge_to_swap = list(set(p.edges) & set(node_to_swap.edges))
                assert len(edge_to_swap) == 1
                edge_to_swap = edge_to_swap[0]

                graph.swap_edge_node(edge_to_swap, node_to_swap, old_to_new[node_to_swap])

            # Update affectede edges
            new_edges = []
            for affected_edge in affected:
                try:
                    node_from = list({affected_edge.source, affected_edge.target} & set(old_to_new.keys()))
                    assert len(node_from) == 1
                    node_from = node_from[0]
                    node_to = old_to_new[node_from]
                    other = affected_edge.source if affected_edge.target == node_from else affected_edge.target

                    # Make sure we don't make duplicate paths
                    if not {node_to, other} in new_edges:
                        graph.swap_edge_node(affected_edge, node_from, node_to)
                        new_edges.append({node_to, other})
                        affected_paths.add(affected_edge.path)
                    else:
                        graph.remove_path(affected_edge.path.id)
                except AssertionError:
                    raise

            # Resolve edge segmentation
            affected_paths = list(affected_paths)
            while affected_paths:
                p = affected_paths.pop()
                nodes = p.get_nodes()
                for node in [nodes[0], nodes[-1]]:
                    if len(node.edges) == 2:
                        path1, path2 = node.edges[0].path, node.edges[1].path
                        if path1 == path2:
                            continue
                        new_path = graph.merge_path(path1, path2)
                        if path1 in affected_paths:
                            affected_paths.remove(path1)
                        if path2 in affected_paths:
                            affected_paths.remove(path2)

                        affected_paths.append(new_path)

            # Update the rtree index
    return graph


def make_sidewalks(street_graph, distance_to_sidewalk=15):
    """
    Make a new graph with new sidewalks and crosswalks from the passed graph of streets.
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
    import math
    import numpy as np
    from utilities import latlng_offset_size
    from itertools import product

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

            if not hasattr(curr_node, 'children'):
                curr_node.children = {}
            curr_node.children.setdefault(path.id, []).append(sidewalk_node_1)
            curr_node.children[path.id].append(sidewalk_node_2)
            # for n in [prev_node, curr_node, next_node]:
            #     if not hasattr(n, 'children'):
            #         n.children = {}
            #     n.children.setdefault(path.id, []).append(sidewalk_node_1)
            #     n.children[path.id].append(sidewalk_node_2)

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
    edges_to_swap = {}
    for intersection_node in intersection_nodes:
        adjacent_nodes = street_graph.get_adjacent_nodes(intersection_node)
        adjacent_nodes = sort_nodes(intersection_node, adjacent_nodes)

        if len(adjacent_nodes) == 3:
            # Take care of the case where len(adj_nodes) == 3.
            # Identify the largest angle that are formed by three segments
            # Make a dummy node between two vectors that form the largest angle
            vectors = [intersection_node.vector_to(adjacent_node, normalize=True) for adjacent_node in adjacent_nodes]
            angles = [math.acos(np.dot(vectors[i - 1], vectors[i])) for i in range(3)]
            idx = np.argmax(angles)
            vec_idx = (idx + 1) % 3
            d = latlng_offset_size(intersection_node.lat, vector=vectors[vec_idx], distance=distance_to_sidewalk)
            dummy_coordinate = intersection_node.vector() - vectors[vec_idx] * d
            dummy_node = Node(-1, dummy_coordinate[0], dummy_coordinate[1])
            adjacent_nodes.insert(idx, dummy_node)

        # Create crosswalk nodes
        assert len(adjacent_nodes) > 3
        crosswalk_nodes = []
        for i in range(len(adjacent_nodes)):
            # Take a pair of adjacent nodes and make a new node between them.
            vec_intersection_to_adjacent_1 = intersection_node.vector_to(adjacent_nodes[i - 1], normalize=True)
            vec_intersection_to_adjacent_2 = intersection_node.vector_to(adjacent_nodes[i], normalize=True)
            vector_intersection_to_crosswalk = vec_intersection_to_adjacent_1 + vec_intersection_to_adjacent_2
            vector_intersection_to_crosswalk /= np.linalg.norm(vector_intersection_to_crosswalk)
            d = latlng_offset_size(intersection_node.lat, vector=vector_intersection_to_crosswalk, distance=distance_to_sidewalk)
            crosswalk_coordinate = intersection_node.vector() + vector_intersection_to_crosswalk * d
            crosswalk_node = sidewalk_graph.create_node(float(crosswalk_coordinate[1]), float(crosswalk_coordinate[0]))
            crosswalk_nodes.append(crosswalk_node)
            crosswalk_node.parents = [adjacent_nodes[i - 1], adjacent_nodes[i]]

        # Create crosswalk paths
        crosswalk_paths = []
        for crosswalk_node_pair in window(crosswalk_nodes, 2):
            crosswalk = sidewalk_graph.create_path(nodes=crosswalk_node_pair)
            crosswalk_paths.append(crosswalk)
        crosswalk = sidewalk_graph.create_path(nodes=[crosswalk_nodes[-1], crosswalk_nodes[0]])
        crosswalk_paths.append(crosswalk)

        # Connect the crosswalk nodes to appropriate sidewalk nodes
        for street_path_id in intersection_node.children:
            street_path = street_graph.get_path(street_path_id)
            street_nodes = street_path.get_nodes()
            idx = street_nodes.index(intersection_node)
            adjacent_node = street_nodes[1] if idx == 0 else street_nodes[idx - 1]

            sidewalk_edges = map(lambda edge_set: list(edge_set)[0],
                                 filter(lambda edges: len(edges) > 0,
                                        map(lambda pair: set(pair[0].edges) & set(pair[1].edges),
                                            product(adjacent_node.children[street_path_id], intersection_node.children[street_path_id]))))

            for sidewalk_edge in sidewalk_edges:
                if sidewalk_edge.source in intersection_node.children[street_path_id]:
                    node_to_swap = sidewalk_edge.source
                    other = sidewalk_edge.target
                else:
                    node_to_swap = sidewalk_edge.target
                    other = sidewalk_edge.source

                # Identify which one of crosswalk_nodes to swap
                curr_crosswalk_nodes = filter(lambda node: adjacent_node in node.parents, crosswalk_nodes)
                assert len(curr_crosswalk_nodes) == 2  # Two crosswalk nodes should have been created from each adj node

                crosswalk_node = curr_crosswalk_nodes[0]
                vec_intersection_to_adjacent_node = intersection_node.vector_to(adjacent_node, normalize=True)
                vec_intersection_to_sidewalk_node = intersection_node.vector_to(other, normalize=True)
                vec_intersection_to_crosswalk_node = intersection_node.vector_to(crosswalk_node, normalize=True)
                if np.cross(vec_intersection_to_adjacent_node, vec_intersection_to_crosswalk_node) * np.cross(vec_intersection_to_adjacent_node, vec_intersection_to_sidewalk_node) < 0:
                    crosswalk_node = curr_crosswalk_nodes[1]
                edges_to_swap.setdefault(sidewalk_edge, []).append((node_to_swap, crosswalk_node))

    # Swap sidewalk edges
    for sidewalk_edge in edges_to_swap:
        node_pairs = edges_to_swap[sidewalk_edge]
        if 1 < len(sidewalk_edge.path.edges):
            assert len(node_pairs) == 1  # It should safice to swap a single node of an edge
            node_to_swap, crosswalk_node = node_pairs[0]
            sidewalk_graph.swap_edge_node(sidewalk_edge, node_to_swap, crosswalk_node)
        elif len(node_pairs) == 1:
            # Todo: I don' quite get how this happend... Need to be investigated.
            node_to_swap, crosswalk_node = node_pairs[0]
            sidewalk_graph.swap_edge_node(sidewalk_edge, node_to_swap, crosswalk_node)
        elif len(node_pairs) == 2:
            sidewalk_graph.swap_edge(sidewalk_edge, (node_pairs[0][0], node_pairs[1][0]), (node_pairs[0][1], node_pairs[1][1]))
        else:
            raise ValueError("This should not happen.")
    return sidewalk_graph


def sort_nodes(center_node, nodes):
    """
    Sort nodes around the center_node in clockwise
    """
    import math

    def compare_angle(n1, n2):
        angle1 = (math.degrees(center_node.angle_to(n1)) + 360.) % 360
        angle2 = (math.degrees(center_node.angle_to(n2)) + 360.) % 360

        if angle1 < angle2:
            return -1
        elif angle1 == angle2:
            return 0
        else:
            return 1
    return sorted(nodes, cmp=compare_angle)


def main():
    debug("Start...")
    filename = "../resources/SmallMap_04.osm"
    geometric_graph = parse_osm(filename)
    geometric_graph = clean_edge_segmentation(geometric_graph)
    geometric_graph = split_path(geometric_graph)
    geometric_graph = remove_short_edges(geometric_graph)
    # geometric_graph = merge_parallel_edges(geometric_graph)
    # geometric_graph.visualize()
    sidewalk_graph = make_sidewalks(geometric_graph)
    sidewalk_graph.visualize()


if __name__ == "__main__":
    main()
