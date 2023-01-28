import requests
from difflib import SequenceMatcher

class BetFair:
    def __init__(self):
        self.all_events = []

    def combine_all_sportsevents_list(self):
        sports_ids = [1, 2, 3]
        for sport_id in sports_ids:
            url = f"http://209.250.242.175:33332/listEventsBySport/{sport_id}"
            temp = requests.post(url).json()
            self.all_events.append(temp)

    def fetch_matching_eventid(self, teamA=None, teamB=None):
        self.combine_all_sportsevents_list()
        print("A:", teamA, "B:", teamB)
        if teamA and teamB:
            teamA = teamA.replace(" ", "").lower()
            teamB = teamB.replace(" ", "").lower()
            for detail_dict in self.all_events:
                name = detail_dict["name"].replace(" ", "").lower()
                phrase = teamA+"v"+teamB
                s = SequenceMatcher(None, phrase, name)
                if s.ratio() > 0.9:
                    return detail_dict["Id"]
                else:
                    print("Phrase not matched: ", phrase, detail_dict["Id"], s.ratio())
                    return None
        else:
            return None

    def fetch_marketid_from_eventid(self, eventid=None):
        if eventid:
            url = f"http://209.250.242.175:33332/listMarkets/{eventid}"
            temp = requests.post(url).json()
            print(temp)
            temp2 = temp[0]
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
            temp = requests.post(url).json()
            temp2 = temp[0]["Runners"]
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


