import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ✅ Load credentials directly from the GitHub secret
service_account_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

# === CONFIG ===
SPREADSHEET_ID = "1JHey-L5auJNllgxEQvOg_QkBZ6FQhYFrG950SMaT37Q"  # example
SHEET_NAME = "Pickleball Response"
COLUMN_HEADER = "What time slots would you like to book?"
OUTPUT_FILE = "slots.json"

# === READ SHEET ===
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=SHEET_NAME
).execute()

values = result.get("values", [])
if not values:
    print("❌ No data found in sheet.")
    exit()

# First row is headers
headers = values[0]
rows = values[1:]

# Find index of the desired column
try:
    col_index = headers.index(COLUMN_HEADER)
except ValueError:
    print(f"❌ Column '{COLUMN_HEADER}' not found.")
    exit()

# Get the last row’s slot responses
last_row = rows[-1]
slots_raw = last_row[col_index]

# Responses like: "19:00 - 20:00, 20:00 - 21:00"
slots = [s.strip().strip('"') for s in slots_raw.split(",")]

# Save to slots.json
with open(OUTPUT_FILE, "w") as f:
    json.dump({"slots": slots}, f, indent=2)

print(f"✅ Saved slots to {OUTPUT_FILE}: {slots}")
