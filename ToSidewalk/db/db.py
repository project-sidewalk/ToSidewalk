from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from geoalchemy2.shape import *
from shapely.geometry import LineString
import json
import os
import numpy as np

Base = declarative_base()


class DB(object):

    def __init__(self, setting_file="../.settings"):
        """Interacting with PostGIS using Python
        http://gis.stackexchange.com/questions/147240/how-to-efficiently-use-a-postgres-db-with-python
        http://geoalchemy-2.readthedocs.org/en/latest/orm_tutorial.html
        """
        with file(setting_file) as f:

            j = json.loads(f.read())

            if "username" in j:
                user_name = j["username"]
            else:
                user_name = "root"

            if "password" in j:
                password = j["password"]
            else:
                password = ""

            if "database" in j:
                database_name = j["database"]
            else:
                database_name = "routing"

        self.engine = create_engine('postgresql://%s@localhost/%s' % (user_name, database_name), echo=True)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()


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

    setting_file = os.path.relpath("../../", os.path.dirname(__file__)) + "/.settings"
    db = DB(setting_file)
    print db.example_select()

