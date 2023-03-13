"""
for range contracts
on bitcoin using atr not maintaining spread
"""
import numpy as np

from polygon_data import PolygonApi
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
from pnl_update_to_db import PnlToDb

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
file_handler = logging.FileHandler("log_files/strat7_57.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)



class Strategy:
    def __init__(self, event_id, min_buy_qty, avg_qty_multiplier, getOutSellPriceDiff, coin_name,testing=None):
        print("change: no posittion below 20,;yesbuyqty asper pnlifno, viceversa")
        self.userid = None
        self.apitype = None
        self.apitype = 'p'#input("API type: Test or Production (t/p)?: ")
        self.userid = 0#int(input("Enter userid (0 for default): "))
        self.coin_name = coin_name
        self.symbol = None
        self.event_id = event_id
        self.min_buy_qty = min_buy_qty
        self.max_buyorder_qty = None
        self.buyorder_qty1 = None
        self.buyorder_qty2 = None
        self.buyorder_qty3 = None

        self.max_hold_qty = 500
        self.avg_qty_multiplier = avg_qty_multiplier
        self.getOutSellPriceDiff = getOutSellPriceDiff
        self.getoutYesDiff = None
        self.getoutNoDiff = None

        self.absorbing_exposure = 0
        self.absorbing_exposure_limit = 3000

        self.mybet = MyBets(self.apitype, self.userid)
        self.trans = Transactions(self.apitype, self.userid)
        self.order = Order(self.event_id, self.apitype, self.userid)
        self.priceatri = PriceAttri(self.event_id, self.apitype, self.userid)
        self.polygon_obj = PolygonApi()
        self.stratRecorObj = StratRecorder(self.event_id, 7, self.userid)

        self.holding_yes_qty = 0
        self.holding_no_qty = 0
        self.yes_fair_price = None
        self.no_fair_price = None
        self.estimated_yes_fair_price = None
        self.estimated_no_fair_price = None
        self.est_yfp_nodirection = None
        self.est_nfp_nodirection = None
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

        self.atr_value = 0
        self.custom_indi_value = None
        self.time_2_expiry_cat = None
        self.spot_cmp = None
        self.strike_price = None

        self.last_values_dict = dict()
        self.stop_buy_upper_price = 100#int(input('Upper price limit'))
        self.stop_buy_lower_price = 0#int(input('Lower price limit'))
        self.stop_sell_upper_price = 100
        self.yesfp_std = None
        self.nofp_std = None
        self.yes_fpminusbp_std = None
        self.no_fpminusbp_std = None

        self.pnltodb = PnlToDb(event_id)
        self.initialised = False
        self.per_side_exposure_limit = 500
        self.default_spread_each_side = 5
        self.make_max_buy_order_qty = 5
        self.make_stop_lower_price = 20

        self.yes_left_exposure = self.per_side_exposure_limit
        self.no_left_exposure = self.per_side_exposure_limit

    # upgraded to codes_3/utils/set_finance_timeexpiry_category
    def __set_expiry_category(self):
        now = dt.datetime.now()
        end = dt.datetime.fromisoformat(self.priceatri.ends_at)
        delta = end - now
        if delta <= dt.timedelta(minutes=1):
            self.time_2_expiry_cat = "1min"
        elif delta <= dt.timedelta(minutes=3):
            self.time_2_expiry_cat = "3min"
        elif delta <= dt.timedelta(minutes=5):
            self.time_2_expiry_cat = "5min"
        elif delta <= dt.timedelta(minutes=15):
            self.time_2_expiry_cat = "15min"
        elif delta <= dt.timedelta(minutes=30):
            self.time_2_expiry_cat = "30min"
        elif delta <= dt.timedelta(hours=1):
            self.time_2_expiry_cat = "1hr"
        elif delta <= dt.timedelta(hours=2):
            self.time_2_expiry_cat = "2hr"
        elif delta <= dt.timedelta(hours=4):
            self.time_2_expiry_cat = "4hr"
        elif delta <= dt.timedelta(hours=6):
            self.time_2_expiry_cat = "6hr"
        elif delta <= dt.timedelta(hours=8):
            self.time_2_expiry_cat = "8hr"
        else:
            self.time_2_expiry_cat = "12hr"

    #upgraded to codes_3/events/underlyingextractor
    def __set_strike_price(self):
        if self.coin_name == "custom":
            print("taking custom fair price")
            self.strike_price = float(81045.74)
            self.strike_price = float(0)
        else:
            t1 = self.priceatri.title.split(":")
            t2 = t1[3].split("or more?")
            t3 = t2[0]
            self.strike_price = float(t3)
            # self.strike_price = int(self.strike_price)


    #upgraded to codes_3/binance_data/cryptofairprice
    def __set_atr_value(self):
        if self.coin_name == "netflix":
            self.symbol = "NFLX"
        elif self.coin_name == "eth":
            self.symbol = "ETHUSDT"
        elif self.coin_name == "shi":
            self.symbol = "SHIBUSDT"
        elif self.coin_name == "dog":
            self.symbol = "DOGEUSDT"
        elif self.coin_name == "gbp":
            self.symbol = "GBPUSDT"
        elif self.coin_name == "eur":
            self.symbol = "EURUSDT"
        else:
            self.symbol = "BTCUSDT"

        self.atr_value = self.polygon_obj.get_last_atr(symbol=self.symbol, interval=self.time_2_expiry_cat)
        self.custom_indi_value = self.polygon_obj.get_cutom_indi_value(symbol=self.symbol, interval=self.time_2_expiry_cat)

    #upgraded to codes_3/binance_data/cryptofairprice
    def __set_estimated_fair_price(self):
        self.spot_cmp =self.polygon_obj.get_current_price(symbol=self.symbol)

        print("spot-strike", self.spot_cmp - self.strike_price)
        # print("spot+atr-strike", self.spot_cmp + self.atr_value - self.strike_price)
        print("spot+atr", self.spot_cmp + self.atr_value)
        print("spot-atr", self.spot_cmp - self.atr_value)

        if self.strike_price > (self.spot_cmp + self.atr_value):
            self.est_yfp_nodirection = 1
        elif self.strike_price < (self.spot_cmp - self.atr_value):
            self.est_yfp_nodirection = 99
        else:
            self.est_yfp_nodirection = (self.spot_cmp + self.atr_value - self.strike_price) * (98 / (2 * self.atr_value)) + 1

        self.est_nfp_nodirection = 100 - self.est_yfp_nodirection

        # if self.custom_indi_value == 0:
        #     self.estimated_yes_fair_price = self.est_yfp_nodirection
        # elif self.custom_indi_value == -1:
        #     self.estimated_yes_fair_price = (1 + self.est_yfp_nodirection)/2
        # elif self.custom_indi_value == 1:
        #     self.estimated_yes_fair_price = (99 + self.est_yfp_nodirection)/2
        # else:
        #     self.estimated_yes_fair_price = int(self.est_yfp_nodirection)
        #     raise Exception("invalid custom indicator value")
        #
        # self.estimated_yes_fair_price = int(self.estimated_yes_fair_price)

        self.estimated_yes_fair_price = int(self.est_yfp_nodirection)


        # self.estimated_yes_fair_price = int(self.est_yfp_nodirection)
        self.estimated_no_fair_price = 100 - self.estimated_yes_fair_price

    #upgraded to codes_3/binance_data/cryptofairprice
    def __set_fair_price(self):
        self.yes_fair_price = self.estimated_yes_fair_price
        self.no_fair_price = self.estimated_no_fair_price

        # self.yes_fair_price = (2 * self.estimated_yes_fair_price + self.priceatri.yes_ob_vwap) / 3
        # self.no_fair_price = (2 * self.estimated_no_fair_price + self.priceatri.no_ob_vwap) / 3
        # if self.custom_indi_value == 0:
        #     self.yes_fair_price = (2*self.estimated_yes_fair_price + self.priceatri.yes_ob_vwap) / 3
        #     self.no_fair_price = (2 * self.estimated_no_fair_price + self.priceatri.no_ob_vwap) / 3
        # elif self.custom_indi_value == 1:
        #     self.yes_fair_price = (99 + self.estimated_yes_fair_price + self.priceatri.yes_ob_vwap) / 3
        #     self.no_fair_price = (1 + self.estimated_no_fair_price + self.priceatri.no_ob_vwap) / 3
        # elif self.custom_indi_value == -1:
        #     self.yes_fair_price = (1 + self.estimated_yes_fair_price + self.priceatri.yes_ob_vwap) / 3
        #     self.no_fair_price = (99 + self.estimated_no_fair_price + self.priceatri.no_ob_vwap) / 3

        # print("--yes fair price")
        # print(self.priceatri.yes_best_price)
        # print("-")
        # print(self.priceatri.yes_ob_vwap)
        # print("-")
        # print(self.yes_fair_price)
        # print("--")

        # print("--no fair price")
        # print(self.priceatri.no_best_price)
        # print("-")
        # print(self.priceatri.no_ob_vwap)
        # print("-")
        # print(self.no_fair_price)
        # print("--")



    # sets price difference from buy price at which sell and exit if price varied too much
    def __set_getoutsellpricediff(self):
        if self.getOutSellPriceDiff == "dynamic":
            try:
                # client = pm.MongoClient("localhost", 27017)
                # db = client.tradex_strat_data
                # collection = db[f"strat7_{self.event_id}_{self.userid}"]
                # cursor = collection.find()
                # df = pd.DataFrame(cursor)
                df = self.stratRecorObj.get_data_df_from_psql_backtest1(self.event_id)
                if df.shape[0] > 1:
                    self.yesfp_std = int(df["yesfp"].std())
                    self.nofp_std = int(df["npfp"].std())
                    self.yes_fpminusbp_std = int((df["yesfp"]-df["yesbp"]).abs().std())
                    self.no_fpminusbp_std = int((df["npfp"] - df["nobp"]).abs().std())
                else:
                    self.yesfp_std = 0
                    self.nofp_std = 0
                    self.yes_fpminusbp_std = 0
                    self.no_fpminusbp_std = 0

                self.getoutYesDiff = max(5, self.yes_fpminusbp_std)
                self.getoutNoDiff = max(5, self.no_fpminusbp_std)

            except Exception as e:
                print("Reading fair price from mongo error: ", e)
                self.getoutYesDiff = 5
                self.getoutNoDiff = 5
                logger.exception(e)
                # raise e
            print(f"Get out sell to {self.getoutYesDiff} and {self.getoutNoDiff}")
        else:
            self.getoutYesDiff = self.getOutSellPriceDiff
            self.getoutNoDiff = self.getOutSellPriceDiff

    # prints required info including orders, event prices
    def _print_details(self, process):
        print_dict = {"Userid": [self.userid, self.userid],
                      "apiType": [self.apitype, self.apitype],
                      "BestPrice": [self.priceatri.yes_best_price, self.priceatri.no_best_price],
                      "OBvwap": [self.priceatri.yes_ob_vwap, self.priceatri.no_ob_vwap],
                      "e_fp_nodir": [self.est_yfp_nodirection, self.est_nfp_nodirection],
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
                      "MaxHoldQty": [self.max_hold_qty, self.max_hold_qty],
                      "symbol": [self.coin_name, self.symbol],
                      "SpotPrice": [self.spot_cmp, self.spot_cmp],
                      "Strike": [self.strike_price, self.strike_price],
                      "ATR": [self.atr_value, self.atr_value],
                      "spo-stri": [self.spot_cmp - self.strike_price, self.spot_cmp - self.strike_price],
                      "CIV": [self.custom_indi_value, self.custom_indi_value],
                      "int": [self.time_2_expiry_cat, self.time_2_expiry_cat]}
        print(dt.datetime.now(), "-" * 50)
        if process == "initialising":
            print(
                f"Initialising {self.priceatri.eid}: {self.priceatri.title} | started at {self.priceatri.started_at} ends at {self.priceatri.ends_at}")
        elif process == "updating":
            print(
                f"Updating {self.priceatri.eid}: {self.priceatri.title} | started at {self.priceatri.started_at} ends at {self.priceatri.ends_at}")
        print(pd.DataFrame(print_dict, index=["Yes", "No"]))
        print("-" * 10, "PENDING BOOK:")
        print(self.priceatri.yes_pending_orders.head(3))
        print(self.priceatri.no_pending_orders.head(3))
        print("-" * 10, "ORDERS:")
        print(self.mybet.get_event_holdings(self.event_id).head(3))
        print("...")
        print(self.mybet.get_event_holdings(self.event_id).tail(3))

    # stores trigger, orders and prices
    def _strat_status_record(self):
        data_dict = dict()
        data_dict["timestamp"] = str(dt.datetime.now())
        data_dict["side_2_scalp"] = self.side_2_scalp
        data_dict["spot_price"] = self.spot_cmp
        data_dict["strike_price"] = self.strike_price
        data_dict["atr_value"] = self.atr_value
        data_dict["getOutdiff"] = self.getOutSellPriceDiff
        data_dict["yes_getout"] = float(self.getoutYesDiff)
        data_dict["no_getout"] = float(self.getoutNoDiff)
        data_dict["yesfp"] = self.yes_fair_price
        data_dict["nofp"] = self.no_fair_price
        data_dict["yesefp"] = self.estimated_yes_fair_price
        data_dict["noefp"] = self.estimated_no_fair_price
        data_dict["yesbp"] = float(self.priceatri.yes_best_price)
        data_dict["nobp"] = float(self.priceatri.no_best_price)
        data_dict["yesobvwap"] = float(self.priceatri.yes_ob_vwap)
        data_dict["noobvwap"] = float(self.priceatri.no_ob_vwap)
        if (self.priceatri.yes_2ndbest_price == None) or (np.isnan(self.priceatri.yes_2ndbest_price)):
            data_dict["yes2ndbp"] = self.priceatri.yes_2ndbest_price
        else:
            data_dict["yes2ndbp"] = float(self.priceatri.yes_2ndbest_price)
        if (self.priceatri.no_2ndbest_price == None) or (np.isnan(self.priceatri.no_2ndbest_price)):
            data_dict["no2ndbp"] = self.priceatri.no_2ndbest_price
        else:
            data_dict["no2ndbp"] = float(self.priceatri.no_2ndbest_price)
        data_dict["yesabp"] = self.my_avgbuy_price_yes
        data_dict["noabp"] = self.my_avgbuy_price_no
        data_dict["yesasp"] = self.my_avgsell_price_yes
        data_dict["noasp"] = self.my_avgsell_price_no
        data_dict["yesholdqty"] = float(self.holding_yes_qty)
        data_dict["noholdqty"] = float(self.holding_no_qty)
        data_dict["maxbuyqty"] = float(self.max_buyorder_qty)
        data_dict["maxholdqty"] = float(self.max_hold_qty)
        data_dict["orders"] = self.mybet.get_event_holdings(self.event_id).to_dict("records")
        # print(data_dict)
        # self.stratRecorObj._add_one_doc(data_dict)
        # print("strat situation logged to mongo")
        self.stratRecorObj.add_to_psql(str(data_dict["timestamp"]), self.userid, self.event_id, None, data_dict["yesfp"], data_dict["nofp"] , data_dict["yesbp"] , data_dict["nobp"])

    # used to compare change in prices and other params
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

    # sends and cancels required orders as per strong side, stopBuyingUpper/LowerPrice
    def __scalp_side(self, asset, trigger, pausebuy, pausesell):
        print("pausebuy: ", pausebuy, "worstcaselimit: ", self.pnltodb.worstcase_limit_reached, "pnlworst: ", self.pnltodb.pnl_worst_2)
        print("pausebuy: ", pausebuy, "worstcaselimit: ", self.pnltodb.worstcase_limit_reached, "pnlworst: ", self.pnltodb.pnl_worst_2)
        print("pausebuy: ", pausebuy, "worstcaselimit: ", self.pnltodb.worstcase_limit_reached, "pnlworst: ", self.pnltodb.pnl_worst_2)
        print("pausebuy: ", pausebuy, "worstcaselimit: ", self.pnltodb.worstcase_limit_reached, "pnlworst: ", self.pnltodb.pnl_worst_2)
        print()
        if self.pnltodb.worstcase_limit_reached:
            print("worst limit worst limit worst limit worst limit worst limit ")
            print("worst limit worst limit worst limit worst limit worst limit ")
            print("worst limit worst limit worst limit worst limit worst limit ")
        if asset == "Y":
            if (not pausebuy) and (not self.pnltodb.worstcase_limit_reached):
            # if (not pausebuy) and (self.atr_value < abs(self.spot_cmp - self.strike_price)) and (not self.pnltodb.worstcase_limit_reached):
                temp_price, temp_qty, set_priceqty_message = self.__get_send_order_price_qty2("Y", "buy")
                if (temp_qty > 0) and (temp_price <= self.stop_buy_upper_price) and (not self.order.is_same_order("Y", temp_price, temp_qty, "buy")) and (not self._is_myorder_best("Y")):
                    self.order.cancel_all_pending_buy("Y", f"{trigger},NewBuyParams")
                    self.priceatri.update_priceatri()
                    # price_qty_message_list = self.get_staggered_priceqty_list()
                    # for pqm in price_qty_message_list:
                    #     self.__send_buy_orders(f"{trigger},ScalpingYes,{pqm[2]}", "Y", pqm[0], pqm[1])
                    temp_price, temp_qty, set_priceqty_message = self.__get_send_order_price_qty2("Y", "buy")
                    self.__send_buy_orders(f"{trigger},ScalpingYes,{set_priceqty_message}", "Y", temp_price, temp_qty)

            else:
                self.order.cancel_all_pending_buy("Y", f"{trigger},PausingBuy")
                self.priceatri.update_priceatri()
                print("Pausing YES buy")
            if not pausesell:
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("Y", "sell")
                if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("Y", f"{trigger},NewSellParams")
                    self.priceatri.update_priceatri()
                    sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("Y", "sell")
                    self.__send_all_sell(f"{trigger},SellingBoughtQty,{set_priceqty_message}", "Y", sell_price, sell_qty)
            else:
                self.order.cancel_all_pending_sell("Y", f"{trigger},PausingSell")
                self.priceatri.update_priceatri()
                print("Pausing YES sell")

            self.order.cancel_all_pending_buy("N", f"{trigger},CancelOppSideOrders")
            self.priceatri.update_priceatri()
            if self.holding_no_qty > 0:
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("N", "sell")
                if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("N", f"{trigger},NewSellParams")
                    self.priceatri.update_priceatri()
                    sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("N", "sell")
                    self.__send_all_sell(f"{trigger},SellingOppSideBoughtQty,{set_priceqty_message}", "N", sell_price, sell_qty)
        elif asset == "N":
            if (not pausebuy) and (not self.pnltodb.worstcase_limit_reached):
            # if (not pausebuy) and (self.atr_value < abs(self.spot_cmp - self.strike_price)) and (not self.pnltodb.worstcase_limit_reached):
                temp_price, temp_qty, set_priceqty_message = self.__get_send_order_price_qty2("N", "buy")
                if (temp_qty > 0) and (temp_price <= self.stop_buy_upper_price) and (not self.order.is_same_order("N", temp_price, temp_qty, "buy")) and (not self._is_myorder_best("N")):
                    self.order.cancel_all_pending_buy("N", f"{trigger},NewBuyParams")
                    self.priceatri.update_priceatri()
                    temp_price, temp_qty, set_priceqty_message = self.__get_send_order_price_qty2("N", "buy")
                    self.__send_buy_orders(f"{trigger},ScalpingNo,{set_priceqty_message}", "N", temp_price, temp_qty)
            else:
                self.order.cancel_all_pending_buy("N", f"{trigger},PausingBuy")
                self.priceatri.update_priceatri()
                print("Pausing NO buy")

            if not pausesell:
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("N", "sell")
                if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("N", f"{trigger},NewSellParams")
                    self.priceatri.update_priceatri()
                    sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("N", "sell")
                    self.__send_all_sell(f"{trigger},SellingBoughtQty,{set_priceqty_message}", "N", sell_price, sell_qty)
            else:
                self.order.cancel_all_pending_sell("N", f"{trigger},PausingSell")
                self.priceatri.update_priceatri()
                print("Pausing NO sell")

            self.order.cancel_all_pending_buy("Y", f"{trigger},CancelOppSideOrders")
            self.priceatri.update_priceatri()
            if self.holding_yes_qty > 0:
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("Y", "sell")
                if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("Y", f"{trigger},NewSellParams")
                    self.priceatri.update_priceatri()
                    sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("Y", "sell")
                    self.__send_all_sell(f"{trigger},SellingOppSideBoughtQty,{set_priceqty_message}", "Y", sell_price, sell_qty)


    def __scalp_side2(self, asset, trigger):
        self.pnltodb.update()
        self.set_left_to_expose()
        self.set_buy_price_with_spread()
        self.set_qty_to_trade_asper_exposure()
        pausebuy = "empty"
        # print("pausebuy: ", pausebuy, "worstcaselimit: ", self.pnltodb.worstcase_limit_reached, "pnlworst: ", self.pnltodb.pnl_worst_2)
        # print("pausebuy: ", pausebuy, "worstcaselimit: ", self.pnltodb.worstcase_limit_reached, "pnlworst: ", self.pnltodb.pnl_worst_2)
        # print("pausebuy: ", pausebuy, "worstcaselimit: ", self.pnltodb.worstcase_limit_reached, "pnlworst: ", self.pnltodb.pnl_worst_2)
        # print("pausebuy: ", pausebuy, "worstcaselimit: ", self.pnltodb.worstcase_limit_reached, "pnlworst: ", self.pnltodb.pnl_worst_2)
        print()
        # if self.pnltodb.worstcase_limit_reached:
        #     print("worst limit worst limit worst limit worst limit worst limit ")
        #     print("worst limit worst limit worst limit worst limit worst limit ")
        #     print("worst limit worst limit worst limit worst limit worst limit ")
        if asset == "Y":
            print("yes | exposed: ", self.pnltodb.pnl_if_no, " | left: ", self.yes_left_exposure)
            if self.yes_left_exposure > 0:
                self.set_left_to_expose()
                self.set_buy_price_with_spread()
                self.set_qty_to_trade_asper_exposure()
                temp_price = self.yes_buyprice_w_spread
                temp_qty = self.yes_buyqty
                print(f"yes order price: {temp_price} qty: {temp_qty}")
                if (temp_qty > 0) and (not self.order.is_same_order(asset, temp_price, temp_qty, "buy")):
                    self.order.cancel_all_pending_buy(asset, "new_buy_make_order")
                    self.priceatri.update_priceatri()
                    self.set_left_to_expose()
                    self.set_buy_price_with_spread()
                    self.set_qty_to_trade_asper_exposure()
                    temp_price = self.yes_buyprice_w_spread
                    temp_qty = self.yes_buyqty
                    temp_message = "make_with_spread"
                    print(f"yes order price: {temp_price} qty: {temp_qty}, just before send order")
                    self.__send_buy_orders(temp_message, asset, temp_price, temp_qty)
                else:
                    print("x"*10 ,"qty zero or same order", "qty: ", temp_qty, "price: ", temp_price)
            else:
                print("yes | exposed: ", self.pnltodb.pnl_if_no, " | left: ", self.yes_left_exposure)
                print("x"*10 ,"yes too much exposed, paused buying")
                self.order.cancel_all_pending_buy(asset, "too much exposed")
                self.priceatri.update_priceatri()
                self.set_left_to_expose()
                self.set_buy_price_with_spread()
                self.set_qty_to_trade_asper_exposure()
        elif asset == "N":
            print()
            print("no | exposed: ", self.pnltodb.pnl_if_yes, " | left: ", self.no_left_exposure)
            if self.no_left_exposure > 0:
                self.set_left_to_expose()
                self.set_buy_price_with_spread()
                self.set_qty_to_trade_asper_exposure()
                temp_price = self.no_buyprice_w_spread
                temp_qty = self.no_buyqty
                print(f"no order price: {temp_price} qty: {temp_qty}")
                if (temp_qty > 0) and (not self.order.is_same_order(asset, temp_price, temp_qty, "buy")):
                    self.order.cancel_all_pending_buy(asset, "new_buy_make_order")
                    self.priceatri.update_priceatri()
                    self.set_left_to_expose()
                    self.set_buy_price_with_spread()
                    self.set_qty_to_trade_asper_exposure()
                    temp_price = self.no_buyprice_w_spread
                    temp_qty = self.no_buyqty
                    temp_message = "make_with_spread"
                    print(f"no order price: {temp_price} qty: {temp_qty}, just before send order")
                    self.__send_buy_orders(temp_message, asset, temp_price, temp_qty)
                else:
                    print("x"*10 ,"qty zero or same order", "qty: ", temp_qty, "price: ", temp_price)
            else:
                print("no | exposed: ", self.pnltodb.pnl_if_yes, " | left: ", self.no_left_exposure)
                print("x"*10 ,"no too much exposed, paused buying")
                self.order.cancel_all_pending_buy(asset, "too much exposed")
                self.priceatri.update_priceatri()
                self.set_left_to_expose()
                self.set_buy_price_with_spread()
                self.set_qty_to_trade_asper_exposure()



    # if holding qty is changed sell all qty new order and cancel previous
    def __hold_qty_change_process(self, trigger):
        if (self.side_2_scalp == "Y") and (self.holding_yes_qty > 0):
            sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("Y", "sell")
            if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("Y", f"{trigger},HoldQtyChange")
                self.priceatri.update_priceatri()
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("Y", "sell")
                self.__send_all_sell(f"{trigger},SellingYesNewQty,{set_priceqty_message}", "Y", sell_price, sell_qty)
            # if self.holding_no_qty > 0:
            #     sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("N", "sell")
            #     if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
            #         self.order.cancel_all_pending_sell("N", "holding qty changed")
            #         self.__send_all_sell("N", sell_price, sell_qty)
        elif (self.side_2_scalp == "N") and (self.holding_no_qty > 0):
            sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("N", "sell")
            if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("N",f"{trigger},HoldQtyChange")
                self.priceatri.update_priceatri()
                sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty2("N", "sell")
                self.__send_all_sell(f"{trigger},SellingNoNewQty,{set_priceqty_message}", "N", sell_price, sell_qty)
            # if self.holding_yes_qty > 0:
            #     sell_price, sell_qty, set_priceqty_message = self.__get_send_order_price_qty("Y", "sell")
            #     if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
            #         self.order.cancel_all_pending_sell("Y")
            #         self.__send_all_sell("Y", sell_price, sell_qty)

    #upgraded to codes_3/events_analyser
    def _get_situation(self):
        # if (self.yes_fair_price >= 50):
        #     self.strong_side = "Y"
        # elif (self.no_fair_price < 50):
        #     self.strong_side = "N"

        # diff_fair_best_y = self.yes_fair_price - self.priceatri.yes_best_price
        # diff_fair_best_n = self.no_fair_price - self.priceatri.no_best_price
        # if (diff_fair_best_y > diff_fair_best_n):
        #     self.side_2_scalp = "Y"
        # else:
        #     self.side_2_scalp = "N"

        # if (self.side_2_scalp == "Y"):
        #     if self.priceatri.yes_best_price < self.stop_buy_lower_price:
        #         self.side_2_scalp = "N"
        # if (self.side_2_scalp == "N"):
        #     if self.priceatri.no_best_price < self.stop_buy_lower_price:
        #         self.side_2_scalp = "Y"
        if self.yes_fair_price >= self.no_fair_price:
            self.strong_side = "Y"
        else:
            self.strong_side = "N"

        self.side_2_scalp = self.strong_side

    # reads current holding qty, avgexecute buy/sell prices and limits buy orders qty to 99
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

        self.buyorder_qty3 = math.floor(self.max_buyorder_qty * 0.5)
        self.buyorder_qty2 = math.floor(self.max_buyorder_qty * 0.35)
        self.buyorder_qty1 = self.max_buyorder_qty - self.buyorder_qty3 - self.buyorder_qty2

    # to check if order between 3rd best price and your price at 1st best price in cancelled
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

    # if at +1 price wouldn't be a take order
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


    # increase/decrease qty as per range price is in
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

    def get_staggered_priceqty_list(self, asset, side):
        temp_list = []
        if asset == "Y":
            if side == "buy":
                first_qty = self.buyorder_qty1
                first_price = self.yes_fair_price - 5
                first_message = "first_buy"

                second_qty = self.buyorder_qty2
                second_price = self.yes_fair_price - 6
                second_message = "second_buy"

                third_qty = self.buyorder_qty3
                third_price = self.yes_fair_price - 7
                third_message = "third_buy"

                temp_list = [(first_message, first_price, first_qty), (second_message, second_price, second_qty), (third_message, third_price, third_qty)]
                return temp_list
            elif side == "sell":
                sell_qty = self.holding_yes_qty
                sellorder_qty3 = math.floor(sell_qty * 0.5)
                sellorder_qty2 = math.floor(sell_qty * 0.35)
                sellorder_qty1 = sell_qty - sellorder_qty3 - sellorder_qty2

                sellorder_price1 = 100 - self.no_fair_price - 5
                sellorder_price2 = 100 - self.no_fair_price - 6
                sellorder_price3 = 100 - self.no_fair_price - 7

                sellorder_message1 = "1stsell"
                sellorder_message2 = "2ndsell"
                sellorder_message3 = "3rdsell"

                temp_list = [(sellorder_message1, sellorder_price1, sellorder_qty1), (sellorder_message2, sellorder_price2, sellorder_qty2),
                             (sellorder_message3, sellorder_price3, sellorder_qty3)]
                return temp_list
        elif asset == "N":
            if side == "buy":
                first_qty = self.buyorder_qty1
                first_price = self.no_fair_price - 5
                first_message = "first_buy"

                second_qty = self.buyorder_qty2
                second_price = self.no_fair_price - 6
                second_message = "second_buy"

                third_qty = self.buyorder_qty3
                third_price = self.no_fair_price - 7
                third_message = "third_buy"

                temp_list = [(first_message, first_price, first_qty), (second_message, second_price, second_qty),
                             (third_message, third_price, third_qty)]
                return temp_list
            elif side == "sell":
                sell_qty = self.holding_yes_qty
                sellorder_qty3 = math.floor(sell_qty * 0.5)
                sellorder_qty2 = math.floor(sell_qty * 0.35)
                sellorder_qty1 = sell_qty - sellorder_qty3 - sellorder_qty2

                sellorder_price1 = 100 - self.yes_fair_price - 5
                sellorder_price2 = 100 - self.yes_fair_price - 6
                sellorder_price3 = 100 - self.yes_fair_price - 7

                sellorder_message1 = "1stsell"
                sellorder_message2 = "2ndsell"
                sellorder_message3 = "3rdsell"

                temp_list = [(sellorder_message1, sellorder_price1, sellorder_qty1),
                             (sellorder_message2, sellorder_price2, sellorder_qty2),
                             (sellorder_message3, sellorder_price3, sellorder_qty3)]
                return temp_list


    # gives price and qty as per order being sent
    def __get_send_order_price_qty(self, asset, side):
        if asset == "Y":
            if side == "buy":
                # self._get_revised_buy_maxqty("Y")
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
                # self._get_revised_buy_maxqty("N")
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

    def __get_send_order_price_qty2(self, asset, side):
        print("using get_send_order_price_qty...")
        if asset == "Y":
            if side == "buy":
                # self._get_revised_buy_maxqty("Y")
                qty_temp = self.max_buyorder_qty  # - self.holding_yes_qty
                price_temp = self.yes_fair_price - 5
                makeorbestmessage = "atfairprice"
                message = f"BasicBuy,{makeorbestmessage}"
                return price_temp, qty_temp, message
            elif side == "sell":
                sell_qty = self.holding_yes_qty
                # sell_price = int(self.yes_fair_price)
                # sell_price = self.priceatri.yes_best_price + 2
                # print("X" * 20, f"my_buy_price_yes =  {self.my_buy_price_yes} type = {type(self.my_buy_price_yes)}")
                if (self.my_avgbuy_price_yes > self.priceatri.yes_best_price + self.getoutYesDiff) and (
                        self.estimated_yes_fair_price < 85):
                    sell_price = 100 - self.no_fair_price + 5
                    message = "sellatfairprice"
                elif (self.my_avgbuy_price_yes == 0) or (np.isnan(self.my_avgbuy_price_yes)) or (
                        np.isnan(self.my_lastbuy_price_yes)):
                    sell_price = 100 - self.no_fair_price + 5
                    message = "NullAvgBuySell,atYesBest+1"
                    print("Yes my_avgbuy_price unavailable")
                    logger.critical(f"{self.event_id}: Yes my_avgbuy_price unavailable")
                else:
                    # sell1 = int(self.my_avgbuy_price_yes) + 1
                    # sell2 = int(self.my_lastbuy_price_yes) + 1
                    # sell_price = max(sell1, sell2)
                    sell_price = 100 - self.no_fair_price + 5
                    message = "sellatfairprice"
                return sell_price, sell_qty, message
        elif asset == "N":
            if side == "buy":
                # self._get_revised_buy_maxqty("N")
                qty_temp = self.max_buyorder_qty  # - self.holding_no_qty
                price_temp = self.no_fair_price - 5
                makeorbestmessage = "buyatfair"
                message = f"BasicBuy,{makeorbestmessage}"
                return price_temp, qty_temp, message
            elif side == "sell":
                sell_qty = self.holding_no_qty
                # sell_price = int(100 - self.yes_fair_price)
                # sell_price = self.priceatri.no_best_price + 2
                # print("X"*20,f"my_buy_price_no =  {self.my_buy_price_no} type = {type(self.my_buy_price_no)}")

                if (self.my_avgbuy_price_no > self.priceatri.no_best_price + self.getoutNoDiff) and (
                        self.estimated_no_fair_price < 85):
                    sell_price = 100 - self.yes_fair_price + 5
                    message = "sellatfair"
                elif (self.my_avgbuy_price_no == 0) or (np.isnan(self.my_avgbuy_price_no)) or (
                        np.isnan(self.my_lastbuy_price_no)):
                    sell_price = 100 - self.yes_fair_price + 5
                    message = "sellatfair"
                    print("No my_buy_price unavailable")
                    logger.critical(f"{self.event_id}: No my_buy_price unavailable")
                else:
                    # sell1 = int(self.my_avgbuy_price_no) + 1
                    # sell2 = int(self.my_lastbuy_price_no) + 1
                    # sell_price = max(sell1, sell2)
                    sell_price = 100 - self.yes_fair_price + 5
                    message = "sellatfair"
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

    def get_spread_and_side_as_per_exposure(self):
        if self.pnltodb.pnl_if_yes > self.per_side_exposure_limit:
            pass


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

    #trade both sides with exposure control
    # def set_left_to_expose(self):
    #     if self.pnltodb.pnl_if_no < 0:
    #         self.no_left_exposure = self.per_side_exposure_limit + self.pnltodb.pnl_if_no
    #     else:
    #         self.no_left_exposure = self.per_side_exposure_limit
    #
    #     if self.pnltodb.pnl_if_yes < 0:
    #         self.yes_left_exposure = self.per_side_exposure_limit + self.pnltodb.pnl_if_yes
    #     else:
    #         self.yes_left_exposure = self.per_side_exposure_limit

    def set_left_to_expose(self):
        if self.pnltodb.pnl_if_no < 0:
            self.yes_left_exposure = self.per_side_exposure_limit + self.pnltodb.pnl_if_no
        else:
            self.yes_left_exposure = self.per_side_exposure_limit

        if self.pnltodb.pnl_if_yes < 0:
            self.no_left_exposure = self.per_side_exposure_limit + self.pnltodb.pnl_if_yes
        else:
            self.no_left_exposure = self.per_side_exposure_limit

    def set_buy_price_with_spread(self):
        temp_yes_buyprice_w_spread = self.estimated_yes_fair_price - self.default_spread_each_side
        # self.yes_buyprice_w_spread = max(1, temp_yes_buyprice_w_spread)
        self.yes_buyprice_w_spread = temp_yes_buyprice_w_spread
        temp_no_buyprice_w_spread = self.estimated_no_fair_price - self.default_spread_each_side
        # self.no_buyprice_w_spread = max(1, temp_no_buyprice_w_spread)
        self.no_buyprice_w_spread = temp_no_buyprice_w_spread

    def set_qty_to_trade_asper_exposure(self):
        if (self.yes_left_exposure <= 0) or (self.yes_buyprice_w_spread <= self.make_stop_lower_price):
            print(
                f"yes | qty: zero | leftexpo:{self.yes_left_exposure} | pnlifno:{self.pnltodb.pnl_if_no} | buyprice:{self.yes_buyprice_w_spread} | fp:{self.estimated_yes_fair_price} | holdqty: {self.holding_yes_qty}")
            self.yes_buyqty = 0
        else:
            self.yes_buyqty = math.floor(abs(self.yes_left_exposure) / self.yes_buyprice_w_spread)
            print(
                f"yes | qty: {self.yes_buyqty} | leftexpo:{self.yes_left_exposure} | pnlifno:{self.pnltodb.pnl_if_no} | buyprice:{self.yes_buyprice_w_spread} | fp:{self.estimated_yes_fair_price} | holdqty: {self.holding_yes_qty}")
            if self.yes_buyqty > self.make_max_buy_order_qty:
                self.yes_buyqty = self.make_max_buy_order_qty

        # self.no_buyprice_w_spread <= self.make_stop_lower_price - self.

        if (self.no_left_exposure <= 0) or (self.no_buyprice_w_spread <= self.make_stop_lower_price):
            print(
                f"no  | qty: zero | leftexpo:{self.no_left_exposure} | pnlifyes:{self.pnltodb.pnl_if_yes} | buyprice:{self.no_buyprice_w_spread} | fp:{self.estimated_no_fair_price} | holdqty: {self.holding_no_qty}")
            self.no_buyqty = 0
        else:
            self.no_buyqty = math.floor(self.no_left_exposure / self.no_buyprice_w_spread)
            print(
                f"no  | qty: {self.no_buyqty} | leftexpo:{self.no_left_exposure} | pnlifyes:{self.pnltodb.pnl_if_yes} | buyprice:{self.no_buyprice_w_spread} | fp:{self.estimated_no_fair_price} | holdqty: {self.holding_no_qty}")
            if self.no_buyqty > self.make_max_buy_order_qty:
                self.no_buyqty = self.make_max_buy_order_qty

    def make_both_sides(self):
        self.set_left_to_expose()
        self.set_buy_price_with_spread()
        self.set_qty_to_trade_asper_exposure()
        self.__send_buy_orders("make_w_spread", "Y", self.yes_buyprice_w_spread, self.yes_buyqty)
        self.__send_buy_orders("make_w_spread", "N", self.no_buyprice_w_spread, self.no_buyqty)

    def keep_a_check_2(self):
        print("entering keepacheck2")
        self.priceatri.update_priceatri()
        self.set_left_to_expose()
        self.set_buy_price_with_spread()
        self.set_qty_to_trade_asper_exposure()
        trigger = "no change but making"
        print("TRIGGER: ", trigger)
        self.__scalp_side2("Y", trigger)
        self.__scalp_side2("N", trigger)
        # yes_but_zero = (self.side_2_scalp == "Y") and (self.holding_yes_qty == 0)
        # no_but_zero = (self.side_2_scalp == "N") and (self.holding_no_qty == 0)
        # if yes_but_zero or no_but_zero:
        #     if yes_but_zero:
        #         trigger = "YesSignalZeroHolding"
        #     elif no_but_zero:
        #         trigger = "NoSignalZeroHolding"
        #     else:
        #         trigger = "unidentified"
        #     print("TRIGGER: ", trigger)
        #     self.__scalp_side2("Y", trigger)
        #     self.__scalp_side2("N", trigger)
        #
        # try:
        #     hold_y_qty_changed = (self.last_values_dict["y_h_qty"] != self.holding_yes_qty)
        #     hold_n_qty_changed = (self.last_values_dict["n_h_qty"] != self.holding_no_qty)
        #     situ_changed = (self.last_values_dict["strong_side"] != self.strong_side)
        #     scalpside_changed = (self.last_values_dict["side2scalp"] != self.side_2_scalp)
        #     yfprice_changed = (self.last_values_dict["yes_fprice"] != self.yes_fair_price)
        #     nfprice_changed = (self.last_values_dict["no_fprice"] != self.no_fair_price)
        #     yavgbuy_changed = (self.last_values_dict["yavgbuy"] != self.my_avgbuy_price_yes)
        #     navgbuy_changed = (self.last_values_dict["navgbuy"] != self.my_avgbuy_price_no)
        #     maxbuyqty_changed = (self.last_values_dict["maxbuyqty"] != self.max_buyorder_qty)
        # except KeyError:
        #     print("lastvalues dict empty so skiping further changes")
        #     logger.warning(f"{self.event_id}: last_values_dict empty")
        # else:
        #     "entering iflese after yesnozeroholding"
        #     if hold_y_qty_changed or hold_n_qty_changed:
        #         if hold_y_qty_changed:
        #             trigger = "HoldYesQtyChange"
        #         elif hold_n_qty_changed:
        #             trigger = "HoldNoQtyChange"
        #         else:
        #             trigger = "unidentified"
        #         print("TRIGGER: ", trigger)
        #         self.__scalp_side2("Y", trigger)
        #         self.__scalp_side2("N", trigger)
        #     if situ_changed or scalpside_changed or yfprice_changed or nfprice_changed or yavgbuy_changed or navgbuy_changed:
        #         if situ_changed:
        #             trigger = "SituationChange"
        #         elif scalpside_changed:
        #             trigger = "ScalpSideChange"
        #         elif yfprice_changed:
        #             trigger = "YesFairPriceChange"
        #         elif nfprice_changed:
        #             trigger = "NoFairPriceChange"
        #         elif yavgbuy_changed:
        #             trigger = "YesAvgBuyPriceChange"
        #         elif navgbuy_changed:
        #             trigger = "NoAvgBuyPriceChange"
        #         elif maxbuyqty_changed:
        #             trigger = "MaxBuyQtyChange"
        #         else:
        #             trigger = "Un-identified"
        #         print("TRIGGER: ", trigger)
        #         self.__scalp_side2("Y", trigger)
        #         self.__scalp_side2("N", trigger)
        #     else:
        #         trigger = "no change but making"
        #         print("TRIGGER: ", trigger)
        #         self.__scalp_side2("Y", trigger)
        #         self.__scalp_side2("N", trigger)

    # monitors change in scenario
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

    # absorf low hanging fruits
    def absorb_high_probable_orderbook(self):
        print("absorb exposure: ", self.absorbing_exposure, "limit: ", self.absorbing_exposure_limit)
        if (dt.datetime.now() + dt.timedelta(minutes=5) >= dt.datetime.fromisoformat(self.priceatri.ends_at)) \
                and (abs(self.spot_cmp - self.strike_price) >= self.atr_value * 1):
            absorb_side = "N" if (self.estimated_yes_fair_price == 99) else "Y" if (self.estimated_no_fair_price == 99) else None
            print(f"Absorbing '{absorb_side}' order book")
            if absorb_side == "N":
                for i in self.priceatri.no_pending_orders.index:
                    print("absorb exposure: ", self.absorbing_exposure, "limit: ", self.absorbing_exposure_limit)
                    buy_price = 100 - self.priceatri.no_pending_orders["price"].loc[i]
                    buy_qty = self.priceatri.no_pending_orders["qty"].loc[i]
                    self.absorbing_exposure = self.absorbing_exposure + (buy_price * buy_qty)
                    if self.absorbing_exposure < self.absorbing_exposure_limit:
                        self.__send_buy_orders("absorbing orderbook", "Y", buy_price, buy_qty)
                    else:
                        pass
            elif absorb_side == "Y":
                for i in self.priceatri.yes_pending_orders.index:
                    print("absorb exposure: ", self.absorbing_exposure, "limit: ", self.absorbing_exposure_limit)
                    buy_price = 100 - self.priceatri.yes_pending_orders["price"].loc[i]
                    buy_qty = self.priceatri.yes_pending_orders["qty"].loc[i]
                    self.absorbing_exposure = self.absorbing_exposure + (buy_price * buy_qty)
                    if self.absorbing_exposure < self.absorbing_exposure_limit:
                        self.__send_buy_orders("absorbing orderbook", "N", buy_price, buy_qty)
                    else:
                        pass
            else:
                pass

        elif (dt.datetime.now() + dt.timedelta(minutes=15) >= dt.datetime.fromisoformat(self.priceatri.ends_at)) \
                and (abs(self.spot_cmp - self.strike_price) >= self.atr_value * 5):
            absorb_side = "N" if (self.estimated_yes_fair_price == 99) else "Y" if (self.estimated_no_fair_price == 99) else None
            print(f"Absorbing '{absorb_side}' order book")
            if absorb_side == "N":
                for i in self.priceatri.no_pending_orders.index:
                    print("absorb exposure: ", self.absorbing_exposure, "limit: ", self.absorbing_exposure_limit)
                    buy_price = 100 - self.priceatri.no_pending_orders["price"].loc[i]
                    buy_qty = self.priceatri.no_pending_orders["qty"].loc[i]
                    self.absorbing_exposure = self.absorbing_exposure + (buy_price * buy_qty)
                    if self.absorbing_exposure < self.absorbing_exposure_limit:
                        self.__send_buy_orders("absorbing orderbook", "Y", buy_price, buy_qty)
                    else:
                        pass
            elif absorb_side == "Y":
                for i in self.priceatri.yes_pending_orders.index:
                    print("absorb exposure: ", self.absorbing_exposure, "limit: ", self.absorbing_exposure_limit)
                    buy_price = 100 - self.priceatri.yes_pending_orders["price"].loc[i]
                    buy_qty = self.priceatri.yes_pending_orders["qty"].loc[i]
                    self.absorbing_exposure = self.absorbing_exposure + (buy_price * buy_qty)
                    if self.absorbing_exposure < self.absorbing_exposure_limit:
                        self.__send_buy_orders("absorbing orderbook", "N", buy_price, buy_qty)
                    else:
                        pass
            else:
                pass
        elif abs(self.spot_cmp - self.strike_price) >= self.atr_value * 8:
            absorb_side = "N" if (self.estimated_yes_fair_price == 99) else "Y" if (self.estimated_no_fair_price == 99) else None
            print(f"Absorbing '{absorb_side}' order book")
            if absorb_side == "N":
                for i in self.priceatri.no_pending_orders.index:
                    print("absorb exposure: ", self.absorbing_exposure, "limit: ", self.absorbing_exposure_limit)
                    buy_price = 100 - self.priceatri.no_pending_orders["price"].loc[i]
                    buy_qty = self.priceatri.no_pending_orders["qty"].loc[i]
                    self.absorbing_exposure = self.absorbing_exposure + (buy_price * buy_qty)
                    if self.absorbing_exposure < self.absorbing_exposure_limit:
                        self.__send_buy_orders("absorbing orderbook", "Y", buy_price, buy_qty)
                    else:
                        pass
            elif absorb_side == "Y":
                for i in self.priceatri.yes_pending_orders.index:
                    print("absorb exposure: ", self.absorbing_exposure, "limit: ", self.absorbing_exposure_limit)
                    buy_price = 100 - self.priceatri.yes_pending_orders["price"].loc[i]
                    buy_qty = self.priceatri.yes_pending_orders["qty"].loc[i]
                    self.absorbing_exposure = self.absorbing_exposure + (buy_price * buy_qty)
                    if self.absorbing_exposure < self.absorbing_exposure_limit:
                        self.__send_buy_orders("absorbing orderbook", "N", buy_price, buy_qty)
                    else:
                        pass
            else:
                pass

    def initialise(self):
        print("version 1.5")
        print("calling pnltodbupdate")
        self.pnltodb.update()
        logger.info(f"{self.event_id}: Initialising event")

        print("calling initialise priceatri")
        self.priceatri.initialise_priceatri()

        print("calling set expiry cat")
        self.__set_expiry_category()
        print("calling set strike price")
        self.__set_strike_price()
        print("calling set atr value")
        self.__set_atr_value()
        print("calling set estimate fp")
        self.__set_estimated_fair_price()
        print("calling set fp")
        self.__set_fair_price()

        print("calling cancel pending buy/sell reset")
        self.order.cancel_all_pending_buy("Y", "Starting fresh")
        self.order.cancel_all_pending_buy("N", "Starting fresh")
        self.order.cancel_all_pending_sell("Y", "Starting fresh")
        self.order.cancel_all_pending_sell("N", "Starting fresh")

        print("calling set situation")
        self._get_situation()
        print("calling set qty")
        self._set_qty()
        self._print_details("initialising")
        print("calling set getoutsellpricediff")
        self.__set_getoutsellpricediff()
        print("calling keepacheck2")
        self.keep_a_check_2()
        print("calling updatelastvaluesdict")
        self._update_last_values()
        print("calling strat status record")
        self._strat_status_record()
        print("calling pnltodb update")
        self.pnltodb.update()
        self.initialised = True

    def update(self):
        self.pnltodb.update()
        self.priceatri.update_priceatri()

        self.__set_expiry_category()
        self.__set_strike_price()
        self.__set_atr_value()
        self.__set_estimated_fair_price()
        self.__set_fair_price()

        self._get_situation()
        self._set_qty()
        self._print_details("updating")
        self.__set_getoutsellpricediff()
        self.keep_a_check_2()
        # self.absorb_high_probable_orderbook()
        self._update_last_values()
        self._strat_status_record()
        self.pnltodb.update()

