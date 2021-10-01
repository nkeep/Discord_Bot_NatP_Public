import discord
import os
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
token_txt = os.path.join(THIS_FOLDER, 'token.txt')

TOKEN = open(token_txt,"r").readline()

intents = discord.Intents.default()

client = discord.Client(intents = intents)

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('.hello'):

        await message.channel.send('Hello!')

client.run(TOKEN)
