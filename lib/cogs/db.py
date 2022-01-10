from discord import Member, ChannelType, File
from discord.ext.commands import Cog
from discord.ext.commands import command, has_permissions
from typing import Optional

from ..db import db

import math
import requests
import uuid
import shutil
import os

path_separator = "/"
if os.name == 'nt':
    path_separator = "\\"

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
files = os.path.join(THIS_FOLDER, ".." + path_separator + "files" + path_separator + "db" + path_separator)

class DB(Cog):
    def __init__(self, bot):
    	self.bot = bot

    @command(name="db")
    async def db(self, ctx, first):
        print('db command called')
        try: #Think this is needed for if you delete a record and then call it again (sql query throws error)
            response = db.record(f"SELECT * FROM db WHERE name = '{first}'")
            print(response[1])
            if response:
                if response[2] == 1:
                    location = response[1]
                    await ctx.send(file=File(rf'{location}'))
                else:
                    await ctx.send(response[1])
            else:
                await ctx.send("Command doesn't exist")
        except:
            await ctx.send("Command doesn't exist")

    @command(name="dbadd")
    async def dbadd(self, ctx, first, *, second: Optional[str]):
        if first and second: #text command
            print("something")
            command = db.field(f"SELECT name FROM db WHERE name = '{first}'")
            if not command:
                second = second.replace("'", r"\'")
                db.execute(f"INSERT INTO db VALUES('{first}', E'{second}', 0)")
                db.commit()
                await ctx.send("successfully added command")
            else:
                await ctx.send("command already exists")
        elif first and not second: #check for file
            try:
                url = ctx.message.attachments[0].url
                if url[0:26] == "https://cdn.discordapp.com":
                    r = requests.get(url, stream=True)
                    fileName = str(uuid.uuid4()) + "." + str(url.split('.')[-1])
                    with open(files + fileName, 'wb') as out_file:
                        shutil.copyfileobj(r.raw, out_file)
                        db.execute(f"INSERT INTO db VALUES('{first}','{files + fileName}', 1)")
                        db.commit()
                        await ctx.send("successfully added command")
            except:
                print("upload failed")
        else:
            await ctx.send("Invalid syntax")

    @command(name="dbremove")
    async def dbremove(self, ctx, first):
        command = db.field(f"SELECT * FROM db WHERE name = '{first}'")
        if command:
            db.execute(f"DELETE FROM db WHERE name = '{first}'")
            await ctx.send(f"Successfully deleted {first}")
        else:
            await ctx.send("Command doesn't exist")

    @command(name="dbupdate")
    async def dbupdate(self, ctx, first, second: Optional[str]):
        if first and second:
            db.execute(f"UPDATE db SET name='{first}', result='{second}', isfile=0 WHERE name='{first}'")
            db.commit()
            await ctx.send(f"Successfully updated {first}")

        elif first and not second:
            try:
                url = ctx.message.attachments[0].url
                if url[0:26] == "https://cdn.discordapp.com":
                    r = requests.get(url, stream=True)
                    fileName = str(uuid.uuid4()) + "." + str(url.split('.')[-1])
                    with open(file + fileName, 'wb') as out_file:
                        shutil.copyfileobj(r.raw, out_file)
                        db.execute(f"UPDATE db SET name='{first}', {files + fileName}, isfile=1 WHERE name='{first}'")
                        db.commit()
                        await ctx.send(f"successfully updated {first}")
            except:
                print("upload failed")

        else:
            await ctx.send("Invalid syntax")

    @command(name="dblist")
    async def dblist(self, ctx):
        try:
            #Old code
            #list = str(db.column(f"SELECT * from db"))
            list = str(db.column("SELECT name FROM db WHERE name !~ '(funny$|funny\d+)' AND name !~ '(who$|who\d+)'"))
            for i in range(math.ceil(len(list)/2000)): #if the list is more than 2k chars, split it up into multiple messages
                await ctx.send(list[i*2000:(i+1)*2000])

            #await ctx.send(str(list))
        except:
            print("dblist command failed")

    @command(name="funnylist")
    async def funnylist(self, ctx):
        print('something')
        try:
            list = db.column("SELECT REGEXP_REPLACE(name, 'funny', '') FROM db WHERE name ~ '(funny$|funny\d+)' ORDER BY CAST (REGEXP_REPLACE(name, 'funny', '0') AS int)")
            output = list[1] + "-"
            prev_num = -1
            new_range = False
            for item in list:
                num = int("0" + item)

                if new_range and num - prev_num == 1:
                    output += "-"
                    new_range = False

                if not num - prev_num == 1 and not new_range:
                    output += str(prev_num) + ", "
                    new_range = True

                elif num-prev_num != 1 and new_range:
                    output += str(prev_num) + ", "

                prev_num = num
            
            output += (str(list[len(list)-1]))
            print(output)
            await ctx.send(output)
        except Exception as e:
            print(e)

    @command(name="wholist")
    async def wholist(self, ctx):
        try:
            list = db.column("SELECT REGEXP_REPLACE(name, 'who', '') FROM db WHERE name ~ '(who$|who\d+)' ORDER BY CAST (REGEXP_REPLACE(name, 'who', '0') AS int);")
            output = list[1] + "-"
            prev_num = -1
            new_range = False
            for item in list:
                num = int("0" + item)

                if new_range and num - prev_num == 1:
                    output += "-"
                    new_range = False

                if not num - prev_num == 1 and not new_range:
                    output += str(prev_num) + ", "
                    new_range = True

                elif num-prev_num != 1 and new_range:
                    output += str(prev_num) + ", "

                prev_num = num
            
            output += (str(list[len(list)-1]))
            await ctx.send(output)
        except:
            print("wholist command failed")

    @command(name="addfunny")
    async def addfunny(self, ctx, *, second: Optional[str]):
        try:
            list = db.column("SELECT REGEXP_REPLACE(name, 'funny', '') FROM db WHERE name ~ '(funny$|funny\d+)' ORDER BY CAST (REGEXP_REPLACE(name, 'funny', '0') AS int);")
            prev_num = -1
            next_num = -1
            for item in list:
                num = int("0" + item)
                if not num - prev_num == 1:
                    next_num = prev_num + 1
                    break
                prev_num =  num
            if next_num == -1 and len(list) > 0:
                next_num = int((list[len(list)-1])) + 1
            elif len(list) == 0:
                next_num = 0

            await ctx.invoke(self.bot.get_command('dbadd'), first='funny' + str(next_num), second=second)
        except Exception as e:
            print(e)

    @command(name="addwho")
    async def addwho(self, ctx, *, second: Optional[str]):
        try:
            list = db.column("SELECT REGEXP_REPLACE(name, 'who', '') FROM db WHERE name ~ '(who$|who\d+)' ORDER BY CAST (REGEXP_REPLACE(name, 'who', '0') AS int);")
            prev_num = -1
            next_num = -1
            for item in list:
                num = int("0" + item)
                if not num - prev_num == 1:
                    next_num = prev_num + 1
                    break
                prev_num =  num
            if next_num == -1 and len(list) > 0:
                next_num = int((list[len(list)-1])) + 1
            elif len(list) == 0:
                next_num = 0

            await ctx.invoke(self.bot.get_command('dbadd'), first='who' + str(next_num), second=second)
        except Exception as e:
            print(e)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("db")

def setup(bot):
	bot.add_cog(DB(bot))
