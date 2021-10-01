import pandas as pd
import psycopg2
import os
import re

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
from config import PSQL_PASSWORD, PSQL_UNAME


conn = psycopg2.connect(
    host="localhost",
    database="discord_bot",
    user=PSQL_UNAME,
    port="5432",
    password=PSQL_PASSWORD)

conn.autocommit = True

cur = conn.cursor()

csv = os.path.join(THIS_FOLDER, 'spongequotes.csv')

spongequotes = pd.read_csv(csv)

# print(spongequotes["Quote"])

for quote in spongequotes["Quote"]:
    quote = quote.replace("'", r"\'")
    cur.execute(f"INSERT INTO sb (quote) VALUES(E'{quote}')") #Need this E string bullshit to insert string with apostrophe
    # print(quote)
