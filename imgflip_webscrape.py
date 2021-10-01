from bs4 import BeautifulSoup
import requests
import psycopg2
import os

path_separator = "/"
if os.name == 'nt':
    path_separator = "\\"

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
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(THIS_FOLDER, "data" + path_separator + "db" + path_separator + "build.sql")
with open(path, "r", encoding="utf-8") as script:
    cur.execute(script.read())



for i in range(1,44):
    print(i)
    html_text = requests.get(f'https://imgflip.com/memetemplates?page={i}').text
    soup = BeautifulSoup(html_text, 'lxml')
    titles = soup.find_all('h3', class_='mt-title')
    for title in titles:
        link = title.find('a')
        meme_data = link['href'].split('/')
        if meme_data[2][0].isdigit():
            try:
                id = int(meme_data[2]) #Extra check to see if the whole thing is an int and not just a string that starts with an int
                cur.execute(f"INSERT INTO memes (meme_id, title) VALUES('{meme_data[2]}', '{meme_data[3].replace('-', ' ')}')")
                print("Meme added: " + meme_data[2] + ", " + meme_data[3].replace('-', ' '))
            except Exception as e:
                print(e)
                print(meme_data)
