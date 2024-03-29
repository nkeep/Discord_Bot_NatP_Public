import asyncio
import datetime as dt
import enum
import random
import re
import os
import typing as t
from enum import Enum
from typing import Optional

import aiohttp
import discord
import wavelink
import math
from discord.ext import commands

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
LYRICS_URL = "https://some-random-api.ml/lyrics?title="
HZ_BANDS = (20, 40, 63, 100, 150, 250, 400, 450, 630, 1000, 1600, 2500, 4000, 10000, 16000)
TIME_REGEX = r"([0-9]{1,2})[:ms](([0-9]{1,2})s?)?"
OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}


class AlreadyConnectedToChannel(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class QueueIsEmpty(commands.CommandError):
    pass


class NoTracksFound(commands.CommandError):
    pass


class PlayerIsAlreadyPaused(commands.CommandError):
    pass


class NoMoreTracks(commands.CommandError):
    pass


class NoPreviousTracks(commands.CommandError):
    pass


class InvalidRepeatMode(commands.CommandError):
    pass


class VolumeTooLow(commands.CommandError):
    pass


class VolumeTooHigh(commands.CommandError):
    pass


class MaxVolume(commands.CommandError):
    pass


class MinVolume(commands.CommandError):
    pass


class NoLyricsFound(commands.CommandError):
    pass


class InvalidEQPreset(commands.CommandError):
    pass


class NonExistentEQBand(commands.CommandError):
    pass


class EQGainOutOfBounds(commands.CommandError):
    pass


class InvalidTimeString(commands.CommandError):
    pass


class RepeatMode(Enum):
    NONE = 0
    ONE = 1
    ALL = 2

class Mode(Enum):
    ALL = math.inf
    TEN_MIN = 10
    THIRTY_MIN = 30

class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_mode = RepeatMode.NONE
        self.mode = Mode.TEN_MIN

    @property
    def is_empty(self):
        return not self._queue

    @property
    def current_track(self):
        if not self._queue:
            raise QueueIsEmpty

        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)

    def add(self, insert, *args):
        skipped_songs = 0
        for i in range(len(args)):
            if args[i].length < (60* self.mode.value):
                if insert:
                    self._queue.insert(self.position + 1, args[0])
                else:
                    self._queue.append(args[i])
            else:
                skipped_songs += 1
        return skipped_songs
            

    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty

        self.position += 1

        if self.position < 0:
            return None
        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.ALL:
                self.position = 0
            else:
                return None
# ADD ERROR MESSAGE TODO
        return self._queue[self.position]

    def update_for_mode(self):
        shift = 0
        for i in range(len(self._queue)):
            index = len(self._queue) - i - 1 #Iterate in reverse
            if (index) == self.position: #Don't remove the currently playing track
                pass
            if self._queue[index].length > (self.mode.value * 60):
                if (index) < self.position:
                    shift += 1
                self._queue.pop(index)
                
        self.position -= shift
    

    def shuffle(self):
        if not self._queue:
            raise QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
        self._queue.extend(upcoming)

    def set_repeat_mode(self, mode):
        if mode == "none":
            self.repeat_mode = RepeatMode.NONE
        elif mode == "1":
            self.repeat_mode = RepeatMode.ONE
        elif mode == "all":
            self.repeat_mode = RepeatMode.ALL

    def empty(self):
        self._queue.clear()
        self.position = 0


# class Player(wavelink.Player):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.queue = Queue()
#         self.eq_levels = [0.] * 15

#     async def connect(self, ctx, channel=None):
#         if self.is_connected:
#             raise AlreadyConnectedToChannel

#         if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
#             raise NoVoiceChannel

#         await super().connect(channel.id)
#         return channel

#     async def teardown(self):
#         try:
#             await self.destroy()
#         except KeyError:
#             pass

#     async def add_tracks(self, ctx, tracks):
#         if not tracks:
#             raise NoTracksFound

#         if isinstance(tracks, wavelink.YouTubePlaylist):
#             self.queue.add(*tracks.tracks)
#         elif len(tracks) == 1:
#             self.queue.add(tracks[0])
#             await ctx.send(f"Added {tracks[0].title} to the queue.")
#         else:
#             if (track := await self.choose_track(ctx, tracks)) is not None:
#                 self.queue.add(track)
#                 await ctx.send(f"Added {track.title} to the queue.")

#         if not self.is_playing and not self.queue.is_empty:
#             await self.start_playback()

#     async def choose_track(self, ctx, tracks):
#         def _check(r, u):
#             return (
#                 r.emoji in OPTIONS.keys()
#                 and u == ctx.author
#                 and r.message.id == msg.id
#             )

#         embed = discord.Embed(
#             title="Choose a song",
#             description=(
#                 "\n".join(
#                     f"**{i+1}.** {t.title} ({t.length//60000}:{str(t.length%60).zfill(2)})"
#                     for i, t in enumerate(tracks[:5])
#                 )
#             ),
#             colour=ctx.author.colour,
#             timestamp=dt.datetime.utcnow()
#         )
#         embed.set_author(name="Query Results")
#         embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

#         msg = await ctx.send(embed=embed)
#         for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
#             await msg.add_reaction(emoji)

#         try:
#             reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
#         except asyncio.TimeoutError:
#             await msg.delete()
#             await ctx.message.delete()
#         else:
#             await msg.delete()
#             return tracks[OPTIONS[reaction.emoji]]

#     async def start_playback(self):
#         await self.play(self.queue.current_track)

#     async def advance(self):
#         try:
#             if (track := self.queue.get_next_track()) is not None:
#                 await self.play(track)
#         except QueueIsEmpty:
#             pass

#     async def repeat_track(self):
#         await self.play(self.queue.current_track)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.node = None
        self.queue = Queue()
        #self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                self.queue.empty()
                await self.get_player(member.guild).disconnect()

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node):
        print(f" Wavelink node `{node.identifier}` ready.")

    # @commands.Cog.listener("on_track_stuck")

    @commands.Cog.listener("on_wavelink_track_end")
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if self.queue.repeat_mode == RepeatMode.ONE:
            await player.play(self.queue.current_track)
        elif self.queue.upcoming:
            await player.play(self.queue.get_next_track())
        else:
            self.queue.empty()

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands are not available in DMs.")
            return False

        return True

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(bot=self.bot,
                                    host='127.0.0.1',
                                    port=2333,
                                    password='youshallnotpass')
        self.node = wavelink.NodePool.get_node()

    def get_player(self, obj):
        if isinstance(obj, discord.Guild):
            return self.node.get_player(obj)

    @commands.command(name="connect", aliases=["join"])
    async def connect_command(self, ctx):
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect(cls=wavelink.Player)
        #player = self.get_player(ctx.guild)
        # channel = await player.connect(ctx, channel)
        await ctx.send(f"Connected to {voice_channel.name}.")

    @connect_command.error
    async def connect_command_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnectedToChannel):
            await ctx.send("Already connected to a voice channel.")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("No suitable voice channel was provided.")

    @commands.command(name="disconnect", aliases=["leave"])
    async def disconnect_command(self, ctx):
        player = self.get_player(ctx.guild)
        self.queue.empty()
        await player.disconnect()
        await ctx.send("Disconnected.")

    @commands.command(name="changemode", aliases=["mode", "setmode", "musicmode"])
    async def changemode(self, ctx, mode: Optional[str]):
        if mode == None:
            await ctx.send("Current mode: " + str(self.queue.mode.value) + " minute mode" + "\n" + "Available modes: 10, 30, all")
            return
        if mode.startswith("10") or mode.lower().startswith("ten"):
            self.queue.mode = Mode.TEN_MIN
            self.queue.update_for_mode()
            await ctx.send("Successfully set mode. Only songs < 10 min will play now.")
        elif mode.startswith("30") or mode.lower().startswith("thirty"):
            self.queue.mode = Mode.THIRTY_MIN
            self.queue.update_for_mode()
            await ctx.send("Successfully set mode. Only songs < 30 min will play now.")
        elif mode.lower().startswith("all"):
            self.queue.mode = Mode.ALL
            await ctx.send("Successfully set mode. All songs will play now.")
        else:
            await ctx.send("Invalid mode. Available options: 10, 30, all")
        

    @commands.command(name="play")
    async def play_command(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx.guild)
        if not player:
            voice_channel = ctx.author.voice.channel
            await voice_channel.connect(cls=wavelink.Player)
        player = self.get_player(ctx.guild)
            
        if not player.is_connected():
            await player.connect(ctx)

        if query is None:
            if self.queue.is_empty:
                raise QueueIsEmpty

            await player.set_pause(False)
            await ctx.send("Playback resumed.")

        else:
            query = query.strip("<>")
            if not re.match(URL_REGEX, query):
                tracks = await wavelink.YouTubeTrack.search(query=query)
                tracks = [track for track in tracks if track.length < (self.queue.mode.value * 60)]
            elif "list=" in query:
                tracks = await self.node.get_playlist(cls=wavelink.YouTubePlaylist, identifier=query)
            else:
                if "youtu.be/" in query:
                    query = query.replace("youtu.be/","www.youtube.com/watch?v=")
                tracks = await self.node.get_tracks(cls=wavelink.YouTubeTrack, query=query)
            await self.add_tracks(ctx, tracks)

    @commands.command(name="playtop")
    async def playtop(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx.guild)
        if not player:
            voice_channel = ctx.author.voice.channel
            await voice_channel.connect(cls=wavelink.Player)
        player = self.get_player(ctx.guild)
            
        if not player.is_connected():
            await player.connect(ctx)

        if query is None:
            if self.queue.is_empty:
                raise QueueIsEmpty

            await player.set_pause(False)
            await ctx.send("Playback resumed.")

        else:
            query = query.strip("<>")
            if "list=" in query:
                await ctx.send("Can't add a playlist with playtop")
            elif not re.match(URL_REGEX, query):
                tracks = await wavelink.YouTubeTrack.search(query=query)
            else:
                if "youtu.be/" in query:
                    query = query.replace("youtu.be/","www.youtube.com/watch?v=")
                tracks = await self.node.get_tracks(cls=wavelink.YouTubeTrack, query=query)
            await self.add_tracks(ctx, tracks, insert=True)

    async def add_tracks(self, ctx, tracks, insert=False):
        player = self.get_player(ctx.guild)
        if not tracks:
            raise NoTracksFound

        if isinstance(tracks, wavelink.YouTubePlaylist):
            if (skipped := self.queue.add(insert, *tracks.tracks)) != len(tracks.tracks):
                message = f"Added {tracks.name} to the queue."
                if skipped:
                    message += f" Skipped {skipped} songs due to mode."
                await ctx.send(message)
            else:
                await ctx.send(f"Failed to add due to mode. Change mode with 'changemode'")
        elif len(tracks) == 1:
            if not (skipped := self.queue.add(insert, tracks[0])):
                await ctx.send(f"Added {tracks[0]} to the queue.")
            else:
                await ctx.send(f"Failed to add due to mode. Change mode with 'changemode'")
        else:
            if (track := await self.choose_track(ctx, tracks)) is not None:
                if not (skipped := self.queue.add(insert, track)):
                    await ctx.send(f"Added {track} to the queue.")
                else:
                    await ctx.send(f"Failed to add due to mode. Change mode with 'changemode'")

        if not player.is_playing() and not self.queue.is_empty:
            await player.play(self.queue.current_track)

    async def choose_track(self, ctx, tracks):
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
                    f"**{i+1}.** {t.title} ({str(int(t.length//3600)).zfill(2)}:{str(int(((t.length//60) %60))).zfill(2)}:{str(int(t.length%60)).zfill(2)})"
                    for i, t in enumerate(tracks[:5])
                )
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Query Results")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar)

        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await msg.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            return tracks[OPTIONS[reaction.emoji]]

    @play_command.error
    async def play_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("No songs to play as the queue is empty.")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("No suitable voice channel was provided.")

    @commands.command(name="pause")
    async def pause_command(self, ctx):
        player = self.get_player(ctx.guild)

        if player.is_paused():
            raise PlayerIsAlreadyPaused

        await player.set_pause(True)
        await ctx.send("Playback paused.")

    @pause_command.error
    async def pause_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("Already paused.")

    @commands.command(name="stop", aliases=["clear"])
    async def stop_command(self, ctx):
        player = self.get_player(ctx.guild)
        self.queue.empty()
        await player.stop()
        await ctx.send("Playback stopped.")

    @commands.command(name="next", aliases=["skip"])
    async def next_command(self, ctx):
        player = self.get_player(ctx.guild)

        await player.stop()

        if not self.queue.upcoming:
            raise NoMoreTracks
        
        await ctx.send("Playing next track in queue.")

    @next_command.error
    async def next_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("This could not be executed as the queue is currently empty.")
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("There are no more tracks in the queue.")

    @commands.command(name="previous")
    async def previous_command(self, ctx):
        player = self.get_player(ctx.guild)

        if not self.queue.history:
            raise NoPreviousTracks

        self.queue.position -= 2
        await player.stop()
        await ctx.send("Playing previous track in queue.")

    @previous_command.error
    async def previous_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("This could not be executed as the queue is currently empty.")
        elif isinstance(exc, NoPreviousTracks):
            await ctx.send("There are no previous tracks in the queue.")

    @commands.command(name="shuffle")
    async def shuffle_command(self, ctx):
        player = self.get_player(ctx.guild)
        self.queue.shuffle()
        await ctx.send("Queue shuffled.")

    @shuffle_command.error
    async def shuffle_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue could not be shuffled as it is currently empty.")

    @commands.command(name="repeat")
    async def repeat_command(self, ctx, mode: str):
        if mode not in ("none", "1", "all"):
            raise InvalidRepeatMode

        player = self.get_player(ctx.guild)
        self.queue.set_repeat_mode(mode)
        await ctx.send(f"The repeat mode has been set to {mode}.")

    @commands.command(name="queue", aliases=["q"])
    async def queue_command(self, ctx, show: t.Optional[int] = 10):
        def _check(r, u):
            return (
                r.emoji == "⬅️" or r.emoji == "➡️"
                and u == ctx.author
                and r.message.id == msg.id
            )
        player = self.get_player(ctx.guild)

        page = 0

        if self.queue.is_empty:
            raise QueueIsEmpty

        embed = discord.Embed(
            title="Queue",
            description=f"Showing up to next {show} tracks (" + str(len(self.queue.upcoming)) + " total)",
            colour=ctx.author.colour
        )
        embed.set_footer(text=f"Page {str(page+1)}")
        embed.add_field(
            name="Currently playing",
            value=getattr(player.track, "title", "No tracks currently playing."),
            inline=False
        )
        if upcoming := self.queue.upcoming:
            embed.add_field(
                name="Next up",
                value="\n".join(str(i+1) + ". " + t.title for i, t in enumerate(upcoming[page:show])),
                inline=False
            )

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        
        while(True):
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=_check)
            except:
                break
            else:
                await msg.remove_reaction(reaction, user)
                if reaction.emoji == "⬅️" and page > 0:
                    page -= 1
                elif reaction.emoji == "➡️" and (show*(page+1)) < len(self.queue.upcoming):
                    page += 1
                else:
                    pass
                #Could put this in a function perhaps
                embed = discord.Embed(
                    title="Queue",
                    description=f"Showing up to next {show} tracks (" + str(len(self.queue.upcoming)) + " total)",
                    colour=ctx.author.colour
                )
                embed.set_footer(text=f"Page {str(page+1)}")
                embed.add_field(
                    name="Currently playing",
                    value=getattr(player.track, "title", "No tracks currently playing."),
                    inline=False
                )
                if upcoming := self.queue.upcoming:
                    embed.add_field(
                        name="Next up",
                        value="\n".join(str(i+1+(page*show)) + ". " + t.title for i, t in enumerate(upcoming[(page*show):show*(page + 1)])),
                        inline=False
                    )
                msg = await msg.edit(embed=embed)

    @queue_command.error
    async def queue_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue is currently empty.")


    # Requests -----------------------------------------------------------------

    @commands.group(name="volume", invoke_without_command=True)
    async def volume_group(self, ctx, volume: int):
        player = self.get_player(ctx.guild)

        if volume < 0:
            raise VolumeTooLow

        if volume > 150:
            raise VolumeTooHigh

        await player.set_volume(volume)
        await ctx.send(f"Volume set to {volume:,}%")

    @volume_group.error
    async def volume_group_error(self, ctx, exc):
        if isinstance(exc, VolumeTooLow):
            await ctx.send("The volume must be 0% or above.")
        elif isinstance(exc, VolumeTooHigh):
            await ctx.send("The volume must be 150% or below.")

    @volume_group.command(name="up", hidden=True)
    async def volume_up_command(self, ctx):
        player = self.get_player(ctx.guild)

        if player.volume == 150:
            raise MaxVolume

        await player.set_volume(value := min(player.volume + 10, 150))
        await ctx.send(f"Volume set to {value:,}%")

    @volume_up_command.error
    async def volume_up_command_error(self, ctx, exc):
        if isinstance(exc, MaxVolume):
            await ctx.send("The player is already at max volume.")

    @volume_group.command(name="down", hidden=True)
    async def volume_down_command(self, ctx):
        player = self.get_player(ctx.guild)

        if player.volume == 0:
            raise MinVolume

        await player.set_volume(value := max(0, player.volume - 10))
        await ctx.send(f"Volume set to {value:,}%")

    @volume_down_command.error
    async def volume_down_command_error(self, ctx, exc):
        if isinstance(exc, MinVolume):
            await ctx.send("The player is already at min volume.")

    @commands.command(name="lyrics", hidden=True)
    async def lyrics_command(self, ctx, name: t.Optional[str]):
        player = self.get_player(ctx.guild)
        name = name or self.queue.current_track.title

        async with ctx.typing():
            async with aiohttp.request("GET", LYRICS_URL + name, headers={}) as r:
                if not 200 <= r.status <= 299:
                    raise NoLyricsFound

                data = await r.json()

                if len(data["lyrics"]) > 2000:
                    return await ctx.send(f"<{data['links']['genius']}>")

                embed = discord.Embed(
                    title=data["title"],
                    description=data["lyrics"],
                    colour=ctx.author.colour,
                    timestamp=dt.datetime.utcnow(),
                )
                embed.set_thumbnail(url=data["thumbnail"]["genius"])
                embed.set_author(name=data["author"])
                await ctx.send(embed=embed)

    @lyrics_command.error
    async def lyrics_command_error(self, ctx, exc):
        if isinstance(exc, NoLyricsFound):
            await ctx.send("No lyrics could be found.")

    @commands.command(name="eq", hidden=True)
    async def eq_command(self, ctx, preset: str):
        player = self.get_player(ctx.guild)

        eq = getattr(wavelink.eqs.Equalizer, preset, None)
        if not eq:
            raise InvalidEQPreset

        await player.set_eq(eq())
        await ctx.send(f"Equaliser adjusted to the {preset} preset.")

    @eq_command.error
    async def eq_command_error(self, ctx, exc):
        if isinstance(exc, InvalidEQPreset):
            await ctx.send("The EQ preset must be either 'flat', 'boost', 'metal', or 'piano'.")

    @commands.command(name="adveq", aliases=["aeq"], hidden=True)
    async def adveq_command(self, ctx, band: int, gain: float):
        player = self.get_player(ctx.guild)

        if not 1 <= band <= 15 and band not in HZ_BANDS:
            raise NonExistentEQBand

        if band > 15:
            band = HZ_BANDS.index(band) + 1

        if abs(gain) > 10:
            raise EQGainOutOfBounds

        player.eq_levels[band - 1] = gain / 10
        eq = wavelink.eqs.Equalizer(levels=[(i, gain) for i, gain in enumerate(player.eq_levels)])
        await player.set_eq(eq)
        await ctx.send("Equaliser adjusted.")

    @adveq_command.error
    async def adveq_command_error(self, ctx, exc):
        if isinstance(exc, NonExistentEQBand):
            await ctx.send(
                "This is a 15 band equaliser -- the band number should be between 1 and 15, or one of the following "
                "frequencies: " + ", ".join(str(b) for b in HZ_BANDS)
            )
        elif isinstance(exc, EQGainOutOfBounds):
            await ctx.send("The EQ gain for any band should be between 10 dB and -10 dB.")

    @commands.command(name="playing", aliases=["np"])
    async def playing_command(self, ctx):
        player = self.get_player(ctx.guild)

        if not player.is_playing():
            raise PlayerIsAlreadyPaused

        embed = discord.Embed(
            title="Now playing",
            colour=ctx.author.colour,
            timestamp=dt.datetime.now(),
        )
        embed.set_author(name="Playback Information")
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar)
        embed.add_field(name="Track title", value=self.queue.current_track.title, inline=False)
        embed.add_field(name="Artist", value=self.queue.current_track.author, inline=False)

        position = divmod(player.position, 60)
        length = divmod(self.queue.current_track.length, 60)
        embed.add_field(
            name="Position",
            value=f"{int(position[0]):02}:{round(position[1]):02}/{int(length[0])}:{round(length[1]):02}",
            inline=False
        )

        await ctx.send(embed=embed)

    @playing_command.error
    async def playing_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("There is no track currently playing.")

    @commands.command(name="skipto", aliases=["playindex"])
    async def skipto_command(self, ctx, index: int):
        player = self.get_player(ctx.guild)

        if self.queue.is_empty:
            raise QueueIsEmpty

        if not 0 <= index <= self.queue.length:
            raise NoMoreTracks

        self.queue.position = index - 1
        await player.stop()
        await ctx.send(f"Playing track in position {index}.")

    @skipto_command.error
    async def skipto_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("There are no tracks in the queue.")
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("That index is out of the bounds of the queue.")
        
    @commands.command(name="replace")
    async def replace(self, ctx, query):
        await ctx.invoke(self.bot.get_command('playtop'), query=query)
        await ctx.invoke(self.bot.get_command('skip'))

    @commands.command(name="restart")
    async def restart_command(self, ctx):
        player = self.get_player(ctx.guild)

        if self.queue.is_empty:
            raise QueueIsEmpty

        await player.seek(0)
        await ctx.send("Track restarted.")

    @restart_command.error
    async def restart_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("There are no tracks in the queue.")

    @commands.command(name="seek", hidden=True)
    async def seek_command(self, ctx, position: str):
        player = self.get_player(ctx.guild)

        if self.queue.is_empty:
            raise QueueIsEmpty

        if not (match := re.match(TIME_REGEX, position)):
            raise InvalidTimeString

        if match.group(3):
            secs = (int(match.group(1)) * 60) + (int(match.group(3)))
        else:
            secs = int(match.group(1))

        await player.seek(secs * 1000)
        await ctx.send("Seeked.")


async def setup(bot):
    if os.name != 'nt':
        await bot.add_cog(Music(bot))
