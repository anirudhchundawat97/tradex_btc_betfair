# from strat5 import Strategy as Strategy5
# from strat6 import Strategy as Strategy6
from strat7 import Strategy as Strategy7
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
    strat_num = 7#int(input("Enter Strategy number:"))
    event_id_intake = 'm' #input("Method of fetching event ids auto or manual?(a/m):")
    while True:
        time_now = dt.datetime.now().time()
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
                    if len(eid_input_list) >= 1:
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

                        while dt.datetime.now() <= dt.datetime.fromisoformat(strat_obj_dict[i].priceatri.ends_at):
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
