from discord.ext.commands import Cog
from discord.ext.commands import command
from discord import File
from difflib import get_close_matches
import datetime as dt
from typing import Optional
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import deeppyer
import requests
import asyncio
import discord
import shutil
import uuid
import math
import sys
import os

from ..db import db

path_separator = "/"
if os.name == 'nt':
    path_separator = "\\"

from config import IMGFLIP_PASSWORD

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
files = os.path.join(THIS_FOLDER, ".." + path_separator + "files" + path_separator)
templates = os.path.join(THIS_FOLDER, ".." + path_separator + "files" + path_separator + "templates" + path_separator)

OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}

class Meme(Cog):
    def __init__(self, bot):
    	self.bot = bot

    @command(name="meme")
    async def meme(self, ctx, *, message):
        message = message.split(';')
        if len(message) == 3:
            try:
                meme_names = db.column("SELECT title FROM memes")
                matches = get_close_matches(message[0], meme_names, 5, 0)

                meme = await self.choose_meme(ctx, matches)
                meme_id = db.record(f"SELECT meme_id FROM memes WHERE title='{meme}'")[0]
                params = {
                    'username':"nkeep",
                    'password':IMGFLIP_PASSWORD,
                    'template_id':str(meme_id),
                    'text0':message[1],
                    'text1':message[2]
                }
                response = requests.request('POST', "https://api.imgflip.com/caption_image", params=params).json()
                await ctx.send(response['data']['url'])
            except:
                await ctx.send("Something went wrong, prob the api being dumb")
        else:
            await ctx.send("Need 3 arguments separated by ';'")

    async def choose_meme(self, ctx, memes):
        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == msg.id
            )

        embed = discord.Embed(
            title="Choose a song",
            description=(
                "\n".join(
                    f"**{i+1}.** {t}"
                    for i, t in enumerate(memes[:5])
                )
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.now()
        )
        embed.set_author(name="Query Results")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar)

        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(memes), len(OPTIONS))]:
            await msg.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            return memes[OPTIONS[reaction.emoji]]

    @command(name="deepfry")
    async def deepfry(self, ctx):
        try:
            url = ctx.message.attachments[0].url
            if url[0:26] == "https://cdn.discordapp.com":
                r = requests.get(url, stream=True)
                with open(files + "deepfry.jpg", 'wb') as out_file:
                    try:
                        shutil.copyfileobj(r.raw, out_file)
                        img = Image.open(files+"deepfry.jpg")
                        img = await deeppyer.deepfry(img, flares=False)
                        img.save(files+"deepfry.jpg")
                        await ctx.send(file=File(files+"deepfry.jpg"))
                    except Exception as e:
                        print(e)
        except:
            await ctx.send("Must contain an image upload")

    @command(name="memetext")
    async def memetext(self, ctx, *, text):
        text = text.split(";")
        print(text[0], text[1])
        try:
            url = ctx.message.attachments[0].url
            if url[0:26] == "https://cdn.discordapp.com":
                r = requests.get(url, stream=True)
                filetype = "." + str(url.split('.')[-1])

                with open(files + "memetext" + filetype, 'wb') as out_file:
                    try:
                        shutil.copyfileobj(r.raw, out_file)
                        img = Image.open(files+"memetext" + filetype)
                        draw = ImageDraw.Draw(img)
                        img, draw = drawText(img, draw, text[0], "top")
                        img, draw = drawText(img, draw, text[1], "bottom")
                        img.save(files+"memetext" + filetype)
                        await ctx.send(file=File(files+"memetext" + filetype))
                    except Exception as e:
                        print(e)
        except:
            await ctx.send("Must contain an image upload")

    @command(name="templateadd")
    async def templateadd(self, ctx, name, type, startx: Optional[int], starty: Optional[int], width: Optional[int], height: Optional[int]):
        try:
            url = ctx.message.attachments[0].url
            if url[0:26] == "https://cdn.discordapp.com":
                r = requests.get(url, stream=True)
                fileName = str(uuid.uuid4()) + "." + str(url.split('.')[-1])
                with open(templates + fileName, 'wb') as out_file:
                    shutil.copyfileobj(r.raw, out_file)
                    template = Image.open(templates + fileName)
                    print(templates + fileName)

                    if type == "background" and startx and starty and width and height:
                        db.execute(f"INSERT INTO templates (name, filelocation, type, startx, starty, width, height, size) VALUES('{name}','{templates + fileName}', '{type}',{startx},{starty},{width},{height},'{str(template.size)}')")
                        await ctx.send("Successfully added template")

                    elif type == "foreground":
                        db.execute(f"INSERT INTO templates (name, filelocation, type, size) VALUES('{name}','{templates + fileName}','{type}', '{str(template.size)}')")
                        await ctx.send("Successfully added template")
        except Exception as e:
            print(e)
            await ctx.send("Command failed")
    @command(name="templateremove")
    async def templateremove(self, ctx, first):
        template = db.field(f"SELECT * FROM templates WHERE name = '{first}'")
        if template:
            db.execute(f"DELETE FROM templates WHERE name = '{first}'")
            await ctx.send(f"Successfully deleted {first}")
        else:
            await ctx.send("Template does not exist")

    @command(name="templatesize")
    async def templatesize(self, ctx, first):
        template = db.record(f"SELECT * FROM templates WHERE name = '{first}'")
        await ctx.send(f"Size of {first}: {template[2]}")

    @command(name="templatelist")
    async def templatelist(self, ctx):
        try:
            list = db.column(f"SELECT * from templates")
            await ctx.send(list)
        except:
            await ctx.send("Command failed")

    @command(name="merge")
    async def merge(self, ctx, first):
        try:
            url = ctx.message.attachments[0].url
            if url[0:26] == "https://cdn.discordapp.com":
                r = requests.get(url, stream=True)
                fileName = "upload." + str(url.split('.')[-1])
                with open(templates + fileName, 'wb') as out_file:
                    shutil.copyfileobj(r.raw, out_file)
                    upload = Image.open(templates + fileName)
                    try:
                        template = db.record(f"SELECT * FROM templates WHERE name = '{first}'")
                        print(template)
                        templatePic = Image.open(template[1])
                        if template[2] == "foreground":
                            upload = upload.resize(templatePic.size, Image.ANTIALIAS)
                            upload.paste(templatePic, (0,0), templatePic)
                            upload.save(templates + "merged.png", "PNG")
                            await ctx.send(file=File(rf'{templates + "merged.png"}'))
                        elif template[2] == "background":
                            upload.thumbnail((template[5], template[6]), Image.ANTIALIAS) #Make image as big as possible without ruining aspect ratio

                            if upload.size[0] == template[5]: #if width is maxed, then center vertically
                                try:
                                    templatePic.paste(upload, (template[3], int((template[6] - upload.size[1])/2) + template[4]), upload)
                                except:
                                    templatePic.paste(upload, (template[3], int((template[6] - upload.size[1])/2) + template[4]))
                            elif upload.size[1] == template[6]: #if height is maxed, center horizontally
                                try:
                                    templatePic.paste(upload, (int((template[5] - upload.size[0])/2) + template[3], template[4]), upload)
                                except:
                                    templatePic.paste(upload, (int((template[5] - upload.size[0])/2) + template[3], template[4]))
                            templatePic.save(templates + "merged.png", "PNG")
                            await ctx.send(file=File(rf'{templates + "merged.png"}'))
                    except Exception as e:
                        print(e)
                        await ctx.send("Template does not exist")
        except Exception as e:
            print(e)
            print("Requires a file upload")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("meme")

async def setup(bot):
	await bot.add_cog(Meme(bot))

#Used this guy's code: https://github.com/lipsumar/meme-caption/blob/master/meme.py
def drawText(img, draw, msg, pos):
    fontSize = math.floor(img.width / 8)
    lines = []

    font = ImageFont.truetype(files + "impact.ttf", fontSize)
    w, h = draw.textsize(msg, font)

    imgWidthWithPadding = img.width * 0.99

    # 1. how many lines for the msg to fit ?
    lineCount = 1
    if(w > imgWidthWithPadding):
        lineCount = int(round((w / imgWidthWithPadding) + 1))

    if lineCount > 2:
        while 1:
            fontSize -= 2
            font = ImageFont.truetype("impact.ttf", fontSize)
            w, h = draw.textsize(msg, font)
            lineCount = int(round((w / imgWidthWithPadding) + 1))
            print("try again with fontSize={} => {}".format(fontSize, lineCount))
            if lineCount < 3 or fontSize < 10:
                break

    print("fontsize: {}".format(fontSize))

    print("img.width: {}, text width: {}".format(img.width, w))
    print("Text length: {}".format(len(msg)))
    print("Lines: {}".format(lineCount))


    # 2. divide text in X lines
    lastCut = 0
    isLast = False
    for i in range(0,lineCount):
        if lastCut == 0:
            cut = (len(msg) / lineCount) * i
        else:
            cut = lastCut

        if i < lineCount-1:
            nextCut = int((len(msg) / lineCount) * (i+1))
        else:
            nextCut = len(msg)
            isLast = True

        print("cut: {} -> {}".format(cut, nextCut))

        # make sure we don't cut words in half
        if nextCut == len(msg) or msg[nextCut] == " ":
            print("may cut")
        else:
            print("may not cut")
            while msg[nextCut] != " ":
                nextCut += 1
            print("new cut: {}".format(nextCut))

        print(int(cut), nextCut)
        line = msg[int(cut):nextCut].strip()

        # is line still fitting ?
        w, h = draw.textsize(line, font)
        if not isLast and w > imgWidthWithPadding:
            print("overshot")
            nextCut -= 1
            while msg[nextCut] != " ":
                nextCut -= 1
            print("new cut: {}".format(nextCut))

        lastCut = nextCut
        lines.append(msg[int(cut):nextCut].strip())

    print(lines)

    # 3. print each line centered
    lastY = -h
    if pos == "bottom":
        lastY = img.height - h * (lineCount+1) - 10

    for i in range(0,lineCount):
        w, h = draw.textsize(lines[i], font)
        textX = img.width/2 - w/2
        #if pos == "top":
        #    textY = h * i
        #else:
        #    textY = img.height - h * i
        textY = lastY + h
        draw.text((textX-2, textY-2),lines[i],(0,0,0),font=font)
        draw.text((textX+2, textY-2),lines[i],(0,0,0),font=font)
        draw.text((textX+2, textY+2),lines[i],(0,0,0),font=font)
        draw.text((textX-2, textY+2),lines[i],(0,0,0),font=font)
        draw.text((textX, textY),lines[i],(255,255,255),font=font)
        lastY = textY


    return img, draw
