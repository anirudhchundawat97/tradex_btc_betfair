from time import sleep
import requests as req
import logging
logging.basicConfig(filename="api_caller.log", level=logging.DEBUG, filemode='w', format='%(asctime)s: %(levelname)s: %(message)s')
logging.disable()


def tradex_caller(url_suffix, body={}):
    while True:
        try:
            server_url = "api.theox.co"
            token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                    ".eyJ1c2VyX2lkIjo0MzE0NzAsImlhdCI6MTY1ODc2NTA5MSwiZXhwIjoyNTIyNzY1MDkxfQ.gILXImoCm346" \
                    "-kN1ZV4jkA5WLEHjoc_rKXe0Q0GNDHM "
            url = f"https://{server_url}/v2/{url_suffix}"
            headers = {'Authorization': token}
            response = req.post(url, data=body, headers=headers).json()
            response = _check_response(response)
            return response
        except Exception as e:
            # logging.debug("something failed.")
            print("something failed. ", e)
            sleep(1)
            continue


def _check_response(response):
    try:
        status = response["status"]
    except KeyError:
        return response
    else:
        # logging.debug("something failed.")
        raise Exception("API call Failed", f"StatusValue: {status}")


if __name__ == "__main__":
    suffix = "probe/putcall"

    event_id = 89788
    asset = "Y"
    price = 2
    qty = 1

    body = {
        "probeid": event_id,
        "callvalue": asset,
        "coins": price,
        "noofcontracts": qty,
        "appVersion": 1041
    }
    print(f"----xx_xxxxxxxxx_x Buying  {asset} @Rs{price} qty{qty} in event {event_id}")
    response = tradex_caller(suffix, body)
    print(response)