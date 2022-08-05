from asyncio import sleep
from datetime import datetime
from glob import glob
from random import randint

import discord
from discord import Forbidden, HTTPException, ui, app_commands
from discord import Intents, ClientUser
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound, BadArgument, MissingRequiredArgument
from discord.ext.commands import when_mentioned_or, command, has_permissions
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import os

from ..db import db
from ..groups import db as slashdb


from config import token, default_prefix, path_separator

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
cogs = os.path.join(THIS_FOLDER, ".." + path_separator + "cogs" + path_separator + "*.py")
groups = os.path.join(THIS_FOLDER, ".." + path_separator + "groups" + path_separator + "*.py")
print(cogs)
OWNER_IDS = [143919895694802944]
COGS = [path.split(path_separator)[-1][:-3] for path in glob(cogs)]
GROUPS = [path.split(path_separator)[-1][:-3] for path in glob(groups)]
print(COGS)
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument)

def get_prefix(bot, message):
    prefix=""
    try:
        prefix = db.field(f"SELECT Prefix FROM guilds WHERE GuildID = {message.guild.id}")
    except:
        prefix = default_prefix
    if not prefix:
        prefix = default_prefix
    print(prefix)
    return when_mentioned_or(prefix)(bot, message)

class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"{cog} cog ready")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])

class Bot(BotBase):
    def __init__(self):
        self.ready = False
        self.cogs_ready = Ready()
        self.guild = None
        self.scheduler = AsyncIOScheduler()

        db.autosave(self.scheduler)

        intents = Intents.all()
        intents.message_content = True

        super().__init__(
        command_prefix=get_prefix,
        ownder_ids = OWNER_IDS,
        intents=intents,
        )

    async def setup(self):
        print(COGS)
        for cog in COGS:
            await self.load_extension(f"lib.cogs.{cog}")
            print(f"{cog} cog loaded")
        print("setup complete")

        self.tree.add_command(slashdb.db(self), guild=discord.Object(id=533019434491576323))

        await self.tree.sync(guild=discord.Object(id=533019434491576323))
        await self.tree.sync(guild=discord.Object(id=220180151315595264))
        await self.tree.sync(guild=discord.Object(id=484582649965576199))

        print("added group")

    def run(self, version):
        self.VERSION = version
        print("running setup")
        # self.setup()

        self.TOKEN = token

        print("running bot...")
        super().run(self.TOKEN, reconnect=True)

    async def print_message(self):
        pass

    async def update_pfp(self):
        pfps = os.path.join(THIS_FOLDER, ".." + path_separator + "pfps" + path_separator)
        rand = randint(0,10)
        pic = "nat" + str(rand) + ".jpg"
        print(pfps + pic)
        with open(pfps + pic, 'rb') as image:
            await self.user.edit(avatar=image.read())

    async def on_connect(self):
        await self.setup()
        print("bot connected")

    async def on_disconnect(self):
        print("bot disconnected")

    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            await args[0].send("Something went wrong.")

        raise

    async def on_command_error(self, ctx, exc):

        if any([isinstance(exc, error) for error in IGNORE_EXCEPTIONS]):

            pass

        elif isinstance(exc, CommandNotFound):
            await ctx.send("Hey pal, you just blow in from stupid town?")
            #pass

        elif isinstance(exc, BadArgument):
            pass
        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send("One or more required arguments are missing.")
        elif isinstance(exc.original, HTTPException):
            await ctx.send("Unable to send message")
        elif isinstance(exc.original, Forbidden):
            await ctx.send("I do not have permission to do that")
        else:
            raise exc

    async def on_ready(self):
        if not self.ready:

            self.scheduler.add_job(self.update_pfp, CronTrigger(minute='0,15,30,45'))
            self.scheduler.start()
            #self.guild = self.get_guild()

            while not self.cogs_ready.all_ready():
                await sleep(0.5)

            self.ready = True
            print("bot ready")
        else:
            print("bot reconnected")

    async def on_message(self, message):
        if not message.author.bot: #ignores other bots
            if not message.author.id == 143865454212022272 and not message.author.id == 143863189405302784:
                await self.process_commands(message)

class MS_Bug(ui.Modal, title="MS Bug Report"):
    application = ui.TextInput(label = "Application", style=discord.TextStyle.short, placeholder="Which of Microsoft's shitty products")
    description = ui.TextInput(label="Description", style=discord.TextStyle.long, placeholder="A description of the bug")
    due_date = ui.TextInput(label="Due Date", style=discord.TextStyle.short, placeholder="Please be unrealistic")
    
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Microsoft Bug Report", description=f"""**{self.application.label}**\n{self.application}\n
        **{self.description.label}**\n{self.description}\n 
        **{self.due_date.label}**\n{self.due_date}\n""")
        embed.set_author(name = interaction.user, icon_url=interaction.user.avatar)
        await interaction.response.send_message(embed=embed, content="<@!143863189405302784> Please check your calendar to fix this at your earliest convenience. Thanks")

bot = Bot()
@app_commands.command(name="msbug")
async def msbug(interaction: discord.Interaction):
    await interaction.response.send_modal(MS_Bug())
#
#bot.tree.add_command(msbug, guild=discord.Object(id=533019434491576323))
bot.tree.add_command(msbug, guild=discord.Object(id=220180151315595264))
bot.tree.add_command(msbug, guild=discord.Object(id=484582649965576199))
