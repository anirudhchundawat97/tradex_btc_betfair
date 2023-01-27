from event_data_static import EventDataStatic
from MongoClient import Mongo
from probecallsopen import ProbeCallsOpen
from lasttradesinfo import LastTradesInfo
import pymongo
import datetime as dt
from time import sleep

class DataRecorder:
    def add_one_doc(self, eid, data):
        try:
            database = Mongo("tradex_data_0")
            database.insert_dict("tradex_data_0", str(eid), data)
            return
        except pymongo.errors.DuplicateKeyError:
            pass


    def _get_info_data_dict(self, eid):
        data_dict = get_static_event_data_dict(eid)
        data_dict["event_id"] = eid
        data_dict["_id"] = "info"
        return data_dict


    def _get_orders_data_dict(self, eid):
        data_dict = dict()
        data_dict["timestamp"] = dt.datetime.now()
        data_dict["orderbook"] = (get_yesno_orderbook(eid)[0]).to_dict('records')
        data_dict["lasttradesinfo"] = clean_lastTradesInfo_df(eid).to_dict('records')
        return data_dict


    def initialise(self):
        eid_list = get_live_cda_event_ids()
        if 4798 in eid_list:
            eid_list.remove(4798)
        if 11255 in eid_list:
            eid_list.remove(11255)
        # above if condition is to remove event id that has zero orders at all times
        for event in eid_list:
            first_data = _get_info_data_dict(event)
            add_one_doc(event, first_data)
            second_data = _get_orders_data_dict(event)
            add_one_doc(event, second_data)
        print(f"{dt.datetime.now()} initialised {len(eid_list)} events.|",eid_list)


    def update(self):
        eid_list = get_live_cda_event_ids()
        if 4798 in eid_list:
            eid_list.remove(4798)
        if 11255 in eid_list:
            eid_list.remove(11255)
        # above if condition is to remove event id that has zero orders at all times
        for event in eid_list:
            second_data = _get_orders_data_dict(event)
            add_one_doc(event, second_data)
        print(f"{dt.datetime.now()} updated {len(eid_list)} events.| ",eid_list)


if __name__ == "__main__":
    dr_obj = DataRecorder()
    temp2 = get_live_cda_event_ids()
    for id in temp2:
        print("-" * 20)
        data_dict = _get_info_data_dict(id)
        print("info: ", data_dict)
        # data_dict = _get_orders_data_dict(id)
        # print("orders: ", data_dict)
    initialise()
    while True:
        sleep(60)
        update()
