from api_caller import  iso_utc_to_ist
from event_data_static import EventDataStatic
from mybets import MyBets
from order import Order
import datetime as dt
import pandas as pd
from time import sleep
import numpy as np


class Strat0:

    def __init__(self, eid=None, userid=None, apitype=None):
        self.eid = eid or int(input("Enter Event id: "))
        self.userid = userid or int(input("Enter userid: "))
        self.apitype = apitype or input("Enter api type: ")
        self.eds = EventDataStatic(self.apitype, self.userid)
        self.mybet = MyBets(self.apitype, self.userid)
        self.order = Order(self.eid, self.apitype, self.userid)

        self.title = None
        self.started_at = None
        self.ends_at = None

        self.yes_hold_qty = None
        self.no_hold_qty = None
        self.max_hold_qty = None

        self.ycp = None
        self.ncp = None
        self.buyqty = None
        self.sellqty = None
        self.accum_side = None
        self.dump_side = None
        self.last_buy_price_yes = None
        self.last_buy_price_no = None
        self.status = None
        self.switch_side_price = 60

    def _print_details(self):
        print_dict = {"Userid": [self.userid, self.userid],
                      "apiType": [self.apitype, self.apitype],
                      "CMP": [self.ycp, self.ncp],
                      "accum": [self.accum_side, self.accum_side],
                      "dump": [self.dump_side, self.dump_side],
                      "status": [self.status, self.status],
                      "lastBuy": [self.last_buy_price_yes, self.last_buy_price_no],
                      "MyHoldQty": [self.yes_hold_qty, self.no_hold_qty],
                      "BuyQty": [self.buyqty, self.buyqty],
                      "MaxHoldQty": [self.max_hold_qty, self.max_hold_qty]}

        print("-" * 100)
        print(dt.datetime.now(), f"Updating {self.eid}")
        print(f"{self.title} | started at {self.started_at} | ends at {self.ends_at}")
        print("-" * 100)
        print(pd.DataFrame(print_dict, index=["Yes", "No"]))
        print("-" * 10, "ORDERS:")
        print(self.mybet.get_event_holdings(self.eid))

    def set_event_params(self):
        all_event_data = self.eds.get_event_det_from_id(self.eid)
        self.title = all_event_data["title"]
        self.started_at = iso_utc_to_ist(all_event_data["start_date"])
        self.ends_at = iso_utc_to_ist(all_event_data["endsat"])
        self.ycp = np.round(all_event_data["yCP"], 2)
        self.ncp = np.round(all_event_data["nCP"], 2)
        self.last_buy_price_yes = 0
        self.last_buy_price_no = 0


    def update_event_params(self):
        all_event_data = self.eds.get_event_det_from_id(self.eid)
        self.ycp = np.round(all_event_data["yCP"], 2)
        self.ncp = np.round(all_event_data["nCP"], 2)
        self.yes_hold_qty, self.no_hold_qty = self.mybet.get_holding_qty(self.eid)


    def update_accum_side(self):
        if (self.ycp < 50) and (self.ycp > 40):
            self.accum_side = "y"
            self.dump_side = None
            self.status = "neutralnolean"
        elif (self.ycp > 50) and (self.ycp < 60):
            self.accum_side = "n"
            self.dump_side = None
            self.status = "neutralyeslean"
        elif (self.ycp > 60) and (self.ycp < 100):
            self.accum_side = "y"
            self.dump_side = "n"
            self.status = "strongyes"
        elif (self.ycp < 40) and (self.ycp > 0):
            self.accum_side = "n"
            self.dump_side = "y"
            self.status = "strongno"
        else:
            self.accum_side = None
            self.dump_side = None
            self.status = None

    def update_qty(self):
        if self.accum_side == "y":
            self.buyqty = np.round((100 - self.ycp) / 10, 2)
        elif self.accum_side == "n":
            self.buyqty = np.round((100 - self.ncp) / 10, 2)
        else:
            self.buyqty = 0

        if self.dump_side == "y":
            self.sellqty = self.yes_hold_qty
        elif self.dump_side == "n":
            self.sellqty = self.no_hold_qty
        else:
            self.sellqty = 0

    def scalp(self):
        if (self.accum_side == "y") and (self.buyqty > 0) and (self.ycp >= self.last_buy_price_yes+5):
            self.last_buy_price_yes = self.ycp
            self.order._buy(message=self.status, asset="Y", price=None, qty=self.buyqty, cmp=self.ycp)
        elif (self.accum_side == "n") and (self.buyqty > 0) and (self.ncp >= self.last_buy_price_no+5):
            self.last_buy_price_no = self.ncp
            self.order._buy(message=self.status, asset="N", price=None, qty=self.buyqty, cmp=self.ncp)
        else:
            print("No buy action")
            pass

        if (self.dump_side == "y") and (self.sellqty > 0):
            self.order._sell(message=self.status, asset="Y", price=None, qty=self.sellqty, cmp=self.ycp)
        elif (self.dump_side == "n") and (self.sellqty > 0):
            self.order._sell(message=self.status, asset="N", price=None, qty=self.sellqty, cmp=self.ncp)
        else:
            print("No sell action")
            pass

    def initialise(self):
        print("EXISTING ORDERS")
        print(self.mybet.get_event_holdings(self.eid))

        self.set_event_params()
        self.update_accum_side()
        self.update_qty()
        self.scalp()
        self._print_details()

    def update(self):
        self.update_event_params()
        self.update_accum_side()
        self.update_qty()
        self.scalp()
        self._print_details()


if __name__ == "__main__":
    stratobj = Strat0(eid=16703, userid=603727, apitype='p')
    stratobj.initialise()
    while dt.datetime.now() <= dt.datetime.fromisoformat(stratobj.ends_at):
        try:
            stratobj.update()
            sleep(15)
        except Exception as e:
            # logger.exception(e)
            print(e)




