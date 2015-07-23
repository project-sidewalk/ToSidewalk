from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import json
import os

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


if __name__ == "__main__":
    setting_file = os.path.relpath("../../", os.path.dirname(__file__)) + "/.settings"
    db = DB(setting_file)

