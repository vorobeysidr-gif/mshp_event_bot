import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import SCOPES, SPREADSHEET_ID

def get_sheet():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SPREADSHEET_ID).sheet1

def append_lead_row(data):
    sheet = get_sheet()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([
        data.get("name", ""),
        data.get("phone", ""),
        data.get("age", ""),
        data.get("is_mshp_student", ""),
        data.get("time", ""),
        timestamp
    ], value_input_option="USER_ENTERED")