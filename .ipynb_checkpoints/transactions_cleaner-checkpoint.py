import numpy as np

def remove_cancelled_orders(df):
    #only un-comment prints to figure waht is happenin
    og_df = df.copy()
    del_row_indices = []
    for ref in og_df["refid"].unique():
        temp = og_df[og_df["refid"]==ref]
        if (temp.shape[0]>1) and (len(temp["status"].unique())>1) and (temp["status"].unique()[0] != "Sold"):
            # print(temp[["createdat","refid","amount","status","qty","asset","price"]])
            if (len(temp["status"].unique())==2) and (temp["status"].unique()[0] == "Cancelled") and (temp["status"].unique()[1] == "Bought"):
                cancel_index = temp[temp["status"]=="Cancelled"].index[0]
                bought_index = temp[temp["status"]=="Bought"].index[0]
                if (temp["qty"].loc[cancel_index] == temp["qty"].loc[bought_index]) and (temp["price"].loc[cancel_index] == temp["price"].loc[bought_index]):
                    del_row_indices.append(cancel_index)
                    del_row_indices.append(bought_index)
                    # print(del_row_indices)
                elif (temp["qty"].loc[cancel_index] != temp["qty"].loc[bought_index]):
                    new_amount = temp["amount"].loc[cancel_index] + temp["amount"].loc[bought_index]
                    new_qty = temp["qty"].loc[bought_index] - temp["qty"].loc[cancel_index]

                    og_df["qty"].loc[bought_index] = new_qty
                    og_df["amount"].loc[bought_index] = new_amount

                    # print(og_df.loc[bought_index])
                    del_row_indices.append(cancel_index)
                    # print(del_row_indices)

            else:
                print("ErrorErrorErrorErrorErrorErrorErrorErrorErrorError")
                raise Exception
    og_df = og_df.drop(del_row_indices)
    if np.round(df["amount"].sum(),2) == np.round(df["amount"].sum(),2):
        print("Amount sum matches")
    else:
        print("Amount sum un-matched")
        raise Exception
    return og_df