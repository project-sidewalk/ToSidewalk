import db
from Sidewalk import SidewalkEdgeTable

from geoalchemy2.shape import *
from shapely.geometry import LineString
import json
import numpy as np
import os

def main():
    database = db.DB("../../.settings")
    session = database.session
    query = session.query(SidewalkEdgeTable).filter_by(deleted=False)
    for item in query:
        print item.sidewalk_edge_id, item.x1, item.y1


def example_insert(self):
    """
    Example

    http://geoalchemy-2.readthedocs.org/en/latest/core_tutorial.html

    :return:
    """
    filename = os.path.relpath("../../resources", os.path.dirname(__file__)) + "/SmallMap_04_Sidewalks.geojson"
    with open(filename) as f:
        geojson = json.loads(f.read())

    table = SidewalkEdgeTable().__table__
    conn = self.engine.connect()
    for feature in geojson["features"]:
        # print pp.pprint(feature)
        coordinates = feature["geometry"]["coordinates"]
        properties = feature["properties"]

        geom = from_shape(LineString(coordinates), srid=4326)
        sidewalk_edge_id = int(np.uint32(properties["sidewalk_edge_id"]))  # [Issue X] I've just realized functions in pgrouting assume 32bit int, which kind of sucks. Hacking it for now with np.uint32
        x1 = float(properties["x1"])
        y1 = float(properties["y1"])
        x2 = float(properties["x2"])
        y2 = float(properties["y2"])
        way_type = properties["type"]
        source = int(np.uint32(properties["source"]))
        target = int(np.uint32(properties["target"]))

        ins = table.insert().values(geom=geom,
                                    sidewalk_edge_id=sidewalk_edge_id,
                                    x1=x1,
                                    y1=y1,
                                    x2=x2,
                                    y2=y2,
                                    way_type=way_type,
                                    source=source,
                                    target=target,
                                    deleted=False,
                                    parent_sidewalk_edge_id=None)

        conn.execute(ins)


if __name__ == "__main__":
    main()
