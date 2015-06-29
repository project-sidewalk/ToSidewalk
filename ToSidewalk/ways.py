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
        return self.parent_ways

    def export(self):
        if self.parent_ways and self.parent_ways.parent_network:
            geojson = {}
            geojson['type'] = "FeatureCollection"
            geojson['features'] = []
            feature = self.get_geojson_features()
            geojson['features'].append(feature)
            return json.dumps(geojson)

    def get_geojson_features(self):
        feature = {}
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
        return self.nids

    def get_shared_node_ids(self, other):
        """
        Other could be either a list of node ids or a Way object
        """
        if type(other) == list:
            return list(set(self.nids) & set(other))
        else:
            return list(set(self.nids) & set(other.get_node_ids()))

    def remove_node(self, nid_to_remove):
        # http://stackoverflow.com/questions/2793324/is-there-a-simple-way-to-delete-a-list-element-by-value-in-python
        self.nids = [nid for nid in self.nids if nid != nid_to_remove]

    def swap_nodes(self, nid_from, nid_to):

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
        way.parent_ways = self
        self.ways[way.id] = way

    def belongs_to(self):
        return self.parent_network

    def get(self, wid):
        assert wid in self.ways
        return self.ways[wid]

    def get_list(self):
        return self.ways.values()

    def remove(self, wid):
        # http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
        del self.ways[wid]
        return

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
        """  Set the parent street id """
        self.street_id = street_id
        return

class Sidewalks(Ways):
    def __init__(self):
        super(Sidewalks, self).__init__()
        self.street_id = None

