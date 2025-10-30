# python-dotenv is optional for local testing; if it's not installed,
# we silently continue and rely on the environment variables already set.
from dotenv import load_dotenv

import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
ADMIN_ID = os.getenv("ADMIN_ID")
POLICY_URL = os.getenv("POLICY_URL")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]