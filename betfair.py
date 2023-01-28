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

    def combine_all_sportsevents_list(self):
        # sports_ids = [1, 2, 3]
        # for sport_id in sports_ids:
        #     url = f"http://209.250.242.175:33332/listEventsBySport/{sport_id}"
        #     temp = requests.get(url)
        #     # print(temp.text)
        #     self.all_events.extend(json.loads(temp.text))
        url = f"http://209.250.242.175:33332/listEventsBySport/1"
        temp = requests.get(url)
        # print(temp.text)
        self.all_events = json.loads(temp.text)

    def fetch_matching_eventid(self, teamA=None, teamB=None):
        self.combine_all_sportsevents_list()
        # print("all event dict")
        # print(self.all_events)
        print("A:", teamA, "B:", teamB)
        if teamA and teamB:
            teamA = teamA.replace(" ", "").lower()
            teamB = teamB.replace(" ", "").lower()
            for detail_dict in self.all_events:
                print("in event finding loop")
                if self.event_id:
                    return self.event_id
                else:
                    # print(type(detail_dict))
                    # print(detail_dict)
                    print()
                    name = detail_dict["name"].replace(" ", "").lower()
                    phrase1 = teamA+"v"+teamB
                    phrase2 = teamB + "v" + teamA
                    s1 = SequenceMatcher(None, phrase1, name)
                    s2 = SequenceMatcher(None, phrase2, name)
                    if (s1.ratio() > 0.85) or (s2.ratio() > 0.85):
                        print("Eventid: ", detail_dict["Id"])
                        self.event_id = detail_dict["Id"]
                    else:
                        print("Phrase not matched: ", phrase1,phrase2, name, detail_dict["Id"], s1.ratio(), s2.ratio())
                        self.event_id = None
        else:
            return None

    def fetch_marketid_from_eventid(self):
        if self.event_id:
            url = f"http://209.250.242.175:33332/listMarkets/{self.event_id}"
            temp = requests.get(url)
            # print(temp.text)
            temp2 = json.loads(temp.text)[0]
            print("marketid" , temp2["marketId"])
            return temp2["marketId"]
        else:
            print("betfair eventid:", self.event_id)
            return None

    def get_odds_matching_matchphrase(self, teamA=None, teamB=None):
        if (teamA and teamB) and (not self.event_id):
            self.event_id = self.fetch_matching_eventid(teamA, teamB)
        if self.event_id:
            self.market_id = self.fetch_marketid_from_eventid()
        if self.market_id:
            url = f"http://209.250.242.175:33332/odds/?ids={self.market_id}"
            temp = requests.get(url)
            temp2 = json.loads(temp.text)[0]["Runners"]
            print("Runners:" ,temp2)
            sleep(5)
            for team in temp2:
                teamname = team["runnerName"]
                print("teamA: ",teamA)
                print("foundteam: ",teamname)
                sleep(5)
                s = SequenceMatcher(None, teamname, teamA)
                print(s.ratio())
                sleep(2)
                if s.ratio() >= 0.85:
                    self.odds_decimal = team["ExchangePrices"]["AvailableToBack"][2]["price"]
                    print()
                    print(self.odds_decimal)
                    self.odds_percent = (1 / self.odds_decimal) * 100
                    print()
                    sleep(5)
                    return self.odds_percent

            return 0
        else:
            return 0

if __name__ == "__main__":
    import requests
    t1 = requests.get("http://209.250.242.175:33332/listEventsBySport/1")
    print(dir(t1))
    print("---------text",type(t1.text),t1.text)
    print()
    print("---------text", type(json.loads(t1.text)), json.loads(t1.text))
    print(json.loads(t1.text)[0])



