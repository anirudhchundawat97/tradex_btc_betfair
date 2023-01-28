import warnings
import numpy as np
import datetime as dt
from time import sleep
from realised_scalping_pnl import ScalpingPnl
from unrealised_holding_pnl import HoldingPnl
from update_gsheet2 import Gsheet

warnings.filterwarnings("ignore")

eid_list1_sheet1 = [11427, 11426, 11425, 11424, 11423, 11422, 11421, 11420, 11419, 11418,
                    11528, 11527, 11526, 11525, 11524, 11489, 11488, 11487, 11486, 11485, 11484, 11483,
                    11561, 11560, 11559, 11558, 11557, 11556, 11555, 11554, 11553, 11552, 11551, 11550,
                    11680, 11679, 11678, 11677,
                    11726, 11727, 11728, 11729,
                    11771, 11772, 11773, 11774]
# list2 from other account
eid_list2_sheet1 = [11826, 11825, 11824, 11823,
                    11858, 11857, 11856, 11855,
                    11929, 11928, 11927, 11926,
                    11982, 11983, 11984, 11985,
                    12025, 12026, 12027, 12028,
                    12055, 12056, 12057, 12058,
                    12098, 12099, 12100, 12101,
                    12146, 12147, 12148, 12149,
                    12177, 12178, 12179, 12180,
                    12230, 12231, 12232, 12233,
                    12294, 12293, 12292, 12288,
                    12358, 12359, 12360, 12361,
                    12397, 12399, 12400, 12401]
# moved to sheet 2 because 100 rows full
eid_list1_sheet2 = [12461, 12462, 12463, 12464,
                    12525, 12526, 12527, 12528,
                    12579, 12580, 12581,
                    12646, 12647, 12648, 12649,
                    12725, 12732, 12733, 12737,
                    12796, 12797, 12798, 12799,
                    12854, 12855, 12856, 12857,
                    12916, 12917, 12918, 12919,
                    12963, 12964, 12965, 12969,
                    13043, 13044, 13045, 13046,
                    13090, 13091, 13092, 13093,
                    13161, 13162, 13163, 13164,
                    13231, 13232, 13233, 13234,
                    13290, 13291, 13292, 13296,
                    13434, 13435, 13436, 13437,
                    13477, 13478, 13479, 13480,
                    13558, 13559, 13560, 13561,
                    13635, 13636, 13640, 13641, 13642, 13643, 13644, 13645,
                    13715, 13716, 13717, 13718, 13719, 13720, 13721, 13722,
                    13762, 13763, 13764, 13765, 13766, 13767, 13768, 13769,
                    13839, 13840, 13841, 13842, 13843, 13844, 13845, 13846]
eid_list1_sheet3 = [13909, 13910, 13911, 13912, 13913, 13914, 13915, 13916,
                    13977, 13978, 13979, 13983, 13984, 13985, 13986, 13987,
                    14042, 14043, 14044, 14045, 14046, 14047, 14048, 14049,
                    14093, 14094, 14095, 14096, 14097, 14098, 14099, 14100,
                    14163, 14164, 14165, 14166, 14167, 14168, 14169, 14170,
                    14233, 14234, 14235, 14236, 14237, 14238, 14239, 14240,
                    14285, 14286, 14287, 14288, 14289, 14290, 14292, 14293,
                    14359, 14360, 14361, 14362, 14363, 14364, 14365, 14366,
                    14437, 14438, 14439, 14440, 14441, 14442, 14443, 14444,
                    14521, 14522, 14523, 14524, 14525, 14526, 14527, 14528,
                    14631, 14632, 14633, 14634, 14635, 14636, 14637, 14638,
                    14688, 14689, 14690, 14691, 14692, 14693, 14694, 14695,
                    14746, 14747, 14748, 14749, 14750, 14751, 14752, 14753,
                    14804, 14805, 14806, 14807, 14808, 14809, 14810, 14811,
                    14886, 14887, 14888, 14889, 14890, 14891, 14892, 14893,
                    14972, 14973, 14974, 14975, 14976, 14977, 14978, 14979,
                    15055, 15056, 15057, 15058, 15059, 15060, 15061, 15062,
                    15143, 15144, 15145, 15146, 15147, 15148, 15149, 15150]
eid_list1_sheet4 = [15218, 15219, 15220, 15221, 15222, 15223, 15224, 15225,
                    15289, 15290, 15291, 15292, 15293, 15294, 15295, 15296,
                    15361, 15362, 15363, 15364, 15365, 15366, 15367, 15368,
                    15449, 15450, 15451, 15452, 15453, 15454, 15455, 15456,
                    15542, 15543, 15544, 15545, 15546, 15547, 15549, 15550,
                    15654, 15655, 15656, 15657, 15658, 15659, 15660, 15661,
                    15754, 15755, 15756, 15757, 15758, 15759, 15760, 15761,
                    15846, 15847, 15848, 15849, 15850, 15851, 15852, 15853,
                    15923, 15939, 15940, 15941, 15942, 15943, 15944, 15945,
                    16035, 16036, 16037, 16038, 16039, 16040, 16041, 16042,
                    16121, 16122, 16123, 16124, 16125, 16126, 16127, 16128,
                    16239, 16240, 16241, 16242, 16243, 16244, 16245, 16246,
                    16338, 16339, 16340, 16341, 16342, 16343, 16344, 16345,
                    16469, 16470, 16471, 16472, 16473, 16474, 16475, 16476,
                    16533, 16534, 16535, 16536, 16537, 16538, 16539, 16540,
                    16610, 16611, 16612, 16613, 16614, 16615, 16616, 16617,
                    16715, 16716, 16717, 16718, 16719, 16720, 16721, 16722,
                    16805, 16806, 16807, 16808, 16809, 16810, 16811, 16812,
                    16921, 16922, 16923, 16924, 16925, 16926, 16927, 16928,
                    17035, 17036, 17037, 17038, 17039, 17040, 17041, 17042,
                    17181, 17183, 17184, 17186, 17187,
                    17293, 17292, 17291, 17290, 17289,
                    17399, 17398, 17397, 17396, 17395,
                    17510, 17509, 17508, 17507, 17506,
                    17608, 17609, 17610, 17611, 17612,
                    17696, 17697, 17698, 17699, 17700, 17701, 17702, 17703, 17705,
                    17827, 17826, 17825, 17824, 17823]
eid_list_now = [17827, 17826, 17825, 17824, 17823]

gs = Gsheet()
while True:
    try:
        t1 = dt.datetime.now()
        i = 196
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
