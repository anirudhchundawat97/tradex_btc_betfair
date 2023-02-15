print("started...")
from betfair_data import BetfairData
from betfair_api import BetfairApi
from withpostgres import Postgres1
import datetime as dt
from time import sleep
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
file_handler = logging.FileHandler("log_files/bf_data_saver1.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

print("before betfair")
bfa = BetfairApi()
print("before    postgres")
pg = Postgres1()
print("after postgres")
all_events = []
for sport in ["soccer", "tennis", "cricket"]:
    all_events.extend(bfa.list_events_by_sport(sportname=sport))

while True:
    try:
        for e in all_events:
            comp = e["competitionName"]
            eventname = e["name"]
            split_eventname = eventname.split("v")
            team1 = split_eventname[0]
            team2 = split_eventname[1]
            bf = BetfairData(competition=comp, underlying_1=team1, underlying_2=team2, format="sports_towinagainst")
            bf.initialise()
            bf.update()
            data_dict = {"datetime": dt.datetime.now()+dt.timedelta(hours=5, minutes=30),
                         "eventid": bf.matched_event_id,
                         "compid": "null",
                         "eventname": bf.matched_event_name,
                         "compname": bf.matched_competition_name,
                         "team1name": bf.underlying_1,
                         "team2name": bf.underlying_2,
                         "team1back": bf.underlying_1_back_df.to_dict(),
                         "team1lay": bf.underlying_1_lay_df.to_dict(),
                         "team2back": bf.underlying_2_back_df.to_dict(),
                         "team2lay": bf.underlying_2_lay_df.to_dict(),
                         "inplay": bf.event_inplay}
            pg.insert_into_db(data_dict)
            print(data_dict)
        print("-"*20)
        sleep(30)
    except Exception as e:
        print("x"*10,e)
        logger.exception(e)
