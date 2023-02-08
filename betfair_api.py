import json

import requests


def sportid_from_sport(sportname):
    if sportname == "soccer":
        return 1
    elif sportname == "tennis":
        return 2
    elif sportname == "cricket":
        return 4
    else:
        raise Exception("Invalid sport name")


class BetfairApi:
    # ip needs to be whitelisted to use this api
    _site_ip = "http://209.250.242.175:33332"

    # sports mean soccer, cricket, tennis etc
    # competition mean leagues like La liga, IPL
    # events mean match names
    # markets mean match odds, total runs etc
    # inplay events mean matches that have started
    _routes = {"listcompetitionbysport": "/listCompetitions/{sportid}",
               "listeventsbysportncompetition": "/listEventsByCompetition/{sportid}/{competid}",
               "listeventsbysport": "/listEventsBySport/{sportid}",
               "listmarketsbyevent": "/listMarkets/{eventid}",
               "listinplayeventsbysport": "/listInplayEvents/{sportid}",
               "marketoddsbymarketid": "/odds/?ids={marketids}"}

    def __init__(self):
        pass

    def list_compet_by_sport(self, sportname, route="listcompetitionbysport"):
        return self._request(route=route, url_args={"sportid": sportid_from_sport(sportname)})

    def list_events_by_sport_n_competid(self, sportname, compid, route="listeventsbysportncompetition"):
        return self._request(route=route, url_args={"sportid": sportid_from_sport(sportname), "competid": compid})

    def list_events_by_sport(self, sportname, route="listeventsbysport"):
        return self._request(route=route, url_args={"sportid": sportid_from_sport(sportname)})

    def list_markets_by_eventid(self, eventid, route="listmarketsbyevent"):
        return self._request(route=route, url_args={"eventid": eventid})

    def list_inplay_events_by_sport(self, sportname, route="listinplayeventsbysport"):
        return self._request(route=route, url_args={"sportid": sportid_from_sport(sportname)})

    def list_odds_by_marketid(self, marketid, route="marketoddsbymarketid"):
        return self._request(route=route, url_args={"marketids": marketid})

    def _request(self, route, url_args):
        if url_args:
            uri = self._routes[route].format(**url_args)
        else:
            uri = self._routes[route]

        url = self._site_ip + uri

        try:
            r = requests.get(url)
            data = json.loads(r.text)
            return data
        except Exception as e:
            print(e)
            raise Exception(e)
