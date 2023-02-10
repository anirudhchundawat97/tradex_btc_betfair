import psycopg2
import dbconfig as config
import logging


class Postgres1:
    def __init__(self):
        print("before connect")
        print(config.sql_user1)
        self.connection = psycopg2.connect(dbname=config.sql_dbname1, host=config.sql_host1,
                                           port=config.sql_port1, user=config.sql_user1,
                                           password=config.sql_password1)
        print(self.connection)
        logging.info(f"{self.connection}")
        print("before curser")
        self.cursor = self.connection.cursor()

    def insert_into_db(self, data_dict):
        # insert data into DB
        postgres_insert_query = '''insert into test_mm_betfair (
                                                datetime,
                                                eventid,
                                                compid,
                                                eventname,
                                                compname,
                                                team1name,
                                                team2name,
                                                team1back,
                                                team1lay,
                                                team2back,
                                                team2lay,
                                                inplay)
                                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'''
        record_to_insert = (str(data_dict["datetime"]),
                            str(data_dict["eventid"]),
                            str(data_dict["compid"]),
                            str(data_dict["eventname"]),
                            str(data_dict["compname"]),
                            str(data_dict["team1name"]),
                            str(data_dict["team2name"]),
                            str(data_dict["team1back"]),
                            str(data_dict["team1lay"]),
                            str(data_dict["team2back"]),
                            str(data_dict["team2lay"]),
                            str(data_dict["inplay"]),
                            )
        print("before execute")
        self.cursor.execute(postgres_insert_query, record_to_insert)
        print("before commit")
        self.connection.commit()

if __name__ == "__main__":
    db = Postgres1()
    data_dict = {"datetime": 12345,
                 "eventid": 213453,
                 "compid": 74635,
                 "eventname": "sher v cheetah",
                 "compname": "jungle premier league",
                 "team1name": "sher",
                 "team2name": "cheetah",
                 "team1back": [{"lay":[1.23, 1.26]}],
                 "team1lay": [{"lay":[1.23, 1.26]}],
                 "team2back": [{"lay":[1.23, 1.26]}],
                 "team2lay": [{"lay":[1.23, 1.26]}],
                 "inplay": True}
    db.insert_into_db(data_dict)
