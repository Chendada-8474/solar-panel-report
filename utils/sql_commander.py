from pyproj import Transformer
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import pandas as pd
import geopandas as gpd
import yaml
import os


DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(DIR_PATH, "init.yaml")) as file:
    connection_info = yaml.load(file, Loader=yaml.Loader)

MYSQL_PW = connection_info["mysql"]["password"]
MYSQL_IP = connection_info["mysql"]["ip"]
MYSQL_DB_NAME = connection_info["mysql"]["database_name"]

engine = create_engine(
    "mysql+pymysql://root:%s@%s/%s" % (MYSQL_PW, MYSQL_IP, MYSQL_DB_NAME)
)

db_session = scoped_session(sessionmaker(bind=engine))


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


def get_user_ids(admin=False) -> set:
    if admin:
        sql = """
        SELECT telegram_id FROM user WHERE admin = 1;
        """
    else:
        sql = """
        SELECT telegram_id FROM user;
        """

    return set(tg_id[0] for tg_id in db_session.execute(sql).fetchall())


def get_solar_panel_types():
    sql = """
    SELECT * FROM solar_panel_type;
    """
    return db_session.execute(sql).fetchall()


def get_ponds_nearby_as_geopandas(x: float, y: float, range=500):
    half_range = 500 // 2
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


def update_panel_type(ponds):
    sql = """
    UPDATE fishpond SET solar_panel_type = %s WHERE fishpond_id = %s;
    """
    for fishpond_id, panel_type in zip(ponds["fishpond_id"], ponds["solar_panel_type"]):
        db_session.execute(sql % (fishpond_id, panel_type))
        db_session.commit()


if __name__ == "__main__":
    print(get_solar_panel_types())
    # print(get_ponds_nearby_as_geopandas(120.147275611372, 23.0510545102663))
