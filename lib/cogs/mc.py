from discord.ext.commands import Cog
from discord.ext.commands import command
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

import pexpect
import re

from ..db import db

server_status = 0
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class MC(Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.scheduler.add_job(self.check_status, CronTrigger(minute='0,15,30,45'))

        global server_status
        try:
            status = (pexpect.run('/home/nkeep/mcrcon/mcrcon -H 0.0.0.0 -p bananabread -w 5 "list"')).decode()
            p = re.compile("Connection failed")
            if p.match(status): #Server is not live
                server_status = 0
            else:
                server_status = 1
        except:
            pass


    async def check_status(self):
        global server_status
        if server_status == 0:
            return
        else:
            players = pexpect.run('/home/nkeep/mcrcon/mcrcon -H 0.0.0.0 -p bananabread -w 5 "list"')
            players = players.decode()
            p = re.compile("There are (\d+) of")
            m = p.match(players)
            online_players = m.group(1)
            if online_players == "0": #No one is online, shutdown server
                pexpect.run('/home/nkeep/mcrcon/mcrcon -H 0.0.0.0 -p bananabread -w 5 "say Server is stopping due to inactivity" save-all stop')
                server_status = 0

    @command(name="mcstart")
    async def mcstart(self, ctx):
        global server_status
        if server_status == 0:
            try:
                await ctx.send("Starting mc server")
                child = pexpect.spawn('sh')
                child.expect([pexpect.TIMEOUT,'#'])

                child.sendline('screen -r')
                child.expect([pexpect.TIMEOUT, '#'])

                child.sendline('cd /home/nkeep/minecraft/minecraft_1_19_paper/')
                child.expect([pexpect.TIMEOUT, '#'])

                child.sendline('bash start.sh')
                child.expect('Done', timeout = 60)

                server_status = 1
                child.sendline('\001d')
                child.terminate()

                await ctx.send("mc server started")
            except:
                await ctx.send("Failed to start server")
        else:
            await ctx.send("Sever already running")

    @command(name="mclist")
    async def mclist(self, ctx):
        global server_status
        if server_status == 1:
            try:
                players = pexpect.run('/home/nkeep/mcrcon/mcrcon -H 0.0.0.0 -p bananabread -w 5 "list"')
                players = players.decode()
                p = re.compile("There are (\d+) of.*online: (.*)")
                m = p.match(players)
                num_players = m.group(1)
                online_players = m.group(2)
                online_players = ansi_escape.sub('',online_players)
                if num_players == "0": 
                    await ctx.send("No players online")
                else:
                    await ctx.send(num_players + " Players online: " + online_players)
            except:
                await ctx.send("Failed to get list")
        else:
            await ctx.send("Server must be running to use this command. Use mcstart to start server")

    @command(name="mcweatherclear", aliases=["mcwc", "mctoggledownfall"])
    async def mcweatherclear(self, ctx):
        await mc_command(ctx, "weather clear")

    @command(name="mctimeset0", aliases=["mcts0", "mctimesetday", "mctsd"])
    async def mctimeset0(self, ctx):
        await mc_command(ctx, "time set 0")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("mc")

async def setup(bot):
	await bot.add_cog(MC(bot))

async def mc_command(ctx, command):
    global server_status
    if server_status == 1:
        try:
            pexpect.run(f'/home/nkeep/mcrcon/mcrcon -H 0.0.0.0 -p bananabread -w 5 "{command}"')
        except:
            await ctx.send("Failed to clear weather")
    else:
        await ctx.send("Server must be running to use this command. Use mcstart to start server")