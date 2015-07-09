import logging as log
import math
import numpy as np
import os
import gzip
import glob
import shutil
from latlng import LatLng
from nodes import Node, Nodes
from ways import Sidewalk, Sidewalks, Street
from utilities import window, latlng_offset_size, latlng_offset
from network import OSM, parse
from datetime import datetime
log.basicConfig(format="", level=log.DEBUG)

# dummy_street = Street()
distance_to_sidewalk = 0.00008

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
    v_new = v_curr + v * 0.00011
    # v_new = v_curr + np.array(latlng_offset(v_curr[0], vector=v, distance=7))
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


def connect_crosswalk_nodes(sidewalk_network, crosswalk_node_ids):
    """
    Connect crosswalk nodes to sidewalk nodes. Then remove redundant sidewalk nodes around the intersection.
    :param sidewalk_network:
    :param crosswalk:
    :return:
    """
    # crosswalk_node_ids = crosswalk.get_node_ids()[:-1]  # Crosswalk has a redundant node at the end.

    for crosswalk_node_id in crosswalk_node_ids[:-1]:
        try:
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
                try:
                    sidewalk_node_1_from_intersection, sidewalk_node_2_from_intersection = intersection_node.get_sidewalk_nodes(shared_street_id)
                except TypeError:
                    # Todo: Issue #29. Sometimes shared_street_id does not exist in the intersection_node.
                    log.exception("connect_crosswalk_nodes(): shared_street_id %s does not exist." % shared_street_id)
                    continue
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

                sidewalk_network.swap_nodes(node_to_swap, crosswalk_node)
        except ValueError:
            log.exception("Error while connecting crosswalk nodes, so skipping...")
            continue
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
        try:
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
                dummy_vector = - vectors[vec_idx] * distance_to_sidewalk
                inverse_vec = - vectors[vec_idx]
                # dummy_vector = inverse_vec * latlng_offset_size(vectors[vec_idx][1], vectors[vec_idx][0],
                #                                                 vector=inverse_vec,
                #                                                 distance=distance_to_sidewalk)
                dummy_coordinate_vector = v_curr + dummy_vector
                dummy_node = Node(None, dummy_coordinate_vector[0], dummy_coordinate_vector[1])
                adj_street_nodes.insert(idx, dummy_node)

            # Create crosswalk nodes and add a cross walk to the data structure
            try:
                crosswalk_nodes = make_crosswalk_nodes(intersection_node, adj_street_nodes)
            except ValueError:
                raise

            crosswalk_node_ids = [node.id for node in crosswalk_nodes]
            crosswalk_node_ids.append(crosswalk_node_ids[0])
            # crosswalk = Sidewalk(None, crosswalk_node_ids, "crosswalk")

            # Add nodes to the network
            for crosswalk_node in crosswalk_nodes:
                sidewalk_network.add_node(crosswalk_node)
                sidewalk_network.nodes.crosswalk_node_ids.append(crosswalk_node.id)

            # Add crosswalks to the network
            crosswalk_node_id_pairs = window(crosswalk_node_ids, 2)
            for node_id_pair in crosswalk_node_id_pairs:
                n1 = sidewalk_network.nodes.get(node_id_pair[0])
                n2 = sidewalk_network.nodes.get(node_id_pair[1])
                if len(n1.get_way_ids()) == 1 and len(n2.get_way_ids()) == 1:
                    crosswalk = Sidewalk(None, list(node_id_pair), "footway")
                else:
                    crosswalk = Sidewalk(None, list(node_id_pair), "crosswalk")
                sidewalk_network.add_way(crosswalk)

            # Connect the crosswalk nodes with correct sidewalk nodes
            connect_crosswalk_nodes(sidewalk_network, crosswalk_node_ids)
        except ValueError:
            log.exception("ValueError in make_sidewalks, so skipping...")
            continue
    return

def split_large_osm_file(filename):
    command = "java -Xmx4000M -jar splitter.jar --output=xml --output-dir=data --max-nodes=15000 " + filename + " > splitter.log"
    os.system(command)
def merge_sidewalks(sidewalk_network1, sidewalk_network2):
    """Returns a merged sidewalk network

    Takes two sidewalk networks and merges them without duplicating sidewalk data"""

    for node in sidewalk_network1.nodes.get_list():
        node.confirmed = True

    '''
    # add new nodes from sidewalk_network2 to sidewalk_network1
    for sidewalk_node in sidewalk_network2.nodes.get_list():
        in_other = False
        same_node = None
        for other_sidewalk_node in sidewalk_network1.nodes.get_list():
            if sidewalk_node.location() == other_sidewalk_node.location():
                in_other = True
                same_node = other_sidewalk_node
        if not in_other: # If street network 2 contains the node but street network 1 does not
            sidewalk_network1.add_node(sidewalk_node) # Add node from street network 2 to street network 1
        else: # If both networks contain the node
            sidewalk_network2.nodes.update(sidewalk_node.id, same_node)
    '''
    # add new nodes from sidewalk_network2 to sidewalk_network1

    network1_dict = {}
    for sidewalk_node in sidewalk_network1.nodes.get_list():
        network1_dict[sidewalk_node.location] = sidewalk_node

    for sidewalk_node in sidewalk_network2.nodes.get_list():
        if sidewalk_node.location not in network1_dict:
            sidewalk_network1.add_node(sidewalk_node)
        else:
            sidewalk_network2.nodes.update(sidewalk_node.id, network1_dict[sidewalk_node.location])

    # add new ways from sidewalk_network2 to sidewalk_network1
    for way in sidewalk_network2.ways.get_list():
        # ensure all ways have correct nids, if incorrect update to correct nid from network1
        for nid in way.get_node_ids():
            if sidewalk_network1.nodes.get(nid) is None:
                 way.swap_nodes(nid, sidewalk_network2.nodes.get(nid).id)

        has_confirmed_parents = False
        for nid in way.get_node_ids():
            if sidewalk_network1.nodes.get(nid).confirmed:
                has_confirmed_parents = True
        if not has_confirmed_parents:
            sidewalk_network1.add_way(way)

    return sidewalk_network1

def main(street_network):
    sidewalk_network = make_sidewalks(street_network)
    make_crosswalks(street_network, sidewalk_network)

    return sidewalk_network

if __name__ == "__main__":
    filename = "../resources/SmallMap_04.osm"
    # filename = "../resources/ParallelLanes_03.osm"
    # filename = "../resources/tests/out2340_3134.pbfr"
    street_network = parse(filename)
    street_network.preprocess()
    sidewalk_network = main(street_network)

    # street_network.merge_parallel_street_segments2()
    with open("../resources/SmallMap_04_Sidewalks.geojson", "wb") as f:
        geojson = sidewalk_network.export(data_type="ways")
        print geojson
        print >>f, geojson

    with open("../resources/SmallMap_04_SidewalkNodes.geojson", "wb") as f:
        geojson = sidewalk_network.export(data_type="nodes")
        print >>f, geojson

    with open("../resources/SmallMap_04_Streets.geojson", "wb") as f:
        geojson = street_network.export(data_type="ways")
        print >>f, geojson

    with open("../resources/SmallMap_04_StreetNodes.geojson", "wb") as f:
        geojson = street_network.export(data_type="nodes")
        print >>f, geojson

    print geojson
    # f = open('output.geojson', 'w')
    # print >>f, geojson
    # print sidewalk_network.export()


    #filename = "../resources/SmallMap_04.osm"
    # filename = "../resources/ParallelLanes_03.osm"
    # filename = "../resources/tests/out2340_3134.pbfr"





    # filename = "../resources/SimpleWay_01.osm"
    # filename = "../resources/Simple4WayIntersection_01.osm"
    #filename = "../resources/SmallMap_01.osm"
    #filename = "../resources/SmallMap_02.osm"

    # filename = "../resources/ParallelLanes_03.osm"
    # filename = "../resources/MapPair_B_01.osm"
    # filename = "../resources/SegmentedStreet_01.osm"
    # filename = "../resources/ParallelLanes_03.osm"
    #filename = "../resources/ParallelLanes_03.osm"
    #filename = "../resources/MapPair_B_01.osm"
    # filename = "../resources/SegmentedStreet_01.osm"
    #filename = "../resources/ParallelLanes_03.osm"

    #filename = "../resources/SmallMap_04.osm"

    """

    # Clear the data directory before beginning
    shutil.rmtree('data/')
    filename = "../resources/benningv2.osm"

    split_large_osm_file(filename)

    files = glob.glob("data/*.gz")
    log.debug("Working with " + str(files))
    # Decompress each GZ file
    for filename in files:
        f = gzip.open(filename, 'rb')
        file_content = f.read()
        log.debug("writing to "+filename+".osm")
        outfile = open(filename+".osm", "w")
        outfile.write(file_content)
        outfile.close()
    files = glob.glob("data/*.osm")

    street_networks = []
    for filename in files:
        log.debug("Parsing " + filename)
        try:
            new_street_network = parse(filename)
            street_networks.append(new_street_network)
        except:
            log.exception("Failed to create this street network, skipping...")
            continue

    print("Preprocessing street networks...")
    for street_network in street_networks:
        try:

            street_network.preprocess()
            print(street_network.export())
        except:
            log.exception("Error preprocessing this street network. Skipping.")
            continue

        street_network.parse_intersections()

    print("Merging sidewalk networks...")
    sidewalk_networks = []
    print("1")
    for street_network in street_networks:
        try:
            sidewalk_networks.append(main(street_network))
        except:
            log.exception("Uh oh, creating this sidewalk network failed. Skipping...")
            continue
    sidewalk_network_main = sidewalk_networks[0]
    print("2")
    for sidewalk_network in sidewalk_networks[1:]:
        sidewalk_network_main = merge_sidewalks(sidewalk_network_main, sidewalk_network)
    print("3")
    geojson = sidewalk_network_main.export(format="geojson")

    f = open('output.geojson','w')
    print >>f, geojson

    """