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
from   Cogs import Time
import youtube_dl
import functools

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

    @commands.command()
    async def roll(self, ctx, dice : str):
        """Rolls a dice in NdN±N format."""
        try:
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
        except Exception:
            await ctx.channel.send('Format has to be in NdN±N!')
            return
        numbers = []
        number_sum = 0
        for r in range(rolls):
            roll = random.randint(1, limit)
            number_sum += roll
            numbers.append(str(roll))

        number_string = ", ".join(numbers)
        number_string = "```\n= Dice Rolls ========================\n" + number_string
        if not add == 0:
            sign = "+"
            if add < 0:
                sign = ""
            number_string += "\n\n= Pre-Total =========================\n{}".format(number_sum)
            number_string += "\n\n= Modifier ==========================\n{}{}".format(sign, add)
        
        number_string += "\n\n= Final Total =======================\n{}```".format(number_sum + add)
        await ctx.channel.send(number_string)

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
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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

        local_time = Time.Time.getUserTime(self, ctx.author, self.settings, member.joined_at)
        if not local_time['zone']:
            time_str = "{} UTC".format(local_time['time'])
        else:
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
                await asyncio.sleep(3)
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
            await self.current.channel.send('Now playing *{}* - [{:02d}h:{:02d}m:{:02d}s] - requested by *{}*'.format(self.playlist[0]["song"], round(hours), round(minutes), round(seconds), DisplayName.name(self.playlist[0]['requester'])))

            await self.play_next_song.wait()

            self.total_playing_time = datetime.datetime.now() - datetime.datetime.now()
            # Song is done
            if "Error" in self.playlist[0]:
                await self.current.channel.send("An error occurred trying to play *{}* - removing from the queue.".fromat(self.playlist[0]["song"]))
                # We got an error
                # Remove the song and jump back
                del self.playlist[0]
                continue

            if self.repeat:
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

    async def onready(self):
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
        voice = await channel.connect()
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
            state.voice = await summoned_channel.connect() # self.bot.join_voice_channel(summoned_channel)
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

        #await state.songs.put(entry)

        opts = {
            'f': 'bestaudio',
            'default_search': 'auto',
            'quiet': True
        }

        song = song.strip('<>')

        # Check if url - if not, remove /
        matches = re.finditer(self.regex, song)
        matches = list(matches)
        if not len(matches):
            song = song.replace('/', '')

        #info = await self.bot.loop.run_in_executor(None, func)
        
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
                playlist=plist,
                download=False,
                process=False
            )

        if info.get('url', '').startswith('ytsearch'):
            info = await self.downloader.extract_info(
                self.bot.loop,
                song,
                download=False,
                process=True,    # ASYNC LAMBDAS WHEN
                retry_on_error=True,
                playlist=False
            )
            if not info:
                return
            if not all(info.get('entries', [])):
                # empty list, no data
                return
            song = info['entries'][0]['webpage_url']
            info = await self.downloader.extract_info(self.bot.loop, song, download=False, process=False)

        if "entries" in info:
            # Multiple songs - let's add what we need
            #
            if author_perms >= playlist_level:
                # We can add up to playlist_max
                entries_added = 0
                entries_skipped = 0
                
                mess = await ctx.channel.send("Adding songs from playlist...")

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
                    await mess.edit(content="Enqueuing song {} of {} from *{}* ({} skipped)...".format(entries_added, total_songs, info['title'], entries_skipped))
                    
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
                            await mess.edit(content="*{}* Cancelled - *1* song loaded.".format(info['title']))
                        else:
                            await mess.edit(content="*{}* Cancelled - *{}* songs loaded.".format(info['title'], entries_added))
                        return
                # Unlock our playlisting
                self.settings.setServerStat(ctx.guild, "Playlisting", None)
                self.settings.setServerStat(ctx.guild, "PlaylistRequestor", None)

                await mess.edit(content=" ")
                if entries_added-entries_skipped == 1:
                    await ctx.channel.send("Enqueued *{}* song from *{}* - (*{}* skipped)".format(entries_added-entries_skipped, info['title'], entries_skipped))
                else:
                    await ctx.channel.send("Enqueued *{}* songs from *{}* - (*{}* skipped)".format(entries_added-entries_skipped, info['title'], entries_skipped))
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
                    await ctx.send("I couldn't load that song :(")
                    return
        
        seconds = info.get('duration', 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        state.playlist.append({ 'song': info.get('title'), 'duration': info.get('duration'), 'ctx': ctx, 'requester': ctx.message.author, 'raw_song': song})
        # state.playlist.append({ 'song': info.get('title'), 'duration': info.get('duration'), 'ctx': ctx, 'requester': ctx.message.author, 'raw_song': info['formats'][len(info['formats'])-1]['url']})
        await ctx.channel.send('Enqueued - *{}* - [{:02d}h:{:02d}m:{:02d}s] - requested by *{}*'.format(info.get('title'), round(hours), round(minutes), round(seconds), DisplayName.name(ctx.message.author)))

    
    @commands.command(pass_context=True, no_pm=True)
    async def repeat(self, ctx, *, repeat = None):
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

        if repeat == None:
            # Just checking
            if state.repeat:
                await ctx.channel.send('Repeat is currently **on**.')
            else:
                await ctx.channel.send('Repeat is currently **off**.')
            return
        elif repeat.lower() == "on" or repeat.lower() == "yes" or repeat.lower() == "true":
            # Trying to enable repeat
            if state.repeat:
                await ctx.channel.send('Repeat will remain **on**.')
            else:
                state.repeat = True
                await ctx.channel.send('Repeat is now **on**.')
            return
        elif repeat.lower() == "off" or repeat.lower() == "no" or repeat.lower() == "false":
            # Trying to disable repeat
            if not state.repeat:
                await ctx.channel.send('Repeat will remain **off**.')
            else:
                state.repeat = False
                await ctx.channel.send('Repeat is now **off**.')
            return
        else:
            # No working variable - let's just output repeat status
            if state.repeat:
                await ctx.channel.send('Repeat is currently **on**.')
            else:
                await ctx.channel.send('Repeat is currently **off**.')
            return


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
            if not hasPerms:
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
            state.audio_player.cancel()
            del self.voice_states[server.id]
            state.playlist = []
            state.repeat = False
            await state.voice.disconnect()
        except:
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

            await ctx.channel.send('Now playing - *{}* [at {:02d}h:{:02d}m:{:02d}s] - {}%'.format(state.playlist[0]["song"],round(hours), round(minutes), round(seconds), round(percent, 2)))


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
            total_seconds += seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60

            playlist_string += '{}. *{}* - [{:02d}h:{:02d}m:{:02d}s] - requested by *{}*\n'.format(count, str(i["song"]),round(hours), round(minutes), round(seconds), DisplayName.name(i['requester']))
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
        await ctx.channel.send('Deleted *{}* from playlist'.format(str(current["song"])))
        del state.playlist[idx]
