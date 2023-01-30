from api_caller import ApiCaller, iso_utc_to_ist
import pandas as pd
import numpy as np
import logging
import datetime as dt
from time import sleep
from pprint import pprint

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
file_handler = logging.FileHandler("log_files/event_data_static.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class EventDataStatic:
    def __init__(self, apitype=None, userid=None):
        # print("initialising Event data Static")
        self.api_obj = ApiCaller(apitype, userid)

    def get_live_cda_event_ids(self):
        """
        Make 'getprobes' TradexAPI call and filter CDA events using 'is_price_editable' boolean data
        :return: list of active CDA event ids
        """
        data = self.api_obj.tradex_caller("getprobes")
        if ("probes" in data.keys()) and (len(data["probes"]) > 0):
            event_det_df = pd.DataFrame(data["probes"])
            event_det_df["type"] = np.where(event_det_df["is_price_editable"] == False, "IM", "CDA")
            cda_det_df = event_det_df[event_det_df["type"] == "CDA"]
            active_event_ids = cda_det_df["id"].to_list()
            return active_event_ids
        else:
            logger.critical("Active CDA event ids not fetched.")
            print("Active CDA event ids not fetched.")
            return []

    def get_live_im_event_ids(self):
        """
        Make 'getprobes' TradexAPI call and filter CDA events using 'is_price_editable' boolean data
        :return: list of active CDA event ids
        """
        data = self.api_obj.tradex_caller("getprobes")
        if ("probes" in data.keys()) and (len(data["probes"]) > 0):
            event_det_df = pd.DataFrame(data["probes"])
            event_det_df["type"] = np.where(event_det_df["is_price_editable"] == False, "IM", "CDA")
            cda_det_df = event_det_df[event_det_df["type"] == "IM"]
            active_event_ids = cda_det_df["id"].to_list()
            return active_event_ids
        else:
            logger.critical("Active IM event ids not fetched.")
            print("Active IM event ids not fetched.")
            return []

    def get_event_det_from_id(self, _id):
        """
        Get raw data from 'getprobes' TradexAPI call for specific event id
        :param id: Event id (int)
        :return: dictionary containing raw data for event id
        """
        _id = int(_id)
        data = self.api_obj.tradex_caller("getprobes")
        event_det_df = pd.DataFrame(data["probes"])
        event_det_df.set_index("id", inplace=True)
        event_details_dict = event_det_df.loc[_id].to_dict()
        return event_details_dict

    def get_static_event_data_dict(self, id):
        """
        Get title, started_at, and ends_at data for particular event id
        :param id: event id (int)
        :return: dict with event title, started_at and ends_at
        """
        try:
            raw_data = self.get_event_det_from_id(id)
            data_dict = {"title": raw_data["title"],
                         "started_at": iso_utc_to_ist(raw_data["start_date"]),
                         "ends_at": iso_utc_to_ist(raw_data["endsat"])}
            return data_dict
        except:
            logger.critical("Error in fetching static event data for id")
            print("Error in fetching static event data for id")
            return {}


if __name__ == "__main__":
    # temp3 = get_event_det_from_id(7810)
    # print(temp3)
    # temp1 = get_static_event_data_dict(9711)
    # print(temp1)
    # temp3 = temp1["ends_at"].isoformat()
    # print(temp3)
    # print(dt.datetime.fromisoformat(temp3))

    while True:
        obj = EventDataStatic('p', 0)
        temp2 = obj.get_live_cda_event_ids()
        eid_list = []
        for id in temp2:
        # for id in [13157, 13158]:
            data_dict = obj.get_static_event_data_dict(id)
            # if "Bitcoin USDT Price at" in data_dict["title"]:
            if "" in data_dict["title"]:
                print(id, data_dict["title"], data_dict["started_at"], " to ", data_dict["ends_at"])
                # print(type(data_dict["ends_at"]))
                eid_list.append(id)
                # print(type(data_dict["ends_at"]))
                # print(pd.to_datetime(data_dict["ends_at"]))
            # print(id, data_dict["title"], data_dict["started_at"], " to ", data_dict["ends_at"])
            # print((data_dict["title"][29:35]))
        eid_list.sort()
        print(eid_list)
        sleep_sec = 30
        print("Done.", dt.datetime.now(), "-----"*20,"next at", dt.datetime.now()+dt.timedelta(seconds=sleep_sec))
        sleep(sleep_sec)

    # obj = EventDataStatic('p', 0)
    # temp2 = obj.get_event_det_from_id(17032)
    # pprint(temp2)

