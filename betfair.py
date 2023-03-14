import requests
from difflib import SequenceMatcher
import json
from time import sleep


class BetFair:
    def __init__(self):
        self.all_events = []
        self.event_id = None
        self.market_id = None
        self.odds_decimal = None
        self.odds_percent = None

        self.odds_decimal_a_back = None
        self.odds_percent_a_back = None
        self.odds_decimal_a_lay = None
        self.odds_percent_a_lay = None

        self.odds_decimal_b = None
        self.odds_percent_b = None
        self.sport_id = None

    def combine_all_sportsevents_list(self, sport_id):
        # sports_ids = [1, 2, 3]
        # for sport_id in sports_ids:
        #     url = f"http://209.250.242.175:33332/listEventsBySport/{sport_id}"
        #     temp = requests.get(url)
        #     # print(temp.text)
        #     self.all_events.extend(json.loads(temp.text))
        if not self.sport_id:
            # self.sport_id = int(input("enter sport category, 1-soccer, 2-tennis, 4-cricket: "))
            self.sport_id = sport_id
        url = f"http://209.250.242.175:33332/listEventsBySport/{self.sport_id}"
        temp = requests.get(url)
        # print(temp.text)
        self.all_events = json.loads(temp.text)

    def fetch_matching_eventid(self, league=None, teamA=None, teamB=None, sport_id=None):
        self.combine_all_sportsevents_list(sport_id=sport_id)
        # print("all event dict")
        # print(self.all_events)
        print("league: ", league, "A:", teamA, "B:", teamB)
        if teamA and teamB:
            teamA = teamA.replace(" ", "").lower()
            teamB = teamB.replace(" ", "").lower()
            # if "women" in league:
            #     teamA = teamA+"women"
            #     teamB = teamB+"women"
            for detail_dict in self.all_events:
                print("in event finding loop")
                if self.event_id:
                    return self.event_id
                else:
                    # print(type(detail_dict))
                    # print(detail_dict)
                    # print()
                    # print(detail_dict.keys())
                    print(detail_dict["name"])
                    name = detail_dict["name"].replace(" ", "").lower()
                    phrase1 = teamA + "v" + teamB
                    phrase2 = teamB + "v" + teamA
                    s1 = SequenceMatcher(None, phrase1, name)
                    s2 = SequenceMatcher(None, phrase2, name)
                    if (s1.ratio() > 0.9) or (s2.ratio() > 0.9):
                        print(detail_dict)
                        print("Phrase matched Eventid: ", detail_dict["Id"])
                        self.event_id = detail_dict["Id"]
                    else:
                        print("Phrase not matched: ", phrase1, phrase2, name, detail_dict["Id"], s1.ratio(), s2.ratio())
                        self.event_id = None
        else:
            return None

    def fetch_marketid_from_eventid(self):
        if self.event_id:
            url = f"http://209.250.242.175:33332/listMarkets/{self.event_id}"
            temp = requests.get(url)
            temp1 = json.loads(temp.text)
            print(temp1)
            temp2 = temp1[0]
            print("marketid", temp2["marketId"])
            return temp2["marketId"]
        else:
            print("betfair eventid:", self.event_id)
            return None

    def get_odds_matching_matchphrase(self, league=None, teamA=None, teamB=None, sport_id=None):
        try:
            teamA = teamA.replace(" ", "").lower()
            teamB = teamB.replace(" ", "").lower()
        except:
            pass
        if "women" in league:
            teamA = teamA + "women"
            teamB = teamB + "women"
        if (teamA and teamB) and (not self.event_id):
            self.event_id = self.fetch_matching_eventid(league=league, teamA=teamA, teamB=teamB, sport_id=sport_id)
        if self.event_id:
            self.market_id = self.fetch_marketid_from_eventid()
        if self.market_id:
            url = f"http://209.250.242.175:33332/odds/?ids={self.market_id}"
            temp = requests.get(url)
            temp2 = json.loads(temp.text)[0]["Runners"]
            match_inplay = json.loads(temp.text)[0]["inplay"]
            self.match_inplay = True if match_inplay == "True" else False if match_inplay == "False" else None
            print("Runners:", temp2)
            # sleep(5)
            for team in temp2:
                teamname = team["runnerName"].replace(" ", "").lower()
                print("teamA: ", teamA)
                print("foundteam: ", teamname)
                # sleep(5)
                s = SequenceMatcher(None, teamname, teamA)
                print(s.ratio())
                # sleep(2)
                if s.ratio() >= 0.85:
                    all_back = team["ExchangePrices"]["AvailableToBack"]
                    self.odds_decimal_a_back = all_back[2]["price"]
                    all_lay = team["ExchangePrices"]["AvailableToLay"]
                    self.odds_decimal_a_lay = all_lay[0]["price"]

                    # print()
                    if self.odds_decimal_a_back != 0:
                        self.odds_percent_a_back = (1 / self.odds_decimal_a_back) * 100
                    else:
                        self.odds_percent_a_back = 0
                    if self.odds_percent_a_lay != 0:
                        self.odds_percent_a_lay = 100 - ((1 / self.odds_decimal_a_lay) * 100)
                    else:
                        self.odds_percent_a_lay = 0

                    print("team A backs:" , all_back, "best to precent:", self.odds_percent_a_back)
                    print("team A lays:" , all_lay, "best to percent:", self.odds_percent_a_lay)
                    print("percent sum:", self.odds_percent_a_back + self.odds_percent_a_lay)

                    return self.odds_percent_a_back, self.odds_percent_a_lay

            for team in temp2:
                teamname = team["runnerName"].replace(" ", "").lower()
                print("teamA: ", teamA)
                print("foundteam: ", teamname)
                # sleep(5)
                s = SequenceMatcher(None, teamname, teamA)
                print(s.ratio())
                # sleep(2)
                if s.ratio() >= 0.85:
                    all_back = team["ExchangePrices"]["AvailableToBack"]
                    self.odds_decimal_a_back = all_back[2]["price"]
                    all_lay = team["ExchangePrices"]["AvailableToLay"]
                    self.odds_decimal_a_lay = all_lay[0]["price"]

                    # print()
                    self.odds_percent_a_back = 100 - ((1 / self.odds_decimal_a_back) * 100)
                    self.odds_percent_a_lay = (1 / self.odds_decimal_a_lay) * 100

                    print("team A backs:" , all_back, "best to precent:", self.odds_percent_a_back)
                    print("team A lays:" , all_lay, "best to precent:", self.odds_percent_a_lay)
                    print("percent sum:", self.odds_percent_a_back + self.odds_percent_a_lay)

                    return self.odds_percent_a_back, self.odds_percent_a_lay

            return 0, 0
        else:
            return 0, 0


if __name__ == "__main__":
    import requests
    import pandas as pd
    from pprint import pprint

    sport_id = int(input("enter sport category, 1-soccer, 2-tennis, 4-cricket: "))
    t1 = requests.get(f"http://209.250.242.175:33332/listEventsBySport/{sport_id}")
    print("-"*20, "list events by sport")
    pprint(json.loads(t1.text))
    sport_events_df = pd.DataFrame(json.loads(t1.text))
    print("Columns:")
    print(sport_events_df.columns)
    print("Competitions:")
    print(sport_events_df["competitionName"].unique())
    print("Team Names:")
    print(sport_events_df["name"].unique())
    print("---fetching from list competition by sport api call")
    t2 = requests.get(f"http://209.250.242.175:33332/listCompetitions/{sport_id}")
    comp_df = pd.DataFrame(json.loads(t2.text))
    print("Columns:")
    print(comp_df.columns)
    print("Comp Names:")
    print(comp_df["Name"].unique())
    print()
    print()
    # print("-" * 20, "list competitions by sport")
    # sport_id = int(input("enter sport category, 1-soccer, 2-tennis, 4-cricket: "))
    # t1 = requests.get(f"http://209.250.242.175:33332/listCompetitions/{sport_id}")
    # print(json.loads(t1.text))
    print("-" * 20, "list events by sport")
    sport_id = int(input("enter sport category, 1-soccer, 2-tennis, 4-cricket: "))
    t2 = requests.get(f"http://209.250.242.175:33332/listEventsBySport/{sport_id}")
    pprint(json.loads(t2.text))
    # print("-" * 20, "list events by sport and competition")
    # sport_id = int(input("enter sport category, 1-soccer, 2-tennis, 4-cricket: "))
    # comp_id = int(input("enter competition id: "))
    # t3 = requests.get(f"http://209.250.242.175:33332/listEventsByCompetition/{sport_id}/{comp_id}")
    # print(json.loads(t3.text))
    print("-" * 20, "list inplay events by sport")
    sport_id = int(input("enter sport category, 1-soccer, 2-tennis, 4-cricket: "))
    t4 = requests.get(f"http://209.250.242.175:33332/listInplayEvents/{sport_id}")
    pprint(json.loads(t4.text))
    print("-" * 20, "list markets by eventid")
    event_id = int(input("enter eventid: "))
    t5 = requests.get(f"http://209.250.242.175:33332/listMarkets/{event_id}")
    pprint(json.loads(t5.text))
    print("-" * 20, "list market odds by marketid")
    market_id = float(input("enter market id: "))
    t6 = requests.get(f"http://209.250.242.175:33332/odds/?ids={market_id}")
    pprint(json.loads(t6.text))

