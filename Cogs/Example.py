import asyncio
import discord
import random
import datetime
import subprocess
import re
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import downloader
from   Cogs import UserTime
from   Cogs import PickList
import youtube_dl
import functools

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Example(bot, settings))
    bot.add_cog(Music(bot, settings))

if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    # note that on windows this DLL is automatically provided for you
    discord.opus.load_opus('opus')

class Example:

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    @commands.command()
    async def add(self, ctx, left : int, right : int):
        """Adds two numbers together."""
        await ctx.channel.send(left + right)

    def _roll_string(self, roll):
        # Helper function to give comprehensive breakdown of rolls
        total_rolls = roll["roll_list"]
        vantage     = roll["vantage"]
        add         = roll["add"]
        
        # Format rolls
        dice_string = ""
        final_total = None
        # Format the initial raw rolls
        dice_string += "```\n= Dice Rolls ========================\n"
        dice_rolls = []
        pre_list = []
        total_list = []
        for r in total_rolls:
            dice_rolls.append(", ".join(r['rolls']))
            pre_list.append(r['sum'])
            total_list.append(r['sum']+add)
            
        dice_string += "\n-------------------------------------\n".join(dice_rolls)
        
        # Format modifiers
        if not add == 0:
            sign = "+"
            if add < 0:
                sign = ""
            dice_string += "\n\n= Pre-Total =========================\n{}".format(
                "\n-------------------------------------\n".join([str(x) for x in pre_list])
            )
            dice_string += "\n\n= Modifier ==========================\n{}{}".format(sign, add)
            
        # Format advantage/disadvantage
        if vantage != None:
            if vantage == True:
                # Advantage
                dice_string += "\n\n= Advantage =========================\n"
                total_format = []
                for t in total_list:
                    if t == max(total_list):
                        final_total = t
                        total_format.append("*{}*".format(t))
                    else:
                        total_format.append(str(t))
                dice_string += "\n-------------------------------------\n".join(total_format)
            else:
                # Disadvantage
                dice_string += "\n\n= Disadvantage ======================\n"
                total_format = []
                for t in total_list:
                    if t == min(total_list):
                        final_total = t
                        total_format.append("*{}*".format(t))
                    else:
                        total_format.append(str(t))
                dice_string += "\n-------------------------------------\n".join(total_format)
        
        # Format final total
        if final_total == None:
            final_total = total_list[0]
        dice_string += "\n\n= Final Total =======================\n{}```".format(final_total)
        if len(dice_string) > 2000:
            dice_string = "```\nThe details of this roll are longer than 2,000 characters```"
        return dice_string
    
    def _get_roll_total(self, roll):
        # Helper function to get the final total of a roll
        total_rolls = roll["roll_list"]
        vantage     = roll["vantage"]
        add         = roll["add"]
        total_list = []
        total_crit = []
        total_fail = []
        for r in total_rolls:
            total_list.append(r['sum']+add)
            total_crit.append(r['crit'])
            total_fail.append(r['fail'])

        if vantage != None:
            if vantage == True:
                # Advantage
                highest = max(total_list)
                i = total_list.index(highest)
                return { "total" : highest, "crit" : total_crit[i], "fail" : total_fail[i] }
            else:
                # Disadvantage
                lowest = min(total_list)
                i = total_list.index(lowest)
                return { "total" : lowest, "crit" : total_crit[i], "fail" : total_fail[i] }
        return { "total" : total_list[0], "crit" : total_crit[0], "fail" : total_fail[0] }
        
    @commands.command()
    async def roll(self, ctx, *, dice : str = "1d20"):
        """Rolls a dice in NdN±Na/d format."""
        dice_list = dice.split()
        dice_setup = []
        for dice in dice_list:
            try:
                vantage = None
                d = dice
                if dice.lower().endswith("a"):
                    # Advantage
                    vantage = True
                    dice = dice[:-1]
                elif dice.lower().endswith("d"):
                    # Disadvantage
                    vantage = False
                    dice = dice[:-1]
                parts = dice.split('d')
                rolls = int(parts[0])
                limit = parts[1]
                add   = 0
                if "-" in limit:
                    parts = limit.split('-')
                    limit = int(parts[0])
                    add = int(parts[1])*-1
                elif "+" in limit:
                    parts = limit.split('+')
                    limit = int(parts[0])
                    add = int(parts[1])
                else:
                    limit = int(limit)
                if limit < 1:
                    continue
                dice_setup.append({ "vantage" : vantage, "rolls" : rolls, "limit" : limit, "add" : add, "original" : d })
            except Exception:
                pass
        if not len(dice_setup):
            await ctx.send('Format has to be in NdN±Na/d!')
            return
        if len(dice_setup) > 10:
            await ctx.send("I can only process up to 10 dice rolls at once :(")
            return
        # Got valid dice - let's roll them!
        final_dice = []
        for d in dice_setup:
            vantage = d["vantage"]
            add     = d["add"]
            limit   = d["limit"]
            rolls   = d["rolls"]
            if vantage != None:
                attempts = 2
            else:
                attempts = 1
            total_rolls = []

            # Roll for however many attempts we need
            for i in range(attempts):
                numbers = []
                number_sum = 0
                crit = False
                crit_fail = False
                for r in range(rolls):
                    roll = random.randint(1, limit)
                    if roll == 1:
                        crit_fail = True
                    if roll == limit:
                        crit = True
                    number_sum += roll
                    numbers.append(str(roll))
                total_rolls.append({ "rolls" : numbers, "sum" : number_sum, "crit" : crit, "fail" : crit_fail })
                
            dice_dict = {
                "roll_list" : total_rolls,
                "add" : add,
                "vantage" : vantage,
                "original" : d["original"]
            }
            roll_total = self._get_roll_total(dice_dict)
            dice_dict["total"] = roll_total["total"]
            dice_dict["crit"] = roll_total["crit"]
            dice_dict["fail"] = roll_total["fail"]
            final_dice.append(dice_dict)
            
        # Get a stripped list of items
        dice_list = []
        for d in final_dice:
            d_string = "{} - {}".format(d["original"], d["total"])
            extra = ""
            if d["crit"]:
                extra += "C"
            if d["fail"]:
                extra += "F"
            if len(extra):
                d_string += " (" + extra + ")"
            dice_list.append(d_string)
        # Display the table then wait for a reaction
        message = None
        while True:
            index, message = await PickList.Picker(list=dice_list, title="Pick a roll to show details:", ctx=ctx, timeout=300, message=message).pick()
            if index < 0:
                # Edit message to replace the pick title
                await message.edit(content=message.content.replace("Pick a roll to show details:", "Roll results:"))
                return
            # Show what we need
            new_mess = "{}. {}:\n{}".format(index+1, dice_list[index], self._roll_string(final_dice[index]))
            await message.edit(content=new_mess)
            # Add the stop reaction - then wait for it or the timeout
            await message.add_reaction("◀")
            # Setup a check function
            def check(reaction, user):
                return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) == "◀"
            # Attempt to wait for a response
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=30, check=check)
            except:
                # Didn't get a reaction
                pass
            # Clear our our reactions
            await message.clear_reactions()
            # Reset back to our totals
            continue

        

    @commands.command(description='For when you wanna settle the score some other way')
    async def choose(self, ctx, *choices : str):
        """Chooses between multiple choices."""
        msg = random.choice(choices)
        msg = Nullify.clean(msg)
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def joined(self, ctx, *, member : str = None):
        """Says when a member joined."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False
        
        if member is None:
            member = ctx.message.author
            
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                if suppress:
                    msg = Nullify.clean(msg)
                await ctx.channel.send(msg)
                return

        # Get localized user time
        local_time = UserTime.getUserTime(ctx.author, self.settings, member.joined_at)
        time_str = "{} {}".format(local_time['time'], local_time['zone'])
            
        await ctx.channel.send('*{}* joined *{}*'.format(DisplayName.name(member), time_str))

class VoiceEntry:
    def __init__(self, message, player, title, duration, ctx):
        self.requester = message.author
        self.channel = message.channel
        self.player = player
        self.title = title
        self.duration = duration
        self.ctx = ctx

    def __str__(self):
        fmt = '*{}* requested by *{}*'.format(self.title, DisplayName.name(self.requester))
        seconds = self.duration
        if seconds:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            fmt = fmt + ' [length: {:02d}h:{:02d}m:{:02d}s]'.format(round(hours), round(minutes), round(seconds))
        return fmt

class VoiceState:
    def __init__(self, bot, settings):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.playlist = []
        self.repeat = False
        self.votes = []
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())
        self.audio_process = None
        self.start_time = datetime.datetime.now()
        self.total_playing_time = datetime.datetime.now() - datetime.datetime.now()
        self.is_paused = False
        self.settings = settings

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.voice
        return not player.is_paused() and player.is_playing()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.votes = []
        if self.voice.is_playing():
            self.voice.stop()

    def toggle_next(self, error):
        if error:
            print("Error and shit... Should probably handle this one day.")
            
        try:
            comm = self.audio_process.communicate()
            rc = self.audio_process.returncode
            if not rc == 0:
                self.playlist[0]["Error"] = True
                print("Exited abnormally!: {}".format(rc))
        except Exception:
            print("Couldn't get return.")
            
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:

            self.play_next_song.clear()

            if len(self.playlist) <= 0:
                await asyncio.sleep(1)
                continue

            self.start_time = datetime.datetime.now()
            self.current = await self.create_youtube_entry(self.playlist[0]["ctx"], self.playlist[0]["raw_song"], self.playlist[0]['song'], self.playlist[0]['duration'])

            #Check if youtube-dl found the song
            if self.current == False:
                del self.playlist[0]
                continue
            
            seconds = self.playlist[0]["duration"]
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60

            self.votes = []
            self.votes.append({ 'user' : self.current.requester, 'value' : 'keep' })
            await self.current.channel.send('Now playing - `{}` - [{:02d}h:{:02d}m:{:02d}s] - requested by *{}*'.format(self.playlist[0]["song"].replace('`', '\\`'), round(hours), round(minutes), round(seconds), DisplayName.name(self.playlist[0]['requester'])))

            await self.play_next_song.wait()
            
            self.total_playing_time = datetime.datetime.now() - datetime.datetime.now()
            # Song is done
            if self.playlist[0].get("Error", None):
                await self.current.channel.send("An error occurred trying to play `{}` - removing from the queue.".format(self.playlist[0]["song"].replace('`', '\\`')))
                # We got an error
            elif self.repeat:
                self.playlist.append(self.playlist[0])
            del self.playlist[0]


    async def create_youtube_entry(self, ctx, song: str, title: str, duration):

        opts = {
            'buffersize': '20000000',
            'f': 'bestaudio',
            'default_search': 'auto',
            'quiet': True
        }
        volume = self.settings.getServerStat(ctx.message.guild, "Volume")
        defVolume = self.settings.getServerStat(ctx.message.guild, "DefaultVolume")
        if volume:
            volume = float(volume)
        else:
            if defVolume:
                volume = float(self.settings.getServerStat(ctx.message.guild, "DefaultVolume"))
            else:
                # No volume or default volume in settings - go with 60%
                volume = 0.6

        try:

            # Get the link to the video - should prevent dead urls
            entry = await downloader.Downloader().extract_info(
                self.bot.loop,
                song,
                download=False,
                process=True,    # ASYNC LAMBDAS WHEN
                retry_on_error=True,
                playlist=False
            )

            # Reset the song to the direct link
            song = entry['formats'][len(entry['formats'])-1]['url']


            # Create a rewrite player because why not...
            # PS - Look at all these shitty attempts?!
            #
            # audioProc = subprocess.Popen( [ "youtube-dl", "-q", "-o", "-", song ], stdout=subprocess.PIPE )
            # before_args = "-reconnect_streamed 1"
            # audioProc = subprocess.Popen( "youtube-dl -o - \"" + song + "\"", shell=True, stdout=subprocess.PIPE )
            # ffsource = discord.FFmpegPCMAudio(audioProc.stdout, before_options=before_args, pipe=True)
            # audioProc = subprocess.Popen( "youtube-dl -o - \"" + song + "\" | ffmpeg -i pipe:0 -ac 2 -f s16le -ar 48000 pipe:1 -reconnect_streamed 1", stdout=subprocess.PIPE, shell=True )
            #
            # VICTORY!
            #
            audioProc = subprocess.Popen( "ffmpeg -hide_banner -loglevel error -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2 -i \"" + song + "\" -ac 2 -f s16le -ar 48000 pipe:1", stdout=subprocess.PIPE, shell=True )
            self.audio_process = audioProc
            rawAudio = discord.PCMAudio(audioProc.stdout)
            volumeSource = discord.PCMVolumeTransformer(rawAudio)
            #
            # ffsource = discord.FFmpegPCMAudio(song, before_options=before_args, pipe=True)
            # volumeSource = discord.PCMVolumeTransformer(ffsource)
            self.voice.play(volumeSource, after=self.toggle_next)

        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'.format(type(e).__name__, e)
            await ctx.channel.send(fmt)
            return False
        else:
            #self.voice.volume = volume
            self.voice.source.volume = volume
            entry = VoiceEntry(ctx.message, self.voice, title, duration, ctx)
            return entry

class Music:
    """Voice related commands.

    Works in multiple servers at once.
    """
    def __init__(self, bot, settings):
        self.bot = bot
        self.voice_states = {}
        self.settings = settings
        self.downloader = downloader.Downloader()
        # Regex for extracting urls from strings
        self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")

    # Proof of concept stuff for reloading cog/extension
    def _is_submodule(self, parent, child):
        return parent == child or child.startswith(parent + ".")

    @asyncio.coroutine
    async def on_loaded_extension(self, ext):
        # See if we were loaded
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        # Clear any previous playlist settings
        for guild in self.bot.guilds:
            self.settings.setServerStat(guild, "Playlisting", None)
            self.settings.setServerStat(guild, "PlaylistRequestor", None)

    async def _check_role(self, ctx):
        isAdmin = ctx.author.permissions_in(ctx.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
            for role in ctx.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True
        if isAdmin:
            # Admin and bot-admin override
            return True
        promoArray = self.settings.getServerStat(ctx.guild, "DJArray")
        if not len(promoArray):
            await ctx.send("There are no dj roles set yet.  Use `{}adddj [role]` to add some.".format(ctx.prefix))
            return None
        for aRole in promoArray:
            for role in ctx.author.roles:
                if str(role.id) == str(aRole["ID"]):
                    return True
        return False

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot, self.settings)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await channel.connect(timeout=10, reconnect=False)
        state = self.get_voice_state(channel.guild)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    async def _user_in_voice(self, ctx):
        # Check if we're in a voice channel
        # voiceChannel = self.bot.voice_client_in(ctx.message.guild)
        voiceChannel = None
        for client in self.bot.voice_clients:
            if client.guild == ctx.guild:
                # Found it?
                voiceChannel = client.channel

        if not voiceChannel:
            # We're not in a voice channel
            return None

        channel = ctx.message.channel
        author  = ctx.message.author
        server  = ctx.message.guild

        # Check if user is admin
        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True
        if isAdmin:
            return True
        
        # Here, user is not admin - make sure they're in the voice channel
        # Check if the user in question is in a voice channel
        if ctx.message.author in voiceChannel.members:
            return True
        # If we're here - we're not admin, and not in the same channel, deny
        return False

    @asyncio.coroutine
    async def on_voice_state_update(self, user, beforeState, afterState):
        if not user.guild:
            return
        # Get our member on the same server as the user
        botMember = DisplayName.memberForID(self.bot.user.id, user.guild)
        botVoice = botMember.voice
        if not botVoice:
            # We're not in a voice channel - don't care
            return
        voiceChannel = botVoice.channel

        if not beforeState.channel is voiceChannel:
            # Not pertaining to our channel
            return

        if len(beforeState.channel.members) > 1:
            # More than one user
            return

        # if we made it here - then we're alone - disconnect
        server = beforeState.channel.guild
        state = self.get_voice_state(server)

        self.settings.setServerStat(server, "Volume", None)

        if state.is_playing():
            player = state.voice
            player.stop()
        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            state.playlist = []
            state.repeat = False
            await state.voice.disconnect()
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def pmax(self, ctx, *, max_songs = None):
        """Sets the maximum number of songs to load from a playlist (owner only).
        The higher the number, the long it takes to load (-1 to load all).
        Default is 25."""

        # Only allow owner
        isOwner = self.settings.isOwner(ctx.author)
        if isOwner == None:
            msg = 'I have not been claimed, *yet*.'
            await ctx.channel.send(msg)
            return
        elif isOwner == False:
            msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
            await ctx.channel.send(msg)
            return
        
        if max_songs == None:
            lev = 25
            try:
                lev = self.settings.serverDict['PlistMax']
            except KeyError:
                pass
            if lev == -1:
                await ctx.channel.send("The current playlist max is set to: *All songs*")
            elif lev == 1:
                await ctx.channel.send("The current playlist max is set to: *1 song*")
            else:
                await ctx.channel.send("The current playlist max is set to: *{} songs*".format(lev))
        else:
            try:
                max_songs = int(max_songs)
            except Exception:
                await ctx.channel.send("Playlist max must be an integer.")
                return
            if max_songs < -1:
                max_songs = -1
            self.settings.serverDict['PlistMax'] = max_songs
            if max_songs == -1:
                await ctx.channel.send("The playlist max is now set to: *All songs*")
            elif max_songs == 1:
                await ctx.channel.send("The playlist max is now set to: *1 song*")
            else:
                await ctx.channel.send("The playlist max is now set to: *{} songs*".format(max_songs))


    @commands.command(pass_context=True, no_pm=True)
    async def pdelay(self, ctx, *, delay = None):
        """Sets the delay in seconds between loading songs in playlist (owner only).
        Lower delay may result in Youtube block - default is 3."""

        # Only allow owner
        isOwner = self.settings.isOwner(ctx.author)
        if isOwner == None:
            msg = 'I have not been claimed, *yet*.'
            await ctx.channel.send(msg)
            return
        elif isOwner == False:
            msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
            await ctx.channel.send(msg)
            return
        
        if delay == None:
            lev = 3
            try:
                lev = self.settings.serverDict['PlistDelay']
            except KeyError:
                pass
            if lev == 1:
                await ctx.channel.send("The current playlist load delay is set to: *1 second*")
            else:
                await ctx.channel.send("The current playlist load delay is set to: *{} seconds*".format(lev))
        else:
            try:
                delay = int(delay)
            except Exception:
                await ctx.channel.send("Delay must be an integer.")
                return
            if delay < 0:
                delay = 0
            self.settings.serverDict['PlistDelay'] = delay
            if delay == 1:
                await ctx.channel.send("The playlist load delay is now set to: *1 second*")
            else:
                await ctx.channel.send("The playlist load delay is now set to: *{} seconds*".format(delay))


    @commands.command(pass_context=True, no_pm=True)
    async def plevel(self, ctx, *, level = None):
        """Sets the access level for playlists (owner only):
        0 = Everyone
        1 = Bot Admins and up
        2 = Admins and up
        3 = Owner
        4 = Disabled (default)"""

        # Only allow owner
        isOwner = self.settings.isOwner(ctx.author)
        if isOwner == None:
            msg = 'I have not been claimed, *yet*.'
            await ctx.channel.send(msg)
            return
        elif isOwner == False:
            msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
            await ctx.channel.send(msg)
            return

        if level == None:
            # Get the current level
            lev = 4
            pword = "Disabled"
            try:
                lev = self.settings.serverDict['PlistLevel']
            except KeyError:
                pass

            if lev == 0:
                pword = "Everyone"
            elif lev == 1:
                pword = "Bot Admins"
            elif lev == 2:
                pword = "Admins"
            elif lev == 3:
                pword = "Owner"
            await ctx.channel.send("The current playlist level is set to: *{} ({})*".format(pword, lev))
        else:
            try:
                level = int(level)
            except Exception:
                await ctx.channel.send("Level must be an integer from 0 to 4.")
                return
            if level < 0 or level > 4:
                await ctx.channel.send("Level must be an integer from 0 to 4.")
                return
            pword = "Disabled"
            if level == 0:
                pword = "Everyone"
            elif level == 1:
                pword = "Bot Admins"
            elif level == 2:
                pword = "Admins"
            elif level == 3:
                pword = "Owner"
            self.settings.serverDict['PlistLevel'] = level
            await ctx.channel.send("Playlist level is now set to: *{} ({})*".format(pword, level))

    @commands.command(pass_context=True, no_pm=True)
    async def pskip(self, ctx):
        """Skips loading the rest of a playlist - can only be done by the requestor, or bot-admin/admin."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        try:
            playlisting = self.settings.getServerStat(ctx.guild, "Playlisting")
            requestor   = self.settings.getServerStat(ctx.guild, "PlaylistRequestor")
        except Exception:
            playlisting = None
            requestor   = None

        if playlisting == None:
            await ctx.channel.send("I'm not currently adding a playlist.")
            return

        # Check requestor id - and see if we have it
        if not ctx.author.id == requestor:
            #admin/bot-admin only
            isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
            if not isAdmin:
                checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
                for role in ctx.message.author.roles:
                    for aRole in checkAdmin:
                        # Get the role that corresponds to the id
                        if str(aRole['ID']) == str(role.id):
                            isAdmin = True
            if not isAdmin:
                await ctx.channel.send('You do not have sufficient privileges to access this command.')
                return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return
        elif userInVoice == None:
            await ctx.channel.send('I\'m not in a voice channel.  Use the `{}summon`, `{}join [channel]` or `{}play [song]` commands to start playing something.'.format(ctx.prefix, ctx.prefix, ctx.prefix))
            return

        # At this point - we *should* have everything we need to cancel - so do it
        self.settings.setServerStat(ctx.guild, "Playlisting", None)
        self.settings.setServerStat(ctx.guild, "PlaylistRequestor", None)

        await ctx.send("Playlist loading canceled!")


    @commands.command(pass_context=True, no_pm=True)
    async def playingin(self, ctx):
        """Shows the number of servers the bot is currently playing music in."""
        playing_in = 0
        for serv in self.bot.guilds:
            state = self.get_voice_state(serv)
            if state.voice and state.voice.is_playing():
                playing_in += 1
        
        if len(self.bot.guilds) == 1:
            msg = "Playing music in {} of {} server.".format(playing_in, len(self.bot.guilds))
        else:
            msg = "Playing music in {} of {} servers.".format(playing_in, len(self.bot.guilds))

        await ctx.channel.send(msg)


    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel : str = None):
        """Joins a voice channel."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # No channel sent
        if channel == None:
            await ctx.channel.send("Usage: `{}join [channel name]`".format(ctx.prefix))
            return
        
        found_channel = None
        for c in ctx.guild.channels:
            # Go through our channels, look for VoiceChannels,
            # and compare names
            if not type(c) is discord.VoiceChannel:
                continue
            # Check name case-insensitive
            if c.name.lower() == channel.lower():
                # Found it!
                found_channel = c
                break
                
        if found_channel == None:
            # We didn't find it...
            await ctx.channel.send("I couldn't find that voice channel...")
            return
        
        # At this point - we have a channel - set channel to found_channel
        channel = found_channel
        
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await ctx.channel.send('Already in a voice channel...')
        except discord.InvalidArgument:
            await ctx.channel.send('This is not a voice channel...')
        except asyncio.TimeoutError:
            await ctx.channel.send("I timed out when connecting to that channel...")
        except:
            await ctx.channel.send("Unknown error when connecting...")
        else:
            await ctx.channel.send('Ready to play audio in ' + channel.name)


    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return

        state = self.get_voice_state(ctx.message.guild)

        if state.is_playing():
            await ctx.channel.send('I\`m already playing in a channel, Join me there instead! :D')
            return
        
        if ctx.message.author.voice is None:
            await ctx.channel.send('You are not in a voice channel.')
            return False
        summoned_channel = ctx.message.author.voice.channel

        if state.voice is None:
            success = False
            try:
                await self.create_voice_client(summoned_channel)
            except discord.ClientException:
                msg = 'Already in a voice channel...'
            except discord.InvalidArgument:
                msg = 'This is not a voice channel...'
            except asyncio.TimeoutError:
                msg = "I timed out when connecting to that channel..."
            except:
                msg = "Unknown error when connecting..."
            else:
                msg = 'Ready to play audio in ' + summoned_channel.name
                success = True
            if ctx.command.name == "summon":
                await ctx.send(msg)
            return success
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song : str = None):
        """Plays a song.

        If there is a song currently in the queue, then it is
        queued until the next song is done playing.

        This command automatically searches as well from YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
        """

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return

        if song == None:
            await ctx.channel.send('Sweet.  I will *totally* add nothing to my list.  Thanks for the *superb* musical suggestion...')
            return

        state = self.get_voice_state(ctx.message.guild)
        
        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return
        else:
            # Check if we're already adding a playlist
            try:
                playlisting = self.settings.getServerStat(ctx.guild, "Playlisting")
            except Exception:
                playlisting = None
            if playlisting:
                await ctx.channel.send("I'm currently importing a playlist - please wait for that to finish before enqueuing more songs.")
                return

        # Send a starter message
        message = await ctx.send("Collecting sound bytes...")

        song = song.strip('<>')

        # Check if url - if not, remove /
        matches = re.finditer(self.regex, song)
        matches = list(matches)
        if not len(matches):
            song = song.replace('/', '')
        
        # First we check for our permission level
        author_perms = 0
        checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
        for role in ctx.author.roles:
            for aRole in checkAdmin:
                # Get the role that corresponds to the id
                if str(aRole['ID']) == str(role.id):
                    author_perms = 1
        if ctx.message.author.permissions_in(ctx.message.channel).administrator:
            author_perms = 2
        if self.settings.isOwner(ctx.author):
            author_perms = 3

        # Get server info
        playlist_level = 4
        try:
            playlist_level = self.settings.serverDict['PlistLevel']
        except KeyError:
            pass
        playlist_max = 25
        try:
            playlist_max = self.settings.serverDict['PlistMax']
        except KeyError:
            pass
        playlist_delay = 3
        try:
            playlist_delay = self.settings.serverDict['PlistDelay']
        except KeyError:
            pass
        
        if author_perms >= playlist_level:
            plist = True
        else:
            plist = False
        info = await self.downloader.extract_info(
                self.bot.loop,
                song,
                download=False,
                process=False,
                playlist=plist
            )

        if not info:
            # We got nothing
            await message.edit(content="Whoops!  Looks like that wasn't a supported link...")
            return

        if info.get('url', '').startswith('ytsearch'):
            index = 0
            if self.settings.getServerStat(ctx.guild, "YTMultiple"):
                info['url'] = info['url'].replace("ytsearch:", "ytsearch5:")
            info = await self.downloader.extract_info(
                self.bot.loop,
                #song,
                info['url'],
                download=False,
                process=True,    # ASYNC LAMBDAS WHEN
                retry_on_error=True,
                playlist=False
            )
            if not info:
                await message.edit(content="No results for that search :(")
                return
            if not len(info.get('entries', [])):
                # empty list, no data
                await message.edit(content="No results for that search :(")
                return
            if len(info['entries']) > 1:
                # Show a list
                list_show = "Please select the number of the video you'd like to add:"
                index, message = await PickList.Picker(
                    title=list_show,
                    list=[x['title'] for x in info['entries']],
                    ctx=ctx,
                    message=message
                ).pick()

                if index < 0:
                    if index == -3:
                        await message.edit(content="Something went wrong :(")
                    elif index == -2:
                        await message.edit(content="Times up!  We can search for music another time.")
                    else:
                        await message.edit(content="Aborting!  We can search for music another time.")
                    return
                    
            # Got a song!
            song = info['entries'][index]['webpage_url']
            info = await self.downloader.extract_info(self.bot.loop, song, download=False, process=False)

        if "entries" in info:
            # Multiple songs - let's add what we need
            #
            if author_perms >= playlist_level:
                # We can add up to playlist_max
                entries_added = 0
                entries_skipped = 0
                
                await message.edit(content="Adding songs from playlist...")

                entries = info['entries']
                entries = list(entries)

                # Get the dropped song's positionn in the playlist
                index = 0
                found = False
                for e in entries:
                    if not e.get('ie_key', '').lower() == 'youtube':
                        index += 1
                        continue
                    eurl = e.get('url')
                    if "v="+eurl in info['webpage_url']:
                        # We found it!
                        found = True
                        break
                    index += 1

                if not found:
                    index = 0
                
                if playlist_max > -1:
                    if len(entries) - index > playlist_max:
                        total_songs = playlist_max
                    else:
                        total_songs = len(entries) - index
                else:
                    total_songs = len(entries) - index

                # Lock our playlisting
                self.settings.setServerStat(ctx.guild, "Playlisting", True)
                # Add requestor's id
                self.settings.setServerStat(ctx.guild, "PlaylistRequestor", ctx.author.id)

                checkIndex = 0
                for entry in entries:
                    # Start with the song that was dropped
                    if checkIndex < index:
                        checkIndex += 1
                        continue
                    # Increment our count
                    entries_added += 1
                    if not entry.get('ie_key', '').lower() == 'youtube':
                        entries_skipped += 1
                        continue

                    # Edit our status message
                    await message.edit(content="Enqueuing song {} of {} from `{}` ({} skipped)...".format(entries_added, total_songs, info['title'].replace('`', '\\`'), entries_skipped))
                    
                    # Create a new video url and get info
                    new_url = "https://youtube.com/v/" + entry.get('url', '')
                    try:
                        entry = await self.downloader.extract_info(
                            self.bot.loop,
                            new_url,
                            download=False,
                            process=True,    # ASYNC LAMBDAS WHEN
                            retry_on_error=True,
                            playlist=False
                        )
                    except Exception:
                        entries_skipped += 1
                        continue
                    if entry == None:
                        entries_skipped += 1
                        continue

                    # Get duration info
                    seconds = entry.get('duration')
                    hours = seconds // 3600
                    minutes = (seconds % 3600) // 60
                    seconds = seconds % 60

                    # Add the song
                    #state.playlist.append({ 'song': entry.get('title'), 'duration': entry.get('duration'), 'ctx': ctx, 'requester': ctx.message.author, 'raw_song': entry['formats'][len(entry['formats'])-1]['url']})
                    state.playlist.append({ 'song': entry.get('title'), 'duration': entry.get('duration'), 'ctx': ctx, 'requester': ctx.message.author, 'raw_song': new_url })

                    # Check if we're out of bounds
                    if playlist_max > -1 and entries_added >= playlist_max:
                        break
                    # Try not to get blocked :/
                    await asyncio.sleep(playlist_delay)
                    # Check if we're still playing
                    state = self.get_voice_state(ctx.message.guild)
                    if state.voice == None or self.settings.getServerStat(ctx.guild, "Playlisting") == None:
                        if entries_added == 1:
                            await message.edit(content="*{}* Cancelled - *1* song loaded.".format(info['title']))
                        else:
                            await message.edit(content="*{}* Cancelled - *{}* songs loaded.".format(info['title'], entries_added))
                        return
                # Unlock our playlisting
                self.settings.setServerStat(ctx.guild, "Playlisting", None)
                self.settings.setServerStat(ctx.guild, "PlaylistRequestor", None)

                if entries_added-entries_skipped == 1:
                    await message.edit(content="Enqueued *{}* song from `{}` - (*{}* skipped)".format(entries_added-entries_skipped, info['title'].replace('`', '\\`'), entries_skipped))
                else:
                    await message.edit(content="Enqueued *{}* songs from `{}` - (*{}* skipped)".format(entries_added-entries_skipped, info['title'].replace('`', '\\`'), entries_skipped))
                return
            else:
                # We don't have enough perms
                entries = info['entries']
                entries = list(entries)
                entry = entries[0]
                if entry.get('ie_key', '').lower() == 'youtube':
                    # Create a new video url and get info
                    new_url = "https://youtube.com/v/" + entry.get('url', '')
                    try:
                        entry = await self.downloader.extract_info(
                            self.bot.loop,
                            new_url,
                            download=False,
                            process=True,    # ASYNC LAMBDAS WHEN
                            retry_on_error=True,
                            playlist=False
                        )
                    except Exception:
                        entry = None
                        pass
                    info = entry
                else:
                    info = None
                
                if info == None:
                    await message.edit(content="I couldn't load that song :(")
                    return

        if info.get('title') == None:
            # We got nothing
            await message.edit(content="Whoops!  Looks like that wasn't a supported link...")
            return
        
        seconds = info.get('duration', 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        state.playlist.append({ 'song': info.get('title'), 'duration': info.get('duration'), 'ctx': ctx, 'requester': ctx.message.author, 'raw_song': song})
        # state.playlist.append({ 'song': info.get('title'), 'duration': info.get('duration'), 'ctx': ctx, 'requester': ctx.message.author, 'raw_song': info['formats'][len(info['formats'])-1]['url']})
        await message.edit(content='Enqueued - `{}` - [{:02d}h:{:02d}m:{:02d}s] - requested by *{}*'.format(info.get('title').replace('`', '\\`'), round(hours), round(minutes), round(seconds), DisplayName.name(ctx.message.author)))

    
    @commands.command(pass_context=True, no_pm=True)
    async def repeat(self, ctx, *, yes_no = None):
        """Checks or sets whether to repeat or not."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return

        state = self.get_voice_state(ctx.message.guild)
        current = state.repeat
        setting_name = "Repeat"
        if yes_no == None:
            if current:
                msg = "{} currently *enabled.*".format(setting_name)
            else:
                msg = "{} currently *disabled.*".format(setting_name)
        elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
            yes_no = True
            if current == True:
                msg = '{} remains *enabled*.'.format(setting_name)
            else:
                msg = '{} is now *enabled*.'.format(setting_name)
        elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
            yes_no = False
            if current == False:
                msg = '{} remains *disabled*.'.format(setting_name)
            else:
                msg = '{} is now *disabled*.'.format(setting_name)
        else:
            msg = "That's not a valid setting."
            yes_no = current
        if not yes_no == None and not yes_no == current:
            state.repeat = yes_no
        await ctx.send(msg)

        
    @commands.command(pass_context=True, no_pm=True)
    async def willrepeat(self, ctx):
        """Displays whether or not repeat is active."""
        # Check user credentials
        state = self.get_voice_state(ctx.message.guild)
        if state.repeat:
            await ctx.channel.send('Repeat is currently **on**.')
        else:
            await ctx.channel.send('Repeat is currently **off**.')



    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value = None):
        """Sets the volume of the currently playing song."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return
        elif userInVoice == None:
            await ctx.channel.send('I\'m not in a voice channel.  Use the `{}summon`, `{}join [channel]` or `{}play [song]` commands to start playing something.'.format(ctx.prefix, ctx.prefix, ctx.prefix))
            return
        
        if not value == None:
            # We have a value, let's make sure it's valid
            try:
                value = int(value)
            except Exception:
                await ctx.channel.send('Volume must be an integer.')
                return

        state = self.get_voice_state(ctx.message.guild)
        if state.is_playing():
            player = state.voice
            if value == None:
                # No value - output current volume
                await ctx.channel.send('Current volume is {:.0%}'.format(player.source.volume))
                return
            if value < 0:
                value = 0
            if value > 100:
                value = 100
            player.source.volume = value / 100
            self.settings.setServerStat(ctx.message.guild, "Volume", player.source.volume)
            await ctx.channel.send('Set the volume to {:.0%}'.format(player.source.volume))
        else:
            # Not playing anything
            await ctx.channel.send('Not playing anything right now...')
            return

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return
        elif userInVoice == None:
            await ctx.channel.send('I\'m not in a voice channel.  Use the `{}summon`, `{}join [channel]` or `{}play [song]` commands to start playing something.'.format(ctx.prefix, ctx.prefix, ctx.prefix))
            return

        state = self.get_voice_state(ctx.message.guild)
        if state.voice.is_playing():
            player = state.voice
            player.pause()
            state.total_playing_time += (datetime.datetime.now() - state.start_time)
            state.is_paused = True

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return
        elif userInVoice == None:
            await ctx.channel.send('I\'m not in a voice channel.  Use the `{}summon`, `{}join [channel]` or `{}play [song]` commands to start playing something.'.format(ctx.prefix, ctx.prefix, ctx.prefix))
            return

        state = self.get_voice_state(ctx.message.guild)
        if state.voice.is_paused():
            player = state.voice
            player.resume()
            state.start_time = datetime.datetime.now()
            state.is_paused = False


    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.

        This also clears the queue.
        """

        channel = ctx.message.channel
        author  = ctx.message.author
        server  = ctx.message.guild

        # Check for role requirements
        requiredRole = self.settings.getServerStat(server, "RequiredStopRole")
        if requiredRole == "":
            #admin only
            isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
            if not isAdmin:
                checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
                for role in ctx.message.author.roles:
                    for aRole in checkAdmin:
                        # Get the role that corresponds to the id
                        if str(aRole['ID']) == str(role.id):
                            isAdmin = True
            if not isAdmin:
                await channel.send('You do not have sufficient privileges to access this command.')
                return
        else:
            #role requirement
            hasPerms = False
            for role in author.roles:
                if str(role.id) == str(requiredRole):
                    hasPerms = True
            if not hasPerms and not ctx.message.author.permissions_in(ctx.message.channel).administrator:
                await channel.send('You do not have sufficient privileges to access this command.')
                return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return
        elif userInVoice == None:
            await ctx.channel.send('I\'m not in a voice channel.  Use the `{}summon`, `{}join [channel]` or `{}play [song]` commands to start playing something.'.format(ctx.prefix, ctx.prefix, ctx.prefix))
            return

        server = ctx.message.guild
        state = self.get_voice_state(server)

        self.settings.setServerStat(ctx.message.guild, "Volume", None)

        # Reset our playlist-related vars
        self.settings.setServerStat(ctx.guild, "Playlisting", None)
        self.settings.setServerStat(ctx.guild, "PlaylistRequestor", None)

        if state.is_playing():
            player = state.voice
            player.stop()

        try:
            message = await ctx.channel.send('Stopping...')
            state.audio_player.cancel()
            del self.voice_states[server.id]
            state.playlist = []
            state.repeat = False
            await state.voice.disconnect(force=True)
            await message.edit(content="I've left the voice channel!")
        except Exception as e:
            print("Stop exception: {}".format(e))
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return
        elif userInVoice == None:
            await ctx.channel.send('I\'m not in a voice channel.  Use the `{}summon`, `{}join [channel]` or `{}play [song]` commands to start playing something.'.format(ctx.prefix, ctx.prefix, ctx.prefix))
            return

        state = self.get_voice_state(ctx.message.guild)
        if not state.voice.is_playing():
            await ctx.channel.send('Not playing anything right now...')
            return

        # Get song requester
        state = self.get_voice_state(ctx.message.guild)
        requester = state.playlist[0]['requester']
        requesterAdmin = requester.permissions_in(ctx.message.channel).administrator
        if not requesterAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in requester.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        requesterAdmin = True


        # Check if user is admin
        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True
        if isAdmin:
            # Check if the requester is also an admin
            if not requesterAdmin:
                # Auto skip.
                await ctx.channel.send('My *Admin-Override* module is telling me to skip.')
                state.skip()
                return

        voter = ctx.message.author
        vote = await self.has_voted(ctx.message.author, state.votes)
        if vote != False:
            vote["value"] = 'skip'
        else:
            state.votes.append({ 'user': ctx.message.author, 'value': 'skip' })
        
        result = await self._vote_stats(ctx)

        if(result["total_skips"] >= result["total_keeps"]):
            await ctx.channel.send('Looks like skips WINS! sorry guys, skipping the song...')
            state.skip()
        # if voter == state.current.requester:
        # 	await ctx.channel.send('Requester requested skipping...')
        # 	state.skip()
        # elif voter.id not in state.skip_votes:
        # 	state.skip_votes.add(voter.id)
        # 	total_votes = len(state.skip_votes)
        # 	if total_votes >= 3:
        # 		await ctx.channel.send('Skip vote passed, skipping the song...')
        # 		state.skip()
        # 	else:
        # 		await ctx.channel.send('Skip vote added, currently at [{}/3]'.format(total_votes))
        # else:
        # 	await ctx.channel.send('You have already voted to skip this.')

    # @commands.command(pass_context=True, no_pm=True)
    # async def keep(self, ctx):
    # 	"""Vote to keep a song. The song requester can automatically skip.
    # 	"""

    @commands.command(pass_context=True, no_pm=True)
    async def keep(self, ctx):
        """Vote to keep a song."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return
        elif userInVoice == None:
            await ctx.channel.send('I\'m not in a voice channel.  Use the `{}summon`, `{}join [channel]` or `{}play [song]` commands to start playing something.'.format(ctx.prefix, ctx.prefix, ctx.prefix))
            return

        state = self.get_voice_state(ctx.message.guild)
        if not state.is_playing():
            await ctx.channel.send('Not playing anything right now...')
            return

        voter = ctx.message.author
        vote = await self.has_voted(ctx.message.author, state.votes)
        if vote != False:
            vote["value"] = 'keep'
        else:
            state.votes.append({ 'user': ctx.message.author, 'value': 'keep' })
        
        await self._vote_stats(ctx)

    
    @commands.command(pass_context=True, no_pm=True)
    async def unvote(self, ctx):
        """Remove your song vote."""

        state = self.get_voice_state(ctx.message.guild)
        if not state.is_playing():
            await ctx.channel.send('Not playing anything right now...')
            return

        voter = ctx.message.author
        vote = await self.has_voted(ctx.message.author, state.votes)
        if vote != False:
            for voted in state.votes:
                if(ctx.message.author == voted["user"]):
                    # Found our vote - remove it
                    state.votes.remove(voted)
        else:
            await ctx.channel.send('Your non-existent vote has been removed.')

        result = await self._vote_stats(ctx)

        if(result["total_skips"] >= result["total_keeps"]):
            await ctx.channel.send('Looks like skips WINS! sorry guys, skipping the song...')
            state.skip()
        
    
    @commands.command(pass_context=True, no_pm=True)
    async def vote_stats(self, ctx):
        return await self._vote_stats(ctx)

    async def _vote_stats(self, ctx):
        state = self.get_voice_state(ctx.message.guild)
        total_skips = 0
        total_keeps = 0
        for vote in state.votes:
            XP = self.settings.getUserStat(vote["user"], ctx.message.guild, "XP")
            if vote["value"] == 'skip':
                total_skips = total_skips + XP
            else:
                total_keeps = total_keeps + XP
        
        await ctx.channel.send('**Total Votes**:\nKeeps Score: *{:,}*\nSkips Score : *{:,}*'.format(total_keeps, total_skips))

        return {'total_skips': total_skips, 'total_keeps': total_keeps}

    async def has_voted(self, user , votes):

        for vote in votes:
            if(user == vote["user"]):
                return vote

        return False


    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Shows info about currently playing."""

        state = self.get_voice_state(ctx.message.guild)
        if state.voice == None or not state.voice.is_playing():
            await ctx.channel.send('Not playing anything.')
        else:
            diff_time = state.total_playing_time  + (datetime.datetime.now() - state.start_time)

            if state.is_paused:
                diff_time = state.total_playing_time

            seconds = diff_time.total_seconds()
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60

            #percent = diff_time.total_seconds() / state.current.player.duration * 100
            dSeconds = state.playlist[0]["duration"]
            percent = diff_time.total_seconds() / dSeconds * 100

            await ctx.channel.send('Now playing - `{}` [at {:02d}h:{:02d}m:{:02d}s] - {}%'.format(state.playlist[0]["song"].replace('`', '\\`'),round(hours), round(minutes), round(seconds), round(percent, 2)))


    @commands.command(pass_context=True, no_pm=True)
    async def playlist(self, ctx):
        """Shows current songs in the playlist."""
        state = self.get_voice_state(ctx.message.guild)
        if len(state.playlist) <= 0:
                        await ctx.channel.send('No songs in the playlist')
                        return
        # Get our length
        totalSongs = len(state.playlist)
        if totalSongs > 15:
            playlist_string  = '**__Current Playlist (showing 1-15 out of {}):__**\n\n'.format(totalSongs)
        else:
            playlist_string  = '**__Current Playlist (1-{}):__**\n\n'.format(totalSongs)
        #playlist_string += '```Markdown\n'
        count = 1
        total_seconds = 0
        for i in state.playlist:
            if count > 15:
                break

            seconds = i["duration"]
            if not seconds:
                playlist_string += '{}. `{}` - [Unknown time] - requested by *{}*\n'.format(count, str(i["song"]).replace('`', '\\`'), DisplayName.name(i['requester']))
            else:
                total_seconds += seconds
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60
                playlist_string += '{}. `{}` - [{:02d}h:{:02d}m:{:02d}s] - requested by *{}*\n'.format(count, str(i["song"]).replace('`', '\\`'),round(hours), round(minutes), round(seconds), DisplayName.name(i['requester']))
            count = count + 1
        #playlist_string += '```'
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        playlist_string  += '\n**Total Time: **[{:02d}h:{:02d}m:{:02d}s]'.format(round(hours), round(minutes), round(seconds))
        if state.repeat:
            playlist_string += '\nRepeat is **on**'

        await ctx.channel.send(playlist_string)


    @commands.command(pass_context=True, no_pm=True)
    async def removesong(self, ctx, idx : int = None):
        """Removes a song in the playlist by the index."""

        # Role check
        chk = await self._check_role(ctx)
        if chk == False:
            await ctx.send("You need a dj role to do that!")
            return
        elif chk == None:
            return

        # Check user credentials
        userInVoice = await self._user_in_voice(ctx)
        if userInVoice == False:
            await ctx.channel.send('You\'ll have to join the same voice channel as me to use that.')
            return
        elif userInVoice == None:
            await ctx.channel.send('I\'m not in a voice channel.  Use the `{}summon`, `{}join [channel]` or `{}play [song]` commands to start playing something.'.format(ctx.prefix, ctx.prefix, ctx.prefix))
            return

        channel = ctx.message.channel
        author  = ctx.message.author
        server  = ctx.message.guild

        canRemove = False
        # Check for role requirements
        requiredRole = self.settings.getServerStat(server, "RequiredStopRole")
        if requiredRole == "":
            #admin only
            isAdmin = author.permissions_in(channel).administrator
            if isAdmin:
                canRemove = True
        else:
            #role requirement
            hasPerms = False
            for role in author.roles:
                if str(role.id) == str(requiredRole):
                    hasPerms = True
            if hasPerms:
                canRemove = True

        if idx == None:
            await ctx.channel.send('Umm... Okay.  I successfully removed *0* songs from the playlist.  That\'s what you wanted, right?')
            return

        if not type(idx) == int:
            await ctx.channel.send('Indexes need to be integers, yo.')
            return

        idx = idx - 1
        state = self.get_voice_state(ctx.message.guild)
        if idx < 0 or idx >= len(state.playlist):
            await ctx.channel.send('Invalid song index, please refer to `{}playlist` for the song index.'.format(ctx.prefix))
            return
        current = state.playlist[idx]
        if idx == 0:
            await ctx.channel.send('Cannot delete currently playing song, use `{}skip` instead'.format(ctx.prefix))
            return
        if not current['requester'].id == ctx.message.author.id:
            # Not the owner of the song - check if we *can* delete
            if not canRemove:
                await channel.send('You do not have sufficient privileges to remove *other* users\' songs.')
                return
        await ctx.channel.send('Deleted `{}` from playlist'.format(str(current["song"]).replace('`', '\\`')))
        del state.playlist[idx]
