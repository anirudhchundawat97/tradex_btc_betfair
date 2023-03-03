from transactions_c3 import Transactions
import numpy as np
from topsql_c3 import ToPostgres
import datetime as dt
import warnings
warnings.filterwarnings("ignore")

start = 23802
end = 23804

start_eid = start or int(input("update pnl from eid: "))
end_eid = end or int(input("update pnl upto eid: "))
eid_list = range(start_eid, end_eid)

eid_list = [24149,24136,24144,24148,24132,24147,24150,24146,24145,24143,24142,24139,24135,24134,24133,24124,24128,24119,24130,24131,24129,24127,24115,24126,24125,24123,24122,24111,24121,24118,24107,24117,24116,24114,24098,24113,24112,24110,24109,24094,24108,24106,24090,24105,24102,24097,24086,24096,24095,24093,24092,24080,24091,24089,24088,24076,24087,24085,24072,24084,24083,24079,24078,24068,24077,24075,24061,24074,24073,24071,24070,24057,24069,24067,24053,24066,24063,24060,24048,24059,24058,24056,24055,24040,24054,24052,24051,24036,24049,24047,24032,24046,24043,24039,24038,24028,24037,24035,24020,24034,24033,24031,24030,24016,24029,24027,24012,24026,24023,24019,24007,24018,24017,24015,24001,24014,24013,24011,23994,24009,24008,24006,23988,24005,24004,24000,23999,23984,23996,23993,23979,23991,23989,23987,23975,23986,23985,23983,23982,23981,23978,23977,23976,23974,23973,23972]

tpg = ToPostgres()

while True:
    for i in eid_list:
        txn = Transactions(i, "p", 603727)
        txn.update()

        if (txn.event_txn_df is None) or txn.event_txn_df.empty:
            pnl = np.nan
            qty = np.nan
            pnl_worst = np.nan
        else:
            pnl = txn.event_txn_df["amount"].iloc[:].sum()
            qty = txn.event_txn_df["qty"].iloc[:].sum()

        if "Settled" in txn.event_txn_df["status"].values:
            settle = True
        elif (np.isnan(pnl)) and (np.isnan(qty)):
            settle = False
        else:
            settle = False
        print(i, f"{pnl:>8}", f"{settle:<11}", f"{qty:>6}")
        tpg.update_live_pnl(qty, settle, pnl, i)
        print(dt.datetime.now())

