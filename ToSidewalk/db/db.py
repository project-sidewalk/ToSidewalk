from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from shapely.geometry import LineString, mapping
from shapely.wkb import loads
import json



Base = declarative_base()


class DB(object):

    def __init__(self):
        """Interacting with PostGIS using Python
        http://gis.stackexchange.com/questions/147240/how-to-efficiently-use-a-postgres-db-with-python
        http://geoalchemy-2.readthedocs.org/en/latest/orm_tutorial.html
        """
        with file("../.settings") as f:
            j = json.loads(f.read())

            if "username" in j:
                user_name = j["username"]
            else:
                user_name = "kotarohara"

            if "password" in j:
                password = j["password"]
            else:
                password = ""

            if "database" in j:
                database_name = j["database"]
            else:
                database_name = "routing"

        engine = create_engine('postgresql://%s@localhost/%s' % (user_name, database_name), echo=True)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def example(self):
        """Example
        """
        query = self.session.query(WaysTable)
        feature_collection = {
            "type": "FeatureCollection",
            "features": []
        }

        for item in query:
            linestring = mapping(LineString(loads(str(item.wkb_geometry), hex=True)))
            feature = {
                "type": "Feature",
                "geometry": linestring,
                "properties": {}
            }
            feature_collection["features"].append(feature)
        return json.dumps(feature_collection)

class WaysTable(Base):
    __tablename__ = "ogrgeojson"
    ogc_fid = Column(Integer, primary_key=True)
    wkb_geometry = Column(Geometry("LINESTRING"))
    stroke = Column(String)
    type = Column(String)
    id = Column(String)
    user = Column(String)

if __name__ == "__main__":
    db = DB()
    print db.example()
