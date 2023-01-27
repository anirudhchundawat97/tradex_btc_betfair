from transactions import Transactions#get_event_transactions, clean_transactions_df, _get_transactions_df
# from event_data_static import get_static_event_data_dict
from api_caller import ApiCaller#tradex_caller

import pandas as pd
# from fpdf import FPDF
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
pd.set_option("display.max_rows",500)
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import pymongo as pm

class EdaEventTrades:
    def __init__(self, event_id, generate_report=False, apitype=None, userid=None):
        self.api_obj = ApiCaller(apitype, userid)
        self.trans = Transactions(apitype, userid)
        self.eid = event_id
        self.generate_report = generate_report
        self.df = None
        self.dfz = None
        self.df_b = None
        self.df_s = None
        self.df_y = None
        self.df_n = None
        self.df_yb = None
        self.df_ys = None
        self.df_nb = None
        self.df_ns = None
        
        self.process_transactions(self.eid)
        # self.etitle = get_static_event_data_dict(self.eid)["title"]
        
    def get_event_hist_data(self, event_id):
        client = pm.MongoClient("localhost", 27017)
        db = client.tradex_data_0
        collection = db[str(event_id)]
        cursor = collection.find({"_id" : { "$ne" : "info"},
                                 },{"_id":0})
        df = pd.DataFrame(cursor)
        return df
    
    def get_best_price(self, event_id):
        hist_data = self.get_event_hist_data(event_id)
        hist_data["best_y_p"] = np.nan
        hist_data["best_n_p"] = np.nan
        hist_data["best_y_q"] = np.nan
        hist_data["best_n_q"] = np.nan
        for i in range(hist_data.shape[0]):
            temp = pd.DataFrame(hist_data["orderbook"][i])
            if not temp.empty:
                temp_y = temp[temp["asset"]=="Y"].copy().sort_values(by="price",ascending=False).reset_index(drop=True)
                # print(temp_y)
                if not temp_y.empty:
                    # print("best y price",temp_y["price"].iloc[0])
                    # print("best y qty",temp_y["qty"].iloc[0])
                    hist_data["best_y_p"].iloc[i] = temp_y["price"].iloc[0]
                    hist_data["best_y_q"].iloc[i] = temp_y["qty"].iloc[0]
                temp_n = temp[temp["asset"]=="N"].copy().sort_values(by="price",ascending=False).reset_index(drop=True)
                # print(temp_n)
                if not temp_n.empty:
                    # print("best n price",temp_n["price"].iloc[0])
                    # print("best n qty",temp_n["qty"].iloc[0])
                    hist_data["best_n_p"].iloc[i] = temp_n["price"].iloc[0]
                    hist_data["best_n_q"].iloc[i] = temp_n["qty"].iloc[0]
        # hist_data = hist_data.set_index("timestamp")
        return hist_data
        
    def _set_true_buy_qty(self, df):
        refid_counts =  df.refid.value_counts()
        refid_repeats = refid_counts[refid_counts>1].index
        for j in refid_repeats:
            temp_df = df[df["refid"]==j]
            if temp_df["status"].to_list() != ["Sold","Sold"]:
                mask = (df["status"]=="Bought") & (df["refid"] == j)
                df["qty"].loc[mask] = temp_df["qty"].sum()
        return df
    
    def process_transactions(self, eid):
        #fetching transactions from tradex api
        self.df = self.trans.get_event_transactions(eid)
        #inverting dataframe
        self.df = self.df[::-1].reset_index(drop=True)
        #removing cancelled qty
        self.dfz = self.df
        self.dfz["qty"] = np.where(self.dfz["status"]=="Cancelled",self.dfz["qty"]*-1,self.dfz["qty"])
        self.dfz = self._set_true_buy_qty(self.dfz)
        #calculating amount
        self.dfz["amount"] = self.dfz["qty"]*self.dfz["price"]
        self.dfz["amount"] = np.where(self.dfz["status"]=="Cancelled",0, self.dfz["amount"])
        self.dfz["amount"] = np.where(self.dfz["status"]=="Bought",self.dfz["amount"]*-1,self.dfz["amount"])
        #removing cancelled and zero qty rows
        self.dfz = self.dfz[self.dfz["status"]!="Cancelled"].reset_index(drop=True)
        self.dfz = self.dfz[self.dfz["qty"]>0].reset_index(drop=True)
        #segregating buy and sold dataframes
        self.df_b = self.dfz[self.dfz["status"]=="Bought"]
        self.df_s = self.dfz[self.dfz["status"]=="Sold"]
        #segregating Yes and No dataframes
        self.df_y = self.dfz[self.dfz["asset"]=="Y"]
        self.df_n = self.dfz[self.dfz["asset"]=="N"]
        #segregating yes/no/buy/sell dataframes
        self.df_yb = self.df_b[self.df_b["asset"]=="Y"]
        self.df_ys = self.df_s[self.df_s["asset"]=="Y"]
        self.df_nb = self.df_b[self.df_b["asset"]=="N"]
        self.df_ns = self.df_s[self.df_s["asset"]=="N"]
        for _df in [self.dfz,self.df_b, self.df_s, self.df_y, self.df_n, self.df_yb, self.df_ys, self.df_nb, self.df_ns]:
            _df["cum_amount"] = _df["amount"].cumsum()
            _df["cum_amount_%change"] = _df["cum_amount"].pct_change()

        info_dict = {"BuyQty":[self.df_yb["qty"].sum(), self.df_nb["qty"].sum()],
                     "SellQty":[self.df_ys["qty"].sum(), self.df_ns["qty"].sum()],
                     "NetQty":[self.df_yb["qty"].sum()-self.df_ys["qty"].sum(), self.df_nb["qty"].sum()-self.df_ns["qty"].sum()]
                    }
        info_df = pd.DataFrame(info_dict,index=["Yes","No"])
        # print(info_df)
        return 
    
    def plot_yesno_trade_price(self, filename = None):
        fig = make_subplots(rows=2, cols=1,shared_xaxes=True, vertical_spacing=0.02,specs=[[{"secondary_y": False}],[{"secondary_y": False}]])
        fig.add_trace(go.Scatter(x=self.df_yb["createdat"], 
                                 y=self.df_yb["price"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='green'),
                                 customdata=self.df_yb["qty"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="YesBuyprice"),row=1, col=1) #yes buy price
        fig.add_trace(go.Scatter(x=self.df_ys["createdat"],
                                 y=self.df_ys["price"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='blue'),
                                 customdata=self.df_ys["qty"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="YesSellPrice"),row=1, col=1) #yes sell price
        fig.add_trace(go.Scatter(x=self.df_nb["createdat"], 
                                 y=self.df_nb["price"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='red'),
                                 customdata=self.df_nb["qty"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="NoBuyPrice"),row=2, col=1) #no buy price
        fig.add_trace(go.Scatter(x=self.df_ns["createdat"], 
                                 y=self.df_ns["price"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='orange'),
                                 customdata=self.df_ns["qty"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="NoSellPrice"),row=2, col=1) #no sell price

        fig.update_traces(marker_size=3)
        fig.update_layout(height=600, width=1200,title_text=f"Prices traded for Yes and No - {self.eid}")
        if filename is None:
            fig.show()
        else:
            fig.write_image(filename)
    
    def plot_yesno_tradeNbest_price(self, filename = None):
        best_data = self.get_best_price(self.eid)
        fig = make_subplots(rows=2, cols=1,shared_xaxes=True, vertical_spacing=0.02,specs=[[{"secondary_y": False}],[{"secondary_y": False}]])
        fig.add_trace(go.Scatter(x=self.df_yb["createdat"], 
                                 y=self.df_yb["price"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='green'),
                                 customdata=self.df_yb["qty"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="YesBuyprice"),row=1, col=1) #yes buy price
        fig.add_trace(go.Scatter(x=self.df_ys["createdat"],
                                 y=self.df_ys["price"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='blue'),
                                 customdata=self.df_ys["qty"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="YesSellPrice"),row=1, col=1) #yes sell price
        fig.add_trace(go.Scatter(x= best_data["timestamp"],
                                 y=best_data["best_y_p"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='lightgreen'),
                                 customdata=best_data["best_y_q"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="YesBestPrice"),row=1, col=1) #yes best price
        fig.add_trace(go.Scatter(x=self.df_nb["createdat"], 
                                 y=self.df_nb["price"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='red'),
                                 customdata=self.df_nb["qty"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="NoBuyPrice"),row=2, col=1) #no buy price
        fig.add_trace(go.Scatter(x=self.df_ns["createdat"], 
                                 y=self.df_ns["price"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='orange'),
                                 customdata=self.df_ns["qty"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="NoSellPrice"),row=2, col=1) #no sell price
        fig.add_trace(go.Scatter(x= best_data["timestamp"],
                                 y=best_data["best_n_p"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='yellow'),
                                 customdata=best_data["best_n_q"],
                                 hovertemplate="%{customdata}@Price%{y}", 
                                 name="NoBestPrice"),row=2, col=1) #no best price

        fig.update_traces(marker_size=3)
        fig.update_layout(height=600, width=1200,title_text=f"Best&Trade Prices  for Yes and No - {self.eid}")
        if filename is None:
            fig.show()
        else:
            fig.write_image(filename)
            
    def plot_traded_value(self, filename = None):
        fig = make_subplots(rows=3, cols=1,shared_xaxes=True, vertical_spacing=0.02,specs=[[{"secondary_y": False}],[{"secondary_y": False}],[{"secondary_y": False}]])
        
        customdata =  np.stack((self.df_yb['qty'], self.df_yb['price']), axis=-1)
        fig.add_trace(go.Scatter(x=self.df_yb["createdat"],
                                 y=self.df_yb["cum_amount"]*-1, 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='green'),
                                 customdata=customdata,
                                 hovertemplate="qty%{customdata[0]}@Price%{customdata[1]}", 
                                 name="YesBuyValue"),row=1, col=1) #yes buy Value
        customdata =  np.stack((self.df_ys['qty'], self.df_ys['price']), axis=-1)
        fig.add_trace(go.Scatter(x=self.df_ys["createdat"], 
                                 y=self.df_ys["cum_amount"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='blue'),
                                 customdata=customdata,
                                 hovertemplate="qty%{customdata[0]}@Price%{customdata[1]}", 
                                 name="YesSellValue"),row=1, col=1) #yes sell Value

        customdata =  np.stack((self.df_nb['qty'], self.df_nb['price']), axis=-1)
        fig.add_trace(go.Scatter(x=self.df_nb["createdat"], 
                                 y=self.df_nb["cum_amount"]*-1, 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='red'),
                                 customdata=customdata,
                                 hovertemplate="qty%{customdata[0]}@Price%{customdata[1]}", 
                                 name="NoBuyValue"),row=2, col=1) #no buy Value
        customdata =  np.stack((self.df_ns['qty'], self.df_ns['price']), axis=-1)
        fig.add_trace(go.Scatter(x=self.df_ns["createdat"], 
                                 y=self.df_ns["cum_amount"], 
                                 mode='lines+markers', 
                                 line=dict(width=1, color='orange'),
                                 customdata=customdata,
                                 hovertemplate="qty%{customdata[0]}@Price%{customdata[1]}", 
                                 name="NoSellValue"),row=2, col=1) #no sell Value

        holding_value = self.df_y["cum_amount"]*-1
        fig.add_trace(go.Scatter(x=self.df_y["createdat"],
                                  y=holding_value , 
                                  name="YesHoldValue"),secondary_y=False,row=3, col=1)
        holding_value = self.df_n["cum_amount"]*-1
        fig.add_trace(go.Scatter(x=self.df_n["createdat"],
                                 y=holding_value , 
                                 name="NoHoldValue"),secondary_y=False,row=3, col=1)

        fig.update_traces(marker_size=3)
        fig.update_layout(height=900, width=1200,title_text=f"Value traded for Yes and No - {self.eid}")
        if filename is None:
            fig.show()
        else:
            fig.write_image(filename)
            
    def get_trades_info(self):
        z_info = Info(self.dfz)
        b_info = Info(self.df_b)
        s_info = Info(self.df_s)
        y_info = Info(self.df_y)
        n_info = Info(self.df_n)
        yb_info = Info(self.df_yb)
        ys_info = Info(self.df_ys)
        nb_info = Info(self.df_nb)
        ns_info = Info(self.df_ns)
        
        info_dict = {"AllTotalQty":z_info.totqty,
                    "BuyTotalQty":b_info.totqty,
                    "SellTotalQty":s_info.totqty,
                    "YesTotalQty":y_info.totqty,
                    "NoTotalQty":n_info.totqty,
                    "YesBuyTotalQty":yb_info.totqty,
                    "YesSellTotalQty":ys_info.totqty,
                    "NoBuyTotalQty":nb_info.totqty,
                    "NoSellTotalQty":ns_info.totqty,
                    "AllMaxQty":z_info.maxqty,
                    "BuyMaxQty":b_info.maxqty,
                    "SellMaxQty":s_info.maxqty,
                    "YesMaxQty":y_info.maxqty,
                    "NoMaxQty":n_info.maxqty,
                    "YesBuyMaxQty":yb_info.maxqty,
                    "YesSellMaxQty":ys_info.maxqty,
                    "NoBuyMaxQty":nb_info.maxqty,
                    "NoSellMaxQty":ns_info.maxqty,
                    "AllMinQty":z_info.minqty,
                    "BuyMinQty":b_info.minqty,
                    "SellMinQty":s_info.minqty,
                    "YesMinQty":y_info.minqty,
                    "NoMinQty":n_info.minqty,
                    "YesBuyMinQty":yb_info.minqty,
                    "YesSellMinQty":ys_info.minqty,
                    "NoBuyMinQty":nb_info.minqty,
                    "NoSellMinQty":ns_info.minqty,
                    "AllAvgQty":z_info.avgqty,
                    "BuyAvgQty":b_info.avgqty,
                    "SellAvgQty":s_info.avgqty,
                    "YesAvgQty":y_info.avgqty,
                    "NoAvgQty":n_info.avgqty,
                    "YesBuyAvgQty":yb_info.avgqty,
                    "YesSellAvgQty":ys_info.avgqty,
                    "NoBuyAvgQty":nb_info.avgqty,
                    "NoSellAvgQty":ns_info.avgqty,
                    "AllTradeCount":z_info.count,
                    "BuyTradeCount":b_info.count,
                    "SellTradeCount":s_info.count,
                    "YesTradeCount":y_info.count,
                    "NoTradeCount":n_info.count,
                    "YesBuyTradeCount":yb_info.count,
                    "YesSellTradeCount":ys_info.count,
                    "NoBuyTradeCount":nb_info.count,
                    "NoSellTradeCount":ns_info.count,
                    "AllMaxPrice":z_info.maxprice,
                    "BuyMaxPrice":b_info.maxprice,
                    "SellMaxPrice":s_info.maxprice,
                    "YesMaxPrice":y_info.maxprice,
                    "NoMaxPrice":n_info.maxprice,
                    "YesBuyMaxPrice":yb_info.maxprice,
                    "YesSellMaxPrice":ys_info.maxprice,
                    "NoBuyMaxPrice":nb_info.maxprice,
                    "NoSellMaxPrice":ns_info.maxprice,
                    "AllMinPrice":z_info.minprice,
                    "BuyMinPrice":b_info.minprice,
                    "SellMinPrice":s_info.minprice,
                    "YesMinPrice":y_info.minprice,
                    "NoMinPrice":n_info.minprice,
                    "YesBuyMinPrice":yb_info.minprice,
                    "YesSellMinPrice":ys_info.minprice,
                    "NoBuyMinPrice":nb_info.minprice,
                    "NoSellMinPrice":ns_info.minprice,
                    "AllAvgPrice":z_info.avgprice,
                    "BuyAvgPrice":b_info.avgprice,
                    "SellAvgPrice":s_info.avgprice,
                    "YesAvgPrice":y_info.avgprice,
                    "NoAvgPrice":n_info.avgprice,
                    "YesBuyAvgPrice":yb_info.avgprice,
                    "YesSellAvgPrice":ys_info.avgprice,
                    "NoBuyAvgPrice":nb_info.avgprice,
                    "NoSellAvgPrice":ns_info.avgprice,
                    "ScalpTotalPnL":self.dfz["amount"].sum(),
                    "ScalpYesPnL":self.df_y["amount"].sum(),
                    "ScalpNoPnL":self.df_n["amount"].sum(),
                    "OverallPnL":self.trans.get_event_transactions(self.eid)["amount"].sum()}
        return info_dict
        
        
class Info():
    def __init__(self, df):
        self.totqty = df["qty"].sum()
        self.maxqty = df["qty"].max()
        self.minqty = df["qty"].min()
        self.avgqty = df["qty"].mean()

        self.count = df.shape[0]

        self.maxprice = df["price"].max()
        self.minprice = df["price"].min()
        self.avgprice = df["price"].mean()
        
            
        
        
