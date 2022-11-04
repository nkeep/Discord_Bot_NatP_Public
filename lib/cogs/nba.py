from discord.ext.commands import Cog, Command
from discord import Activity, ActivityType
from bs4 import BeautifulSoup
from apscheduler.triggers.cron import CronTrigger
import requests
import datetime
import math
import re
import os

path_separator = "/"
if os.name == 'nt':
    path_separator = "\\"

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

teams_to_watch = ["Milwaukee", "New Orleans", "Brooklyn"]
team_names = ["Bucks", "Pelicans", "Nets"]
is_currently_watching = False

class NBA(Cog):
    def __init__(self, bot):
        self.bot = bot
        # bot.scheduler.add_job(self.check_for_games, CronTrigger(minute="1,16,31,46"))
        bot.scheduler.add_job(self.check_for_games, CronTrigger(minute="*"))

    async def check_for_games(self):
        global is_currently_watching
        if is_currently_watching or datetime.datetime.now().minute in [1,16,31,46]: #Only check every 15 minutes unless a game is happening
            soup = BeautifulSoup(requests.get("https://www.cbssports.com/nba/schedule/").text, "lxml")
            games_table_wrapper = soup.find_all("div", "TableBaseWrapper") 
            upcoming_games = games_table_wrapper[-1] #Current and upcoming games
            
            games_table = upcoming_games.find("table", "TableBase-table")
            games = games_table.find_all("tr", "TableBase-bodyTr")
            
            top_prio_game = math.inf
            top_prio_team = None
            top_prio_score = None
            for game in games:
                cells = game.find_all("td", re.compile("TableBase-bodyTd"))
                team1 = cells[0].find("span", "TeamName").a.text
                team2 = cells[1].find("span", "TeamName").a.text
                score_or_time = cells[2].find("div", "CellGame").a.text
                if re.search("\d{1,2}:\d{2} (am|pm)", score_or_time):
                    continue
                for i in range(len(teams_to_watch)):
                    if teams_to_watch[i] == team1 and i < top_prio_game:
                        top_prio_game = i
                        top_prio_team = team1
                        top_prio_score = score_or_time
                    elif teams_to_watch[i] == team2 and i < top_prio_game:
                        top_prio_game = i
                        top_prio_team = team2
                        top_prio_score = score_or_time

                if top_prio_team and top_prio_score:
                    is_currently_watching = True
                    await self.bot.change_presence(activity=Activity(type=ActivityType.watching, name=team_names[top_prio_game] + " " + score_or_time))
                    break
                else:
                    is_currently_watching = False

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("nba")

async def setup(bot):
    await bot.add_cog(NBA(bot))