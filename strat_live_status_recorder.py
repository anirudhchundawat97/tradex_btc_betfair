from MongoClient import Mongo
import pymongo

class StratRecorder:
    def __init__(self, eid, strategy_num, userid):
        self.event_id = eid
        self.strategy_num = strategy_num
        self.userid = userid

    def _add_one_doc(self, data_dict):
        try:
            database = Mongo("tradex_strat_data")
            database.insert_dict("tradex_strat_data", f"strat{self.strategy_num}_{self.event_id}_{self.userid}", data_dict)
            return
        except pymongo.errors.DuplicateKeyError:
            pass

    # def initialise(self, data_dict):
    #     pass
    #
    # def update(self, data_dict):
    #     pass