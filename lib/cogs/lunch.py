import discord
from discord import ui, app_commands
from discord.ext.commands import command
from discord.ext.commands import Cog
import requests
import json

from config import GIT_KEY

@app_commands.command(name="lunchbug")
async def lunchbug(interaction: discord.Interaction):
    await interaction.response.send_modal(Lunch_Bug())

@app_commands.command(name="lunchonline")
async def lunchbug(interaction: discord.Interaction):
    await interaction.response.send_message("https://lunch.natekeep.com")

@app_commands.command(name="lunchbuglist")
async def lunchbuglist(interaction: discord.Interaction):
    url = f'https://api.github.com/repos/nkeep/Auto_PTCGO/issues'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {GIT_KEY}'
    }
    issueList = requests.get(url, headers=headers)

    if issueList.status_code != 200:
        await interaction.response.send_message("Failed to retreive list")
        return

    issueList = issueList.json()
    issuesText = ""
    numIssues = 0

    for issue in issueList:
        if issue["state"] == "open":
            issuesText += "[" + str(numIssues+1) + ". " + issue["title"] + "](" + issue["html_url"] + ")" + "\n"
            numIssues += 1
    embed = discord.Embed()
    embed.description = issuesText
    await interaction.response.send_message(embed=embed)

class Lunch_Bug(ui.Modal, title="Lunch Bug Report"):
    bugTitle = ui.TextInput(label="Title", style=discord.TextStyle.short)
    description = ui.TextInput(label="Description", style=discord.TextStyle.long, placeholder="Please describe in detail the bug and how to reproduce if necessary")
    
    async def on_submit(self, interaction: discord.Interaction):
        url = f'https://api.github.com/repos/nkeep/Auto_PTCGO/issues'
        headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {GIT_KEY}'
        }
        data = {
            "title": str(self.bugTitle),
            "body": "Reported in Discord by: " + str(interaction.user.name) + "\n" + str(self.description)
        }

        jsonResponse = requests.post(url, headers=headers, data=json.dumps(data))
        if jsonResponse.status_code == 201:
            await interaction.response.send_message(content=str(interaction.user.name) + " created the bug report: " + str(self.bugTitle) + "\n" + jsonResponse.json()["html_url"])
        else:
            await interaction.response.send_message("Failed to create bug request")


class Lunch(Cog):
    def __init__(self, bot):
        self.bot = bot

    # @command(name="lunchbuglist", aliases=["buglist", "lunchbugs"])
    # async def lunchbuglist(self, ctx):
        # url = f'https://api.github.com/repos/nkeep/Auto_PTCGO/issues'
        # headers = {
        #     'Accept': 'application/vnd.github+json',
        #     'Authorization': f'Bearer {GIT_KEY}'
        # }
        # issueList = requests.get(url, headers=headers)

        # if issueList.status_code != 200:
        #     await ctx.send("Failed to retreive list")
        #     return

        # issueList = issueList.json()
        # issuesText = ""
        # numIssues = 0

        # for issue in issueList:
        #     if issue["state"] == "open":
        #         issuesText += "[" + str(numIssues+1) + ". " + issue["title"] + "](" + issue["html_url"] + ")" + "\n"
        #         numIssues += 1
        # embed = discord.Embed()
        # embed.description = issuesText
        # await ctx.send(embed=embed)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("lunch")

async def setup(bot):
    await bot.add_cog(Lunch(bot))
    bot.tree.add_command(lunchbug, guild=discord.Object(id=533019434491576323))
    bot.tree.add_command(lunchbug, guild=discord.Object(id=220180151315595264))
    bot.tree.add_command(lunchbug, guild=discord.Object(id=484582649965576199))
    bot.tree.add_command(lunchbuglist, guild=discord.Object(id=533019434491576323))
    bot.tree.add_command(lunchbuglist, guild=discord.Object(id=220180151315595264))
    bot.tree.add_command(lunchbuglist, guild=discord.Object(id=484582649965576199))
    await bot.tree.sync(guild=discord.Object(id=533019434491576323))
    await bot.tree.sync(guild=discord.Object(id=220180151315595264))
    await bot.tree.sync(guild=discord.Object(id=484582649965576199))
