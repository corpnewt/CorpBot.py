import asyncio
import discord
import random
import configparser
import os
import configparser
import json
from discord.ext import commands
from discord import errors
import globals

bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'), description='A that does stuff.... probably')
settingsFile = "./Settings.txt"
userFile = "./Users.txt"
jsonFile = "Settings.json"
globals.serverList = {}

  ###           ###
 # Initial Setup #
###           ###

def checkServer(server, serverDict):
    # Assumes server = discord.Server and serverList is a dict
    if not "Servers" in serverDict:
        # Let's add an empty placeholder
        serverDict["Servers"] = []
    found = False
    for x in serverDict["Servers"]:
        if x["Name"] == server.name:
            # We found our server
            found = True
            # print("Found our server: " + server.name)

    if found == False:
        # We didn't locate our server
        # print("Server not located, adding...")
        newServer = { "Name" : server.name, "ID" : server.id,
											"AutoRole" : "No", # No/ID/Position
											"DefaultRole" : "1",
											"MinimumXPRole" : "1",
											"XPApprovalChannel" : "",
											"HourlyXP" : "3",
											"IncreasePerRank" : "1",
											"RequireOnline" : "Yes",
											"AdminUnlimited" : "Yes",
											"XPPromote" : "Yes",
											"PromoteBy" : "Array", # Position/Array
											"MaxPosition" : "5",
											"RequiredXP" : "0",
											"DifficultyMultiplier" : "0",
											"PadXPRoles" : "0",
											"XPDemote" : "No",
											"PromotionArray" : [],
											"Links" : [],
											"Members" : [] }
        serverDict["Servers"].append(newServer)

    return serverDict

def checkUser(user, server, serverDict):
	# Make sure our server exists in the list
	serverDict = checkServer(server, serverDict)
	# Check for our username
	found = False
	for x in serverDict["Servers"]:
		if x["ID"] == server.id:
			# We found our server, now to iterate users
			for y in x["Members"]:
				if y["ID"] == user.id:
					found = True
					# Check XP, ID, Discriminator
					if not "XP" in y:
						# print("No XP - adding...")
						y["XP"] = 0
					if not "XPReserve" in y:
						# print("No XP - adding...")
						y["XPReserve"] = 10
					if not "ID" in y:
						# print("No ID - adding...")
						y["ID"] = user.id
					if not "Discriminator" in y:
						# print("No Discriminator - adding...")
						y["Discriminator"] = user.discriminator
					# print("Found our user: " + userName)
			if not found:
				# We didn't locate our user - add them
				newUser = { "Name" : user.name, 
							"XP" : 0,
							"XPReserve" : 10,
							"ID" : user.id, 
							"Discriminator" : user.discriminator }
				x["Members"].append(newUser)
	# All done - return
	return serverDict

def incrementStat(user, server, serverDict, stat, incrementAmount):
    serverDict = checkUser(user, server, serverDict)
    for x in serverDict["Servers"]:
        if x["ID"] == server.id:
            # We found our server, now to iterate users
            for y in x["Members"]:
                if y["ID"] == user.id:
                    tempStat = int(y[stat])
                    tempStat += int(incrementAmount)
                    y[stat] = tempStat
    return serverDict
	
def getUserStat(user, server, serverDict, stat):
	# Make sure our server exists in the list
	serverDict = checkServer(server, serverDict)
	# Check for our username
	found = False
	for x in serverDict["Servers"]:
		if x["ID"] == server.id:
			# We found our server, now to iterate users
			for y in x["Members"]:
				if y["ID"] == user.id:
					return y[stat]
	return None
	
def setUserStat(user, server, serverDict, stat, value):
	# Make sure our server exists in the list
	serverDict = checkServer(server, serverDict)
	# Check for our username
	found = False
	for x in serverDict["Servers"]:
		if x["ID"] == server.id:
			# We found our server, now to iterate users
			for y in x["Members"]:
				if y["ID"] == user.id:
					y[stat] = value
	
def getServerStat(server, serverDict, stat):
	# Make sure our server exists in the list
	serverDict = checkServer(server, serverDict)
	# Check for our username
	found = False
	for x in serverDict["Servers"]:
		if x["ID"] == server.id:
			# We found our server, now to iterate users
			return x[stat]
	return None
	
def setServerStat(server, serverDict, stat, value):
	# Make sure our server exists in the list
	serverDict = checkServer(server, serverDict)
	# Check for our username
	found = False
	for x in serverDict["Servers"]:
		if x["ID"] == server.id:
			# We found our server, now to iterate users
			x[stat] = value
		
async def flushSettings():
	while not bot.is_closed:
		print("Flushed Settings")
		# print("ServerList Flush: {}".format(globals.serverList))
		# Dump the json
		json.dump(globals.serverList, open(jsonFile, 'w'), indent=2)
		await asyncio.sleep(900) # runs only every 15 minutes
	'''await bot.wait_until_ready()
	counter = 0
	channel = discord.Object(id='channel_id_here')
	while not bot.is_closed:
		counter += 1
		await bot.send_message(channel, counter)
		await asyncio.sleep(900) # task runs every 15 minutes'''

async def addXP():
	while not bot.is_closed:
		print("Adding XP")
		
		for server in bot.servers:
			
			#for role in server.roles:
				#if role.position == 1:
					# print("Entry role: {}".format(role.name))
			
			# Iterate through the servers and add them
			globals.serverList = checkServer(server, globals.serverList)
			xpAmount = getServerStat(server, globals.serverList, "HourlyXP")
			onlyOnline = getServerStat(server, globals.serverList, "RequireOnline")
			for user in server.members:
				# print('{}: {}'.format(user.name, str(user.status)))
				bumpXP = False
				if onlyOnline.lower() == "yes":
					if str(user.status).lower() == "online":
						bumpXP = True
				else:
					bumpXP = True
					
				if bumpXP:
					boost = int(getServerStat(server, globals.serverList, "IncreasePerRank"))
					maxPos = int(getServerStat(server, globals.serverList, "MaxPosition"))
					biggest = 0
					xpPayload = 0
					for role in user.roles:
						if role.position <= maxPos and role.position > biggest:
							biggest = role.position
						
					# xpPayload = int(xpAmount)+biggest*boost
					
					xpPayload = int(xpAmount)
					
					#print("{} at level {} out of {}, gets {} XP".format(user.id, biggest, maxPos, xpPayload))
					
					globals.serverList = incrementStat(user, server, globals.serverList, "XPReserve", xpPayload)
					
		await quickFlush()
		await asyncio.sleep(3600) # runs only every 1 minute  #### CHANGE TO 3600 AT SOME POINT ####
		
async def quickFlush():
	# Dump the json
	json.dump(globals.serverList, open(jsonFile, 'w'), indent=2)

# --------------------------------------------- #

  ###                        ###
 # BEGIN: Setup for Playlists #
###                        ###

if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    # note that on windows this DLL is automatically provided for you
    discord.opus.load_opus('opus')

class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = '*{0.title}* uploaded by {0.uploader} and requested by {1.display_name}'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()

class Music:
    """Voice related commands.

    Works in multiple servers at once.
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel : discord.Channel):
        """Joins a voice channel."""
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('Already in a voice channel...')
        except discord.InvalidArgument:
            await self.bot.say('This is not a voice channel...')
        else:
            await self.bot.say('Ready to play audio in ' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say('You are not in a voice channel.')
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song : str):
        """Plays a song.

        If there is a song currently in the queue, then it is
        queued until the next song is done playing.

        This command automatically searches as well from YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
        """
        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            await self.bot.say('Enqueued ' + str(entry))
            await state.songs.put(entry)

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int):
        """Sets the volume of the currently playing song."""

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.

        This also clears the queue.
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.

        3 skip votes are needed for the song to be skipped.
        """

        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return

        voter = ctx.message.author
        if voter == state.current.requester:
            await self.bot.say('Requester requested skipping song...')
            state.skip()
        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 3:
                await self.bot.say('Skip vote passed, skipping song...')
                state.skip()
            else:
                await self.bot.say('Skip vote added, currently at [{}/3]'.format(total_votes))
        else:
            await self.bot.say('You have already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Shows info about the currently played song."""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes)
            await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current, skip_count))
			
  ###                      ###
 # END: Setup for Playlists #
###                      ###

# --------------------------------------------- #

  ###           ###
 # BEGIN: Events #
###           ###

@bot.event
async def on_member_join(member):
	server = member.server
	
	# Initialize User
	globals.serverList = checkUser(member, server, globals.serverList)
	
	fmt = 'Welcome {0.mention} to {1.name}!'
	await bot.send_message(server, fmt.format(member, server))
	# Scan through roles - find "Entry Level" and set them to that
	
	autoRole = getServerStat(server, globals.serverList, "AutoRole")
	defaultRole = getServerStat(server, globals.serverList, "DefaultRole")
	
	if autoRole.lower() == "position":
		newRole = discord.utils.get(server.roles, position=int(defaultRole))
		await bot.add_roles(member, newRole)
	elif autoRole.lower() == "id":
		newRole = discord.utils.get(server.roles, id=defaultRole)
		await bot.add_roles(member, newRole)
		
	await quickFlush()
		
		
	
@bot.event
async def on_ready():
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	# Now we give JSON a try
	if os.path.exists(jsonFile):
		globals.serverList = json.load(open(jsonFile))
	else:
		# No Users.json file - create a placeholder
		globals.serverList = {}
	
	for server in bot.servers:
		# Iterate through the servers and add them
		globals.serverList = checkServer(server, globals.serverList)		
		for user in server.members:
			globals.serverList = checkUser(user, server, globals.serverList)
		
	# await flushSettings()
	bot.loop.create_task(flushSettings())
	bot.loop.create_task(addXP())
	
@bot.event
async def on_message(message):
	# Process commands - then check for mentions
	await bot.process_commands(message)

	'''if message.author == bot.user:
		return
	
	for user in message.mentions:
		print('User: {}'.format(user.name))
		if user == bot.user:
			msg = 'Hello {0.author.mention}'.format(message)
			await bot.send_message(message.channel, msg)'''
	# For adding roles - http://discordpy.readthedocs.io/en/latest/api.html#discord.Client.add_roles
	
  ###           ###
 # END:   Events #
###           ###

# --------------------------------------------- #

  ###             ###
 # BEGIN: Commands #
###             ###

@bot.command()
async def add(left : int, right : int):
    """Adds two numbers together."""
    await bot.say(left + right)

@bot.command()
async def roll(dice : str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await bot.say('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await bot.say(result)

@bot.command(description='For when you wanna settle the score some other way')
async def choose(*choices : str):
    """Chooses between multiple choices."""
    await bot.say(random.choice(choices))
	
@bot.command()
async def joined(member : discord.Member):
    """Says when a member joined."""
    await bot.say('{0.name} joined in {0.joined_at}'.format(member))
	
@bot.command(pass_context=True)
async def getoffline(ctx):
	"""Forces the server to account for offline members - only important to the backend."""
	theServer = ctx.message.author.server
	#print("Hello")
	await bot.request_offline_members(theServer)
	for user in theServer.members:
		print('User: {}'.format(user.name))
	#print('{}'.format(theServer.members))


@bot.command(pass_context=True)
async def playgame(ctx, game : str = None):
	"""Sets the playing status of the bot (admin only)."""
	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	# Only allow admins to change server stats
	if not isAdmin:
		await bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
		return
	
	if game == None:
		await bot.change_status(game=None)
		return
	
	await bot.change_status(game=discord.Game(name=game))
	
	
	
@bot.command(pass_context=True)
async def setxp(ctx, member : discord.Member = None, xpAmount : int = None):
	"""Sets an absolute value for the member's xp (admin only)."""
	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	# Only allow admins to change server stats
	if not isAdmin:
		await bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
		return
		
	# Check for formatting issues
	if xpAmount == None or member == None:
		msg = 'Usage: `$setxp [member] [amount]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	if not type(xpAmount) is int:
		msg = 'Usage: `$setxp [member] [amount]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	if xpAmount < 0:
		msg = 'Usage: `$setxp [member] [amount]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	if type(member) is str:
		try:
			member = discord.utils.get(message.server.members, name=member)
		except:
			print("That member does not exist")
			return
			
	setUserStat(member, ctx.message.server, globals.serverList, "XP", xpAmount)
	msg = '{}\'s XP was set to {}!'.format(member.name, xpAmount)				
	await bot.send_message(ctx.message.channel, msg)
			
			
@setxp.error
async def setxp_error(ctx, error):
    # do stuff
	msg = 'setxp Error: {}'.format(ctx)
	await bot.say(msg)
	
	
	
@bot.command(pass_context=True)
async def setxpreserve(ctx, member : discord.Member = None, xpAmount : int = None):
	"""Set's an absolute value for the member's xp reserve (admin only)."""
	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	# Only allow admins to change server stats
	if not isAdmin:
		await bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
		return
		
	# Check for formatting issues
	if xpAmount == None or member == None:
		msg = 'Usage: `$setxpreserve [member] [amount]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	if not type(xpAmount) is int:
		msg = 'Usage: `$setxpreserve [member] [amount]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	if xpAmount < 0:
		msg = 'Usage: `$setxpreserve [member] [amount]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	if type(member) is str:
		try:
			member = discord.utils.get(message.server.members, name=member)
		except:
			print("That member does not exist")
			return
			
	setUserStat(member, ctx.message.server, globals.serverList, "XPReserve", xpAmount)
	msg = '{}\'s XPReserve was set to {}!'.format(member.name, xpAmount)				
	await bot.send_message(ctx.message.channel, msg)
			
			
@setxpreserve.error
async def setxpreserve_error(ctx, error):
    # do stuff
	msg = 'setxp Error: {}'.format(ctx)
	await bot.say(msg)
	
	
	
@bot.command(pass_context=True)
async def xp(ctx, member : discord.Member = None, xpAmount : int = None):
	"""Gift xp to other members."""
	# Check for formatting issues
	if xpAmount == None or member == None:
		msg = 'Usage: `$xp [member] [amount]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	if not type(xpAmount) is int:
		msg = 'Usage: `$xp [member] [amount]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	if type(member) is str:
		try:
			member = discord.utils.get(message.server.members, name=member)
		except:
			print("That member does not exist")
			return
	
	
	# Initialize User
	globals.serverList = checkUser(member, ctx.message.server, globals.serverList)

	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	adminUnlim = getServerStat(ctx.message.server, globals.serverList, "AdminUnlimited")
	reserveXP = getUserStat(ctx.message.author, ctx.message.server, globals.serverList, "XPReserve")
	minRole = getServerStat(ctx.message.server, globals.serverList, "MinimumXPRole")
	
	approve = True
	decrement = True
	
	# MinimumXPRole
	if ctx.message.author.top_role.position < int(minRole):
		approve = False
		msg = 'You don\'t have the permissions to give xp.'
	
	if xpAmount > int(reserveXP):
		approve = False
		msg = 'You can\'t give {} xp, you only have {}'.format(xpAmount, reserveXP)
	
	if ctx.message.author == member:
		approve = False
		msg = 'You can\'t give yourself xp!  *Nice try...*'
	
	if xpAmount < 0:
		msg = 'Only mods can take away xp!'
		approve = False
	
	# Check admin last - so it overrides anything else
	if isAdmin and adminUnlim.lower() == "yes":
		# No limit - approve
		approve = True
		decrement = False
	
	userRole = member.top_role.position
	
	if approve:
		msg = '{} was given {} XP!'.format(member.name, xpAmount)
		globals.serverList = incrementStat(member, ctx.message.server, globals.serverList, "XP", xpAmount)
		if decrement:
			globals.serverList = incrementStat(ctx.message.author, ctx.message.server, globals.serverList, "XPReserve", (-1*xpAmount))
		
		xpPromote = getServerStat(ctx.message.server, globals.serverList, "XPPromote")
		xpDemote = getServerStat(ctx.message.server, globals.serverList, "XPDemote")
		promoteBy = getServerStat(ctx.message.server, globals.serverList, "PromoteBy")
		requiredXP = int(getServerStat(ctx.message.server, globals.serverList, "RequiredXP"))
		maxPosition = getServerStat(ctx.message.server, globals.serverList, "MaxPosition")
		padXP = getServerStat(ctx.message.server, globals.serverList, "PadXPRoles")
		difficulty = int(getServerStat(ctx.message.server, globals.serverList, "DifficultyMultiplier"))
		
		userXP = getUserStat(member, ctx.message.server, globals.serverList, "XP")
		userXP = int(userXP)+(int(requiredXP)*int(padXP))
				
		if xpPromote.lower() == "yes":
			# We use XP to promote - let's check our levels
			if promoteBy.lower() == "position":
				# We use the position to promote
				gotLevels = 0
				for x in range(0, int(maxPosition)+1):
					# Let's apply our difficulty multiplier
					
					print("{} + {}".format((requiredXP*x), ((requiredXP*x)*difficulty)))
					
					required = (requiredXP*x) + (requiredXP*difficulty)
					print("Level: {}\nXP: {}".format(x, required))
					if userXP >= required:
						gotLevels = x
				if gotLevels > int(maxPosition):
					# If we got too high - let's even out
					gotLevels = int(maxPosition)
				#print("Got: {} Have: {}".format(gotLevels, userRole))
				#if gotLevels > userRole:
					# We got promoted!
					#msg = '{} was given {} XP, and was promoted to {}!'.format(member.name, xpAmount, discord.utils.get(ctx.message.server.roles, position=gotLevels).name)
				gotLevels+=1
				for x in range(0, gotLevels):
					# fill in all the roles between
					for role in ctx.message.server.roles:
						if role.position < gotLevels:
							if not role in member.roles:
								# Only add if we need to
								await bot.add_roles(member, role)
								msg = '{} was given {} XP, and was promoted to {}!'.format(member.name, xpAmount, discord.utils.get(ctx.message.server.roles, position=gotLevels).name)
			elif promoteBy.lower() == "array":
				promoArray = getServerStat(ctx.message.server, globals.serverList, "PromotionArray")
				serverRoles = ctx.message.server.roles
				for role in promoArray:
					# Iterate through the roles, and add what we can
					if int(role['XP']) <= userXP:
						# We *can* have this role, let's see if we already do
						currentRole = None
						for aRole in serverRoles:
							# Get the role that corresponds to the id
							if aRole.id == role['ID']:
								# We found it
								currentRole = aRole
						
						# Now see if we have it, and add it if we don't
						if not currentRole in member.roles:
							await bot.add_roles(member, currentRole)
							msg = '{} was given {} XP, and was promoted to {}!'.format(member.name, xpAmount, currentRole.name)
					else:
						if xpDemote.lower() == "yes":
							# Let's see if we have this role, and remove it.  Demote time!
							currentRole = None
							for aRole in serverRoles:
								# Get the role that corresponds to the id
								if aRole.id == role['ID']:
									# We found it
									currentRole = aRole
						
							# Now see if we have it, and add it if we don't
							if currentRole in member.roles:
								await bot.remove_roles(member, currentRole)
								msg = '{} was demoted from {}!'.format(member.name, currentRole.name)
							
							
	await bot.send_message(ctx.message.channel, msg)
	#await quickFlush()

@xp.error
async def getxp_error(ctx, error):
    # do stuff
	msg = 'xp Error: {}'.format(ctx)
	await bot.say(msg)
	
	
	
@bot.command(pass_context=True)
async def addrole(ctx, role : discord.Role = None, xp : int = None):
	"""Adds a new role to the xp promotion/demotion system (admin only)."""
	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	# Only allow admins to change server stats
	if not isAdmin:
		await bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
		return
		
	if role == None or xp == None:
		msg = 'Usage: `$addrole [role] [required xp]`'
		await bot.send_message(ctx.message.channel, msg)
		return

	if not type(xp) is int:
		msg = 'Usage: `$addrole [role] [required xp]`'
		await bot.send_message(ctx.message.channel, msg)
		return
		
	if type(role) is str:
		try:
			role = discord.utils.get(message.server.roles, name=role)
		except:
			print("That role does not exist")
			return
			
	# Now we see if we already have that role in our list
	promoArray = getServerStat(ctx.message.server, globals.serverList, "PromotionArray")
	
	for aRole in promoArray:
		# Get the role that corresponds to the id
		if aRole['ID'] == role.id:
			# We found it - throw an error message and return
			msg = '{} is already in the list.  Required xp: {}'.format(role.name, aRole['XP'])
			await bot.send_message(ctx.message.channel, msg)
			return
	
	# If we made it this far - then we can add it
	promoArray.append({ 'ID' : role.id, 'Name' : role.name, 'XP' : xp })
	setServerStat(ctx.message.server, globals.serverList, "PromotionArray", promoArray)
	
	msg = '{} added to list.  Required xp: {}'.format(role.name, xp)
	await bot.send_message(ctx.message.channel, msg)
	return

@addrole.error
async def addrole_error(ctx, error):
    # do stuff
	msg = 'addrole Error: {}'.format(ctx)
	await bot.say(msg)		

	
	
@bot.command(pass_context=True)
async def listroles(ctx):
	"""Lists all roles, id's, and xp requirements for the xp promotion/demotion system."""
	promoArray = getServerStat(ctx.message.server, globals.serverList, "PromotionArray")
	
	roleText = "Current Roles:\n"
	
	for arole in promoArray:
		roleText = '{}{} : {} : {} XP\n'.format(roleText, arole['Name'], arole['ID'], arole['XP'])
			
	await bot.send_message(ctx.message.channel, roleText)
	
	
	
	
@bot.command(pass_context=True)
async def removerole(ctx, role : discord.Role = None):
	"""Removes a role from the xp promotion/demotion system (admin only)."""
	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	# Only allow admins to change server stats
	if not isAdmin:
		await bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
		return
		
	if role == None:
		msg = 'Usage: `$removerole [role]`'
		await bot.send_message(ctx.message.channel, msg)
		return
		
	if type(role) is str:
		try:
			role = discord.utils.get(message.server.roles, name=role)
		except:
			print("That role does not exist")
			return
	
	# If we're here - then the role is a real one
	promoArray = getServerStat(ctx.message.server, globals.serverList, "PromotionArray")
	
	for aRole in promoArray:
		# Get the role that corresponds to the id
		if aRole['ID'] == role.id:
			# We found it - let's remove it
			promoArray.remove(aRole)
			setServerStat(ctx.message.server, globals.serverList, "PromotionArray", promoArray)
			msg = '{} removed successfully.'.format(aRole['Name'])
			await bot.send_message(ctx.message.channel, msg)
			return
	
	# If we made it this far - then we didn't find it
	msg = '{} not found in list.'.format(aRole['Name'])
	await bot.send_message(ctx.message.channel, msg)
	
@removerole.error
async def removerole_error(ctx, error):
    # do stuff
	msg = 'removerole Error: {}'.format(ctx)
	await bot.say(msg)		
	

	
@bot.command(pass_context=True)
async def autorole(ctx, setting : str = None, role : discord.Role = None):
	"""Sets the autorole value - can be No, ID, or Position (admin only)."""
	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	# Only allow admins to change server stats
	if not isAdmin:
		await bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
		return
	usageMessage = 'Usage: `$autorole [No/ID/Position] [role]`'
	if setting == None:
		await bot.send_message(ctx.message.channel, usageMessage)
		return
		
	if not type(setting) == str:
		await bot.send_message(ctx.message.channel, usageMessage)
		return
	
	if setting.lower() == "no":
		# We don't need a second var
		setServerStat(ctx.message.server, globals.serverList, "AutoRole", "No")
		msg = 'AutoRole set to No'
		await bot.send_message(ctx.message.channel, msg)
		return
		
	if role == None:
		await bot.send_message(ctx.message.channel, usageMessage)
		return
		
	if type(role) is str:
		try:
			role = discord.utils.get(message.server.roles, id=role)
		except:
			print("That role does not exist")
			return
		
	if setting.lower() == "id":
		# Found the role!  Let's add it
		setServerStat(ctx.message.server, globals.serverList, "AutoRole", "ID")
		setServerStat(ctx.message.server, globals.serverList, "DefaultRole", '{}'.format(role.id))
		msg = 'AutoRole set to ID: {}'.format(role.id)
		await bot.send_message(ctx.message.channel, msg)
		return
	
	if setting.lower() == "position":		
		# Found the role!  Let's add it
		setServerStat(ctx.message.server, globals.serverList, "AutoRole", "Position")
		setServerStat(ctx.message.server, globals.serverList, "DefaultRole", str(role.position))
		msg = 'AutoRole set to Position: {}'.format(role.position)
		await bot.send_message(ctx.message.channel, msg)
		return
		
	await bot.send_message(ctx.message.channel, usageMessage)
	return
	
	
@autorole.error
async def autorole_error(ctx, error):
    # do stuff
	msg = 'autorole Error: {}'.format(ctx)
	await bot.say(msg)		
		
		

@bot.command(pass_context=True)
async def stats(ctx, member: discord.Member = None):
	"""List the xp and xp reserve of a listed member."""
	# await bot.say("You tried this")
	if member is None:
		await bot.say('Usage: `$stats [member]`')
		return
	#if member is None:
	#	bot.say("Usage: $stats @MemberName")
	#	return

	# Ensure user is setup
	globals.serverList = checkUser(member, ctx.message.server, globals.serverList)
	# Get user's xp
	newStat = getUserStat(member, ctx.message.server, globals.serverList, "XP")
	newState = getUserStat(member, ctx.message.server, globals.serverList, "XPReserve")
	
	msg = 'User {} has `{}` XP, and can gift up to `{}` XP!'.format(member, newStat, newState)
	await bot.send_message(ctx.message.channel, msg)
	
	
	
@bot.command(pass_context=True)
async def getstat(ctx, stat : str = None, member : discord.Member = None):
	"""Gets the value for a specific stat for the listed member (case-sensitive)."""
	if member == None:
		member = ctx.message.author
		
	if str == None:
		msg = 'Usage: `$getstat [stat] [member]`'
		await bot.send_message(ctx.message.channel, msg)
		return

	if type(member) is str:
		try:
			member = discord.utils.get(message.server.members, name=member)
		except:
			print("That member does not exist")
			return
		
	if member is None:
		msg = 'Usage: `$getstat [stat] [member]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	
	try:
		newStat = getUserStat(member, ctx.message.author.server, globals.serverList, stat)
	except KeyError:
		msg = '"{}" is not a valid stat for {}'.format(stat, member.name)
		await bot.send_message(ctx.message.channel, msg)
		return
		
	msg = '{} for {} is {}'.format(stat, member.name, newStat)
	await bot.send_message(ctx.message.channel, msg)
	
# Catch errors for stat
@getstat.error
async def getstat_error(ctx, error):
    # do stuff
	msg = 'getstat Error: {}'.format(ctx)
	await bot.say(msg)

	
	
@bot.command(pass_context=True)
async def setsstat(ctx, stat : str = None, value : str = None):
	"""Sets a server stat (admin only)."""
	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	# Only allow admins to change server stats
	if not isAdmin:
		return
	
	if stat == None or value == None:
		msg = 'Usage: $setsstat Stat Value'
		await bot.send_message(ctx.message.channel, msg)
		return
		
	setServerStat(ctx.message.server, globals.serverList, stat, value)
	
	msg = '{} set to {}!'.format(stat, value)
	await bot.send_message(ctx.message.channel, msg)
	
	
@bot.command(pass_context=True)
async def getsstat(ctx, stat : str = None):
	"""Gets a server stat (admin only)."""
	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	# Only allow admins to change server stats
	if not isAdmin:
		return
	
	if stat == None:
		msg = 'Usage: `$getsstat [stat]`'
		await bot.send_message(ctx.message.channel, msg)
		return
		
	value = getServerStat(ctx.message.server, globals.serverList, stat)
	
	msg = '{} is currently {}!'.format(stat, value)
	await bot.send_message(ctx.message.channel, msg)
	
	
	
@bot.command(pass_context=True)
async def addlink(ctx, name : str = None, link : str = None):
	"""Add a link to the link list."""
	if name == None or link == None:
		msg = 'Usage: `$addlink "[link name]" [url]`'
		await bot.send_message(ctx.message.channel, msg)
		return
	
	linkList = getServerStat(ctx.message.server, globals.serverList, "Links")
	if linkList == None:
		linkList = []
	
	linkList.append({"Name" : name, "URL" : link})
	
	setServerStat(ctx.message.server, globals.serverList, "Links", linkList)
	
	msg = '{} added to link list!'.format(name)
	await bot.send_message(ctx.message.channel, msg)
	

@bot.command(pass_context=True)
async def link(ctx, name : str = None):	
	"""Retrieve a link from the link list."""
	if name == None or link == None:
		msg = 'Usage: `$link "[link name]"`'
		await bot.send_message(ctx.message.channel, msg)
		return
	
	linkList = getServerStat(ctx.message.server, globals.serverList, "Links")
	if linkList == None or linkList == []:
		msg = 'No links in list!  You can add some with the `$addlink "[link name]" [url]` command!'
		await bot.send_message(ctx.message.channel, msg)
		return
		
	for alink in linkList:
		if alink['Name'].lower() == name.lower():
			msg = '{}\n{}'.format(alink['Name'], alink['URL'])
			await bot.send_message(ctx.message.channel, msg)
	

	
	
@bot.command(pass_context=True)
async def links(ctx):	
	"""List all links in the link list."""
	linkList = getServerStat(ctx.message.server, globals.serverList, "Links")
	if linkList == None or linkList == []:
		msg = 'No links in list!  You can add some with the `$addlink "[link name]" [url]` command!'
		await bot.send_message(ctx.message.channel, msg)
		return
	
	linkText = ""
	
	for alink in linkList:
		linkText = '{}{}\n'.format(linkText, alink['Name'])
			
	await bot.send_message(ctx.message.channel, linkText)
	
	
	
@bot.command(pass_context=True)
async def removelink(ctx, name : str = None):
	"""Remove a link from the link list."""
	if name == None:
		msg = 'Usage: `$removelink "[link name]"`'
		await bot.send_message(ctx.message.channel, msg)
		return
	
	linkList = getServerStat(ctx.message.server, globals.serverList, "Links")
	if linkList == None or linkList == []:
		msg = 'No links in list!  You can add some with the `$addlink "[link name]" [url]` command!'
		await bot.send_message(ctx.message.channel, msg)
		return
		
	for alink in linkList:
		if alink['Name'].lower() == name.lower():
			linkList.remove(alink)
			setServerStat(ctx.message.server, globals.serverList, "Links", linkList)
			msg = '{} removed from link list!'.format(name)
			await bot.send_message(ctx.message.channel, msg)
			return
	
	msg = '{} not found in link list!'.format(name)
	await bot.send_message(ctx.message.channel, msg)
		
		
@bot.command(pass_context=True)
async def flush(ctx):
	"""Flush the bot settings to disk (admin only)."""
	isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
	# Only allow admins to change server stats
	if not isAdmin:
		return
	# Flush settings
	await quickFlush()
	
	
  ###             ###
 # END:   Commands #
###             ###

# --------------------------------------------- #

  ###       ###
 # Bot Start #
###       ###	
	
bot.add_cog(Music(bot))
# bot.loop.create_task(flushSettings())

bot.run('MjI1NzQ4MjAzMTUxMTYzMzkz.CrtkCA.B4VKoA1_mVAAL1jXbdGi3dY_cdw')

# --------------------------------------------- #

