from discord import Member, ChannelType, File
from discord.ext.commands import Cog
from discord.ext.commands import command, has_permissions
from typing import Optional

from ..db import db

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
            list = db.column(f"SELECT * from db")
            await ctx.send(list)
        except:
            print("dblist command failed")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("db")

def setup(bot):
	bot.add_cog(DB(bot))
