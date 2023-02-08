from betfair_data import BetfairData
from betfair_api import BetfairApi
from withpostgres import Postgres1
import datetime as dt
from time import sleep

bfa = BetfairApi()
pg = Postgres1()
all_events = []
for sport in ["soccer", "tennis", "cricket"]:
    all_events.extend(bfa.list_events_by_sport(sportname=sport))

while True:
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
