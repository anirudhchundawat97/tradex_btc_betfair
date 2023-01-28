import requests
from difflib import SequenceMatcher

class BetFair:
    def __init__(self):
        self.all_events = []

    def combine_all_sportsevents_list(self):
        sports_ids = [1, 2, 3]
        for sport_id in sports_ids:
            url = f"http://209.250.242.175:33332/listEventsBySport/{sport_id}"
            temp = requests.post(url)
            self.all_events.append(temp)

    def fetch_matching_eventid(self, teamA, teamB):
        self.combine_all_sportsevents_list()
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

    def fetch_marketid_from_eventid(self, eventid):
        url = f"http://209.250.242.175:33332/listMarkets/{eventid}"
        temp = requests.post(url)
        temp2 = temp[0]
        return temp2["marketId"]

    def get_odds_matching_matchphrase(self, teamA, teamB):
        event_id = self.fetch_matching_eventid(teamA, teamB)
        market_id = self.fetch_marketid_from_eventid(event_id)
        url = f"http://209.250.242.175:33332/odds/?ids={market_id}"
        temp = requests.post(url)
        temp2 = temp[0]["Runners"]
        for team in temp2:
            teamname = team["runnerName"]
            s = SequenceMatcher(None, teamname, teamA)
            if s.ratio() > 0.9:
                odds = team["ExchangePrices"]["AvailableToBack"][2]["price"]
            else:
                odds = None
        return (1/odds)*100


