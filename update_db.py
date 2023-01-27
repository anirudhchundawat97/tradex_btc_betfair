from api_caller import tradex_caller
from MongoClient import Mongo
import datetime as dt
import event_data_static


def add_one_doc(event_id, data):
    Database = Mongo()
    Database.insert_dict("tradex_test1", str(event_id), data)
    return 42


def updatedb_static_data(id):
    database = Mongo()
    data_dict = {}
    if not database.check_if_collection_in_db(id):
        try:
            data_dict = event_data_static.get_static_event_data_dict(id)
            data_dict["_id"] = "details"
            data_dict["updated_at"] = dt.datetime.now().isoformat()
            add_one_doc(id, data_dict)
        except Exception as e:
            print("Static Data not fetched",f"Exception{e}")
    else:
        pass


def


if __name__ == "__main__":
    temp3 = event_data_static.get_static_event_data_dict(9379)
    print(temp3)
    updatedb_static_data(9379)