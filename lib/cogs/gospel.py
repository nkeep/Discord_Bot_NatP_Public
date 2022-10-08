from discord.ext.commands import Cog, command
from bs4 import BeautifulSoup
from enum import Enum

import requests
import datetime
import calendar
import math
import os

path_separator = "/"
if os.name == 'nt':
    path_separator = "\\"

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

class Reading(Enum):
    FIRST = "Reading 1 "
    SECOND = "Reading 2 "
    GOSPEL = "Gospel "

class Gospel(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="gospel")
    async def gospel(self, ctx):
        reading = readings(Reading.GOSPEL)
        for i in range(math.ceil(len(reading)/2000)): #if the reading is more than 2k chars, split it up into multiple messages
            await ctx.send(reading[i*2000:(i+1)*2000])

    @command(name="firstreading", aliases=["1streading"], hidden=True)
    async def firstreading(self, ctx):
        reading = readings(Reading.FIRST)
        for i in range(math.ceil(len(reading)/2000)):
            await ctx.send(reading[i*2000:(i+1)*2000])

    @command(name="secondreading", aliases=["2ndreading"], hidden=True)
    async def secondreading(self, ctx):
        reading = readings(Reading.SECOND)
        for i in range(math.ceil(len(reading)/2000)):
            await ctx.send(reading[i*2000:(i+1)*2000])

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("gospel")

def setup(bot):
    bot.add_cog(Gospel(bot))

def get_next_sunday():
    today = datetime.date.today()
    sunday = today + datetime.timedelta( (calendar.SUNDAY-today.weekday()) % 7 )
    return sunday.strftime("%m%d%y")

def readings(reading: Reading):
    soup = BeautifulSoup(requests.get(f"https://bible.usccb.org/bible/readings/{get_next_sunday()}.cfm").text, "lxml")

    reading_title = soup.find("h3", class_="name", string=reading.value)

    if not reading_title:
        reading_title = soup.find("h3", class_="name", string=reading.value.replace("1","I").replace("2","II"))

    book=reading_title.find_next_sibling().get_text()
    reading = reading_title.parent.find_next_sibling()
    for br in reading.find_all("br"):
        br.replace_with("\n")

    return ("**" + book.strip() + "**" + "\n" + reading.get_text().strip())