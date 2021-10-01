from discord.ext.commands import Cog
from discord.ext.commands import command
from discord import File
from difflib import get_close_matches
from typing import Optional
from PIL import Image
import deeppyer
import requests
import uuid
import shutil
import os

from ..db import db

path_separator = "/"
if os.name == 'nt':
    path_separator = "\\"

from config import IMGFLIP_PASSWORD

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
files = os.path.join(THIS_FOLDER, ".." + path_separator + "files" + path_separator)
templates = os.path.join(THIS_FOLDER, ".." + path_separator + "files" + path_separator + "templates" + path_separator)

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
                print(matches[0])
                meme_id = db.record(f"SELECT meme_id FROM memes WHERE title='{matches[0]}'")[0]
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

def setup(bot):
	bot.add_cog(Meme(bot))
