import gspread
import pandas as pd

class Gsheet:
    def __init__(self, event_id):
        self.event_id = event_id
        self.sheet = None
        self.event_sheet = None
        self.connect_event_sheet()
        self.update_headers()

    def connect_event_sheet(self):
        sa = gspread.service_account(filename='tradexdash001_googlekey.json')
        self.sheet = sa.open("AnirudhTradex_PnL_Dashboard")

        try:
            self.event_sheet = self.sheet.worksheet(str(self.event_id))
        except gspread.exceptions.WorksheetNotFound:
            print("Creating new worksheet")
            self.event_sheet = self.sheet.add_worksheet(title=str(self.event_id), rows=100, cols=50)

    def update_headers(self):
        self.event_sheet.update('A1',"Realised Scalping PnL")
        self.event_sheet.update('E1', "Total Realised Scalping PnL")
        self.event_sheet.update('H1', "Total UnRealised Holding PnL")
        self.event_sheet.update('J1', "Total PnL")
        self.event_sheet.update('A2:K2',[['Date','Yes','No','Total','Yes','No','Total','If Yes','If No','If Yes','If No']])

        self.event_sheet.format('A1:K2', {'textFormat': {'bold': True}})

    def update_df(self, df):
        self.event_sheet.update([df.columns.values.tolist()] + df.values.tolist())

if __name__ == "__main__":
    gs = Gsheet(7808)
    # gs.update_df(df)
