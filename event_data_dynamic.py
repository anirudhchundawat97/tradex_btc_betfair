# from api_caller import tradex_caller
# import pandas as pd
# import numpy as np
#
# def get_event_pending_orders(id):
#     url_suffix = "probecalls/open"
#     body = {"probeid": id}
#     all_response = tradex_caller(url_suffix, body)
#     return all_response["calls"]
#
# def get_ltp_data(id):
#     url_suffix = "lastTradesInfo"
#     body = {"probeid": id}
#     all_response = tradex_caller(url_suffix, body)
#     return all_response["trades"]
#
# def _best_pending_yn(id):
#     raw_data = get_event_pending_orders(id)
#     df = pd.DataFrame(raw_data)
#     yes_df = df[df["callvalue"] == "Y"]
#     no_df = df[df["callvalue"] == "N"]
#     yes_df = yes_df.sort_values(by="coins", ascending=False).reset_index()
#     no_df = no_df.sort_values(by="coins", ascending=False).reset_index()
#     return yes_df["coins"].iloc[0], no_df["coins"].iloc[0]
#
# def get_price_data(id):
#     best_pend_y, best_pend_n = _best_pending_yn()
#     best_exec_y_buy = 0
#     best_exec_y_sell = 0
#     best_exec_n_buy = 0
#     best_exec_n_sell = 0
#
#
#
# if __name__ == "__main__":
#     temp5 = get_event_pending_orders(9737)
#     y,n = _best_pending_yn(9737)
#     print(temp5)
#     print(y,n)