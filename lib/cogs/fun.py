from discord.ext.commands import Cog, command, BadArgument
from discord import Member
from discord.errors import HTTPException
from typing import Optional
from random import choice, randint
import requests
import re
import os

from ..db import db

from config import CATAPI_KEY

class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="hello", aliases=["hi"], hidden=True)
    async def somecommand(self, ctx):
        await ctx.send(f"Hello {ctx.author.mention}!")

    @command(name="dice", aliases=["roll"])
    async def roll_dice(self, ctx, die_string: str):
        dice, value = (int(term) for term in die_string.split("d"))

        if dice <= 25:
            rolls = [randint(1, value) for i in range(dice)]

            await ctx.send(" + ".join([str(r) for r in rolls]) + f" = {sum(rolls)}")
        else:
            await ctx.send("I can't roll that many dice. Please try a lower number.")

    @command(name="slap")
    async def slap_member(self, ctx, member: Member, *, reason: Optional[str] = "no reason"): #member will take either an id or name, etc and figure out who you're talking about, * will combine all trailing argumnents into one
        await ctx.send(f"{ctx.author.display_name} slapped {member.mention} {reason}!")

    @command(name="ye")
    async def ye(self, ctx):
        response = requests.get('https://api.kanye.rest/').json()
        await ctx.send(response['quote'])

    @command(name="cat")
    async def cat(self, ctx):
        response = requests.get(f'https://api.thecatapi.com/v1/images/search', {'x-api-key':CATAPI_KEY}).json()
        await ctx.send(response[0]['url'])

    @command(name="sb")
    async def sb(self, ctx):
        list = db.column("SELECT quote from sb")
        await ctx.send(list[randint(0, len(list))])

    @command(name="funny")
    async def funny(self, ctx): #Select a random 'funny' command from the db
        all_funnies = db.records("SELECT * FROM db WHERE name LIKE 'funny%%'")
        i = randint(0, len(all_funnies) - 1)
        funny = all_funnies[i]
        if funny[2] == 1:
            location = funny[1]
            await ctx.send(file=File(rf'{location}'))
        else:
            await ctx.send(funny[1])

    @Cog.listener("on_message")
    async def on_message(self, message):

        if message.content.startswith('!play') and message.channel.id != 505589070378958850:
            await message.author.kick(reason="Don't type !play in the non bot-shit channel retard")
            await message.channel.send('fuck you')

        elif re.search("update for", message.content, re.IGNORECASE):
            if randint(1,6) == 6:
                await message.channel.send("don't care, didn't ask, plus ratio")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fun")

def setup(bot):
    bot.add_cog(Fun(bot))
