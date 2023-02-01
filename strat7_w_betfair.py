"""
for range contracts
on bitcoin using atr not maintaining spread
"""
import numpy as np

from betfair import BetFair
from order import Order
from price_attributes import PriceAttri
from event_params import EventParam
from mybets import MyBets
from transactions import Transactions
import pandas as pd
import datetime as dt
import logging
import math
from strat_live_status_recorder import StratRecorder
import pymongo as pm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
file_handler = logging.FileHandler("log_files/strat7_57.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Strategy:
    def __init__(self, event_id, min_buy_qty, avg_qty_multiplier, getOutSellPriceDiff="dynamic"):
        self.userid = None
        self.apitype = None
        self.apitype = 'p'#input("API type: Test or Production (t/p)?: ")
        self.userid = 0#int(input("Enter userid (0 for default): "))
        self.event_id = event_id
        self.min_buy_qty = min_buy_qty
        self.max_buyorder_qty = None
        self.max_hold_qty = 500
        self.avg_qty_multiplier = avg_qty_multiplier
        self.getOutSellPriceDiff = getOutSellPriceDiff
        self.getoutYesDiff = None
        self.getoutNoDiff = None

        self.mybet = MyBets(self.apitype, self.userid)
        self.trans = Transactions(self.apitype, self.userid)
        self.order = Order(self.event_id, self.apitype, self.userid)
        self.priceatri = PriceAttri(self.event_id, self.apitype, self.userid)
        self.betfair_obj = BetFair()
        self.stratRecorObj = StratRecorder(self.event_id, 7, self.userid)

        self.holding_yes_qty = 0
        self.holding_no_qty = 0
        self.yes_fair_price = None
        self.no_fair_price = None
        self.estimated_yes_fair_price = None
        self.estimated_no_fair_price = None
        self.strong_side = None
        self.side_2_scalp = None
        self.my_lastbuy_price_yes = None
        self.my_lastbuy_price_no = None
        self.my_avgbuy_price_yes = None
        self.my_avgbuy_price_no = None
        self.my_avgsell_price_yes = None
        self.my_avgsell_price_no = None

        self.falseavgbuyyes = None
        self.falseavgbuyno = None

        self.last_values_dict = dict()
        self.last_values_dict["yes_fp_to_bp"] = []
        self.last_values_dict["no_fp_to_bp"] = []
        self.stop_buy_upper_price = 100#int(input('Upper price limit'))
        self.stop_buy_lower_price = 0#int(input('Lower price limit'))
        self.stop_sell_upper_price = 85
        self.yesfp_std = None
        self.nofp_std = None
        self.yes_fpminusbp_std = None
        self.no_fpminusbp_std = None

        self.initialised = False

        self.teamA = None
        self.teamB = None
        self.league = None

    def __set_event_match_phrase(self):
        if ":" in self.priceatri.title:
            temp1 = self.priceatri.title.split(":")
            self.league = temp1[0].replace(" ", "").lower()
            temp2 = temp1[1].split("to win against")
            self.teamA = temp2[0]
            self.teamB = temp2[1][:-1]
        else:
            temp1 = ""
            self.league = ""
            temp2 = self.priceatri.title.split("to win against")
            self.teamA = temp2[0]
            self.teamB = temp2[1][:-1]

    def __set_estimated_fair_price(self):
        self.estimated_yes_fair_price = self.betfair_obj.get_odds_matching_matchphrase(league=self.league, teamA=self.teamA, teamB=self.teamB)
        self.estimated_no_fair_price = 100 - self.estimated_yes_fair_price

    def __set_fair_price(self):
        self.yes_fair_price = (2*self.estimated_yes_fair_price + self.priceatri.yes_ob_vwap) / 3
        # print("--yes fair price")
        # print(self.priceatri.yes_best_price)
        # print("-")
        # print(self.priceatri.yes_ob_vwap)
        # print("-")
        # print(self.yes_fair_price)
        # print("--")
        self.no_fair_price = (2*self.estimated_no_fair_price + self.priceatri.no_ob_vwap) / 3
        # print("--no fair price")
        # print(self.priceatri.no_best_price)
        # print("-")
        # print(self.priceatri.no_ob_vwap)
        # print("-")
        # print(self.no_fair_price)
        # print("--")


    def __set_getoutsellpricediff(self):
        if self.getOutSellPriceDiff == "dynamic":
            try:
                abs_yes_list = [abs(x) for x in self.last_values_dict["yes_fp_to_bp"]]
                abs_no_list = [abs(x) for x in self.last_values_dict["no_fp_to_bp"]]
                self.yes_fpminusbp_std = int(np.std(abs_yes_list))
                self.no_fpminusbp_std = int(np.std(abs_no_list))

                self.getoutYesDiff = max(5, self.yes_fpminusbp_std)
                self.getoutNoDiff = max(5, self.no_fpminusbp_std)

            except Exception as e:
                print("Reading fair priceerror: ", e)
                self.getoutYesDiff = 5
                self.getoutNoDiff = 5
                logger.exception(e)
                # raise e
            print(f"Get out sell to {self.getoutYesDiff} and {self.getoutNoDiff}")
        else:
            self.getoutYesDiff = self.getOutSellPriceDiff
            self.getoutNoDiff = self.getOutSellPriceDiff

    def _print_details(self, process):
        print_dict = {"Userid": [self.userid, self.userid],
                      "apiType": [self.apitype, self.apitype],
                      "BestPrice": [self.priceatri.yes_best_price, self.priceatri.no_best_price],
                      "OBvwap": [self.priceatri.yes_ob_vwap, self.priceatri.no_ob_vwap],
                      "EsFairPrice": [self.estimated_yes_fair_price, self.estimated_no_fair_price],
                      "FairPrice": [self.yes_fair_price, self.no_fair_price],
                      "Spread": [100 - self.priceatri.yes_best_price - self.priceatri.no_best_price,
                                 100 - self.priceatri.yes_best_price - self.priceatri.no_best_price],
                      "Strong": [self.strong_side, self.strong_side],
                      "2Scalp": [self.side_2_scalp, self.side_2_scalp],
                      "lastBuy": [self.my_lastbuy_price_yes, self.my_lastbuy_price_no],
                      "AvgBuy": [self.my_avgbuy_price_yes, self.my_avgbuy_price_no],
                      "FalAvgBuy": [self.falseavgbuyyes, self.falseavgbuyno],
                      "AvgSell": [self.my_avgsell_price_yes, self.my_avgsell_price_no],
                      "fpStd": [self.yesfp_std, self.nofp_std],
                      "fp-bpStd": [self.yes_fpminusbp_std, self.no_fpminusbp_std],
                      "getOutDiff": [self.getoutYesDiff, self.getoutNoDiff],
                      "MyHoldQty": [self.holding_yes_qty, self.holding_no_qty],
                      "MaxBuyQty": [self.max_buyorder_qty, self.max_buyorder_qty],
                      "MaxHoldQty": [self.max_hold_qty, self.max_hold_qty]}
        print(dt.datetime.now()+ dt.timedelta(hours=5,minutes=30), "-" * 50)
        if process == "initialising":
            print(
                f"Initialising {self.priceatri.eid}: {self.priceatri.title} | started at {self.priceatri.started_at} ends at {self.priceatri.ends_at}")
        elif process == "updating":
            print(
                f"Updating {self.priceatri.eid}: {self.priceatri.title} | started at {self.priceatri.started_at} ends at {self.priceatri.ends_at}")
        print(pd.DataFrame(print_dict, index=["Yes", "No"]))
        print("League: ", self.league)
        print("team A: ", self.teamA)
        print("team B: ", self.teamB)
        print("winning odds decimal: ",self.betfair_obj.odds_decimal)
        print("winning odds percent: ",self.betfair_obj.odds_percent)
        print("-" * 10, "PENDING BOOK:")
        print(self.priceatri.yes_pending_orders.head(3))
        print(self.priceatri.no_pending_orders.head(3))
        print("-" * 10, "ORDERS:")
        print(self.mybet.get_event_holdings(self.event_id))


    def _update_last_values(self):
        self.last_values_dict["y_h_qty"] = self.holding_yes_qty
        self.last_values_dict["n_h_qty"] = self.holding_no_qty
        self.last_values_dict["strong_side"] = self.strong_side
        self.last_values_dict["side2scalp"] = self.side_2_scalp
        self.last_values_dict["yes_fprice"] = self.yes_fair_price
        self.last_values_dict["no_fprice"] = self.no_fair_price
        self.last_values_dict["yavgbuy"] = self.my_avgbuy_price_yes
        self.last_values_dict["navgbuy"] = self.my_avgbuy_price_no
        self.last_values_dict["maxbuyqty"] = self.max_buyorder_qty
        self.last_values_dict["yes_fp_to_bp"].append(self.yes_fair_price - self.priceatri.yes_best_price)
        self.last_values_dict["no_fp_to_bp"].append(self.no_fair_price - self.priceatri.no_best_price)

    def __scalp_side(self, asset, trigger, pausebuy, pausesell):
        if asset == "Y":
            if not pausebuy:
                temp_price, temp_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "buy")
                if (temp_qty > 0) and (temp_price <= self.stop_buy_upper_price) and (not self.order.is_same_order("Y", temp_price, temp_qty, "buy")) and (not self._is_myorder_best("Y")):
                    self.order.cancel_all_pending_buy("Y", f"{trigger},NewBuyParams")
                    self.priceatri.update_priceatri()
                    temp_price, temp_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "buy")
                    self.__send_buy_orders(f"{trigger},ScalpingYes,{set_priceqty_message}", "Y", temp_price, temp_qty)
            else:
                self.order.cancel_all_pending_buy("Y", f"{trigger},PausingBuy")
                self.priceatri.update_priceatri()
                print("Pausing YES buy")
            if not pausesell:
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "sell")
                if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("Y", f"{trigger},NewSellParams")
                    self.priceatri.update_priceatri()
                    sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "sell")
                    self.__send_all_sell(f"{trigger},SellingBoughtQty,{set_priceqty_message}", "Y", sell_price, sell_qty)
            else:
                self.order.cancel_all_pending_sell("Y", f"{trigger},PausingSell")
                self.priceatri.update_priceatri()
                print("Pausing YES sell")

            self.order.cancel_all_pending_buy("N", f"{trigger},CancelOppSideOrders")
            self.priceatri.update_priceatri()
            if self.holding_no_qty > 0:
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "sell")
                if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("N", f"{trigger},NewSellParams")
                    self.priceatri.update_priceatri()
                    sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "sell")
                    self.__send_all_sell(f"{trigger},SellingOppSideBoughtQty,{set_priceqty_message}", "N", sell_price, sell_qty)
        elif asset == "N":
            if not pausebuy:
                temp_price, temp_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "buy")
                if (temp_qty > 0) and (temp_price <= self.stop_buy_upper_price) and (not self.order.is_same_order("N", temp_price, temp_qty, "buy")) and (not self._is_myorder_best("N")):
                    self.order.cancel_all_pending_buy("N", f"{trigger},NewBuyParams")
                    self.priceatri.update_priceatri()
                    temp_price, temp_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "buy")
                    self.__send_buy_orders(f"{trigger},ScalpingNo,{set_priceqty_message}", "N", temp_price, temp_qty)
            else:
                self.order.cancel_all_pending_buy("N", f"{trigger},PausingBuy")
                self.priceatri.update_priceatri()
                print("Pausing NO buy")

            if not pausesell:
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "sell")
                if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("N", f"{trigger},NewSellParams")
                    self.priceatri.update_priceatri()
                    sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "sell")
                    self.__send_all_sell(f"{trigger},SellingBoughtQty,{set_priceqty_message}", "N", sell_price, sell_qty)
            else:
                self.order.cancel_all_pending_sell("N", f"{trigger},PausingSell")
                self.priceatri.update_priceatri()
                print("Pausing NO sell")

            self.order.cancel_all_pending_buy("Y", f"{trigger},CancelOppSideOrders")
            self.priceatri.update_priceatri()
            if self.holding_yes_qty > 0:
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "sell")
                if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("Y", f"{trigger},NewSellParams")
                    self.priceatri.update_priceatri()
                    sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "sell")
                    self.__send_all_sell(f"{trigger},SellingOppSideBoughtQty,{set_priceqty_message}", "Y", sell_price, sell_qty)

    def __hold_qty_change_process(self, trigger):
        if (self.side_2_scalp == "Y") and (self.holding_yes_qty > 0):
            sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "sell")
            if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("Y", f"{trigger},HoldQtyChange")
                self.priceatri.update_priceatri()
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "sell")
                self.__send_all_sell(f"{trigger},SellingYesNewQty,{set_priceqty_message}", "Y", sell_price, sell_qty)
            # if self.holding_no_qty > 0:
            #     sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "sell")
            #     if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
            #         self.order.cancel_all_pending_sell("N", "holding qty changed")
            #         self.__send_all_sell("N", sell_price, sell_qty)
        elif (self.side_2_scalp == "N") and (self.holding_no_qty > 0):
            sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "sell")
            if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("N",f"{trigger},HoldQtyChange")
                self.priceatri.update_priceatri()
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "sell")
                self.__send_all_sell(f"{trigger},SellingNoNewQty,{set_priceqty_message}", "N", sell_price, sell_qty)
            # if self.holding_yes_qty > 0:
            #     sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "sell")
            #     if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
            #         self.order.cancel_all_pending_sell("Y")
            #         self.__send_all_sell("Y", sell_price, sell_qty)

    def _get_situation(self):
        if self.yes_fair_price >= self.no_fair_price:
            self.strong_side = "Y"
        else:
            self.strong_side = "N"

        self.side_2_scalp = self.strong_side


    def _set_qty(self):
        # write_exec_buy_order(self.event_id)

        self.holding_yes_qty, self.holding_no_qty = self.mybet.get_holding_qty(self.event_id)
        try:
            self.my_avgbuy_price_yes, self.my_avgsell_price_yes, self.my_avgbuy_price_no, self.my_avgsell_price_no, self.falseavgbuyyes, self.falseavgbuyno = self.trans.get_avg_buysell_price(
                self.event_id)
        except TypeError:
            self.my_avgbuy_price_yes, self.my_avgsell_price_yes, self.my_avgbuy_price_no, self.my_avgsell_price_no = 0, 0, 0, 0
        self.my_lastbuy_price_yes, self.my_lastbuy_price_no = self.mybet.get_buy_price(self.event_id)

        self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * self.avg_qty_multiplier
        if (self.max_buyorder_qty is None) or (self.max_buyorder_qty < self.min_buy_qty):
            self.max_buyorder_qty = self.min_buy_qty
        elif self.max_buyorder_qty >= 100:
            self.max_buyorder_qty = 99

    def _is_myorder_best(self, asset):
        if asset == "Y":
            if not self.priceatri.yes_pending_orders.empty:
                best_price = self.priceatri.yes_pending_orders["price"].iloc[0]
                best_qty = self.priceatri.yes_pending_orders["qty"].iloc[0]
            else:
                best_price = 0
                best_qty = 0
            if not np.isnan(self.priceatri.yes_2ndbest_price) and (self.priceatri.yes_best_price >= self.priceatri.yes_2ndbest_price+2):
                buying_at_competitive = False
            else:
                buying_at_competitive = True
        elif asset == "N":
            if not self.priceatri.no_pending_orders.empty:
                best_price = self.priceatri.no_pending_orders["price"].iloc[0]
                best_qty = self.priceatri.no_pending_orders["qty"].iloc[0]
            else:
                best_price = 0
                best_qty = 0
            if not np.isnan(self.priceatri.no_2ndbest_price) and (self.priceatri.no_best_price >= self.priceatri.no_2ndbest_price+2):
                buying_at_competitive = False
            else:
                buying_at_competitive = True
        else:
            best_price = 0
            best_qty = 0
            buying_at_competitive = True

        if (self.order.is_same_order(asset, best_price, best_qty, "buy")) and buying_at_competitive:
            return True
        else:
            return False

    def __get_make_price_or_best(self, asset):
        if asset == "Y":
            if (self.priceatri.yes_best_price + 1) < (100 - self.priceatri.no_best_price):
                return self.priceatri.yes_best_price + 1, "atbest+1"
            else:
                return self.priceatri.yes_best_price, "atbest"
        elif asset == "N":
            if (self.priceatri.no_best_price + 1) < (100 - self.priceatri.yes_best_price):
                return self.priceatri.no_best_price + 1, "atbest+1"
            else:
                return self.priceatri.no_best_price, "atbest"

    def _get_revised_buy_maxqty(self, asset):
        if asset == "Y":
            if (self.yes_fair_price < 100) and (self.yes_fair_price >= 90):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 5
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 5
            elif (self.yes_fair_price < 90) and (self.yes_fair_price >= 80):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 4
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 4
            elif (self.yes_fair_price < 80) and (self.yes_fair_price >= 70):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 3
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 3
            elif (self.yes_fair_price < 70) and (self.yes_fair_price >= 60):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 2
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 2
            elif (self.yes_fair_price < 60) and (self.yes_fair_price >= 50):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 1
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 1
            else:
                self.max_buyorder_qty = self.min_buy_qty
        elif asset == "N":
            if (self.no_fair_price < 100) and (self.no_fair_price >= 90):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 5
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 5
            elif (self.no_fair_price < 90) and (self.no_fair_price >= 80):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 4
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 4
            elif (self.no_fair_price < 80) and (self.no_fair_price >= 70):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 3
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 3
            elif (self.no_fair_price < 70) and (self.no_fair_price >= 60):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 2
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 2
            elif (self.no_fair_price < 60) and (self.no_fair_price >= 50):
                self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 1
                if self.max_buyorder_qty < self.min_buy_qty:
                    self.max_buyorder_qty = self.min_buy_qty * 1
            else:
                self.max_buyorder_qty = self.min_buy_qty
        else:
            self.max_buyorder_qty = int(self.priceatri.avg_traded_qty) * 1

        if self.max_buyorder_qty is None:
            self.max_buyorder_qty = self.min_buy_qty
        elif self.max_buyorder_qty >= 100:
            self.max_buyorder_qty = 99

    def __get_send_order_price_qty(self, asset, side):
        if asset == "Y":
            if side == "buy":
                self._get_revised_buy_maxqty("Y")
                qty_temp = self.max_buyorder_qty# - self.holding_yes_qty
                price_temp, makeorbestmessage = self.__get_make_price_or_best("Y")
                message = f"BasicBuy,{makeorbestmessage}"
                return price_temp, qty_temp, message
            elif side == "sell":
                sell_qty = self.holding_yes_qty
                # sell_price = int(self.yes_fair_price)
                # sell_price = self.priceatri.yes_best_price + 2
                # print("X" * 20, f"my_buy_price_yes =  {self.my_buy_price_yes} type = {type(self.my_buy_price_yes)}")
                if (self.my_avgbuy_price_yes > self.priceatri.yes_best_price + self.getoutYesDiff) and (self.estimated_yes_fair_price < 85):
                    sell_price = self.priceatri.yes_best_price + 1
                    message = "getOutSell,atYesBest+1"
                elif (self.my_avgbuy_price_yes == 0) or (np.isnan(self.my_avgbuy_price_yes)) or (
                        np.isnan(self.my_lastbuy_price_yes)):
                    sell_price = self.priceatri.yes_best_price + 1
                    message = "NullAvgBuySell,atYesBest+1"
                    print("Yes my_avgbuy_price unavailable")
                    logger.critical(f"{self.event_id}: Yes my_avgbuy_price unavailable")
                else:
                    # sell1 = int(self.my_avgbuy_price_yes) + 1
                    # sell2 = int(self.my_lastbuy_price_yes) + 1
                    # sell_price = max(sell1, sell2)
                    sell_price = math.ceil(self.my_avgbuy_price_yes) + 1
                    if (100 - sell_price) > (self.priceatri.no_best_price + 1):
                        sell_price = 100 - (self.priceatri.no_best_price + 1)
                        message = "ProfitSell,atBetter"
                    else:
                        message = "ProfitSell,atAvgBuy+1"

                return sell_price, sell_qty, message
        elif asset == "N":
            if side == "buy":
                self._get_revised_buy_maxqty("N")
                qty_temp = self.max_buyorder_qty# - self.holding_no_qty
                price_temp, makeorbestmessage = self.__get_make_price_or_best("N")
                message = f"BasicBuy,{makeorbestmessage}"
                return price_temp, qty_temp, message
            elif side == "sell":
                sell_qty = self.holding_no_qty
                # sell_price = int(100 - self.yes_fair_price)
                # sell_price = self.priceatri.no_best_price + 2
                # print("X"*20,f"my_buy_price_no =  {self.my_buy_price_no} type = {type(self.my_buy_price_no)}")

                if (self.my_avgbuy_price_no > self.priceatri.no_best_price + self.getoutNoDiff) and (self.estimated_no_fair_price < 85):
                    sell_price = self.priceatri.no_best_price + 1
                    message = "getOutSell,atNoBest+1"
                elif (self.my_avgbuy_price_no == 0) or (np.isnan(self.my_avgbuy_price_no)) or (
                        np.isnan(self.my_lastbuy_price_no)):
                    sell_price = self.priceatri.no_best_price + 1
                    message = "NullAvgBuySell,atNoBest+1"
                    print("No my_buy_price unavailable")
                    logger.critical(f"{self.event_id}: No my_buy_price unavailable")
                else:
                    # sell1 = int(self.my_avgbuy_price_no) + 1
                    # sell2 = int(self.my_lastbuy_price_no) + 1
                    # sell_price = max(sell1, sell2)
                    sell_price = math.ceil(self.my_avgbuy_price_no) + 1
                    if (100 - sell_price) > (self.priceatri.yes_best_price + 1):
                        sell_price = 100 - (self.priceatri.yes_best_price + 1)
                        message = "ProfitSell,atBetter"
                    else:
                        message = "ProfitSell,atAvgBuy+1"
                return sell_price, sell_qty, message

    def __send_buy_orders(self, message, asset, price, qty):
        if asset == "Y":
            self.order._buy(message, "Y", price, qty)
        elif asset == "N":
            self.order._buy(message, "N", price, qty)

    def __send_all_sell(self, message, asset, sell_price, sell_qty):
        if (asset == "Y") and (self.holding_yes_qty > 0) and (sell_qty > 0) and (sell_price <= 99):
            self.order._sell(message, "Y", sell_price, sell_qty)
        elif (asset == "N") and (self.holding_no_qty > 0) and (sell_qty > 0) and (sell_price <= 99):
            self.order._sell(message, "N", sell_price, sell_qty)

    # def __take_all_for_spread(self):
    #     if (self.side_2_scalp == "Y"):
    #         mask1 = self.priceatri.no_pending_orders["price"] > (100 - self.yes_fair_price)
    #         mask2 = self.priceatri.no_pending_orders["price"] < (100 - self.yes_fair_price) + self.spread
    #         orders_2_take_yes = self.priceatri.no_pending_orders[mask1 & mask2]
    #         if not orders_2_take_yes.empty:
    #             for i in range(orders_2_take_yes.shape[0]):
    #                 print("--Yes take order--")
    #                 self.__send_buy_orders("Absorbing spread", "Y", 100 - orders_2_take_yes["price"].iloc[i], orders_2_take_yes["qty"].iloc[i])
    #     elif (self.side_2_scalp == "N"):
    #         mask1 = self.priceatri.yes_pending_orders["price"] < (self.yes_fair_price + self.spread)
    #         mask2 = self.priceatri.yes_pending_orders["price"] > self.yes_fair_price
    #         orders_2_take_no = self.priceatri.yes_pending_orders[mask1 & mask2]
    #         if not orders_2_take_no.empty:
    #             for i in range(orders_2_take_no.shape[0]):
    #                 print("--No take order--")
    #                 self.__send_buy_orders("Absorbing spread", "N", 100 - orders_2_take_no["price"].iloc[i], orders_2_take_no["qty"].iloc[i])

    def _keep_a_check(self):
        self.priceatri.update_priceatri()
        yes_but_zero = (self.side_2_scalp == "Y") and (self.holding_yes_qty == 0)
        no_but_zero = (self.side_2_scalp == "N") and (self.holding_no_qty == 0)
        if yes_but_zero or no_but_zero:
            if yes_but_zero:
                trigger = "YesSignalZeroHolding"
            elif no_but_zero:
                trigger = "NoSignalZeroHolding"
            print("TRIGGER: ", trigger)
            if self.side_2_scalp == "Y":
                if (self.priceatri.yes_best_price < self.stop_buy_upper_price) and (self.priceatri.yes_best_price >= self.stop_buy_lower_price) :
                    if self.priceatri.yes_best_price > self.stop_sell_upper_price:
                        self.__scalp_side("Y", trigger, pausebuy=False, pausesell=True)
                    else:
                        self.__scalp_side("Y", trigger, pausebuy=False, pausesell=False)
                elif (self.priceatri.yes_best_price > self.stop_buy_upper_price) or (self.priceatri.yes_best_price <= self.stop_buy_lower_price):
                    if self.priceatri.yes_best_price > self.stop_sell_upper_price:
                        self.__scalp_side("Y", trigger, pausebuy=True, pausesell=True)
                    else:
                        self.__scalp_side("Y", trigger, pausebuy=True, pausesell=False)
            elif self.side_2_scalp == "N":
                if (self.priceatri.no_best_price < self.stop_buy_upper_price) and (self.priceatri.no_best_price >= self.stop_buy_lower_price):
                    if self.priceatri.no_best_price > self.stop_sell_upper_price:
                        self.__scalp_side("N", trigger, pausebuy=False, pausesell=True)
                    else:
                        self.__scalp_side("N", trigger, pausebuy=False, pausesell=False)
                elif (self.priceatri.no_best_price > self.stop_buy_upper_price) or (self.priceatri.no_best_price <= self.stop_buy_lower_price):
                    if self.priceatri.no_best_price > self.stop_sell_upper_price:
                        self.__scalp_side("N", trigger, pausebuy=True, pausesell=True)
                    else:
                        self.__scalp_side("N", trigger, pausebuy=True, pausesell=False)

        try:
            hold_y_qty_changed = (self.last_values_dict["y_h_qty"] != self.holding_yes_qty)
            hold_n_qty_changed = (self.last_values_dict["n_h_qty"] != self.holding_no_qty)
            situ_changed = (self.last_values_dict["strong_side"] != self.strong_side)
            scalpside_changed = (self.last_values_dict["side2scalp"] != self.side_2_scalp)
            yfprice_changed = (self.last_values_dict["yes_fprice"] != self.yes_fair_price)
            nfprice_changed = (self.last_values_dict["no_fprice"] != self.no_fair_price)
            yavgbuy_changed = (self.last_values_dict["yavgbuy"] != self.my_avgbuy_price_yes)
            navgbuy_changed = (self.last_values_dict["navgbuy"] != self.my_avgbuy_price_no)
            maxbuyqty_changed = (self.last_values_dict["maxbuyqty"] != self.max_buyorder_qty)
        except KeyError:
            logger.warning(f"{self.event_id}: last_values_dict empty")
        else:
            if hold_y_qty_changed or hold_n_qty_changed:
                if hold_y_qty_changed:
                    trigger = "HoldYesQtyChange"
                elif hold_n_qty_changed:
                    trigger = "HoldNoQtyChange"
                print("TRIGGER: ", trigger)
                self.__hold_qty_change_process(trigger)
            if situ_changed or scalpside_changed or yfprice_changed or nfprice_changed or yavgbuy_changed or navgbuy_changed:
                if situ_changed:
                    trigger = "SituationChange"
                elif scalpside_changed:
                    trigger = "ScalpSideChange"
                elif yfprice_changed:
                    trigger = "YesFairPriceChange"
                elif nfprice_changed:
                    trigger = "NoFairPriceChange"
                elif yavgbuy_changed:
                    trigger = "YesAvgBuyPriceChange"
                elif navgbuy_changed:
                    trigger = "NoAvgBuyPriceChange"
                elif maxbuyqty_changed:
                    trigger = "MaxBuyQtyChange"
                else:
                    trigger = "Un-identified"
                print("TRIGGER: ", trigger)
                if self.side_2_scalp == "Y":
                    if (self.priceatri.yes_best_price <= self.stop_buy_upper_price) and (self.priceatri.yes_best_price >= self.stop_buy_lower_price):
                        if self.priceatri.yes_best_price > self.stop_sell_upper_price:
                            self.__scalp_side("Y", trigger, pausebuy=False, pausesell=True)
                        else:
                            self.__scalp_side("Y", trigger, pausebuy=False, pausesell=False)
                    elif (self.priceatri.yes_best_price > self.stop_buy_upper_price) or (self.priceatri.yes_best_price < self.stop_buy_lower_price):
                        if self.priceatri.yes_best_price > self.stop_sell_upper_price:
                            self.__scalp_side("Y", trigger, pausebuy=True, pausesell=True)
                        else:
                            self.__scalp_side("Y", trigger, pausebuy=True, pausesell=False)
                elif self.side_2_scalp == "N":
                    if (self.priceatri.no_best_price <= self.stop_buy_upper_price) \
                            and (self.priceatri.no_best_price >= self.stop_buy_lower_price):
                        if self.priceatri.no_best_price > self.stop_sell_upper_price:
                            self.__scalp_side("N", trigger, pausebuy=False, pausesell=True)
                        else:
                            self.__scalp_side("N", trigger, pausebuy=False, pausesell=False)
                    elif (self.priceatri.no_best_price > self.stop_buy_upper_price) \
                            or (self.priceatri.no_best_price < self.stop_buy_lower_price):
                        if self.priceatri.no_best_price > self.stop_sell_upper_price:
                            self.__scalp_side("N", trigger, pausebuy=True, pausesell=True)
                        else:
                            self.__scalp_side("N", trigger, pausebuy=True, pausesell=False)

    def absorb_high_probable_orderbook(self):
        if dt.datetime.now() + dt.timedelta(hours=5,minutes=30)+ dt.timedelta(minutes=20) >= dt.datetime.strptime(self.priceatri.ends_at, "%Y-%m-%dT%H:%M:%S"):
            absorb_side = "N" if (self.estimated_yes_fair_price == 99) else "Y" if (self.estimated_no_fair_price == 99) else None
            print(f"Absorbing '{absorb_side}' order book")
            if absorb_side == "N":
                for i in self.priceatri.no_pending_orders.index:
                    buy_price = 100 - self.priceatri.no_pending_orders["price"].loc[i]
                    buy_qty = self.priceatri.no_pending_orders["qty"].loc[i]
                    self.__send_buy_orders("absorbing orderbook", "Y", buy_price, buy_qty)
            elif absorb_side == "Y":
                for i in self.priceatri.yes_pending_orders.index:
                    buy_price = 100 - self.priceatri.yes_pending_orders["price"].loc[i]
                    buy_qty = self.priceatri.yes_pending_orders["qty"].loc[i]
                    self.__send_buy_orders("absorbing orderbook", "N", buy_price, buy_qty)
            else:
                pass



    def initialise(self):
        logger.info(f"{self.event_id}: Initialising event")

        self.priceatri.initialise_priceatri()

        self.__set_event_match_phrase()
        self.__set_estimated_fair_price()
        self.__set_fair_price()

        self.order.cancel_all_pending_buy("Y", "Starting fresh")
        self.order.cancel_all_pending_buy("N", "Starting fresh")
        self.order.cancel_all_pending_sell("Y", "Starting fresh")
        self.order.cancel_all_pending_sell("N", "Starting fresh")

        self._get_situation()
        self._set_qty()
        self._print_details("initialising")
        self.__set_getoutsellpricediff()
        self._keep_a_check()
        self._update_last_values()
        self.initialised = True

    def update(self):
        self.priceatri.update_priceatri()
        self.__set_estimated_fair_price()
        self.__set_fair_price()

        self._get_situation()
        self._set_qty()
        self._print_details("updating")
        self.__set_getoutsellpricediff()
        self._keep_a_check()
        self.absorb_high_probable_orderbook()
        self._update_last_values()
