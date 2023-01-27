from event_data_static import EventDataStatic
from probecallsopen import ProbeCallsOpen
from lasttradesinfo import LastTradesInfo


class EventParam:
    def __init__(self, eid, apitype=None, userid=None):
        # print("initialising Event Params")
        self.title = None
        self.started_at = None
        self.ends_at = None
        self.eid = eid
        self.yes_pending_orders = None
        self.no_pending_orders = None
        self.last_executed_trades = None
        self.eds = EventDataStatic(apitype, userid)
        self.pco = ProbeCallsOpen(apitype, userid)
        self.lti = LastTradesInfo(apitype, userid)

    def initialise_event(self):
        static_data = self.eds.get_static_event_data_dict(self.eid)
        self.title = static_data["title"]
        self.started_at = static_data["started_at"]
        self.ends_at = static_data["ends_at"]

        full_orderbook, self.yes_pending_orders, self.no_pending_orders = self.pco.get_yesno_orderbook(self.eid)
        self.last_executed_trades = self.lti.clean_lastTradesInfo_df(self.eid)

    def update_event(self):
        full_orderbook, self.yes_pending_orders, self.no_pending_orders = self.pco.get_yesno_orderbook(self.eid)
        self.last_executed_trades = self.lti.clean_lastTradesInfo_df(self.eid)

if __name__=="__main__":
    def dum():
        x = None
        y = 5
        return None

    p,q = dum()
    print(p)
    print(q)

