import pymongo as pm
import pandas as pd

event_id = 13561
userid = 0

client = pm.MongoClient("localhost", 27017)
db = client.tradex_strat_data
collection = db[f"strat7_{event_id}_{userid}"]
cursor = collection.find()
df = pd.DataFrame(cursor)
print(df.columns)
print(df["yesfp"])
print(df["yesfp"].std())
print(df.shape[0])
if not df.empty:
    yesfp_std = int(df["yesfp"].std())
    nofp_std = int(df["nofp"].std())
    yes_fpminusbp_std = int((df["yesfp"]-df["yesbp"]).abs().std())
    no_fpminusbp_std = int((df["nofp"] - df["nobp"]).abs().std())