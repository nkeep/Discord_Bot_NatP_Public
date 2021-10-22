from discord.ext.commands import Cog
from discord.ext.commands import command
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import hltv_module as hltv
import json

from ..db import db

important_matches = []

class CSGO(Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.scheduler.add_job(self.look_for_matches, CronTrigger(hour="0", minute="0"))
        self.get_db_matches()
        self.look_for_matches()

    def get_db_matches(self): #Used to repopulate the important matches list if bot is restarted
        global important_matches
        all_matches = db.records(f"SELECT * FROM csgo")
        for match in all_matches:
            id = match[0]
            match = json.loads(match[1])
            self.bot.scheduler.add_job(self.notify_match, CronTrigger(minute=match["time"][3:5], hour=match["time"][0:2], day=match["date"][8:10], month=match["date"][5:7]), id=str(id))
            important_matches.append(match.copy())
        print(important_matches)


    def look_for_matches(self):
        global important_matches

        matches = hltv.get_matches()
        for match in matches:
            if match["team1"] == b"Liquid" or match["team2"] == b"Liquid":
                #convert bytes like objects to strings
                match["event"] = match["event"].decode()
                match["team1"] = match["team1"].decode()
                match["team2"] = match["team2"].decode()
                #convert to CST
                time_str = match["date"] + " " + match["time"]
                date_format_str = '%Y-%m-%d %H:%M'
                given_time = datetime.strptime(time_str, date_format_str)
                final_time = given_time - timedelta(hours=7)

                match["date"] = final_time.date().strftime('%Y-%m-%d')
                match["time"] = final_time.time().strftime("%H:%M") #24 hour clock
                if match not in important_matches:
                    important_matches.append(match.copy())
                    db.execute(f"INSERT INTO csgo (data) VALUES('{json.dumps(match)}')")
                    id = db.field(f"SELECT id FROM csgo WHERE data = '{json.dumps(match)}'")
                    self.bot.scheduler.add_job(self.notify_match, CronTrigger(minute=match["time"][3:5], hour=match["time"][0:2], day=match["date"][8:10], month=match["date"][5:7]), id=str(id))

    async def notify_match(self):
        global important_matches
        match = db.record(f"SELECT * FROM csgo")
        id = match[0]
        data = json.loads(match[1])
        db.execute(f"DELETE FROM csgo WHERE id = '{id}'") #remove from db
        channel = self.bot.get_channel(497223372355272714) #bot channel in ss gang
        self.bot.scheduler.remove_job(str(id)) #Remove the job
        important_matches.pop(0) #remove from list
        await channel.send(f"New CSGO match, {data['team1']} vs {data['team2']} <@!143919895694802944>")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("csgo")

def setup(bot):
	bot.add_cog(CSGO(bot))
