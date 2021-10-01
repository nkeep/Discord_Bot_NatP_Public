from Google import Create_Service
import psycopg2
import os

from config import PSQL_PASSWORD, google_sheets_id, PSQL_UNAME



conn = psycopg2.connect(
    host="localhost",
    database="discord_bot",
    user=PSQL_UNAME,
    port="5432",
    password=PSQL_PASSWORD)

conn.autocommit = True
cur = conn.cursor()

API_NAME = 'sheets'
API_VERSION = 'v4'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

response = service.spreadsheets().values().get(
    spreadsheetId = google_sheets_id,
    majorDimension='ROWS',
    range='Spongequotes!A:A'
).execute()

cur.execute("DROP TABLE sb")
cur.execute("""
    CREATE TABLE IF NOT EXISTS sb(
	id BIGSERIAL,
	quote text PRIMARY KEY)
    """)

for quote in response['values']:
    quote = quote.replace("'", r"\'")
    cur.execute(f"INSERT INTO sb (quote) VALUES(E'{quote}')")
