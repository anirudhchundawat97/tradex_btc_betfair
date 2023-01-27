import pymongo
from time import sleep


class Mongo:
    def __init__(self, database_name):
        self.client = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db = None
        self.collection = None
        self.database_name = database_name

    def insert_dict(self, db_name, collection_name, data_dictionary):
        self._set_db(db_name)
        self._set_collection(collection_name)
        self.collection.insert_one(data_dictionary)

    def show_all_database_names(self):
        for db in self.client.list_database_names():
            print(db)

    def _set_db(self, db_name):
        self.db = self.client[db_name]

    def check_if_database_exists(self):
        if str(self.db.name) in self.client.list_database_names():
            print(" Database name found.")
            return 1
        else:
            print(" Database name doesn't exist.")
            return 0

    # def insert_dict(self, db_name, collection_name, data_dictionary):
    #     while True:
    #         try:
    #             self._set_db(db_name)
    #             # self.check_if_database_exists()
    #             self._set_collection(collection_name)
    #             self.collection.insert_one(data_dictionary)
    #         except Exception as e:
    #             print("m" * 200, "exception: ", e)
    #             print()
    #             sleep(3)
    #             continue
    #         break

    def _set_collection(self, collection_name):
        self.collection = self.db[collection_name]

    def insert_dictlist(self, db_name, collection_name, list_of_data_dictionary):
        self._set_db(db_name)
        # self.check_if_database_exists()
        self._set_collection(collection_name)
        self.collection.insert_many(list_of_data_dictionary)

    def check_if_collection_in_db(self, collection_name):
        self._set_db(self.database_name)
        all_colls = self.db.list_collection_names()
        if str(collection_name) in all_colls:
            return True
        else:
            return False


if __name__ == "__main__":
    db = Mongo("tradex_test1")
    # db.set_db("tradex_test0")
    # db.set_collection("event_id_7808")
    temp2 = db.check_if_collection_in_db("0")
    print(temp2)
