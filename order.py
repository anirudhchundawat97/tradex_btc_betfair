import pandas as pd
from api_caller import ApiCaller
from mybets import MyBets
import logging
from pprint import pprint

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s;%(message)s")
log_file_name = "log_files/order7_57.log"
file_handler = logging.FileHandler(log_file_name)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

testing = False


class Order:
    def __init__(self, event_id, apitype=None, userid=None):
        # print("initialising Orders")
        self.event_id = event_id
        self.api_obj = ApiCaller(apitype, userid)
        self.mybet = MyBets(apitype, userid)
        print(f"Logging orders to {log_file_name} Testing:{testing}")

    def _buy(self, message, asset, price, qty, cmp=None, coins=None):
        suffix = "probe/putcall"
        if price:
            body = {
                "probeid": self.event_id,
                "callvalue": asset,
                "coins": price,
                "noofcontracts": qty,
                "appVersion": 1041
            }
        else:
            body = {"appVersion": 1058,
                    "callvalue": asset,
                    "coins": str(coins),
                    "noofcontracts": qty,
                    "preventSlippage": False,
                    "probeid": self.event_id,
                    "proptionid": 10,
                    "ptype": "bet",
                    "tradeType": "Buy",
                    "trade_initiated_price": cmp}
        pprint(body)
        print(f"-----Buying  {asset} @Rs{price} qty{qty} in event {self.event_id}, message:{message}")
        logger.info(
            f"log:pre;eid:{self.event_id};call:sent;type:place;order:buy;asset:{asset};price:{price};qty:{qty};orderid:buysend;respmessg:null;message:{message}")
        try:
            if not testing:
                response = self.api_obj.tradex_caller(suffix, body)
                logger.info(
                    f"log:post;eid:{self.event_id};call:response;type:place;order:buy;asset:{asset};price:{price};qty:{qty};orderid:{response['call']['orderId']};respmessg:null;message:{message}")
            else:
                response = dict()
                response["call"]["orderid"] = "dummy"
                logger.info(
                    f"log:post;eid:{self.event_id};call:response;type:place;order:buy;asset:{asset};price:{price};qty:{qty};orderid:{response['call']['orderId']}respmessg:null;;message:{message}")
        except KeyError:
            logger.info("api call response not recorded")
            try:
                if response["status"] in ["failed", "ERROR"]:
                    logger.info(
                        f"log:post;eid:{self.event_id};call:response;type:place;order:buy;asset:{asset};price:{price};qty:{qty};orderid:noresponse_{response['message']};respmessg:null;message:{message}")
                    print(f"api call response: {response['status']} message:{response['message']}")
                else:
                    logger.info(
                        f"log:post;eid:{self.event_id};call:response;type:place;order:buy;asset:{asset};price:{price};qty:{qty};orderid:noresponse_nomessage;respmessg:null;message:{message}")
                    # print("response: ", response)
            except:
                logger.info(
                    f"log:post;eid:{self.event_id};call:response;type:place;order:buy;asset:{asset};price:{price};qty:{qty};orderid:noresponse_noresponse;respmessg:null;message:{message}")
                # print("response: ", response)
        return response

    def _sell(self, message, asset, price, qty, cmp=None):
        suffix = "event/makeexit"
        if price:
            body = {
                "probeid": self.event_id,
                "callvalue": asset,
                "coins": price,
                "noofcontracts": qty,
                "appVersion": 1041
            }
        else:
            body = {"appVersion": 1058,
                    "callvalue": asset,
                    "coins": "NA",
                    "noofcontracts": qty,
                    "preventSlippage": False,
                    "probeid": self.event_id,
                    "tradeType": "Sell",
                    "trade_initiated_price": cmp}
        pprint(body)
        print(f"-----Selling {asset} @Rs{price} qty{qty} in event {self.event_id}, message:{message}")
        logger.info(
            f"log:pre;eid:{self.event_id};call:sent;type:place;order:sell;asset:{asset};price:{price};qty:{qty};orderid:sellsend;respmessg:null;message:{message}")
        try:
            if not testing:
                response = self.api_obj.tradex_caller(suffix, body)
                logger.info(
                    f"log:post;eid:{self.event_id};call:response;type:place;order:sell;asset:{asset};price:{price};qty:{qty};orderid:{response['call']['orderId']};respmessg:null;message:{message}")
            else:
                response = dict()
                response["call"]["orderid"] = "dummy"
                logger.info(
                    f"log:post;eid:{self.event_id};call:response;type:place;order:sell;asset:{asset};price:{price};qty:{qty};orderid:{response['call']['orderId']};respmessg:null;message:{message}")

        except KeyError:
            logger.info("api call response not recorded")
            try:
                if response["status"] in ["failed", "ERROR"]:
                    logger.info(
                        f"log:post;eid:{self.event_id};call:response;type:place;order:sell;asset:{asset};price:{price};qty:{qty};orderid:noresponse_{response['message']};respmessg:null;message:{message}")
                    print(f"api call response: {response['status']} message:{response['message']}")
                else:
                    logger.info(
                        f"log:post;eid:{self.event_id};call:response;type:place;order:sell;asset:{asset};price:{price};qty:{qty};orderid:noresponse_nomessage;respmessg:null;message:{message}")
                    # print("response: ", response)
            except:
                logger.info(
                    f"log:post;eid:{self.event_id};call:response;type:place;order:sell;asset:{asset};price:{price};qty:{qty};orderid:noresponse_noresponse;respmessg:null;message:{message}")
                # print("response: ", response)
        return response

    def _cancel_buy(self, message, asset, price, order_id):
        suffix = "event/cancelcall"
        body = {
            "orderid": order_id,
            "probeid": self.event_id,
            "callvalue": asset,
            "coins": price,
            "appVersion": 1041
        }
        logger.info(
            f"log:pre;eid:{self.event_id};call:sent;type:cancel;order:buy;asset:{asset};price:{price};qty:null;orderid:{order_id};respmessg:null;message:{message}")
        if not testing:
            response = self.api_obj.tradex_caller(suffix, body)
            try:
                if response["success"]:
                    logger.info(
                        f"log:post;eid:{self.event_id};call:response;type:cancel;order:buy;asset:{asset};price:{price};qty:null;orderid:{order_id};respmessg:null;message:{message}")
                else:
                    logger.info(
                        f"log:post;eid:{self.event_id};call:response;type:cancel;order:buy;asset:{asset};price:{price};qty:null;orderid:{order_id};respmessg:notsuccess;message:{message}")
            except KeyError:
                logger.info(
                    f"log:post;eid:{self.event_id};call:response;type:cancel;order:buy;asset:{asset};price:{price};qty:null;orderid:{order_id};respmessg:nosuccesskey;message:{message}")
        else:
            response = "dummy"
            logger.info(
                f"log:post;eid:{self.event_id};call:response;type:cancel;order:buy;asset:{asset};price:{price};qty:dummy;orderid:{order_id};respmessg:null;message:{message}")
        return response

    def _cancel_sell(self, message, asset, price, order_id):
        suffix = "event/cancelonhold"
        body = {
            "orderid": order_id,
            "probeid": self.event_id,
            "callvalue": asset,
            "coins": price,
            "appVersion": 1041
        }
        # logger.info(f"{self.event_id}: cancel sell sent: {order_id} {self.event_id} {asset} {price}, message:{message}")
        logger.info(
            f"log:pre;eid:{self.event_id};call:sent;type:cancel;order:sell;asset:{asset};price:{price};qty:null;orderid:{order_id};respmessg:null;message:{message}")
        if not testing:
            response = self.api_obj.tradex_caller(suffix, body)
            try:
                if response["success"]:
                    logger.info(
                        f"log:post;eid:{self.event_id};call:response;type:cancel;order:sell;asset:{asset};price:{price};qty:null;orderid:{order_id};respmessg:null;message:{message}")
                else:
                    logger.info(
                        f"log:post;eid:{self.event_id};call:response;type:cancel;order:sell;asset:{asset};price:{price};qty:null;orderid:{order_id};respmessg:notsuccess;message:{message}")
            except KeyError:
                logger.info(
                    f"log:post;eid:{self.event_id};call:response;type:cancel;order:sell;asset:{asset};price:{price};qty:null;orderid:{order_id};respmessg:nosuccesskey;message:{message}")
        else:
            response = "dummy"
            logger.info(
                f"log:post;eid:{self.event_id};call:response;type:cancel;order:sell;asset:{asset};price:{price};qty:dummy;orderid:{order_id};respmessg:null;message:{message}")
        return response

    def cancel_all_pending_sell(self, asset, message):
        df = self.mybet.get_event_holdings(self.event_id)
        if not df.empty:
            mask_pending_sell = (df["side"] == "sell") & (df["asset"] == asset) & (df["status"] == "pending")
            temp_df = df[mask_pending_sell]
            if not temp_df.empty:
                print("cancelling: ")
                print(temp_df[["status", "price", "asset", "qty", "orderid", "side", "createdat", "buyprice"]])
                for i in range(temp_df.shape[0]):
                    self._cancel_sell(message=message,
                                      asset=temp_df.iloc[i]["asset"],
                                      price=temp_df.iloc[i]["price"],
                                      order_id=temp_df.iloc[i]["orderid"])

    def cancel_all_pending_buy(self, asset, message):
        df = self.mybet.get_event_holdings(self.event_id)
        if not df.empty:
            mask_pending_buy = (df["side"] == "buy") & (df["asset"] == asset) & (df["status"] == "pending")
            temp_df = df[mask_pending_buy]
            if not temp_df.empty:
                print("cancelling: ")
                print(temp_df[["status", "price", "asset", "qty", "orderid", "side", "createdat", "buyprice"]])
                for i in range(temp_df.shape[0]):
                    self._cancel_buy(message=message,
                                     asset=temp_df.iloc[i]["asset"],
                                     price=temp_df.iloc[i]["price"],
                                     order_id=temp_df.iloc[i]["orderid"])

    def is_same_order(self, asset, price, qty, side):
        df = self.mybet.get_event_holdings(self.event_id)
        if not df.empty:
            asset_mask = (df["asset"] == asset)
            price_mask = (df["price"] == price)
            qty_mask = (df["qty"] == qty)
            side_mask = (df["side"] == side)
            status_mask = (df["status"] == "pending")
            temp_df = df[asset_mask & price_mask & qty_mask & side_mask & status_mask]
            if temp_df.shape[0] >= 1:
                print("Same order exits. passing")
                return True


if __name__ == "__main__":
    # print(get_event_holdings(7810))
    od = Order(15071, apitype='p', userid=0)

    # resp = od._buy("trying","N",86,10)
    # resp = od._buy("testing","Y",10,10)
    resp = od._buy("testing", "Y", 12, 2)
    # resp = od._sell("testing", "Y", 70, 5)
    # resp = od.cancel_all_pending_buy("Y","dummy")
    print(resp)
    pprint(resp)
    # print(resp["call"]["orderId"])

# {'success': True, 'status': 'ERROR', 'message': 'Taking time. Please try again!'}

# {'success': True,
# 'call': {'rank': -1, 'returns': 100, 'probeid': 15071, 'callvalue': 'Y', 'coins': 65, 'noofcontracts': 3, 'appVersion': '1041', 'userid': 603727, 'preventSlippage': False, 'allowedSlippage': 4, 'orderId': 'od_1674361929724680'},
# 'user': {'coinse': 3724939.74, 'userid': 603727, 'coinsb': 0, 'coinsw': 0, 'coinsd': 4677501.37},
# 'calls': [{'rank': -1, 'coins': 65, 'callvalue': 'Y', 'userid': 603727, 'noofcontracts': 3, 'orderid': 'od_1674361929724680', 'status': 'O', 'createdat': '2023-02-04T12:10:21.259415+00:00', 'lastprice': 0}, {'rank': 0, 'coins': 50, 'callvalue': 'N', 'userid': 603727, 'noofcontracts': 25, 'orderid': 'od_1672403731763847', 'status': 'EX', 'createdat': '2022-12-30T18:03:33.753628+00:00', 'lastprice': 47.28}, {'rank': -1, 'coins': 65, 'callvalue': 'Y', 'userid': 603727, 'noofcontracts': 3, 'orderid': 'od_1674361929724680', 'status': 'A', 'createdat': '2023-02-04T12:10:21.259415+00:00', 'lastprice': 0}],
# 'msg': None, 'partiallyExecuted': False, 'unmatched': 3, 'matched': 0}

# {'error': 'Invalid Request',
#  'message': 'Invalid Request',
#  'status': 'failed',
# 'success': False}
