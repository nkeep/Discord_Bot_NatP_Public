from discord.ext.commands import Cog
from discord.ext.commands import command
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

import pexpect

from ..db import db

server_status = 0


class MC(Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.scheduler.add_job(self.check_status, CronTrigger(minute='0,15,30,45'))

        global server_status
        try:
            child = pexpect.spawn('sh', timeout=2)
            child.expect([pexpect.TIMEOUT,'#'])
            child.sendline('screen -r')
            # child.expect('> ') #Works with paper
            # Need this for reg server.jar
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print(current_time)

            one_second_after = current_time[-2:]
            size = len(current_time)
            time_one_second_later = current_time[:size-2] + one_second_after
            child.sendline('\n')
            child.expect(current_time + ".*|" + time_one_second_later + ".*", timeout=5)
            #End

            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print(current_time)

            one_second_after = current_time[-2:]
            size = len(current_time)
            time_one_second_later = current_time[:size-2] + one_second_after

            child.sendline('list')
            child.expect(current_time + ".*|" + time_one_second_later + ".*", timeout=5) #If we are in mc server then this will match and will set server_status to 1

            server_status = 1
            child.sendline('\001d')
            child.terminate()
        except:
            pass


    async def check_status(self):
        global server_status
        if server_status == 0:
            pass
        else:
            child = pexpect.spawn('sh')
            child.expect([pexpect.TIMEOUT,'#'])
            child.sendline('screen -r')
            child.expect([pexpect.TIMEOUT, '>'])

            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")

            child.sendline('list')
            child.expect(current_time + ".*", timeout=5)

            list = child.after.decode().split("There are ")
            if list[1][0] == "0": #No one is online, shutdown server
                child.sendline('stop')
                server_status = 0
            child.sendline('\001d')
            child.terminate()


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

                child.sendline('cd /home/nkeep/minecraft/minecraft_1_18_experimental/')
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
                child = pexpect.spawn('sh', timeout=2)
                child.expect([pexpect.TIMEOUT,'#'])
                child.sendline('screen -r')
                child.expect([pexpect.TIMEOUT, '>'])

                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                print(current_time)

                one_second_after = current_time[-2:]
                size = len(current_time)
                time_one_second_later = current_time[:size-2] + one_second_after

                child.sendline('list')
                child.expect(current_time + ".*|" + time_one_second_later + ".*", timeout=5)

                list = child.after.decode().split("online:")
                child.sendline('\001d')
                child.terminate()
                no_players = list[0].split("There are ")
                if no_players[1][0] == "0": #No one is online, shutdown server
                    await ctx.send("No players online")
                else:
                    await ctx.send("Players online: " + list[1].strip('>'))
            except:
                await ctx.send("Failed to get list")
        else:
            await ctx.send("Server must be running to use this command. Use mcstart to start server")


    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("mc")

async def setup(bot):
	await bot.add_cog(MC(bot))
