"""
for range contracts
on bitcoin using atr and maintaining a bid ask spread
"""
from binance_data import BinanceApi
from order import Order
from price_attributes import PriceAttri
from event_params import EventParam
from mybets import get_holding_qty, get_holding_value, get_buy_price
from mybets import get_event_holdings
import pandas as pd
import datetime as dt
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
file_handler = logging.FileHandler("log_files/strat6.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Strategy:
    def __init__(self, event_id, spread=6, min_buy_qty=15, avg_qty_multiplier=1):
        self.event_id = event_id
        self.spread = spread
        self.min_buy_qty = min_buy_qty
        self.avg_qty_multiplier = avg_qty_multiplier

        self.order = Order(self.event_id)
        self.priceatri = PriceAttri(self.event_id)
        self.binance_obj = BinanceApi()

        self.holding_yes_qty = 0
        self.holding_no_qty = 0
        self.yes_fair_price = None
        self.strong_side = None
        self.side_2_scalp = None
        self.my_buy_price_yes = None
        self.my_buy_price_no = None

        self.atr_value = 0
        self.time_2_expiry_cat = None
        self.spot_cmp = None
        self.strike_price = None

        self.last_values_dict = dict()

    def __set_expiry_category(self):
        now = dt.datetime.now()
        end = dt.datetime.fromisoformat(self.priceatri.ends_at)
        delta = end - now
        if delta <= dt.timedelta(minutes=1):
            self.time_2_expiry_cat = "1min"
        elif delta <= dt.timedelta(minutes=5):
            self.time_2_expiry_cat = "5min"
        elif delta <= dt.timedelta(minutes=15):
            self.time_2_expiry_cat = "15min"
        elif delta <= dt.timedelta(hours=1):
            self.time_2_expiry_cat = "1hr"
        elif delta <= dt.timedelta(hours=2):
            self.time_2_expiry_cat = "2hr"
        else:
            self.time_2_expiry_cat = "6hr"

    def __set_strike_price(self):
        self.strike_price = int(self.priceatri.title[25:31])


    def __set_atr_value(self):
        self.atr_value = self.binance_obj.get_last_atr(symbol="BTCUSDT", interval=self.time_2_expiry_cat)


    def __set_fair_price(self):
        self.spot_cmp = int(float(self.binance_obj.get_current_price(symbol="BTCUSDT")["price"]))
        if self.strike_price >= (self.spot_cmp + self.atr_value):
            self.yes_fair_price = 1
        elif self.strike_price <= (self.spot_cmp - self.atr_value):
            self.yes_fair_price = 99
        else:
            self.yes_fair_price = -99*((1-self.strike_price+self.spot_cmp-self.atr_value)/(2*self.atr_value))



    def _print_details(self, process):
        print_dict = {"TotValue": [self.priceatri.yes_tot_value, self.priceatri.no_tot_value],
                      "ValPerPP": [self.priceatri.yes_value_per_pp, self.priceatri.no_value_per_pp],
                      "BestPrice": [self.priceatri.yes_best_price, self.priceatri.no_best_price],
                      "Spread": [100-self.priceatri.yes_best_price-self.priceatri.no_best_price, 100-self.priceatri.yes_best_price-self.priceatri.no_best_price],
                      "StrongSide": [self.strong_side, self.strong_side],
                      "Side2Scalp": [self.side_2_scalp, self.side_2_scalp],
                      "FairPrice": [self.yes_fair_price, 100 - self.yes_fair_price],
                      "MyBuyPrice": [self.my_buy_price_yes, self.my_buy_price_no],
                      "MyHoldQty": [self.holding_yes_qty, self.holding_no_qty],
                      "MaxBuyQty": [self.max_buy_qty, self.max_buy_qty],
                      "SpotPrice": [self.spot_cmp, self.spot_cmp],
                      "Strike": [self.strike_price, self.strike_price],
                      "ATR": [self.atr_value, self.atr_value],}
        print(pd.DataFrame(print_dict, index=["Yes", "No"]))
        print("-" * 10,"PENDING BOOK:")
        print(self.priceatri.yes_pending_orders.head(7))
        print(self.priceatri.no_pending_orders.head(7))
        print("-" * 10,"ORDERS:")
        print(get_event_holdings(self.event_id))
        print(dt.datetime.now(), "-" * 50)
        if process == "initialising":
            print(f"Initialising {self.priceatri.eid}: {self.priceatri.title} | started at {self.priceatri.started_at} ends at {self.priceatri.ends_at}")
        elif process == "updating":
            print(f"Updating {self.priceatri.eid}: {self.priceatri.title} | started at {self.priceatri.started_at} ends at {self.priceatri.ends_at}")

    def _update_last_values(self):
        self.last_values_dict["y_h_qty"] = self.holding_yes_qty
        self.last_values_dict["n_h_qty"] = self.holding_no_qty
        self.last_values_dict["strong_side"] = self.strong_side
        self.last_values_dict["side2scalp"] = self.side_2_scalp
        self.last_values_dict["yes_fprice"] = self.yes_fair_price

    def __scalp_side(self, asset):
        if asset == "Y":
            temp_price, temp_qty = self.__get_send_order_price_qty("Y", "buy")
            if (temp_qty > 0) and (not self.order.is_same_order("Y", temp_price, temp_qty, "buy")):
                self.order.cancel_all_pending_buy("Y", "New buy order params")
                self.__send_buy_orders("Scalping yes", "Y", temp_price, temp_qty)

            sell_price, sell_qty = self.__get_send_order_price_qty("Y", "sell")
            if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("Y", "New sell order params")
                self.__send_all_sell("Selling bought qty","Y", sell_price, sell_qty)

            self.order.cancel_all_pending_buy("N", "Cancel opp. side orders")
            if self.holding_no_qty > 0:
                sell_price, sell_qty = self.__get_send_order_price_qty("N", "sell")
                if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("N", "New sell order params")
                    self.__send_all_sell("Selling opp side bought qty","N", sell_price, sell_qty)
        elif asset == "N":
            temp_price, temp_qty = self.__get_send_order_price_qty("N", "buy")
            if (temp_qty > 0) and (not self.order.is_same_order("N", temp_price, temp_qty, "buy")):
                self.order.cancel_all_pending_buy("N", "New buy order params")
                self.__send_buy_orders("Scalping no","N", temp_price, temp_qty)

            sell_price, sell_qty = self.__get_send_order_price_qty("N", "sell")
            if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("N", "New sell order params")
                self.__send_all_sell("Selling bought qty", "N", sell_price, sell_qty)

            self.order.cancel_all_pending_buy("Y", "Cancel opp. side orders")
            if self.holding_yes_qty > 0:
                sell_price, sell_qty = self.__get_send_order_price_qty("Y", "sell")
                if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("Y", "New sell order params")
                    self.__send_all_sell("Selling opp side bought qty","Y", sell_price, sell_qty)

    def __hold_qty_change_process(self):
        if (self.side_2_scalp == "Y") and (self.holding_yes_qty > 0):
            sell_price, sell_qty = self.__get_send_order_price_qty("Y", "sell")
            if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("Y", "holding qty changed")
                self.__send_all_sell("Selling w/ new qty","Y", sell_price, sell_qty)
            # if self.holding_no_qty > 0:
            #     sell_price, sell_qty = self.__get_send_order_price_qty("N", "sell")
            #     if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
            #         self.order.cancel_all_pending_sell("N", "holding qty changed")
            #         self.__send_all_sell("N", sell_price, sell_qty)
        elif (self.side_2_scalp == "N") and (self.holding_no_qty > 0):
            sell_price, sell_qty = self.__get_send_order_price_qty("N", "sell")
            if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("N", "holding qty changed")
                self.__send_all_sell("Selling w/ new qty","N", sell_price, sell_qty)
            # if self.holding_yes_qty > 0:
            #     sell_price, sell_qty = self.__get_send_order_price_qty("Y", "sell")
            #     if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
            #         self.order.cancel_all_pending_sell("Y")
            #         self.__send_all_sell("Y", sell_price, sell_qty)

    def _get_situation(self):
        if self.yes_fair_price >= 50:
            self.strong_side = "Y"
        else:
            self.strong_side = "N"
        if (self.priceatri.yes_best_price is not None) and (self.priceatri.no_best_price is not None):
            if (self.priceatri.yes_best_price > self.yes_fair_price) or (self.priceatri.no_best_price < (100 - self.yes_fair_price)):
                self.side_2_scalp = "N"
            else:
                self.side_2_scalp = "Y"

    def _set_qty(self):
        self.holding_yes_qty, self.holding_no_qty = get_holding_qty(self.event_id)
        yes_bought_value, no_bought_value = get_holding_value(self.event_id)
        self.my_buy_price_yes, self.my_buy_price_no = get_buy_price(self.event_id)

        self.max_buy_qty = int(self.priceatri.avg_traded_qty) * self.avg_qty_multiplier
        if (self.max_buy_qty is None) or (self.max_buy_qty < self.min_buy_qty):
            self.max_buy_qty = self.min_buy_qty
        elif self.max_buy_qty >= 100:
            self.max_buy_qty = 99

    def __get_send_order_price_qty(self, asset, side):
        if asset == "Y":
            if side == "buy":
                qty_temp = self.max_buy_qty - self.holding_yes_qty
                price_temp = int(self.yes_fair_price - self.spread)
                return price_temp, qty_temp
            elif side == "sell":
                sell_qty = self.holding_yes_qty
                sell_price = int(self.yes_fair_price)
                return sell_price, sell_qty
        elif asset == "N":
            if side == "buy":
                qty_temp = self.max_buy_qty - self.holding_no_qty
                price_temp = int(100 - self.yes_fair_price - self.spread)
                return price_temp, qty_temp
            elif side == "sell":
                sell_qty = sell_qty = self.holding_no_qty
                sell_price = int(100 - self.yes_fair_price)
                return sell_price, sell_qty

    def __send_buy_orders(self, message, asset, price, qty):
        if asset == "Y":
            self.order._buy(message,"Y", price, qty)
        elif asset == "N":
            self.order._buy(message,"N", price, qty)

    def __send_all_sell(self, message, asset, sell_price, sell_qty):
        if (asset == "Y") and (self.holding_yes_qty > 0) and (sell_qty > 0) and (sell_price <= 99):
            self.order._sell(message, "Y", sell_price, sell_qty)
        elif (asset == "N") and (self.holding_no_qty > 0) and (sell_qty > 0) and (sell_price <= 99):
            self.order._sell(message, "N", sell_price, sell_qty)

    def __take_all_for_spread(self):
        if (self.side_2_scalp == "Y"):
            mask1 = self.priceatri.no_pending_orders["price"] > (100 - self.yes_fair_price)
            mask2 = self.priceatri.no_pending_orders["price"] < (100 - self.yes_fair_price) + self.spread
            orders_2_take_yes = self.priceatri.no_pending_orders[mask1 & mask2]
            if not orders_2_take_yes.empty:
                for i in range(orders_2_take_yes.shape[0]):
                    print("--Yes take order--")
                    self.__send_buy_orders("Absorbing spread", "Y", 100 - orders_2_take_yes["price"].iloc[i], orders_2_take_yes["qty"].iloc[i])
        elif (self.side_2_scalp == "N"):
            mask1 = self.priceatri.yes_pending_orders["price"] < (self.yes_fair_price + self.spread)
            mask2 = self.priceatri.yes_pending_orders["price"] > self.yes_fair_price
            orders_2_take_no = self.priceatri.yes_pending_orders[mask1 & mask2]
            if not orders_2_take_no.empty:
                for i in range(orders_2_take_no.shape[0]):
                    print("--No take order--")
                    self.__send_buy_orders("Absorbing spread", "N", 100 - orders_2_take_no["price"].iloc[i], orders_2_take_no["qty"].iloc[i])


    def _keep_a_check(self):
        yes_but_zero = (self.side_2_scalp == "Y") and (self.holding_yes_qty == 0)
        no_but_zero = (self.side_2_scalp == "N") and (self.holding_no_qty == 0)
        if yes_but_zero or no_but_zero:
            print("Scalp Condition: Strong side but qty zero")
            if self.side_2_scalp == "Y":
                self.__take_all_for_spread()
                self.__scalp_side("Y")
            elif self.side_2_scalp == "N":
                self.__take_all_for_spread()
                self.__scalp_side("N")

        try:
            hold_y_qty_changed = (self.last_values_dict["y_h_qty"] != self.holding_yes_qty)
            hold_n_qty_changed = (self.last_values_dict["n_h_qty"] != self.holding_no_qty)
            situ_changed = (self.last_values_dict["strong_side"] != self.strong_side)
            scalpside_changed = (self.last_values_dict["side2scalp"] != self.side_2_scalp)
            fprice_changed = (self.last_values_dict["yes_fprice"] != self.yes_fair_price)
        except KeyError:
            logger.warning(f"{self.event_id}: last_values_dict empty")
        else:
            if hold_y_qty_changed or hold_n_qty_changed:
                print("Scalp Condition: Holding qty changed")
                self.__hold_qty_change_process()
            if situ_changed or scalpside_changed or fprice_changed:
                print("Scalp Condition: Strong side changed")
                if self.side_2_scalp == "Y":
                    self.__take_all_for_spread()
                    self.__scalp_side("Y")
                elif self.side_2_scalp == "N":
                    self.__take_all_for_spread()
                    self.__scalp_side("N")

    def initialise(self):
        logger.info(f"{self.event_id}: Initialising event")
        self.priceatri.initialise_priceatri()

        self.__set_expiry_category()
        self.__set_strike_price()
        self.__set_atr_value()
        self.__set_fair_price()

        self._get_situation()
        self._set_qty()
        self._print_details("initialising")
        self._keep_a_check()
        self._update_last_values()

    def update(self):
        self.priceatri.update_priceatri()

        self.__set_expiry_category()
        self.__set_strike_price()
        self.__set_atr_value()
        self.__set_fair_price()

        self._get_situation()
        self._set_qty()
        self._print_details("updating")
        self._keep_a_check()
        self._update_last_values()