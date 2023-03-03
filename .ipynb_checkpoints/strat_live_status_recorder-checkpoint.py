from MongoClient import Mongo
import pymongo
import psycopg2
import dbconfig as config
from psycopg2.extras import Json
import pandas as pd

class StratRecorder:
    def __init__(self, eid, strategy_num, userid):
        self.event_id = eid
        self.strategy_num = strategy_num
        self.userid = userid

    def _add_one_doc(self, data_dict):
        try:
            database = Mongo("tradex_strat_data")
            database.insert_dict("tradex_strat_data", f"strat{self.strategy_num}_{self.event_id}_{self.userid}", data_dict)
            return
        except pymongo.errors.DuplicateKeyError:
            pass

    def add_to_psql(self, timestamp, uid, eid, data_dict, yesfp, npfp, yesbp, nobp):
        try:
            connection = psycopg2.connect(dbname=config.sql_dbname_viz, host=config.sql_host_viz,
                                          port=config.sql_port_viz, user=config.sql_user_viz,
                                          password=config.sql_password_viz)
            cursor = connection.cursor()
            postgres_insert_query = f'''insert into mm_backtest_ref1 (
                                                                    timestamp,
                                                                    uid,
                                                                    eid,
                                                                    data_dict,
                                                                    yesfp,
                                                                    npfp,
                                                                    yesbp,
                                                                    nobp)
                                                                    VALUES( %s, %s, %s, %s, %s, %s, %s, %s);'''
            record_to_insert = (timestamp, float(uid), float(eid), Json(data_dict), float(yesfp), float(npfp), float(yesbp), float(nobp))
            cursor.execute(postgres_insert_query, record_to_insert)
            connection.commit()
        except Exception as e:
            print("psql write error: ", e)
            print("psql write error: ", e)
            print("psql write error: ", e)
            pass

    def get_data_df_from_psql(self, eventid):
        try:
            connection = psycopg2.connect(dbname=config.sql_dbname_viz, host=config.sql_host_viz,
                                          port=config.sql_port_viz, user=config.sql_user_viz,
                                          password=config.sql_password_viz)
            sql_query = f"SELECT * FROM mm_backtest_ref1 " \
                        f"WHERE eid={eventid};"
            data_df = pd.read_sql_query(sql_query, connection)
            return data_df
        except Exception as e:
            print("psql read error: ", e)
            print("psql read error: ", e)
            print("psql read error: ", e)
            return pd.DataFrame()



    # def initialise(self, data_dict):
    #     pass
    #
    # def update(self, data_dict):
    #     pass