import gspread
import pandas as pd


class Gsheet:
    def __init__(self, category):
        # self.event_id = event_id
        self.sheet = None
        self.event_sheet = None
        self.connect_event_sheet(category)
        self.update_headers()

    def connect_event_sheet(self, category):
        sa = gspread.service_account(filename='tradexdash001_googlekey.json')
        self.sheet = sa.open("AnirudhTradex_PnL_Dashboard2")

        try:
            if category == "btc":
                self.event_sheet = self.sheet.worksheet("Range contracts pnl 5")
            elif category == "betfair":
                self.event_sheet = self.sheet.worksheet("Sports contracts pnl 1")
        except gspread.exceptions.WorksheetNotFound:
            print("Creating new worksheet")
            if category == "btc":
                self.event_sheet = self.sheet.add_worksheet(title="Range contracts pnl 5", rows=2000, cols=50)
            elif category == "betfair":
                self.event_sheet = self.sheet.add_worksheet(title="Sports contracts pnl 1", rows=250, cols=50)

    def update_headers(self):

        self.event_sheet.update('A1:N1', [
            ["EventId", "Date", "Net Pnl", "Closed", "Settled", "IfYesTotal", "IfNoTotal", "IfYesHoldPnl",
             "IfNoHoldPnl", "RealisedYESpnl", "RealisedNOpnl", "TotQtyTraded", "YesQty", "NoQty"]])
        self.event_sheet.format('A1:C1', {'textFormat': {'bold': True}})

    def update_df(self, df):
        self.event_sheet.update([df.columns.values.tolist()] + df.values.tolist())


if __name__ == "__main__":
    gs = Gsheet(7808)
    # gs.update_df(df)
