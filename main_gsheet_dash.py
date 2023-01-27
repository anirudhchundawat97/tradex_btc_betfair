import warnings

warnings.filterwarnings("ignore")
import datetime as dt
from time import sleep

from realised_scalping_pnl import ScalpingPnl
from unrealised_holding_pnl import HoldingPnl
from update_gsheet2 import Gsheet

eid = int(input("Enter Event id: "))
while True:
    try:
        t1 = dt.datetime.now()
        spnl = ScalpingPnl(eid)
        spnl.get_transactions()
        realised_daywise_pnl = spnl.calculate_daywise_pnl()

        hpnl = HoldingPnl(eid)
        hpnl.total_pnl_at_resolution()

        gs = Gsheet(eid)
        i = 3
        for d in realised_daywise_pnl.index.get_level_values('date').to_list():
            cell = f'A{i}'
            # print(cell, str(d))
            gs.event_sheet.update(cell, str(d))

            cell = f'B{i}'
            try:
                yes_pnl_date = realised_daywise_pnl[d]["YES"]
            except KeyError:
                try:
                    yes_pnl_date = realised_daywise_pnl[d]["Y"]
                except KeyError:
                    yes_pnl_date = 0
            # print(cell, yes_pnl_date)
            gs.event_sheet.update(cell, float(yes_pnl_date))

            cell = f'C{i}'
            try:
                no_pnl_date = realised_daywise_pnl[d]["NO"]
            except KeyError:
                try:
                    no_pnl_date = realised_daywise_pnl[d]["N"]
                except KeyError:
                    no_pnl_date = 0
            # print(cell, no_pnl_date)
            gs.event_sheet.update(cell, float(no_pnl_date))

            cell = f'D{i}'
            total_pnl_date = yes_pnl_date + no_pnl_date
            # print(cell, total_pnl_date)
            gs.event_sheet.update(cell, float(total_pnl_date))

            i += 1

        # print(spnl.yes_total_pnl, type(spnl.yes_total_pnl))
        gs.event_sheet.update('E3', spnl.yes_total_pnl)
        gs.event_sheet.update('F3', spnl.no_total_pnl)
        gs.event_sheet.update('G3', spnl.yes_total_pnl + spnl.no_total_pnl)

        # print(hpnl.pnl_if_yes, type(hpnl.pnl_if_yes))
        gs.event_sheet.update('H3', float(hpnl.pnl_if_yes))
        gs.event_sheet.update('I3', float(hpnl.pnl_if_no))

        gs.event_sheet.update('J3', float(hpnl.pnl_if_yes + spnl.yes_total_pnl + spnl.no_total_pnl))
        gs.event_sheet.update('K3', float(hpnl.pnl_if_no + spnl.yes_total_pnl + spnl.no_total_pnl))
        gs.event_sheet.update('L1', "updated at: " + str(dt.datetime.now()))
        print("Yes Total PnL:", hpnl.pnl_if_yes + spnl.yes_total_pnl + spnl.no_total_pnl)
        print("No Total PnL:", hpnl.pnl_if_no + spnl.yes_total_pnl + spnl.no_total_pnl)
        t2 = dt.datetime.now()
        print(t2)
        print(t2 - t1)
    except Exception as e:
        print(f"Event{eid}", e)
        print("Last failed run at: ", dt.datetime.now())
        print("Next run at: ", dt.datetime.now() + dt.timedelta(seconds=60))
        sleep(60)
    else:
        print("Updated.",eid)
        print("Last successful run at: ", dt.datetime.now())
        print("Next run at: ", dt.datetime.now() + dt.timedelta(seconds=180))
        sleep(180)
