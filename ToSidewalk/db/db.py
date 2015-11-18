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

        self.engine = create_engine('postgresql://%s:%s@localhost/%s' % (user_name, password, database_name), echo=False)
        session = sessionmaker(bind=self.engine)
        self.session = session()


def grant_permissions(username="sidewalk"):
    query = """
    GRANT ALL ON SEQUENCE sidewalk.street_edge_parent_edge_seq TO %s;
    GRANT ALL ON SEQUENCE sidewalk.street_edge_street_node_id_seq TO %s;
    GRANT ALL ON SEQUENCE sidewalk.street_edge_assignment_count_street_edge_assignment_count_i_seq TO %s;
    GRANT ALL ON SEQUENCE sidewalk.logininfo_id_seq TO %s;
    GRANT ALL ON SEQUENCE sidewalk.user_login_info_id_seq TO %s;
    GRANT ALL ON SEQUENCE sidewalk.user_password_info_id_seq TO %s;
    GRANT ALL ON SEQUENCE sidewalk.user_password_info_id_seq TO %s;
    """
    query = """
    GRANT ALL
        ON ALL SEQUENCES IN SCHEMA sidewalk
        TO %s
    """ % username

def _remove_records(database):
    query = """
    DELETE FROM sidewalk.user;
    DELETE FROM sidewalk.user_login_info;
    DELETE FROM sidewalk.user_password_info;
    DELETE FROM sidewalk.login_info;
    DELETE FROM sidewalk.audit_task_interaction;
    DELETE FROM sidewalk.audit_task_environment;
    DELETE FROM sidewalk.audit_task;
    DELETE FROM street_edge_street_node;
    DELETE FROM sidewalk.street_edge_parent_edge;
    DELETE FROM sidewalk.street_edge;
    DELETE FROM sidewalk.street_node;
    """
    database.engine.execute(query)
    return

if __name__ == "__main__":
    setting_file = os.path.relpath("../../", os.path.dirname(__file__)) + "/.settings"
    db = DB(setting_file)


