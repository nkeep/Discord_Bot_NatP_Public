import discord
from discord import Member, ChannelType, File
from discord import app_commands as apc
from typing import Optional
from discord.message import Attachment

from ..db import db as dbs

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

bot_channels = [505589070378958850, 871493456021835797, 497223372355272714]
funny_mines = [944367282098941992]
db_commands = None

class db(apc.Group):

    """Manage general commands"""
    def __init__(self, bot: discord.ext.commands.Bot):
        global db_commands
        super().__init__()
        self.bot = bot

        db_commands = sorted(dbs.column("SELECT name FROM db WHERE name !~ '(funny$|funny\d+$)' AND name !~ '(who$|who\d+$)'"))

        print(db_commands)

    @apc.command()
    async def db(self, interaction: discord.Interaction, name: str):
        if not 'funny' in name:
            try:
                response = dbs.record(f"SELECT * FROM db WHERE name = '{name}'")
                if response:
                    if response[2] == 1:
                        location = response[1]
                        print(location)
                        await interaction.response.send_message(file=File(rf'{location}')) #TODO: This doesn't work for big files for some reason
                    else:
                        await interaction.response.send_message(response[1])
                    dbs.execute(f"UPDATE db SET uses = uses + 1 WHERE name = '{name}'")
                else:
                    await interaction.response.send_message("Command doesn't exist")
            except Exception as e:
                print(e)

    @db.autocomplete('name')
    async def db_autocomplete(
    interaction: discord.Interaction,
    current: str,
    namespace: apc.Namespace
    ) -> list[apc.Choice[str]]:
        name = db_commands
        print(current.data['options'][0]['options'][0]['value'])
        return [
            apc.Choice(name=nm, value=nm)
            for nm in name if current.data['options'][0]['options'][0]['value'].lower() in nm.lower()
        ]

    @apc.command(name="dbadd")
    async def dbadd(self, interaction: discord.Interaction, name: str, text: Optional[str], file: Optional[Attachment]):
        global db_commands
        print(name)

        if not 'funny' in name:
            if name and text: #text command
                command = dbs.field(f"SELECT name FROM db WHERE name = '{name}'")
                if not command:
                    text = text.replace("'", r"\'")
                    dbs.execute(f"INSERT INTO db VALUES('{name}', E'{text}', 0, '{interaction.user.id}', 0)")
                    dbs.commit()
                    db_commands = sorted(dbs.column("SELECT name FROM db WHERE name !~ '(funny$|funny\d+$)' AND name !~ '(who$|who\d+$)'"))
                    await interaction.response.send_message("successfully added command")
                else:
                    await interaction.response.send_message("command already exists")
            elif name and file: #check for file
                try:
                    url = file.url
                    if url[0:26] == "https://cdn.discordapp.com":
                        r = requests.get(url, stream=True)
                        fileName = str(uuid.uuid4()) + "." + str(url.split('.')[-1])
                        with open(files + fileName, 'wb') as out_file:
                            shutil.copyfileobj(r.raw, out_file)
                            dbs.execute(f"INSERT INTO db VALUES('{name}','{files + fileName}', 1, {interaction.user.id}, 0)")
                            db_commands = sorted(dbs.column("SELECT name FROM db WHERE name !~ '(funny$|funny\d+$)' AND name !~ '(who$|who\d+$)'"))
                            await interaction.response.send_message("successfully added command")
                except Exception as e:
                    print(e)
            else:
                await interaction.response.send_message("Invalid syntax")

    @apc.command(name="dbremove")
    async def dbremove(self, interaction: discord.Interaction, name: str):
        command = dbs.record(f"SELECT * FROM db WHERE name = '{name}'")
        print(command)
        if command:
            dbs.execute(f"DELETE FROM db WHERE name = '{name}'")
            await interaction.response.send_message(f"Successfully deleted {name}")
            if command[2]:
                try:
                    os.remove(command[1])
                except Exception as e:
                    print(e)
        else:
            await interaction.response.send_message("Command doesn't exist")

    @dbremove.autocomplete('name')
    async def dbremove_autocomplete(
    interaction: discord.Interaction,
    current: str,
    namespace: apc.Namespace
    ) -> list[apc.Choice[str]]:
        name = db_commands
        print(current.data['options'][0]['options'][0]['value'])
        return [
            apc.Choice(name=nm, value=nm)
            for nm in name if current.data['options'][0]['options'][0]['value'].lower() in nm.lower()
        ]

    @apc.command(name="dbupdate")
    async def dbupdate(self, interaction: discord.Interaction, name: str, text: Optional[str], file: Optional[Attachment]):
        if name and text:
            dbs.execute(f"UPDATE db SET name='{name}', result='{text}', isfile=0 WHERE name='{name}'")
            await interaction.response.send_message(f"Successfully updated {name}")

        elif name and file:
            try:
                url = file.url
                if url[0:26] == "https://cdn.discordapp.com":
                    r = requests.get(url, stream=True)
                    fileName = str(uuid.uuid4()) + "." + str(url.split('.')[-1])
                    with open(files + fileName, 'wb') as out_file:
                        shutil.copyfileobj(r.raw, out_file)
                        dbs.execute(f"UPDATE db SET name='{name}', result='{files + fileName}', isfile=1 WHERE name='{name}'")
                        await interaction.response.send_message(f"successfully updated {name}")
            except Exception as e:
                print(e)

    @dbupdate.autocomplete('name')
    async def dbupdate_autocomplete(
    interaction: discord.Interaction,
    current: str,
    namespace: apc.Namespace
    ) -> list[apc.Choice[str]]:
        name = db_commands
        print(current.data['options'][0]['options'][0]['value'])
        return [
            apc.Choice(name=nm, value=nm)
            for nm in name if current.data['options'][0]['options'][0]['value'].lower() in nm.lower()
        ]

    @apc.command(name="dblist")
    async def dblist(self, interaction: discord.Interaction):
        if interaction.channel.id in bot_channels:
            try:
                list = str(sorted(dbs.column("SELECT name FROM db WHERE name !~ '(funny$|funny\d+$)' AND name !~ '(who$|who\d+$)'")))
                for i in range(math.ceil(len(list)/2000)): #if the list is more than 2k chars, split it up into multiple messages
                    await interaction.response.send_message(list[i*2000:(i+1)*2000])
            except:
                print("dblist command failed")
        else:
            await interaction.response.send_message("You can only use this command in the bot channel")
