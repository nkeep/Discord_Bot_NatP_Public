from discord import Member, ChannelType
from discord.ext.commands import Cog
from discord.ext.commands import command, has_permissions

from ..db import db


class Misc(Cog):
    def __init__(self, bot):
    	self.bot = bot

    @command(name="prefix")
    async def change_prefix(self, ctx, new: str):
        if not ctx.channel.type is ChannelType.private:
            if len(new) > 5:
                await ctx.send("The prefix can not be more than 5 characters in length.")
            else:
                id = db.field(f"SELECT GuildID FROM guilds WHERE GuildID = {ctx.guild.id}")
                print(id)
                if id:
                    print("guild already in db")
                    db.execute(f"UPDATE guilds SET Prefix = '{new}' WHERE GuildID = {ctx.guild.id}")
                    await ctx.send(f"Prefix set to {new}.")
                else:
                    try:
                        print("guild not in db, adding to db")
                        print(new)
                        print(ctx.guild.id)
                        db.execute(f"INSERT INTO guilds VALUES({ctx.guild.id},'{new}')")
                        await ctx.send(f"Prefix set to {new}.")
                    except Exception as e:
                        print(e)

        else:
            await ctx.send("Cannot change prefix in DMs")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("misc")


async def setup(bot):
	await bot.add_cog(Misc(bot))
