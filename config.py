from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
ADMIN_ID = os.getenv("ADMIN_ID")
POLICY_URL = os.getenv("POLICY_URL")
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH')
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
