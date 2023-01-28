# from strat5 import Strategy as Strategy5
# from strat6 import Strategy as Strategy6
from strat7_w_betfair import Strategy as Strategy7
from time import sleep
import logging
import datetime as dt
from event_data_static import EventDataStatic

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
log_file_name = "log_files/main_strat7_57.log"
file_handler = logging.FileHandler(log_file_name)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if __name__ == "__main__":
    print(f"Logging to {log_file_name}")
    strat_num = 7  # int(input("Enter Strategy number:"))
    event_id_intake = 'm'  # input("Method of fetching event ids auto or manual?(a/m):")
    while True:
        time_now = dt.datetime.now().time()
        strategy_start_hr = 15
        strategy_runfor_hr = 1
        if True:#(time_now > dt.time(strategy_start_hr, 0, 0)) and (time_now < dt.time(strategy_start_hr + strategy_runfor_hr, 0, 0)):
            # if strat_num == 5:
            #     try:
            #         eid = int(input("Enter event id:"))
            #         strat = Strategy5(event_id=eid, opp_direction_move_margin=2, avg_qty_multiplier=4, min_buy_qty=15)
            #         strat.initialise()
            #         print(strat.priceatri.title)
            #         print(dt.datetime.fromisoformat(strat.priceatri.started_at))
            #         print(dt.datetime.fromisoformat(strat.priceatri.ends_at))
            #
            #         while dt.datetime.now() <= dt.datetime.fromisoformat(strat.priceatri.ends_at):
            #             strat.update()
            #             sleep(15)
            #         print("EVENT ENDED.")
            #     except Exception as e:
            #         logger.exception(e)
            #         raise e
            # elif strat_num == 6:
            #     try:
            #         eid_input_list = []
            #         strat_obj_dict = {}
            #         add_more = "Y"
            #         while add_more in ["Y","y"]:
            #             eid_temp = int(input("Enter event id :"))
            #             eid_input_list.append(eid_temp)
            #             add_more = input("Add more id? (Y/N)")
            #         eid_input_str_list = ["strobj"+str(x) for x in eid_input_list]
            #         for strobj, eid in zip(eid_input_str_list, eid_input_list):
            #             strat_obj_dict[strobj] = Strategy6(event_id=eid, spread=6, min_buy_qty=15, avg_qty_multiplier=1)
            #             print(f"Strategy object {strobj} created for eid {eid}")
            #
            #         for i in eid_input_str_list:
            #             try:
            #                 strat_obj_dict[i].initialise()
            #                 print(strat_obj_dict[i].priceatri.title)
            #                 print(dt.datetime.fromisoformat(strat_obj_dict[i].priceatri.started_at))
            #                 print(dt.datetime.fromisoformat(strat_obj_dict[i].priceatri.ends_at))
            #                 sleep(60)
            #             except Exception as e:
            #                 logger.exception(e)
            #                 print(e,"eid",i,strat_obj_dict[i])
            #
            #         # while dt.datetime.now() <= dt.datetime.fromisoformat(i.priceatri.ends_at):
            #         while True:
            #             for j in eid_input_str_list:
            #                 try:
            #                     strat_obj_dict[j].update()
            #                     sleep(60)
            #                 except Exception as e:
            #                     logger.exception(e)
            #                     print(e,"eid",j,strat_obj_dict[j])
            #             print("#"*20)
            #             print("#" * 20)
            #             print("#" * 20)
            #             print("#" * 20)
            #             print("#"*20)
            #             sleep(120)
            #         print("EVENT ENDED.")
            #     except Exception as e:
            #         logger.exception(e)
            #         raise e
            # elif strat_num == 66:
            #     try:
            #         eid = int(input("Enter event id:"))
            #         strat = Strategy6(event_id=eid, spread=6, min_buy_qty=15, avg_qty_multiplier=1)
            #         strat.initialise()
            #         print(strat.priceatri.title)
            #         print(dt.datetime.fromisoformat(strat.priceatri.started_at))
            #         print(dt.datetime.fromisoformat(strat.priceatri.ends_at))
            #
            #         while dt.datetime.now() <= dt.datetime.fromisoformat(strat.priceatri.ends_at):
            #             strat.update()
            #             sleep(60)
            #         print("EVENT ENDED.")
            #     except Exception as e:
            #         logger.exception(e)
            #         raise e
            if strat_num == 7:
                try:
                    while True:
                        eid_input_list = []
                        strat_obj_dict = {}
                        if event_id_intake in ["m", "M"]:
                            add_more = "Y"
                            while add_more in ["Y", "y"]:
                                eid_temp = int(input("Enter event id :"))
                                eid_input_list.append(eid_temp)
                                add_more = input("Add more id? (Y/N)")
                        elif event_id_intake in ["a", "A"]:
                            eds = EventDataStatic(apitype='p', userid=0)
                            temp2 = eds.get_live_cda_event_ids()
                            for id in temp2:
                                data_dict = eds.get_static_event_data_dict(id)
                                if "Bitcoin USDT will stay above" in data_dict["title"]:
                                    print(id, data_dict["title"], data_dict["started_at"], " to ", data_dict["ends_at"])
                                    eid_input_list.append(id)
                        eid_input_list.sort()
                        print("Event ids:")
                        print(eid_input_list)
                        if len(eid_input_list) > 0:
                            eid_input_str_list = ["strobj" + str(x) for x in eid_input_list]
                            for strobj, eid in zip(eid_input_str_list, eid_input_list):
                                print("Creating strat obj for ", eid)
                                strat_obj_dict[strobj] = Strategy7(event_id=eid, min_buy_qty=25, avg_qty_multiplier=5,
                                                                   getOutSellPriceDiff="dynamic")
                                print(f"Strategy object {strobj} created for eid {eid}")

                            for i in eid_input_str_list:
                                try:
                                    strat_obj_dict[i].initialise()
                                    print(strat_obj_dict[i].priceatri.title)
                                    print(dt.datetime.fromisoformat(strat_obj_dict[i].priceatri.started_at))
                                    print(dt.datetime.fromisoformat(strat_obj_dict[i].priceatri.ends_at))
                                    sleep(5)
                                except Exception as e:
                                    logger.exception(e)
                                    print(e, "eid", i, strat_obj_dict[i])

                            while (dt.datetime.now()+dt.timedelta(hours=5, minutes=30)) <= dt.datetime.strptime(strat_obj_dict[i].priceatri.ends_at, "%Y-%m-%dT%H:%M:%S"):
                                # while True:
                                for j in eid_input_str_list:
                                    try:
                                        strat_obj_dict[j].update()
                                        sleep(5)
                                    except Exception as e:
                                        logger.exception(e)
                                        print(e, "eid", j, strat_obj_dict[j])
                                print("#" * 20)
                                print("#" * 20)
                                print("#" * 20)
                                print("#" * 20)
                                print("#" * 20)
                                sleep(60)
                            print("EVENT ENDED.")
                            break
                        else:
                            print("Less than 8 event id active")
                    print("Process terminated.")
                except Exception as e:
                    logger.exception(e)
                    raise e
            elif strat_num == 8:
                try:
                    eid_list = []
                    eid_input_str_list = []
                    strat_obj_dict = {}
                    eds = EventDataStatic(apitype='p', userid=0)
                    while True:
                        print(eid_list)
                        print(eid_input_str_list)
                        print(strat_obj_dict)
                        temp2 = eds.get_live_cda_event_ids()
                        for id in temp2:
                            if id not in eid_list:
                                data_dict = eds.get_static_event_data_dict(id)
                                # Bitcoin USDT Price at 06:20 PM Today: 22811.13 or more?
                                if "Bitcoin USDT Price at" in data_dict["title"]:
                                    print(id, data_dict["title"], data_dict["started_at"], " to ", data_dict["ends_at"])
                                    eid_list.append(id)
                                    obj_name = "strobj" + str(id)
                                    eid_input_str_list.append(obj_name)
                                    print("Creating strat obj for ", id)
                                    strat_obj_dict[obj_name] = Strategy7(event_id=id, min_buy_qty=25,
                                                                         avg_qty_multiplier=5,
                                                                         getOutSellPriceDiff="dynamic")
                                    print(f"Strategy object {obj_name} created for eid {id}")
                                    strat_obj_dict[obj_name].initialise()
                        for i in eid_input_str_list:
                            print(strat_obj_dict[i].priceatri.title)
                            print(strat_obj_dict[i].priceatri.ends_at, type(strat_obj_dict[i].priceatri.ends_at))
                            try:
                                if not strat_obj_dict[i].initialise:
                                    strat_obj_dict[i].initialise()
                                    print(strat_obj_dict[i].priceatri.title)
                                    print(strat_obj_dict[i].priceatri.ends_at, type(strat_obj_dict[i].priceatri.ends_at))
                                    print(dt.datetime.fromisoformat(strat_obj_dict[i].priceatri.started_at))
                                    print(dt.datetime.fromisoformat(strat_obj_dict[i].priceatri.ends_at))
                                elif (strat_obj_dict[i].initialise) and (dt.datetime.now() <= dt.datetime.fromisoformat(
                                        strat_obj_dict[i].priceatri.ends_at)):
                                    strat_obj_dict[i].update()
                                elif dt.datetime.now() > dt.datetime.fromisoformat(strat_obj_dict[i].priceatri.ends_at):
                                    print("removed ", i, "id: ", int(i[6:]))
                                    eid_list.remove(int(i[6:]))
                                    eid_input_str_list.remove(i)
                                    del strat_obj_dict[i]
                                else:
                                    print("No action")
                            except Exception as e:
                                logger.exception(e)
                                print(e, "eid", i, strat_obj_dict[i])

                        if dt.datetime.now().time() > time_now > dt.time(strategy_start_hr + strategy_runfor_hr, 0, 0):
                            print("time up")
                            break
                except Exception as e:
                    print(e)
        elif time_now > dt.time(strategy_start_hr + strategy_runfor_hr, 0, 0):
            print("Time up")
            break
        else:
            time_remain = dt.datetime.now().replace(hour=strategy_start_hr, minute=0, second=00) - dt.datetime.now()
            if (time_remain < dt.timedelta(minutes=3)) and (time_now < dt.time(18, 0, 0)):
                print("Time to market open: ", time_remain, "waiting 15secs")
                sleep(15)
            elif (time_remain > dt.timedelta(minutes=1)) and (time_now < dt.time(strategy_start_hr, 0, 0)):
                sleep_time = time_remain / 2
                print("last run: ", time_now, "next run: ", (dt.datetime.now() + sleep_time).time())
                print("Time to market open: ", time_remain, f"waiting {sleep_time}")
                print()
                sleep(sleep_time.total_seconds())
