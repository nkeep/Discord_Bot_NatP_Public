import psycopg2
import os

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

cur.execute("SELECT * FROM db")
data_list = cur.fetchall()

for data in data_list:
    if data[2] == 1: #is file
        new = data[1].replace("\\", "/")
        new = new.replace("files", "files/db")
        cur.execute(f"UPDATE db SET result='{new}' WHERE name='{data[0]}'")

cur.execute("SELECT * FROM templates")
data_list = cur.fetchall()

for data in data_list:
    new = data[1].replace("\\","/")
    cur.execute(f"UPDATE templates SET filelocation='{new}' WHERE name='{data[0]}'")
