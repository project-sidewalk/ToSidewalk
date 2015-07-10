from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from geoalchemy2.shape import *
from shapely.geometry import LineString, mapping, Point
import shapely.wkb as wkb
import json
import os
import pprint as pp
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

    def example2(self):
        """Example
        """
        query = self.session.query(WaysTable)
        feature_collection = {
            "type": "FeatureCollection",
            "features": []
        }

        for item in query:
            linestring = mapping(LineString(wkb.loads(str(item.wkb_geometry), hex=True)))
            feature = {
                "type": "Feature",
                "geometry": linestring,
                "properties": {}
            }
            feature_collection["features"].append(feature)
        return json.dumps(feature_collection)

    def example_select(self):
        """
        Example

        :return:
        """
        query = self.session.query(SidewalkEdgesTable)
        for item in query:
            print item

    def example_insert(self):
        """
        Example

        http://geoalchemy-2.readthedocs.org/en/latest/core_tutorial.html

        :return:
        """
        filename = os.path.relpath("../../resources", os.path.dirname(__file__)) + "/SmallMap_04_Sidewalks.geojson"
        with open(filename) as f:
            geojson = json.loads(f.read())

        table = SidewalkEdgesTable().__table__
        conn = self.engine.connect()
        for feature in geojson["features"]:
            # print pp.pprint(feature)
            coordinates = feature["geometry"]["coordinates"]
            properties = feature["properties"]

            geom = from_shape(LineString(coordinates), srid=4326)
            way_id = int(np.uint32(properties["id"]))  # [Issue X] I've just realized functions in pgrouting assume 32bit int, which kind of sucks. Hacking it for now with np.uint32
            osm_ways = str(properties["osm_ways"])
            cost = float(properties["cost"])
            reverse_cost = float(properties["reverse_cost"])
            user = properties["user"]
            x1 = float(properties["x1"])
            y1 = float(properties["y1"])
            x2 = float(properties["x2"])
            y2 = float(properties["y2"])
            way_type = properties["type"]
            source = int(np.uint32(properties["source"]))
            target = int(np.uint32(properties["target"]))

            ins = table.insert().values(geom=geom,
                                        way_id=way_id,
                                        osm_ways=osm_ways,
                                        cost=cost,
                                        reverse_cost=reverse_cost,
                                        user=user,
                                        x1=x1,
                                        y1=y1,
                                        x2=x2,
                                        y2=y2,
                                        way_type=way_type,
                                        source=source,
                                        target=target)

            conn.execute(ins)


class WaysTable(Base):
    __tablename__ = "ogrgeojson"
    ogc_fid = Column(Integer, primary_key=True)
    wkb_geometry = Column(Geometry("LINESTRING"))
    stroke = Column(String)
    type = Column(String)
    id = Column(String)
    user = Column(String)

class SidewalkEdgesTable(Base):
    __tablename__ = "sidewalk_edges"
    sidewalk_edge_id = Column(Integer, primary_key=True, autoincrement=True, name="sidewalk_edge_id")
    way_id = Column(Integer, name="way_id")
    geom = Column(Geometry("LineString", srid=4326), name="geom")
    osm_ways = Column(String, name="osm_ways")
    cost = Column(Float, name="cost")
    reverse_cost = Column(Float, name="reverse_cost")
    user = Column(String, name="user")
    x1 = Column(Float, name="x1")
    y1 = Column(Float, name="y1")
    x2 = Column(Float, name="x2")
    y2 = Column(Float, name="y2")
    way_type = Column(String, name="way_type")
    source = Column(Integer, name="source")
    target = Column(Integer, name="target")


if __name__ == "__main__":
    setting_file = os.path.relpath("../../", os.path.dirname(__file__)) + "/.settings"
    db = DB(setting_file)
    print db.example_insert()
