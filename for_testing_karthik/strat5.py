"""
based on bayes theorem to update up and down probability
"""
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
file_handler = logging.FileHandler("log_files/strategy4_0.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Strategy:
    def __init__(self, event_id, opp_direction_move_margin=2, avg_qty_multiplier=4, min_buy_qty=15):
        self.no_sellatloss = False
        self.yes_sellatloss = False
        self.opp_direction_move_margin = opp_direction_move_margin
        self.avg_qty_multiplier = avg_qty_multiplier
        self.min_buy_qty = min_buy_qty
        self.event_id = event_id

        self.order = Order(self.event_id)
        self.eventparams = EventParam(self.event_id)
        self.priceatri = PriceAttri(self.event_id)

        self.yes_tohold_qty = 0
        self.no_tohold_qty = 0
        self.max_buy_qty = None
        self.holding_yes_qty = 0
        self.holding_no_qty = 0
        self.signal1_a = None
        self.signal1_b = None
        self.signal2 = None
        self.strong_side = None
        self.signal_strength = None
        self.my_buy_price_yes = None
        self.my_buy_price_no = None

        self.last_values_dict = dict()

    def __get_up_down_prob(self, trade_price, fe, informed=0.3):
        p_fa_gt_fe = (99 - fe) / 99
        p_inf_buy = ((informed * 1) + ((1 - informed) * 0.5))
        p_uni_buy = ((informed * 0) + ((1 - informed) * 0.5))
        p_h_given_e = p_fa_gt_fe * ((p_inf_buy + p_uni_buy) / 2)
        p_fa_lt_fe = fe / 99
        p_inf_buy = ((informed * 0) + ((1 - informed) * 0.5))
        p_uni_buy = ((informed * 1) + ((1 - informed) * 0.5))
        p_not_h_given_e = p_fa_lt_fe * ((p_inf_buy + p_uni_buy) / 2)

        fa_up_prob = p_h_given_e / (p_h_given_e + p_not_h_given_e)
        fa_down_prob = p_not_h_given_e / (p_h_given_e + p_not_h_given_e)
        return fa_up_prob, fa_down_prob

    def _print_details(self, process):
        print_dict = {"TotValue": [self.priceatri.yes_tot_value, self.priceatri.no_tot_value],
                      "ValPerPP": [self.priceatri.yes_value_per_pp, self.priceatri.no_value_per_pp],
                      "BestPrice": [self.priceatri.yes_best_price, self.priceatri.no_best_price],
                      "StrongSide": [self.strong_side, self.strong_side],
                      "SignalStrength": [self.signal_strength, self.signal_strength],
                      "ExecPriceAvg": [self.priceatri.yes_executed_avgpri, self.priceatri.no_executed_avgpri],
                      "ExecPriceWAP": [self.priceatri.yes_executed_wap, self.priceatri.no_executed_wap],
                      "MyBuyPrice": [self.my_buy_price_yes, self.my_buy_price_no],
                      "ToHoldQty": [self.yes_tohold_qty, self.no_tohold_qty],
                      "MyHoldQty": [self.holding_yes_qty, self.holding_no_qty],
                      "MaxBuyQty": [self.max_buy_qty, self.max_buy_qty],
                      "SellatLoss": [self.yes_sellatloss, self.no_sellatloss]}
        print(pd.DataFrame(print_dict, index=["Yes", "No"]))
        print("ORDERS:")
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
        self.last_values_dict["signal_strength"] = self.signal_strength

    def __scalp_side(self, asset):
        if asset == "Y":
            temp_price, temp_qty = self.__get_send_order_price_qty("Y", "buy")
            if (temp_qty > 0) and (not self.order.is_same_order("Y", temp_price, temp_qty, "buy")):
                self.order.cancel_all_pending_buy("Y")
                self.__send_buy_orders("Y", temp_price, temp_qty)

            sell_price, sell_qty = self.__get_send_order_price_qty("Y", "sell")
            if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("Y")
                self.__send_all_sell("Y", sell_price, sell_qty)

            self.order.cancel_all_pending_buy("N")
            if (self.holding_no_qty >0) and self.no_sellatloss:
                sell_price, sell_qty = self.__get_send_order_price_qty("N", "sell")
                if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("N")
                    self.__send_all_sell("N", sell_price, sell_qty)
        elif asset == "N":
            temp_price, temp_qty = self.__get_send_order_price_qty("N", "buy")
            if (temp_qty > 0) and (not self.order.is_same_order("N", temp_price, temp_qty, "buy")):
                self.order.cancel_all_pending_buy("N")
                self.__send_buy_orders("N", temp_price, temp_qty)

            sell_price, sell_qty = self.__get_send_order_price_qty("N", "sell")
            if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("N")
                self.__send_all_sell("N", sell_price, sell_qty)

            self.order.cancel_all_pending_buy("Y")
            if (self.holding_yes_qty > 0) and self.yes_sellatloss:
                sell_price, sell_qty = self.__get_send_order_price_qty("Y", "sell")
                if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("Y")
                    self.__send_all_sell("Y", sell_price, sell_qty)

    def __hold_qty_change_process(self):
        if (self.strong_side == "Yes") and (self.holding_yes_qty > 0):
            sell_price, sell_qty = self.__get_send_order_price_qty("Y", "sell")
            if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("Y")
                self.__send_all_sell("Y", sell_price, sell_qty)
            if (self.holding_no_qty > 0) and self.no_sellatloss:
                sell_price, sell_qty = self.__get_send_order_price_qty("N", "sell")
                if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("N")
                    self.__send_all_sell("N", sell_price, sell_qty)
        elif (self.strong_side == "No") and (self.holding_no_qty > 0):
            sell_price, sell_qty = self.__get_send_order_price_qty("N", "sell")
            if not self.order.is_same_order("N", sell_price, sell_qty, "sell"):
                self.order.cancel_all_pending_sell("N")
                self.__send_all_sell("N", sell_price, sell_qty)
            if (self.holding_yes_qty > 0) and self.yes_sellatloss:
                sell_price, sell_qty = self.__get_send_order_price_qty("Y", "sell")
                if not self.order.is_same_order("Y", sell_price, sell_qty, "sell"):
                    self.order.cancel_all_pending_sell("Y")
                    self.__send_all_sell("Y", sell_price, sell_qty)

    def _get_situation(self):
        if self.priceatri.yes_best_price > self.priceatri.no_best_price:
            self.strong_side = "Yes"
        else:
            self.strong_side = "No"

    def _set_qty(self):
        self.holding_yes_qty, self.holding_no_qty = get_holding_qty(self.event_id)
        yes_bought_value, no_bought_value = get_holding_value(self.event_id)
        self.my_buy_price_yes, self.my_buy_price_no = get_buy_price(self.event_id)

        if (self.strong_side == "Yes") \
                and (self.my_buy_price_no > self.priceatri.no_best_price + self.opp_direction_move_margin):
            self.yes_tohold_qty = int(no_bought_value / (100 - self.priceatri.yes_best_price))
            self.no_sellatloss = True
            self.yes_sellatloss = False
        elif (self.strong_side == "No") \
                and (self.my_buy_price_yes > self.priceatri.yes_best_price + self.opp_direction_move_margin):
            self.no_tohold_qty = int(yes_bought_value / (100 - self.priceatri.no_best_price))
            self.no_sellatloss = False
            self.yes_sellatloss = True
        else:
            self.no_sellatloss = False
            self.yes_sellatloss = False

        self.max_buy_qty = int(self.priceatri.avg_traded_qty) * self.avg_qty_multiplier
        if (self.max_buy_qty is None) or (self.max_buy_qty < self.min_buy_qty):
            self.max_buy_qty = self.min_buy_qty
        elif self.max_buy_qty >= 100:
            self.max_buy_qty = 99

    def __get_make_price_or_best(self, asset):
        if asset == "Y":
            if (self.priceatri.yes_best_price + 1) < (100 - self.priceatri.no_best_price):
                return self.priceatri.yes_best_price
            else:
                return self.priceatri.yes_best_price + 1
        elif asset == "N":
            if (self.priceatri.no_best_price + 1) < (100 - self.priceatri.yes_best_price):
                return self.priceatri.no_best_price
            else:
                return self.priceatri.no_best_price + 1

    def __get_send_order_price_qty(self, asset, side):
        if asset == "Y":
            if side == "buy":
                qty_temp = self.max_buy_qty - self.holding_yes_qty# + self.yes_tohold_qty
                price_temp = self.__get_make_price_or_best("Y")
                return price_temp, qty_temp
            elif side == "sell":
                sell_qty = self.holding_yes_qty# - self.yes_tohold_qty
                sell_price = self.priceatri.yes_best_price + 2
                return sell_price, sell_qty
        elif asset == "N":
            if side == "buy":
                qty_temp = self.max_buy_qty - self.holding_no_qty# + self.no_tohold_qty
                price_temp = self.__get_make_price_or_best("N")
                return price_temp, qty_temp
            elif side == "sell":
                sell_qty = sell_qty = self.holding_no_qty# - self.no_tohold_qty
                sell_price = self.priceatri.no_best_price + 2
                return sell_price, sell_qty

    def __send_buy_orders(self, asset, price, qty):
        if asset == "Y":
            self.order._buy("Y", price, qty)
        elif asset == "N":
            self.order._buy("N", price, qty)

    def __send_all_sell(self, asset, sell_price, sell_qty):
        if (asset == "Y") and (self.holding_yes_qty > 0) and (sell_qty > 0) and (sell_price <= 99):
            self.order._sell("Y", sell_price, sell_qty)
        elif (asset == "N") and (self.holding_no_qty > 0) and (sell_qty > 0) and (sell_price <= 99):
            self.order._sell("N", sell_price, sell_qty)

    def __holding_morethan_tohold(self):
        pass

    def _keep_a_check(self):
        yes_but_zero = (self.strong_side == "Yes") and (self.holding_yes_qty == 0)
        no_but_zero = (self.strong_side == "No") and (self.holding_no_qty == 0)
        if yes_but_zero or no_but_zero:
            print("Scalp Condition: Strong side but qty zero")
            if self.strong_side == "Yes":
                self.__scalp_side("Y")
            elif self.strong_side == "No":
                self.__scalp_side("N")

        try:
            hold_y_qty_changed = (self.last_values_dict["y_h_qty"] != self.holding_yes_qty)
            hold_n_qty_changed = (self.last_values_dict["n_h_qty"] != self.holding_no_qty)
            situ_changed = (self.last_values_dict["strong_side"] != self.strong_side)
        except KeyError:
            logger.warning(f"{self.event_id}: last_values_dict empty")
        else:
            if hold_y_qty_changed or hold_n_qty_changed:
                print("Scalp Condition: Holding qty changed")
                self.__hold_qty_change_process()
            # if self.__holding_morethan_tohold():
            #     print("Scalp Condition: Holding > To Hold")
            #     print("no sell orders sent")
            if situ_changed:
                print("Scalp Condition: Strong side changed")
                if self.strong_side == "Y":
                    self.__scalp_side("Y")
                elif self.strong_side == "N":
                    self.__scalp_side("N")

    def initialise(self):
        logger.info(f"{self.event_id}: Initialising event")
        self.priceatri.initialise_priceatri()
        self._get_situation()
        self._set_qty()
        self._print_details("initialising")
        self._keep_a_check()
        self._update_last_values()

    def update(self):
        self.priceatri.update_priceatri()
        self._get_situation()
        self._set_qty()
        self._print_details("updating")
        self._keep_a_check()
        self._update_last_values()
