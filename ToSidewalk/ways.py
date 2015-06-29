import json
import numpy as np
import logging as log
class Way(object):
    def __init__(self, wid=None, nids=[], type=None):
        if wid is None:
            self.id = str(id(self))
        else:
            self.id = str(wid)
        self.nids = list(nids)
        self.type = type
        self.user = 'test'
        self.parent_ways = None

        assert len(self.nids) > 1

    def belongs_to(self):
        """
        Returns a parent Ways object
        :return:
        """
        return self.parent_ways

    def export(self):
        """
        A utility method to export the data as a geojson dump
        :return: A geojson data in a string format.
        """
        if self.parent_ways and self.parent_ways.parent_network:
            geojson = dict()
            geojson['type'] = "FeatureCollection"
            geojson['features'] = []
            feature = self.get_geojson_features()
            geojson['features'].append(feature)
            return json.dumps(geojson)

    def get_geojson_features(self):
        """
        A utilitie method to export the data as a geojson dump
        :return: A dictionary of geojson features
        """
        feature = dict()
        feature['properties'] = {
            'type': self.type,
            'id': self.id,
            'user': self.user,
            "stroke-width": 2,
            "stroke-opacity": 1,
            'stroke': '#e93f3f'
        }
        feature['type'] = 'Feature'
        feature['id'] = 'way/%s' % (self.id)

        coordinates = []
        for nid in self.nids:
            node = self.parent_ways.parent_network.nodes.get(nid)
            coordinates.append([node.lng, node.lat])
        feature['geometry'] = {
            'type': 'LineString',
            'coordinates': coordinates
        }
        return feature

    def get_node_ids(self):
        """
        Get a list of node ids
        :return: A list of node ids
        """
        return self.nids

    def get_shared_node_ids(self, other):
        """
        Get node ids that are shared between two Way objects. other could be either
        a list of node ids or a Way object.
        :param other: A list of node ids or a Way object
        :return: A list of node ids
        """
        if type(other) == list:
            return list(set(self.nids) & set(other))
        else:
            return list(set(self.nids) & set(other.get_node_ids()))

    def remove_node(self, nid_to_remove):
        """
        Remove a node from the data structure
        http://stackoverflow.com/questions/2793324/is-there-a-simple-way-to-delete-a-list-element-by-value-in-python
        :param nid_to_remove: A node id
        """
        self.nids = [nid for nid in self.nids if nid != nid_to_remove]

    def swap_nodes(self, nid_from, nid_to):
        """
        Swap a node that forms the way with another node
        :param nid_from: A node id
        :param nid_to: A node id
        """
        index_from = self.nids.index(nid_from)
        self.nids[index_from] = nid_to


class Ways(object):
    def __init__(self):
        self.ways = {}
        self.intersection_node_ids = []
        self.parent_network = None

    def __eq__(self, other):
        return id(self) == id(other)

    def add(self, way):
        """
        Add a Way object
        :param way: A Way object
        """
        way.parent_ways = self
        self.ways[way.id] = way

    def belongs_to(self):
        """
        Return a parent network
        :return: A Network object
        """
        return self.parent_network

    def get(self, wid):
        """
        Search and return a Way object by its id
        :param wid: A way id
        :return: A Way object
        """
        assert wid in self.ways
        return self.ways[wid]

    def get_list(self):
        """
        Get a list of all Way objects in the data structure
        :return: A list of Way objects
        """
        return self.ways.values()

    def remove(self, wid):
        """
        Remove a way from the data structure
        http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
        :param wid: A way id
        """
        del self.ways[wid]

    def set_intersection_node_ids(self, nids):
        self.intersection_node_ids = nids

# Notes on inheritance
# http://stackoverflow.com/questions/576169/understanding-python-super-with-init-methods
class Street(Way):
    def __init__(self, wid=None, nids=[], type=None):
        super(Street, self).__init__(wid, nids, type)
        self.sidewalk_ids = []  # Keep track of which sidewalks were generated from this way
        self.distance_to_sidewalk = 0.00008
        self.oneway = 'undefined'
        self.ref = 'undefined'

    def getdirection(self):
        startnode=self.parent_ways.parent_network.nodes.get(self.get_node_ids()[0])
        endnode=self.parent_ways.parent_network.nodes.get(self.get_node_ids()[-1])
        startlat=startnode.lat
        endlat = endnode.lat

        if startlat>endlat:
            return 1
        else:
            return -1

    def set_oneway_tag(self, oneway_tag):
        self.oneway = oneway_tag

    def set_ref_tag(self, ref_tag):
        self.ref = ref_tag

    def get_oneway_tag(self):
        return self.oneway

    def get_ref_tag(self):
        return self.ref

    def append_sidewalk_id(self, way_id):
        self.sidewalk_ids.append(way_id)
        return self

    def get_sidewalk_ids(self):
        return self.sidewalk_ids

    def get_length(self):
        start_node = self.parent_ways.parent_network.nodes.get(self.get_node_ids()[0])
        end_node = self.parent_ways.parent_network.nodes.get(self.get_node_ids()[-1])
        vec = np.array(start_node.location()) - np.array(end_node.location())
        length = abs(vec[0] - vec[-1])
        return length

class Streets(Ways):
    def __init__(self):
        super(Streets, self).__init__()

class Sidewalk(Way):
    def __init__(self, wid=None, nids=[], type=None):
        super(Sidewalk, self).__init__(wid, nids, type)

    def set_street_id(self, street_id):
        """
        Set the parent street id
        :param street_id: A street id
        """
        self.street_id = street_id

class Sidewalks(Ways):
    def __init__(self):
        super(Sidewalks, self).__init__()
        self.street_id = None

