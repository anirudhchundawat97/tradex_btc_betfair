from time import sleep
import datetime as dt
import requests as req
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
file_handler = logging.FileHandler("log_files/api_caller.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

api_hit_permin_limit = 5

class ApiCaller:
    def __init__(self, apitype='p', userid=0):
        if apitype is None:
            self.api_type = input("API type: Test or Production (t/p)?: ")
        else:
            self.api_type = apitype
        if userid is None:
            self.userid = int(input("Enter userid (0 for default): "))
        else:
            self.userid = userid
        self.server_url = None
        self.token = None
        self._set_api_url()
        self._set_user_bearer_token()

    def _set_api_url(self):
        if (self.api_type == "t") or (self.api_type == "T"):
            self.server_url = "testapi.theox.co"
        elif (self.api_type == "p") or (self.api_type == "P"):
            self.server_url = "api.theox.co"
        elif (self.api_type == "d") or (self.api_type == "D"):
            self.server_url = "devapi.theox.co"

    def _set_user_bearer_token(self):
        if (self.userid == 0) or (self.userid == 603727):
            # tokenfor mobile-987654321 otpgit  XXX
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo2MDM3MjcsImlhdCI6MTY2Nzk4NjE1OCwiZXhwIjoyNTMxOTg2MTU4fQ.qJP0dKNBQRFojO32SfvyYR2o_Whk3gDy6JkZZ1BUxCM "
        elif self.userid == 11:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoxMSwiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9" \
                         ".k184_iA1GWq2ZlaHRpXmpGG531LEm_FDS5ShBLfoxGQ "
        elif self.userid == 12:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoxMiwiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9.O2l-EzRh" \
                         "-4OgQ8GArqyLxXYffpwAOkrRA-6M9SfJkXE "
        elif self.userid == 13:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoxMywiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9.Nwq" \
                         "-x7IPWgr943clXB5VLSW6JujHJYAOoMh2_H_B3cQ "

        elif self.userid == 14:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoxNCwiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9" \
                         ".FXbWhB_Yj1stdAIq3noVAukjdS0Funt0967HsC_l37I "
        elif self.userid == 15:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoxNSwiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9.Volr9MacMxpVRW0" \
                         "-GIfZOUs4lOklSI8xQqAjr05LIIs "
        elif self.userid == 16:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoxNiwiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9" \
                         ".8uOHY9M1C7T1eg6ZWsYchPEFV10od-FWUSWFlqK2VyE "
        elif self.userid == 17:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoxNywiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9" \
                         ".Oqfd55EEntxUedO55lGEUaBXz9Ydf_9XdZdweVj-tPk "
        elif self.userid == 18:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoxOCwiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9.UAeTggQxUjAHQ1WL" \
                         "-twel0Knri9s2kRtWGMOQTfd6Yo "
        elif self.userid == 20:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoyMCwiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9.GViAbtO7C" \
                         "-ysJMOpvsH5pW3e0fIpEfzqTJHDD4Yv2eg "
        elif self.userid == 21:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjoyMSwiaWF0IjoxNjY5NDQ1NTAwLCJleHAiOjI1MzM0NDU1MDB9" \
                         ".84QmGMHf9SlCtXGHXBsOiymUfBP_RKnq4nNGetQUL-4 "
        #given by prabhat for testing orderid in api response
        elif self.userid == 100:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjozMTAzOCwiaWF0IjoxNjcwMzM0Njc3LCJleHAiOjI1MzQzMzQ2Nzd9.L_FJ4Cm_vLOcUBhB54" \
                         "-u9xh50Ctbs1cJd3DOv-YAnqQ "
        #my test api token
        elif self.userid == 101:
            self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
                         ".eyJ1c2VyX2lkIjozNTgxNiwiaWF0IjoxNjU2MjM1OTc4LCJleHAiOjI1MjAyMzU5Nzh9" \
                         ".FNpWIrzZ5pcCaH3wUXx3FZInt22nYLg9nrPYZx1rRPA "

        else:
            print("Invalid userid or test/production api")

    def tradex_caller(self, url_suffix, body={}, retry_attempts=3, retry_wait_secs=3):
        # print(f"request from {self.userid} in api-{self.api_type}")
        # my token
        # token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
        #         ".eyJ1c2VyX2lkIjo0MzE0NzAsImlhdCI6MTY2MzIzMDU2OCwiZXhwIjoyNTI3MjMwNTY4fQ" \
        #         ".ccnt8CFvAaVdapN2EKUEzTPPdudtwwhT8nejIgcIw0M "

        # tokenfor mobile-0931196164 otp322187
        # token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" \
        #         ".eyJ1c2VyX2lkIjoxOTMyOTcsImlhdCI6MTY2NzYzOTI2OSwiZXhwIjoyNTMxNjM5MjY5fQ" \
        #         ".4v8CiA8hFgNBCZO7QVirQMBlEpXRB2oHQ-vbaa3dh0A "


        url = f"https://{self.server_url}/v2/{url_suffix}"
        headers = {'Authorization': self.token}

        i = 0
        while True:
            try:
                response = req.post(url, data=body, headers=headers).json()
                # response = req.post(url, data=body, headers=headers)
                # response = req.post(url, data=body, headers=headers).json()
                # print("wainting 5 sec...")
                # sleep(5)
                return response
            except Exception as e:
                try:
                    response = req.post(url, data=body, headers=headers)
                    print("Response: ", response)
                    print("Exception: ", e)
                    logger.critical(f"API call failed. User{self.userid} Response:{response}, Exception: {e}")
                except Exception as e:
                    print("Unable to fetch response")
                    print("Exception: ", e)
                    logger.critical(f"API call no response,User{self.userid} Exception: {e}")

                sleep(retry_wait_secs)
                i += 1
                if i <= retry_attempts:
                    continue
                else:
                    raise Exception(f"MaxAttempt({retry_attempts}) exhausted. User{self.userid}")

def iso_utc_to_ist(iso_utc_datetime):
    if iso_utc_datetime[-1:] == "Z":
        ist_datetime = dt.datetime.strptime(iso_utc_datetime, "%Y-%m-%dT%H:%M:%S.%fZ")
        ist_datetime = ist_datetime + dt.timedelta(hours=5, minutes=30)
        ist_datetime = ist_datetime.replace(tzinfo=None)
        return ist_datetime.isoformat()
    else:
        "Error: UTC timezone suffix 'Z' not found"


# def _check_response(response):
#     try:
#         status = response["status"]
#     except KeyError:
#         return response
#     else:
#         # logging.debug("something failed.")
#         raise Exception("API call Failed", f"StatusValue: {status}")


if __name__ == "__main__":
    api_obj = ApiCaller()
    resp = api_obj.tradex_caller("mybetsv2", {"eventsStatus": "'A','F'"})
    print(resp)
    print(resp.keys())