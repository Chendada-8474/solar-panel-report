from datetime import datetime
from pyproj import Transformer
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import geopandas as gpd
import pandas as pd
import yaml
import os


DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(DIR_PATH, "init.yaml")) as file:
    connection_info = yaml.load(file, Loader=yaml.Loader)

MYSQL_PW = connection_info["mysql"]["password"]
MYSQL_IP = connection_info["mysql"]["ip"]
MYSQL_DB_NAME = connection_info["mysql"]["database_name"]

engine = create_engine(
    "mysql+pymysql://root:%s@%s/%s" % (MYSQL_PW, MYSQL_IP, MYSQL_DB_NAME),
    isolation_level="AUTOCOMMIT",
    pool_recycle=3600,
    pool_pre_ping=True,
)

Base = declarative_base()
Base.metadata.reflect(engine)
db_session = scoped_session(sessionmaker(bind=engine))


class ReportLog(Base):
    __table__ = Base.metadata.tables["report_log"]


def _coord_trans(x, y, input_proj="4326", output_proj="3826"):
    input_proj, output_proj = "epsg:%s" % input_proj, "epsg:%s" % output_proj
    x, y = Transformer.from_crs(input_proj, output_proj).transform(y, x)
    return x, y


def _geopandarize(sql: str):
    pd_dataframe = pd.read_sql(sql, engine)
    gpd_dataframe = gpd.GeoDataFrame(
        pd_dataframe,
        crs="EPSG:3826",
        geometry=gpd.GeoSeries.from_wkt(pd_dataframe["geometry"]),
    )
    return gpd_dataframe


def get_admins() -> set:
    sql = "SELECT telegram_id FROM user WHERE admin = 1"
    return set(tg_id[0] for tg_id in db_session.execute(sql).fetchall())


def get_users_by_auth(authorized=True) -> set:
    authorized = 1 if authorized else 0
    sql = "SELECT telegram_id FROM user WHERE authorized = %s" % authorized
    return set(tg_id[0] for tg_id in db_session.execute(sql).fetchall())


def get_solar_panel_types():
    sql = """
    SELECT * FROM solar_panel_type;
    """
    return db_session.execute(sql).fetchall()


def get_ponds_nearby_as_geopandas(x: float, y: float, range=500):
    half_range = range // 2
    x, y = _coord_trans(x, y)

    sql = """
    SELECT fishpond_id, solar_panel_type, centroid_x, centroid_y, ST_ASTEXT(geometry) as geometry from fishpond WHERE %s < centroid_x AND centroid_x < %s AND %s < centroid_y AND centroid_y < %s;
    """ % (
        x - half_range,
        x + half_range,
        y - half_range,
        y + half_range,
    )
    return _geopandarize(sql)


def update_panel_type(updates: dict):
    db_session.rollback()
    sql_update = """
    UPDATE fishpond SET solar_panel_type = %s WHERE fishpond_id = %s;
    """
    for fishpond_id, panel_type in updates.items():
        db_session.execute(sql_update % (panel_type, fishpond_id))
        db_session.commit()


def insert_log(updates: dict, user_id):
    db_session.rollback()
    logs = []
    for fishpond_id, panel_type in updates.items():
        logs.append(
            ReportLog(
                fishpond_id=fishpond_id,
                reporter=user_id,
                solar_panel_type_id=panel_type,
                report_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
    db_session.add_all(logs)
    db_session.commit()


def insert_user(user_id: str, org=None, first_name=None, last_name=None):
    db_session.rollback()
    if not all([org, first_name, last_name]):
        raise "org, first_name and last_name are all requried"
    sql = """
    INSERT INTO user (telegram_id, user_name, org) VALUE ('%s', '%s', '%s')
    """
    user_name = "%s %s" % (first_name, last_name)
    db_session.execute(sql % (user_id, user_name, org))
    db_session.commit()


def get_unauth_info():
    sql = """
    SELECT Telegram_id, user_name, org FROM user WHERE authorized = 0;
    """
    return db_session.execute(sql).fetchall()


def authorize_user(applier_id):
    db_session.rollback()
    sql = """
    UPDATE user SET authorized = 1 WHERE telegram_id = %s;
    """
    db_session.execute(sql % applier_id)
    db_session.commit()


def get_super_admin():
    sql = """
    SELECT Telegram_id FROM user WHERE user_id = 1;
    """
    return db_session.execute(sql).fetchone()[0]


def get_user_name(user_id):
    sql = """
    SELECT user_name FROM user WHERE telegram_id = %s
    """
    return db_session.execute(sql % user_id).fetchone()[0]


if __name__ == "__main__":
    print(get_super_admin())
