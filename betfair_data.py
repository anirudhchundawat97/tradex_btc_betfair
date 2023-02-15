from betfair_api import BetfairApi
import pandas as pd
from difflib import SequenceMatcher

def generate_possible_event_names(underlying1, underlying2):
    underlying1 = underlying1.replace(" ", "").lower()
    underlying2 = underlying2.replace(" ", "").lower()
    eventname1 = underlying1 + "v" + underlying2
    eventname2 = underlying2 + "v" + underlying1
    return eventname1, eventname2


def string_similarity_score(item1, item2):
    item1 = item1.replace(" ", "").lower()
    item2 = item2.replace(" ", "").lower()
    s1 = SequenceMatcher(None, item1, item2)
    return s1.ratio()

def create_probability_col_with_decimal(df):
    df["probability"] = 100 / df["price"]
    return df


def cal_competition_similarity_score(competition, tomatch_compname):
    if tomatch_compname == None:
        tomatch_compname = ""
    else:
        tomatch_compname = tomatch_compname.replace(" ", "").lower()
    score = string_similarity_score(competition, tomatch_compname)
    return score


def cal_event_similarity_score(underlying_1, underlying_2, tomatch_eventname):
    tomatch_eventname = tomatch_eventname.replace(" ", "").lower()
    eventname1, eventname2 = generate_possible_event_names(underlying_1, underlying_2)
    score1 = string_similarity_score(eventname1, tomatch_eventname)
    score2 = string_similarity_score(eventname2, tomatch_eventname)
    return max(score1, score2)


class BetfairData:
    def __init__(self, competition, underlying_1, underlying_2, format):
        self.competition = competition
        self.underlying_1 = underlying_1
        self.underlying_2 = underlying_2
        self.format = format

        self.all_events_info = None

        self.matched_events_info = None
        self.matched_event_name = None
        self.matched_competition_name = None
        self.matched_event_id = None

        self.matched_all_market_info = None
        self.matched_market_info = None
        self.matched_market_id = None

        self.matched_odds_info = None
        self.underlying_1_back_df = None
        self.underlying_1_lay_df = None
        self.underlying_2_back_df = None
        self.underlying_2_lay_df = None
        self.underlying_1_best_back = None
        self.underlying_1_best_lay = None
        self.underlying_1_spread = None
        self.underlying_2_best_back = None
        self.underlying_2_best_lay = None
        self.underlying_2_spread = None
        self.event_status = None #odds become zero after suspended
        self.event_inplay = None

        self.betfair = BetfairApi()
        self.change_underlying_names_if_woman()

    def change_underlying_names_if_woman(self):
        if ("woman" in self.competition) or ("women" in self.competition):
            self.underlying_1 = self.underlying_1 + "women"
            self.underlying_2 = self.underlying_2 + "women"

    def get_all_events_info(self):
        sports_names = ["soccer", "cricket", "tennis"]
        events_info_list = []
        for sport in sports_names:
            temp1 = self.betfair.list_events_by_sport(sport)
            print(temp1)
            events_info_list.extend(temp1)
        self.all_events_info = pd.DataFrame(events_info_list)

    def cal_similarity_score_cols(self):
        self.all_events_info["matching_event_score"] = self.all_events_info.apply(lambda row: cal_event_similarity_score(self.underlying_1, self.underlying_2, row['name']), axis=1)
        self.all_events_info["matching_comp_score"] = self.all_events_info.apply(lambda row: cal_competition_similarity_score(self.competition, row['competitionName']), axis=1)
        self.all_events_info["matching_total_score"] = self.all_events_info["matching_event_score"] + self.all_events_info["matching_comp_score"]
        self.all_events_info = self.all_events_info.sort_values(by="matching_total_score", ascending=False).reset_index(drop=True)
        print(self.all_events_info)

    def set_matching_event_info(self):
        self.matched_events_info = self.all_events_info.iloc[0].to_dict()
        if self.matched_events_info["matching_total_score"] > 1:
            self.matched_event_name = self.matched_events_info["name"]
            self.matched_competition_name = self.matched_events_info["competitionName"]
            self.matched_event_id = self.matched_events_info["Id"]
            print(self.matched_event_id)
        else:
            raise Exception("Wrong event seems to have matched")

    def set_matching_market_info(self):
        markets = self.betfair.list_markets_by_eventid(self.matched_event_id)
        self.matched_all_market_info = pd.DataFrame(markets)
        if self.format == "sports_towinagainst":
            filtered_data = (self.matched_all_market_info[self.matched_all_market_info["marketName"]=='Match Odds']).to_dict()
            self.matched_market_id = filtered_data["marketId"]
            print("mid",self.matched_market_id)
        else:
            raise Exception("Sports event format invalid")

    def update_exchange_prices(self):
        data = self.betfair.list_odds_by_marketid(self.matched_market_id)[0]
        self.event_status = data["Status"]
        runners_data = data["Runners"]
        if self.event_status == "OPEN":
            self.event_inplay = data["inplay"]
            for dict_ in runners_data:
                if string_similarity_score(self.underlying_1, dict_["runnerName"]) > 0.9:
                    self.underlying_1_back_df = pd.DataFrame(dict_["ExchangePrices"]["AvailableToBack"])
                    self.underlying_1_lay_df = pd.DataFrame(dict_["ExchangePrices"]["AvailableToLay"])
                elif string_similarity_score(self.underlying_2, dict_["runnerName"]) > 0.9:
                    self.underlying_2_back_df = pd.DataFrame(dict_["ExchangePrices"]["AvailableToBack"])
                    self.underlying_2_lay_df = pd.DataFrame(dict_["ExchangePrices"]["AvailableToLay"])
                else:
                    raise Exception("No runner/team name matched")
        else:
            self.event_inplay = self.event_status

    def update_probability_cols(self):
        for df in [self.underlying_1_back_df, self.underlying_1_lay_df, self.underlying_2_back_df, self.underlying_2_lay_df]:
            df = create_probability_col_with_decimal(df)

    def update_best_odds_n_spread(self):
        self.underlying_1_back_df = self.underlying_1_back_df.sort_values(by="probability", ascending=True).reset_index(drop=True)
        self.underlying_1_best_back = self.underlying_1_back_df["probability"].iloc[0]
        self.underlying_1_lay_df = self.underlying_1_lay_df.sort_values(by="probability", ascending=False)
        self.underlying_1_best_lay = self.underlying_1_lay_df["probability"].iloc[0]
        self.underlying_2_back_df = self.underlying_2_back_df.sort_values(by="probability", ascending=True)
        self.underlying_2_best_back = self.underlying_2_back_df["probability"].iloc[0]
        self.underlying_2_lay_df = self.underlying_2_lay_df.sort_values(by="probability", ascending=False)
        self.underlying_2_best_lay = self.underlying_2_lay_df["probability"].iloc[0]

        self.underlying_1_spread = self.underlying_1_best_back - self.underlying_1_best_lay
        self.underlying_2_spread = self.underlying_2_best_back - self.underlying_2_best_lay

    def initialise(self):
        try:
            self.get_all_events_info()
            self.cal_similarity_score_cols()
            self.set_matching_event_info()
            self.set_matching_market_info()
        except Exception as e:
            print(e)

    def update(self):
        try:
            self.update_exchange_prices()
            self.update_probability_cols()
            self.update_best_odds_n_spread()
        except Exception as e:
            print(e)

if __name__ == "__main__":
    bfd = BetfairData("Bundesliga", "Schalke", "Wolfsburg", "sports_towinagainst")
    bfd.initialise()
    bfd.update()
    print(bfd.underlying_1_back_df)
    print(bfd.underlying_1_lay_df)
    print(bfd.underlying_2_back_df)
    print(bfd.underlying_2_lay_df)





