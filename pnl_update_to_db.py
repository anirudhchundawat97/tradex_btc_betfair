from transactions_c3 import Transactions
from mybets_c3 import MyBets
from topsql_c3 import ToPostgres
import datetime as dt
from time import sleep

class PnlToDb:
    def __init__(self, event_id):
        self.pnl_worst_2 = None
        print("UPDATED 1.4")
        self.event_id = event_id
        self.mybets = MyBets(event_id, "p", 603727)
        self.transactions = Transactions(event_id, "p", 603727)
        self.topsql = ToPostgres()
        self.pnl_best = None
        self.pnl_worst = None
        self.worstcase_pnl_limit = -1000
        self.worstcase_limit_reached = False
        self.topsql.initialise_live_ref(603727, "p", event_id, dt.datetime.now().isoformat(), self.pnl_worst,
                                        self.pnl_best, self.worstcase_pnl_limit, self.worstcase_limit_reached)
        print(f"PSQL {self.event_id} initialised")

    def _set_holdingqty(self):
        self.holdingqty_yes = self.mybets.holding_yes_qty
        self.holdingqty_no = self.mybets.holding_no_qty

    def _set_realised_pnl(self):
        self.realised_pnl_yes = self.transactions.yes_net_sold_value + self.mybets.unmatched_buy_yes_value
        self.realised_pnl_no = self.transactions.no_net_sold_value + self.mybets.unmatched_buy_no_value

    def _set_hold_possible_pnl(self):
        if not self.mybets.event_holdings_df.empty:
            mask_yes = (self.mybets.event_holdings_df["asset"] == "Y")
            mask_no = (self.mybets.event_holdings_df["asset"] == "N")
            mask_executed = (self.mybets.event_holdings_df["status"] == "executed")
            yes_df = self.mybets.event_holdings_df[mask_yes & mask_executed]
            no_df = self.mybets.event_holdings_df[mask_no & mask_executed]
            # self.yes_hold_if_yes = (yes_df["if_win_price"] * yes_df["qty"]).sum()
            self.yes_hold_if_yes = 100 * yes_df["qty"].sum()
            self.yes_hold_if_no = 0
            # self.no_hold_if_no = (no_df["if_win_price"] * no_df["qty"]).sum()
            self.no_hold_if_no = 100 * no_df["qty"].sum()
            self.no_hold_if_yes = 0
        else:
            self.yes_hold_if_yes = 0
            self.yes_hold_if_no = 0
            self.no_hold_if_no = 0
            self.no_hold_if_yes = 0

    def set_pnl_values(self):
        self.pnl_both_realised = self.realised_pnl_yes + self.realised_pnl_no
        self.pnl_if_yes = self.pnl_both_realised + self.yes_hold_if_yes + self.no_hold_if_yes

        self.pnl_if_no = self.pnl_both_realised + self.yes_hold_if_no + self.no_hold_if_no
        self.pnl_best = max(self.pnl_if_yes, self.pnl_if_no)
        self.pnl_worst_2 = min(self.pnl_if_yes, self.pnl_if_no)
        self.pnl_worst = self.transactions.event_txn_df["amount"].sum()
        print("-" * 10, "pnl_both_realised: ", self.pnl_both_realised)
        print("-" * 10, "realised_pnl_yes: ", self.realised_pnl_yes)
        print("-" * 10, "realised_pnl_no: ", self.realised_pnl_no)
        print("-" * 10, "yes_hold_if_yes: ", self.yes_hold_if_yes)
        print("-" * 10, "no_hold_if_yes: ", self.no_hold_if_yes)
        print("-" * 10, "yes_hold_if_no: ", self.yes_hold_if_no)
        print("-" * 10, "no_hold_if_no: ", self.no_hold_if_no)

        print("-"*10, "pnlifyes: ", self.pnl_if_yes)
        print("-"*10, "pnlifno: ", self.pnl_if_no)
        sleep(5)
        print("-"*10, "pnlbest: ", self.pnl_best)
        print("-"*10, "pnlworst: ", self.pnl_worst)
        print("-"*10, "pnlworst2: ", self.pnl_worst_2)
        if self.pnl_worst_2 <= self.worstcase_pnl_limit:
            self.worstcase_limit_reached = True
        else:
            self.worstcase_limit_reached = False

    def update(self):
        self.mybets.update()
        self._set_holdingqty()
        self._set_hold_possible_pnl()
        self.transactions.update()
        self._set_realised_pnl()
        self.set_pnl_values()
        self.topsql.update_live_ref(603727, self.event_id, dt.datetime.now().isoformat(), self.pnl_worst_2, self.pnl_best,
                                    self.worstcase_limit_reached)
        print(f"PSQL {self.event_id} updated")


if __name__ == "__main__":
    from time import sleep

    eid = 99999
    ptd = PnlToDb(eid)
    while True:
        ptd.update()
        print(ptd.holdingqty_yes)
        print(ptd.realised_pnl_yes)
        print()
