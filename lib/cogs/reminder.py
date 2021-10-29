from discord.ext.commands import Cog, command, BadArgument
from discord import Member, ChannelType
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta

from ..db import db
import re


class Reminder(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.get_db_reminders()

    def get_db_reminders(self):
        all_reminders = db.records("SELECT * FROM reminders")
        #convert to a datetime, see if it's already passed, if so delete, otherwise add job
        now = datetime.now()
        for reminder in all_reminders:
            time = datetime(reminder[1], reminder[2], reminder[3], reminder[4], reminder[5])
            if time < now:
                db.execute(f"DELETE FROM reminders WHERE id = '{reminder[0]}'")
            else:
                self.bot.scheduler.add_job(self.notify_reminder, CronTrigger(minute=reminder[5], hour=reminder[4], day=reminder[3], month=reminder[2], year=reminder[1]), [reminder[0]], id=str(reminder[0]))


    @command(name="regreminderchannel")
    async def regreminderchannel(self, ctx):
        if not ctx.channel.type is ChannelType.private:
            guild = db.record(f"SELECT * FROM guilds WHERE GuildID = '{ctx.guild.id}'")
            if guild:
                db.execute(f"UPDATE guilds SET reminderchannel = '{ctx.channel.id}' WHERE GuildID = '{guild[0]}'")
            else:
                db.execute(f"INSERT INTO guilds VALUES('{ctx.guild.id}', '+', '{ctx.channel.id}')")
            await ctx.send("Set reminder channel")
        else:
            await ctx.send("Cannot set reminder channel in a DM")

    @command(name="remindme")
    async def remindme(self, ctx, *, data):
        arr = data.split()
        time_data = ' '.join(arr[:3]) + " " #get the first 3 words

        channel = ""
        try:
            channel = db.record(f"SELECT reminderchannel FROM guilds WHERE guild = '{ctx.guild.id}'")
        except:
            channel = ctx.channel.id

        if re.match("^\d{1,2}(\/|\-)\d{1,2}", arr[0]) and re.match("^\d{1,2}:\d{1,2}", arr[1]):
            try:
                date = arr[0]
                time = arr[1]
                split_date = re.findall('\d+', date)
                split_time = re.split(':', time)
                if "pm" in split_time[1]:
                    split_time[0] = str(int(split_time[0]) + 12)
                split_time[1] = split_time[1].strip("am").strip("pm")

                month = split_date[0]
                day = split_date[1]
                year = None
                if len(split_date) == 3:
                    year = split_date[2]
                else:
                    year = datetime.now().year
                hour = split_time[0]
                minute = split_time[1]
                reminder = data.split(' ', 2)
                id = db.record(f"INSERT INTO reminders (year, month, day, hour, minute, reminder, username, channel) VALUES('{year}', '{month}', '{day}', '{hour}', '{minute}', '{reminder[2]}', '{ctx.author.id}', '{channel}') RETURNING id")
                id = id[0]
                self.bot.scheduler.add_job(self.notify_reminder, CronTrigger(minute=int(minute), hour=int(hour), day=int(day), month=int(month), year=int(year)), [id], id=str(id))

                await ctx.send(f"Successfully added reminder for {month}/{day}/{year} at {hour}:{minute}")
            except Exception as e:
                print(e)
        #If it matches some form of days, hours, minutes EX: 12d 4h 30m
        elif re.match("\d+(d|day|days) ", time_data, re.IGNORECASE) or re.match("\d+(h|hour|hours) ", time_data, re.IGNORECASE) or re.match("\d+(m|minute|minutes) ", time_data, re.IGNORECASE):
            try:
                day = re.search("\d+(d|day|days) ", time_data, re.IGNORECASE)
                num_params = 0
                if day:
                    day = re.search("\d+", day.group())
                    day = day.group()
                    num_params += 1
                else:
                    day = "0"
                hour = re.search("\d+(h|hour|hours) ", time_data, re.IGNORECASE)
                if hour:
                    hour = re.search("\d+", hour.group())
                    hour = hour.group()
                    num_params += 1
                else:
                    hour = "0"
                minute = re.search("\d+(m|minute|minutes) ", time_data, re.IGNORECASE)
                if minute:
                    minute = re.search("\d+", minute.group())
                    minute = minute.group()
                    num_params += 1
                else:
                    minute = "0"
                reminder = ' '.join(data.split()[num_params:]) #Grab everything that's not part of the time

                now = datetime.now()
                rtime = now + timedelta(hours=int(hour), minutes=int(minute), days=int(day))
                id = db.record(f"INSERT INTO reminders (year, month, day, hour, minute, reminder, username, channel) VALUES('{rtime.year}', '{rtime.month}', '{rtime.day}', '{rtime.hour}', '{rtime.minute}', '{reminder}', '{ctx.author.id}', '{channel}') RETURNING id")
                id = id[0]
                self.bot.scheduler.add_job(self.notify_reminder, CronTrigger(minute=rtime.minute, hour=rtime.hour, day=rtime.day, month=rtime.month, year=rtime.year), [id], id=str(id))
                await ctx.send(f"Successfully added reminder for {rtime.month}/{rtime.day}/{rtime.year} at {rtime.hour}:{rtime.minute}")
            except Exception as e:
                await print(e)
        else:
            await ctx.send("Invalid format")

    async def notify_reminder(self, id):
        reminder = db.record(f"SELECT * FROM reminders WHERE id = '{id}'")
        channel = self.bot.get_channel(int(reminder[8]))
        await channel.send(f"<@!{reminder[7]}> {reminder[6]}")
        try:
            self.bot.scheduler.remove_job(str(id)) #Remove the job
        except:
            pass
        db.execute(f"DELETE FROM reminders WHERE id = '{id}'") #Remove from db

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("reminder")

def setup(bot):
    bot.add_cog(Reminder(bot))
