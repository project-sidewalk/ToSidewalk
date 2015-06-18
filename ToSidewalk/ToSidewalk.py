import logging as log
import math
import numpy as np

from latlng import LatLng
from nodes import Node, Nodes
from ways import Sidewalk, Sidewalks, Street
from utilities import window
from network import OSM, parse

log.basicConfig(format="", level=log.DEBUG)

dummy_street = Street()

def make_sidewalk_nodes(street, prev_node, curr_node, next_node):
    if prev_node is None:
        v = - curr_node.vector_to(next_node, normalize=False)
        vec_prev = curr_node.vector() + v
        prev_node = Node(None, vec_prev[0], vec_prev[1])
    elif next_node is None:
        v = - curr_node.vector_to(prev_node, normalize=False)
        vec_next = curr_node.vector() + v
        next_node = Node(None, vec_next[0], vec_next[1])

    curr_latlng = np.array(curr_node.location())

    v_cp_n = curr_node.vector_to(prev_node, normalize=True)
    v_cn_n = curr_node.vector_to(next_node, normalize=True)
    v_sidewalk = v_cp_n + v_cn_n

    if np.linalg.norm(v_sidewalk) < 0.0000000001:
        v_sidewalk_n = np.array([v_cn_n[1], - v_cn_n[0]])
    else:
        v_sidewalk_n = v_sidewalk / np.linalg.norm(v_sidewalk)

    p1 = curr_latlng + street.distance_to_sidewalk * v_sidewalk_n
    p2 = curr_latlng - street.distance_to_sidewalk * v_sidewalk_n

    p_sidewalk_1 = Node(None, p1[0], p1[1])
    p_sidewalk_2 = Node(None, p2[0], p2[1])

    curr_node.append_sidewalk_node(street.id, p_sidewalk_1)
    curr_node.append_sidewalk_node(street.id, p_sidewalk_2)

    # Figure out on which side you want to put each sidewalk node
    v_c1 = curr_node.vector_to(p_sidewalk_1)
    if np.cross(v_cn_n, v_c1) > 0:
        return p_sidewalk_1, p_sidewalk_2
    else:
        return p_sidewalk_2, p_sidewalk_1


def make_sidewalks(street_network):
    # Go through each street and create sidewalks on both sides of the road.
    sidewalks = Sidewalks()
    sidewalk_nodes = Nodes()
    sidewalk_network = OSM(sidewalk_nodes, sidewalks, street_network.bounds)

    for street in street_network.ways.get_list():
        sidewalk_1_nodes = []
        sidewalk_2_nodes = []

        # Create sidewalk nodes
        for prev_nid, curr_nid, next_nid in window(street.nids, 3, padding=1):
            curr_node = street_network.nodes.get(curr_nid)
            prev_node = street_network.nodes.get(prev_nid)
            next_node = street_network.nodes.get(next_nid)

            n1, n2 = make_sidewalk_nodes(street, prev_node, curr_node, next_node)

            sidewalk_network.add_node(n1)
            sidewalk_network.add_node(n2)

            sidewalk_1_nodes.append(n1)
            sidewalk_2_nodes.append(n2)

        # Keep track of parent-child relationship between streets and sidewalks.
        # And set nodes' adjacency information
        sidewalk_1_nids = [node.id for node in sidewalk_1_nodes]
        sidewalk_2_nids = [node.id for node in sidewalk_2_nodes]
        sidewalk_1 = Sidewalk(None, sidewalk_1_nids, "footway")
        sidewalk_2 = Sidewalk(None, sidewalk_2_nids, "footway")
        sidewalk_1.set_street_id(street.id)
        sidewalk_2.set_street_id(street.id)
        street.append_sidewalk_id(sidewalk_1.id)
        street.append_sidewalk_id(sidewalk_2.id)

        # Add sidewalks to the network
        sidewalk_network.add_way(sidewalk_1)
        sidewalk_network.add_way(sidewalk_2)

    return sidewalk_network


def sort_nodes(center_node, nodes):
    """
    Sort nodes around the center_node in clockwise
    """
    def cmp(n1, n2):
        angle1 = (math.degrees(center_node.angle_to(n1)) + 360.) % 360
        angle2 = (math.degrees(center_node.angle_to(n2)) + 360.) % 360

        if angle1 < angle2:
            return -1
        elif angle1 == angle2:
            return 0
        else:
            return 1
    return sorted(nodes, cmp=cmp)


def make_crosswalk_node(node, n1, n2):
    """
    Make a crosswalk node from three nodes. The first one is a pivot node and two other nodes are ones that are
    connected to the pivot node. The new node is created between the two nodes.
    :param node:
    :param n1:
    :param n2:
    :return:
    """
    v_curr = node.vector()

    v1 = node.vector_to(n1, normalize=True)
    v2 = node.vector_to(n2, normalize=True)
    v = v1 + v2
    v /= np.linalg.norm(v)  # Normalize the vector
    v_new = v_curr + v * node.crosswalk_distance
    return Node(None, v_new[0], v_new[1])


def make_crosswalk_nodes(intersection_node, adj_street_nodes):
    """
    Create new crosswalk nodes
    :param intersection_node:
    :param adj_street_nodes:
    :return: crosswalk_nodes, source_table
    """
    if len(adj_street_nodes) < 4:
        raise ValueError("You need to pass 4 or more nodes for adj_street_nodes ")

    crosswalk_nodes = []
    for i in range(len(adj_street_nodes)):
        n1 = adj_street_nodes[i - 1]
        n2 = adj_street_nodes[i]
        crosswalk_node = make_crosswalk_node(intersection_node, n1, n2)

        # Keep track of from which streets the crosswalk nodes are created.
        way_ids = []
        for wid in n1.get_way_ids():
            way_ids.append(wid)
        for wid in n2.get_way_ids():
            way_ids.append(wid)
        way_ids = intersection_node.get_shared_way_ids(way_ids)

        crosswalk_node.way_ids = way_ids
        crosswalk_nodes.append(crosswalk_node)
        crosswalk_node.parents = (intersection_node, n1, n2)

    return crosswalk_nodes


def connect_crosswalk_nodes(sidewalk_network, crosswalk):
    """
    Connect crosswalk nodes to sidewalk nodes. Then remove redundant sidewalk nodes around the intersection.
    :param sidewalk_network:
    :param crosswalk:
    :return:
    """
    crosswalk_node_ids = crosswalk.get_node_ids()[:-1]  # Crosswalk has a redundant node at the end.

    for crosswalk_node_id in crosswalk_node_ids:
        # Get the intersection node and two nodes that created the intersection sidewalk node
        crosswalk_node = sidewalk_network.nodes.get(crosswalk_node_id)
        intersection_node, adjacent_street_node1, adjacent_street_node2 = crosswalk_node.parents

        # Connect sidewalk nodes created from adjacent_street_node1 and adjacent_street_node2
        # Get sidewalk nodes that are created from the street node, and
        # identify which one should be connected to crosswalk_node
        for adjacent_street_node in [adjacent_street_node1, adjacent_street_node2]:
            # Skip the dummy node
            if len(adjacent_street_node.get_way_ids()) == 0:
                continue

            # Create a vector from the intersection node to the adjacent street node.
            # Then also create a vector from the intersection node to the sidewalk node
            v_adjacent_street_node = intersection_node.vector_to(adjacent_street_node, normalize=True)
            shared_street_id = intersection_node.get_shared_way_ids(adjacent_street_node)[0]
            sidewalk_node_1_from_intersection, sidewalk_node_2_from_intersection = intersection_node.get_sidewalk_nodes(shared_street_id)
            v_sidewalk_node_1_from_intersection = intersection_node.vector_to(sidewalk_node_1_from_intersection, normalize=True)

            # Check which one of sidewalk_node_1_from_intersection and sidewalk_node_2_from_intersection are
            # on the same side of the road with crosswalk_node.
            # If the sign of the cross product from v_adjacent_street_node to v_crosswalk_node is same as
            # that of v_adjacent_street_node to v_sidewalk_node_1_from_intersection, then
            # sidewalk_node_1_from_intersection should be on the same side.
            # Otherwise, sidewalk_node_2_from_intersection should be on the same side with crosswalk_node.
            v_crosswalk_node = intersection_node.vector_to(crosswalk_node, normalize=True)
            if np.cross(v_adjacent_street_node, v_crosswalk_node) * np.cross(v_adjacent_street_node, v_sidewalk_node_1_from_intersection) > 0:
                node_to_swap = sidewalk_node_1_from_intersection
            else:
                node_to_swap = sidewalk_node_2_from_intersection

            sidewalk_network.swap_nodes(node_to_swap.id, crosswalk_node.id)
    return

def make_crosswalks(street_network, sidewalk_network):
    """
    Make crosswalks at intersections
    :param street_network: Street network object
    :param sidewalk_network: Sidewalk network object
    """

    intersection_nodes = street_network.nodes.get_intersection_nodes()
    # intersection_nodes = [street_network.nodes.get(nid) for nid in intersection_node_ids]

    # Create sidewalk nodes for each intersection node and overwrite the adjacency information
    for intersection_node in intersection_nodes:
        adj_street_nodes = street_network.get_adjacent_nodes(intersection_node)
        adj_street_nodes = sort_nodes(intersection_node, adj_street_nodes)
        v_curr = intersection_node.vector()

        if len(adj_street_nodes) == 3:
            # Take care of the case where len(adj_nodes) == 3.
            # Identify the largest angle that are formed by three segments
            # Make a dummy node between two vectors that form the largest angle
            # Using the four nodes (3 original nodes and a dummy node), create crosswalk nodes
            vectors = [intersection_node.vector_to(adj_street_node, normalize=True) for adj_street_node in adj_street_nodes]
            angles = [math.acos(np.dot(vectors[i - 1], vectors[i])) for i in range(3)]

            idx = np.argmax(angles)
            vec_idx = (idx + 1) % 3
            dummy_vector = - vectors[vec_idx] * dummy_street.distance_to_sidewalk
            dummy_coordinate_vector = v_curr + dummy_vector
            dummy_node = Node(None, dummy_coordinate_vector[0], dummy_coordinate_vector[1])
            adj_street_nodes.insert(idx, dummy_node)

        # Create crosswalk nodes and add a cross walk to the data structure
        crosswalk_nodes = make_crosswalk_nodes(intersection_node, adj_street_nodes)
        crosswalk_node_ids = [node.id for node in crosswalk_nodes]
        crosswalk_node_ids.append(crosswalk_node_ids[0])
        crosswalk = Sidewalk(None, crosswalk_node_ids, "crosswalk")
        for crosswalk_node in crosswalk_nodes:
            sidewalk_network.add_node(crosswalk_node)
            sidewalk_network.nodes.crosswalk_node_ids.append(crosswalk_node.id)

        sidewalk_network.add_way(crosswalk)

        # Connect the crosswalk nodes with correct sidewalk nodes
        connect_crosswalk_nodes(sidewalk_network, crosswalk)
    return


def main(street_network):
    sidewalk_network = make_sidewalks(street_network)
    make_crosswalks(street_network, sidewalk_network)

    output = sidewalk_network.export(format='geojson')
    return output


if __name__ == "__main__":
    # filename = "../resources/SimpleWay_01.osm"
    # filename = "../resources/Simple4WayIntersection_01.osm"
    # filename = "../resources/SmallMap_01.osm"
    #filename = "../resources/ParallelLanes_03.osm"
    #filename = "../resources/MapPair_B_01.osm"
    # filename = "../resources/SegmentedStreet_01.osm"
    #filename = "../resources/ParallelLanes_03.osm"

    filename = "../resources/SmallMap_04.osm"
    #filename = "../resources/benning.osm"

    street_network = parse(filename)
    street_network.preprocess()
    street_network.parse_intersections()

    geojson = main(street_network)
    print geojson

