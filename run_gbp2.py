from strat8 import Strategy
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
    strat_num = 8  # int(input("Enter Strategy number:"))
    event_id_intake = 'a'  # input("Method of fetching event ids auto or manual?(a/m):")
    # coin_name = input("enter coin name from [btc, eth, shi, dog, gbp, eur, custom]: ")
    coin_name = "gbp"
    print("new 1.03")
    # coin_name = "custom"
    # custom_phrase_match = "On December 1st, 2027, Bitcoin price will be"
    while True:
        time_now = dt.datetime.now().time()

        if strat_num == 8:
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
                            if coin_name == "btc":
                                # Bitcoin USDT Price at 06:20 PM Today: 22811.13 or more?
                                phrase_match = "Bitcoin USDT Price at"
                            elif coin_name == "eth":
                                # Ethereum USDT Price at 07:05 PM Today: 1642.95 or more?
                                phrase_match = "Ethereum USDT Price at"
                            elif coin_name == "shi":
                                phrase_match = "Shib USDT Price at"
                            elif coin_name == "dog":
                                phrase_match = "Doge USDT Price at"
                            elif coin_name == "gbp":
                                phrase_match = "GBP USDT Price at"
                            elif coin_name == "eur":
                                phrase_match = "EUR USDT Price at"
                            else:
                                phrase_match = "not found not found"

                            if phrase_match in data_dict["title"]:
                                print(id, data_dict["title"], data_dict["started_at"], " to ", data_dict["ends_at"])
                                eid_list.append(id)
                                obj_name = "strobj" + str(id)
                                eid_input_str_list.append(obj_name)
                                print("Creating strat obj for ", id)
                                strat_obj_dict[obj_name] = Strategy(event_id=id, min_buy_qty=25,
                                                                    avg_qty_multiplier=5,
                                                                    getOutSellPriceDiff="dynamic", coin_name=coin_name)
                                print(f"Strategy object {obj_name} created for eid {id}")
                                strat_obj_dict[obj_name].initialise()
                    for i in eid_input_str_list:
                        print(strat_obj_dict[i].priceatri.title)
                        print(strat_obj_dict[i].priceatri.ends_at, type(strat_obj_dict[i].priceatri.ends_at))
                        try:
                            if not strat_obj_dict[i].initialise:
                                strat_obj_dict[i].initialise()
                                print(strat_obj_dict[i].priceatri.title)
                                print(strat_obj_dict[i].priceatri.ends_at,
                                      type(strat_obj_dict[i].priceatri.ends_at))
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

                    # if dt.datetime.now().time() > time_now > dt.time(19, 0, 0):
                    #     print("time up")
                    #     break
            except Exception as e:
                print(e)
                # raise(e)
