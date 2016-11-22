import asyncio
import discord
import time
from   discord.ext import commands
from   discord import errors
from   Cogs import ReadableTime

# Import the cogs

from Cogs import Settings
from Cogs import Xp
from Cogs import Admin
from Cogs import Channel
from Cogs import Feed
from Cogs import Reddit
from Cogs import Comic
from Cogs import Lists
from Cogs import Bot
from Cogs import Example
from Cogs import Humor
from Cogs import Help
from Cogs import Uptime
from Cogs import MadLibs
from Cogs import DrBeer
from Cogs import Setup
from Cogs import Invite

# This should be the main soul of the bot - everything should load from here
bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'), description='A bot that does stuff.... probably')
# Initialize some things
jsonFile = "Settings.json"
# Open our token
with open('token.txt', 'r') as f:
	token = f.read()


# Create our cog classes
cogList = []

# Settings
settings = Settings.Settings(bot, jsonFile)
cogList.append(settings)

# Examples - there are 2 parts here, Example, and Music
example = Example.Example(bot)
music = Example.Music(bot, settings)
cogList.append(example)
cogList.append(music)

# Xp
xp = Xp.Xp(bot, settings)
cogList.append(xp)

# Admin
admin = Admin.Admin(bot, settings)
cogList.append(admin)

# Channel
channel = Channel.Channel(bot, settings)
cogList.append(channel)

# Feed
feed = Feed.Feed(bot, settings, xp)
cogList.append(feed)

# Reddit
reddit = Reddit.Reddit(bot, settings, 100)
cogList.append(reddit)

# Comics
comic = Comic.Comic(bot, settings)
cogList.append(comic)

# Lists
lists = Lists.Lists(bot, settings)
cogList.append(lists)

# Bot
botCog = Bot.Bot(bot, settings)
cogList.append(botCog)

# Humor
humor = Humor.Humor(bot)
cogList.append(humor)

# Humor
uptime = Uptime.Uptime(bot)
cogList.append(uptime)

# MadLibs
madlibs = MadLibs.MadLibs(bot, settings)
cogList.append(madlibs)

# Dr Beer

drbeer = DrBeer.DrBeer(bot, settings)
cogList.append(drbeer)

# Setup

setup = Setup.Setup(bot, settings)
cogList.append(setup)

# Invite

invite = Invite.Invite(bot)
cogList.append(invite)

# Help - Must be last
#help = Help.Help(bot, cogList)
#cogList.append(help)


# Main bot events
@bot.event
async def on_ready():
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	settings.flushSettings()

@bot.event
async def on_voice_state_update(before, after):
	# Let's get all the users in our voice channel, if we're in one

	if not bot.is_voice_connected(before.server):
		return

	voiceChannel = bot.voice_client_in(before.server)
	if not voiceChannel:
		return
	voiceChannel = voiceChannel.channel

	if not before.voice_channel:
		# Not pertaining to our channel
		return

	# Get all the members connected
	voiceList = voiceChannel.voice_members

	if len(voiceList) > 1:
		# We are not alone - hang out still
		return

	# if we made it here - then we're alone - disconnect
	server = before.server
	state = music.get_voice_state(server)

	settings.setServerStat(server, "Volume", None)

	if state.is_playing():
		player = state.player
		player.stop()
	try:
		state.audio_player.cancel()
		del music.voice_states[server.id]
		await state.voice.disconnect()
	except:
		pass

@bot.event
async def on_member_remove(member):
	server = member.server
	settings.removeUser(member, server)

@bot.event
async def on_server_join(server):
	settings.checkServer(server)
	owner = server.owner
	# Let's message hello in the main chat - then pm the owner
	msg = 'Hello everyone! Thanks for inviting me to your server!\n\nFeel free to put me to work.\n\nYou can get a list of my command by typing `$help` either in chat or in PM. (PM is probably better though - I can get *kinda* spammy)'
	await bot.send_message(server, msg)
	msg = 'Hey there - I\'m new here!\n\nWhenever you have a chance, maybe take the time to set me up by typing `$setup` in the main chat.  Thanks!'
	await bot.send_message(owner, msg)

@bot.event
async def on_server_remove(server):
	settings.removeServer(server)

@bot.event
async def on_channel_delete(channel):
	settings.removeChannelID(channel.id, channel.server)

@bot.event
async def on_member_join(member):
	server = member.server
	# Initialize the user
	settings.checkUser(member, server)
	fmt = 'Welcome *{}* to *{}*!'.format(member.name, server.name)
	await bot.send_message(server, fmt.format(member, server))
	# Scan through roles - find "Entry Level" and set them to that

	defaultRole = settings.getServerStat(server, "DefaultRole")
	rules       = settings.getServerStat(server, "Rules")
	
	if defaultRole:
		newRole = discord.utils.get(server.roles, id=str(defaultRole))
		await bot.add_roles(member, newRole)
		fmt = 'You\'ve been auto-assigned the role **{}**!'.format(newRole.name)
		await bot.send_message(server, fmt)

	help = 'Type `$help` for a list of available user commands.'

	# PM User
	fmt = "*{}* Rules:\n{}\n\n{}".format(server.name, rules, help)
	await bot.send_message(member, fmt)

@bot.event
async def on_member_update(before, after):
	server = after.server

	# Check if the member went offline and log the time
	if str(after.status).lower() == "offline":
		currentTime = int(time.time())
		settings.setUserStat(after, server, "LastOnline", currentTime)
			
	settings.checkServer(server)
	try:
		channelMOTDList = settings.getServerStat(server, "ChannelMOTD")
	except KeyError:
		channelMOTDList = []
		
	if len(channelMOTDList) > 0:
		members = 0
		membersOnline = 0
		for member in server.members:
			members += 1
			if str(member.status).lower() == "online":
				membersOnline += 1
			
	for id in channelMOTDList:
		channel = bot.get_channel(id['ID'])
		if channel:
			motd = id['MOTD'] # A markdown message of the day
			listOnline = id['ListOnline'] # Yes/No - do we list all online members or not?	
			if listOnline.lower() == "yes":
				msg = '{} - ({}/{} users online)'.format(motd, int(membersOnline), int(members))
			else:
				msg = motd
			await bot.edit_channel(channel, topic=msg)	

@bot.event
async def on_message(message):
	if not message.server:
		# This wasn't said in a server, process commands, then return
		await bot.process_commands(message)
		return

	# Admin Override - always allow admin commands
	#if message.author.permissions_in(message.channel).administrator:
		#await bot.process_commands(message)
		#return
	
	# Check if we need to ignore or delete the message
	ignore = delete = False
	for cog in cogList:
		check = cog.message(message)
		if check['Delete']:
			delete = True
		if check['Ignore']:
			ignore = True
	
	if delete:
		await bot.delete_message(message)
	if ignore:
		return
	
	settings.flushSettings()
	await bot.process_commands(message)
	
	

# Add our cogs 
# bot.add_cog(Music(bot))

# Module and Class are named the same, must use Settings.Settings to call
i = 0
for cog in cogList:
	i += 1
	bot.add_cog(cog)

print("{} Cog(s) Loaded.".format(i))
	
bot.run(token)
