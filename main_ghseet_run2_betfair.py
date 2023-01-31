import warnings
import numpy as np
import datetime as dt
from time import sleep
from realised_scalping_pnl import ScalpingPnl
from unrealised_holding_pnl import HoldingPnl
from update_gsheet2 import Gsheet

warnings.filterwarnings("ignore")

eid_list1_sheet1 = []
eid_list_now = [17901, 17696, 18012]

gs = Gsheet(category="betfair")
while True:
    try:
        t1 = dt.datetime.now()
        i = 2
        apitype = "p"
        userid = 0
        for eid in eid_list_now:
            print("running for ", eid)
            hpnl = HoldingPnl(eid, apitype, userid)
            hpnl.total_pnl_at_resolution()
            # print(eid, hpnl.pnl_if_yes, hpnl.pnl_if_no, hpnl.pnl_if_yes + hpnl.pnl_if_no)

            spnl = ScalpingPnl(eid, apitype='p', userid=603727)
            spnl.get_transactions()
            spnl.get_true_qty_traded()
            grouped = spnl.calculate_daywise_pnl()

            ifyes_tot = np.round(spnl.yes_total_pnl + spnl.no_total_pnl + hpnl.pnl_if_yes, 2)
            ifno_tot = np.round(spnl.yes_total_pnl + spnl.no_total_pnl + hpnl.pnl_if_no, 2)

            netpnl = spnl.netpnl + hpnl.unexecuted_value

            status1 = "Closed" if ("Closed" in spnl.orders_df["status"].values) else ""
            status2 = "Settled" if ("Settled" in spnl.orders_df["status"].values) else ""

            eid_data = [[eid, str(spnl.first_date), netpnl, status1, status2, ifyes_tot, ifno_tot, hpnl.pnl_if_yes,
                         hpnl.pnl_if_no,
                         spnl.yes_total_pnl,
                         spnl.no_total_pnl, spnl.totalqty, spnl.yesqty, spnl.noqty]]

            status1 = "Closed" if (status1 == "Closed") else "NotClosed"
            status2 = "Settled" if (status2 == "Settled") else "NotSettled"
            print(eid, "|", spnl.first_date, "|", netpnl, "|", status1, "|", status2, "|", spnl.yes_total_pnl, "|",
                  spnl.no_total_pnl)
            gs.event_sheet.update(f'A{i}:N{i}', eid_data)
            gs.event_sheet.update('P1', "updated at: " + str(dt.datetime.now()))
            i += 1
        t2 = dt.datetime.now()
        print("-" * 20, t2)
        print(t2 - t1)
    except Exception as e:
        print(f"Event{eid}", e)
        print("Last failed run at: ", dt.datetime.now())
        print("Next run at: ", dt.datetime.now() + dt.timedelta(seconds=60))
        sleep(60)
        raise e
    else:
        print("Updated.", eid)
        print("Last successful run at: ", dt.datetime.now())
        # print("Next run at: ", dt.datetime.now() + dt.timedelta(seconds=300))
        # sleep(300)
