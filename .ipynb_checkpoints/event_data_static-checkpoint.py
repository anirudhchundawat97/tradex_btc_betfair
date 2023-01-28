from api_caller import tradex_caller, iso_utc_to_ist
import pandas as pd
import numpy as np

def get_live_cda_event_ids():
    """
    Make 'getprobes' TradexAPI call and filter CDA events using 'is_price_editable' boolean data
    :return: list of active CDA event ids
    """
    data = tradex_caller("getprobes")
    event_det_df = pd.DataFrame(data["probes"])
    event_det_df["type"] = np.where(event_det_df["is_price_editable"] == False, "IM", "CDA")
    cda_det_df = event_det_df[event_det_df["type"] == "CDA"]
    active_event_ids = cda_det_df["id"].to_list()
    return active_event_ids

def get_event_det_from_id(_id):
    """
    Get raw data from 'getprobes' TradexAPI call for specific event id
    :param id: Event id (int)
    :return: dictionary containing raw data for event id
    """
    _id = int(_id)
    data = tradex_caller("getprobes")
    event_det_df = pd.DataFrame(data["probes"])
    event_det_df.set_index("id", inplace=True)
    event_details_dict = event_det_df.loc[_id].to_dict()
    return event_details_dict

def get_static_event_data_dict(id):
    """
    Get title, started_at, and ends_at data for particular event id
    :param id: event id (int)
    :return: dict with event title, started_at and ends_at
    """
    raw_data = get_event_det_from_id(id)
    data_dict = {"title": raw_data["title"],
                 "started_at": iso_utc_to_ist(raw_data["start_date"]),
                 "ends_at": iso_utc_to_ist(raw_data["endsat"])}
    return data_dict

if __name__ == "__main__":
    # temp3 = get_event_det_from_id(9711)
    # print(temp3)
    # temp1 = get_static_event_data_dict(9711)
    # print(temp1)
    # temp3 = temp1["ends_at"].isoformat()
    # print(temp3)
    # print(dt.datetime.fromisoformat(temp3))
    temp2 = get_live_cda_event_ids()
    for id in temp2:
        data_dict = get_static_event_data_dict(id)
        print(id, data_dict["title"], data_dict["started_at"])