import psycopg2
import dbconfig as config
import pandas as pd

class ToPostgres:
    def __init__(self):
        self.connection = psycopg2.connect(dbname=config.sql_dbname_viz, host=config.sql_host_viz,
                                           port=config.sql_port_viz, user=config.sql_user_viz,
                                           password=config.sql_password_viz)

    def initialise_live_ref(self, userid, apitype, eventid, updatedatetime, pnlworst, pnlbest, pnl_worst_limit, worst_limit_reached):
        self.cursor = self.connection.cursor()
        postgres_insert_query = f'''insert into mm_live_ref1 (
                                                        uid,
                                                        api,
                                                        eid,
                                                        updatedatetime,
                                                        pnl_worst,
                                                        pnl_best,
                                                        pnl_worst_limit,
                                                        worst_limit_reached)
                                                        VALUES( %s, %s, %s, %s, %s, %s, %s, %s);'''
        record_to_insert = (userid, apitype, eventid, updatedatetime, pnlworst, pnlbest, pnl_worst_limit, worst_limit_reached)
        self.cursor.execute(postgres_insert_query, record_to_insert)
        self.connection.commit()
        print(f"NEW TABLE CREATED {eventid}---------------")
        print(f"NEW TABLE CREATED {eventid}---------------")
        print(f"NEW TABLE CREATED {eventid}---------------")
        print(f"NEW TABLE CREATED {eventid}---------------")

    def update_live_ref(self, userid, eventid, updatedatetime, pnlworst, pnlbest, worst_limit_reached):
        self.cursor = self.connection.cursor()
        postgres_update_query = f"""UPDATE mm_live_ref1
                                    SET updatedatetime = %s, pnl_worst = %s, pnl_best = %s, worst_limit_reached = %s
                                    WHERE uid = %s AND eid = %s ;"""
        record_to_update = (updatedatetime, pnlworst, pnlbest, worst_limit_reached, userid, eventid)
        self.cursor.execute(postgres_update_query, record_to_update)
        self.connection.commit()
        print(f"----------TABLE UPDATED {eventid}")
        print(f"----------TABLE UPDATED {eventid}")
        print(f"----------TABLE UPDATED {eventid}")
        print(f"----------TABLE UPDATED {eventid}")

    def update_live_pnl(self, qty, settle, pnl_final, eventid):
        self.cursor = self.connection.cursor()
        postgres_update_query = f"""UPDATE mm_live_ref1
                                    SET qty_punched = %s, if_settled = %s, pnl_final = %s
                                    WHERE eid = %s ;"""
        record_to_update = (qty, settle, pnl_final, eventid)
        self.cursor.execute(postgres_update_query, record_to_update)
        self.connection.commit()

if __name__ == "__main__":
    import datetime as dt
    psql = ToPostgres()
    psql.initialise_live_ref(11, "z", 111112, dt.datetime.now().isoformat(), -100, None, 1000, False)

    # psql.update_live_ref(11, 111111, dt.datetime.now().isoformat(), -10, 600, True)