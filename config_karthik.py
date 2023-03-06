#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os


BASE_URL = "https://apiv2.api-cricket.com/cricket/"
API_KEY = "ec73e61f126c11e2eb3cec97ca05c9de32054875a7285697c0901b51ce37bc65"

SHEET_ID = "1IIuYXF9OEz9DM2v0qIvKWHm_h5rGSOwD8_K2PWkPjeE"
SHEET_NAME = "Cricket Schedule"

event_creation_auth_token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXNoYm9hcmRfdXNlcl9pZCI6MiwiaWF0IjoxNjYzMjQ1MDAzLCJleHAiOjI1MjcyNDUwMDN9.IkAXy0jKtbWRzMTYMQzB-lMFrO51aXnHz7t3WPQsgFQ'

event_creation_api_url = "https://api.tradexapp.co/v2/createprobe"


event_settlement_auth_token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXNoYm9hcmRfdXNlcl9pZCI6MiwiaWF0IjoxNjYzMjQ1MDAzLCJleHAiOjI1MjcyNDUwMDN9.IkAXy0jKtbWRzMTYMQzB-lMFrO51aXnHz7t3WPQsgFQ'

event_settlement_api_url = "https://api.tradexapp.co/v2/updateprobe"

project_key = 'RS_P_1618253973456818200'
api_key_rz = 'RS5:63a6ed72fd5c53a53acc664e7e261287'

sql_dbname = 'playox'
sql_host = '172.31.10.241'
sql_port = '5432'
sql_user = 'read_write'
sql_password = 'X9JLjXklS8ZHarL268JOKFTM'


sql_host1 =  '172.31.37.108'
sql_port1 = '5432'
sql_user1 =  'postgres_staging'
sql_password1 =  'UIb0FHxlsrUWe82d7gin'
sql_dbname1 = 'playox'


sql_dbname_viz = 'playox'
sql_host_viz = 'analytics.cluster-csf4le3jblm7.ap-south-1.rds.amazonaws.com'
sql_port_viz = '5432'
sql_user_viz = 'analytics'
# sql_password =  os.getenv('DB_PASSWORD')
sql_password_viz = 'x1Py;2]U9Cl-B&=6'

# email_password =  os.getenv('EMAIL_PASSWORD')
email_password = 'qiietdlwcwbmbemo'
email_sender = 'parag@tradexapp.co'
email_receiver_finance = ['kartik@tradexapp.co']
email_receiver = ['kartik@tradexapp.co']