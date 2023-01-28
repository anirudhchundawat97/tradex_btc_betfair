import requests
from difflib import SequenceMatcher
import json

class BetFair:
    def __init__(self):
        self.all_events = []

    def combine_all_sportsevents_list(self):
        sports_ids = [1, 2, 3]
        for sport_id in sports_ids:
            url = f"http://209.250.242.175:33332/listEventsBySport/{sport_id}"
            temp = requests.get(url)
            # print(temp.text)
            self.all_events.extend(json.loads(temp.text))
        # url = f"http://209.250.242.175:33332/listEventsBySport/1"
        # temp = requests.get(url)
        # # print(temp.text)
        # self.all_events = json.loads(temp.text)

    def fetch_matching_eventid(self, teamA=None, teamB=None):
        self.combine_all_sportsevents_list()
        betfair_eid = None
        # print("all event dict")
        # print(self.all_events)
        print("A:", teamA, "B:", teamB)
        if teamA and teamB:
            teamA = teamA.replace(" ", "").lower()
            teamB = teamB.replace(" ", "").lower()
            for detail_dict in self.all_events:
                if betfair_eid:
                    return betfair_eid
                else:
                    # print(type(detail_dict))
                    print(detail_dict)
                    print()
                    name = detail_dict["name"].replace(" ", "").lower()
                    phrase = teamA+"v"+teamB
                    s = SequenceMatcher(None, phrase, name)
                    if s.ratio() > 0.9:
                        print("Eventid: ", detail_dict["Id"])
                        betfair_eid = detail_dict["Id"]
                    else:
                        print("Phrase not matched: ", phrase, detail_dict["Id"], s.ratio())
                        betfair_eid = None
        else:
            return None

    def fetch_marketid_from_eventid(self, eventid=None):
        if eventid:
            url = f"http://209.250.242.175:33332/listMarkets/{eventid}"
            temp = requests.get(url)
            # print(temp.text)
            temp2 = json.loads(temp.text)[0]
            print("marketid" , temp2["marketId"])
            return temp2["marketId"]
        else:
            print("betfair eventid:", eventid)
            return None

    def get_odds_matching_matchphrase(self, teamA=None, teamB=None):
        event_id = None
        market_id = None
        if teamA and teamB:
            event_id = self.fetch_matching_eventid(teamA, teamB)
        if event_id:
            market_id = self.fetch_marketid_from_eventid(event_id)
        if market_id:
            url = f"http://209.250.242.175:33332/odds/?ids={market_id}"
            temp = requests.get(url)
            temp2 = json.loads(temp.text)[0]["Runners"]
            for team in temp2:
                teamname = team["runnerName"]
                s = SequenceMatcher(None, teamname, teamA)
                if s.ratio() > 0.9:
                    odds = team["ExchangePrices"]["AvailableToBack"][2]["price"]
                    return (1 / odds) * 100
                else:
                    odds = None
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



