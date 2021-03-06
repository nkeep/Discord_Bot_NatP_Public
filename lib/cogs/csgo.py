from discord.ext.commands import Cog
from discord.ext.commands import command
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import hltv_module as hltv
import json

from ..db import db

important_matches = []

important_teams = [b"Liquid", b"Kings of Content", b"Evil Geniuses"]

class CSGO(Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.scheduler.add_job(self.look_for_matches, CronTrigger(minute="14,29,44,59"))
        self.remove_old_matches()
        self.get_db_matches()
        self.look_for_matches()

    def get_db_matches(self): #Used to repopulate the important matches list if bot is restarted
        global important_matches
        all_matches = db.records(f"SELECT * FROM csgo")
        for match in all_matches:
            id = match[0]
            match = json.loads(match[1])
            self.bot.scheduler.add_job(self.notify_match, CronTrigger(minute=match["time"][3:5], hour=match["time"][0:2], day=match["date"][8:10], month=match["date"][5:7]), [id], id=str(id) + "csgo")
            important_matches.append(match.copy())
        print(important_matches)


    def look_for_matches(self):
        global important_matches

        matches = hltv.get_matches()
        for match in matches:
            if match["team1"] in important_teams or match["team2"] in important_teams:
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
                    self.bot.scheduler.add_job(self.notify_match, CronTrigger(minute=match["time"][3:5], hour=match["time"][0:2], day=match["date"][8:10], month=match["date"][5:7]), [id], id=str(id) + "csgo")

    async def notify_match(self, id):
        global important_matches
        if self.verify_match(id):
            match = db.record(f"SELECT * FROM csgo WHERE id = {id}")
            data = json.loads(match[1])
            db.execute(f"DELETE FROM csgo WHERE id = '{id}'") #remove from db
            channel = self.bot.get_channel(497223372355272714) #bot channel in ss gang
            self.bot.scheduler.remove_job(str(id) + "csgo") #Remove the job
            important_matches.pop(0) #remove from list
            await channel.send(f"New CSGO match, {data['team1']} vs {data['team2']} <@!143919895694802944>")

    def remove_old_matches(self): #This function looks at past database entries and removes any that have already passed but for some reason are still present
        matches = db.records(f"SELECT * FROM csgo")
        for match in matches:
            data = json.loads(match[1])
            time = datetime.strptime(data["date"] + " " + data["time"], '%Y-%m-%d %H:%M')
            if time < datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M'):
                db.execute(f"DELETE FROM csgo WHERE id = {match[0]}")

    def verify_match(self, id): #This function is used right before someone would be notified for a match since sometimes hltv times change depending on schedules, so it will only notify if the match is still starting at the time in the database
        current_match = db.record(f"SELECT * FROM csgo WHERE id = {id}")
        data = json.loads(current_match[1])
        matches = hltv.get_matches()
        for match in matches:
            if match["team1"].decode() == data["team1"] and match["team2"].decode() == data["team2"]:
                #convert to CST
                print("found the match")
                given_time = datetime.strptime(match["date"] + " " + match["time"], '%Y-%m-%d %H:%M')
                final_time = given_time - timedelta(hours=7)
                match["date"] = final_time.date().strftime('%Y-%m-%d')
                match["time"] = final_time.time().strftime("%H:%M") #24 hour clock

                if match["date"] == data["date"] and match["time"] == data["time"]:
                    print("match is still the same")
                    return True

                print("match time changed")
                db.execute(f"DELETE FROM csgo WHERE id = {id}")
                return False



    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("csgo")

async def setup(bot):
	await bot.add_cog(CSGO(bot))
