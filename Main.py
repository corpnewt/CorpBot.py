import asyncio
import discord
import time
import os
from   discord.ext import commands
from   discord import errors
from   Cogs import ReadableTime

# Import the cogs

from Cogs import Settings
from Cogs import Xp
from Cogs import Admin
from Cogs import BotAdmin
from Cogs import Channel
from Cogs import Feed
from Cogs import Reddit
from Cogs import Comic
from Cogs import Lists
from Cogs import Bot
from Cogs import Example
from Cogs import Humor
from Cogs import Uptime
from Cogs import MadLibs
from Cogs import DrBeer
from Cogs import Setup
from Cogs import Invite
from Cogs import UrbanDict
from Cogs import Server
from Cogs import Fliptime
from Cogs import Remind
from Cogs import Face
from Cogs import Cats
from Cogs import EightBall
from Cogs import Calc
from Cogs import Time
from Cogs import Search
from Cogs import Eat
from Cogs import Profile
from Cogs import Ascii
from Cogs import Promote
from Cogs import MessageXp
from Cogs import Welcome
from Cogs import ServerStats
from Cogs import Strike
from Cogs import Debugging
from Cogs import CardsAgainstHumanity
from Cogs import ChatterBot

# Let's load our prefix file
prefix = '$'
if os.path.exists('prefix.txt'):
	with open('prefix.txt') as f:
		prefix = f.read()
	if not prefix:
		prefix = '$'
# Set up debugging
debug = False
if os.path.exists('debug.txt'):
	debug = True
# This should be the main soul of the bot - everything should load from here
bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), pm_help=None, description='A bot that does stuff.... probably')
# Initialize some things
jsonFile = "Settings.json"
deckFile = "deck.json"
corpSiteAuth = "corpSiteAuth.txt"
# Open our token
with open('token.txt', 'r') as f:
	token = f.read().strip()

# Create our cog classes
cogList = []

# Settings
settings = Settings.Settings(bot, jsonFile)
cogList.append(settings)

# Examples - there are 2 parts here, Example, and Music
example = Example.Example(bot, settings)
music = Example.Music(bot, settings)
cogList.append(example)
cogList.append(music)

# Xp
xp = Xp.Xp(bot, settings)
cogList.append(xp)

# Admin
admin = Admin.Admin(bot, settings)
cogList.append(admin)

# BotAdmin
botadmin = BotAdmin.BotAdmin(bot, settings)
cogList.append(botadmin)

# Channel
channel = Channel.Channel(bot, settings)
cogList.append(channel)

# Feed
feed = Feed.Feed(bot, settings, xp, prefix)
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

# Urban Dictionary
urban = UrbanDict.UrbanDict(bot, settings)
cogList.append(urban)

# Server Info
server = Server.Server(bot, settings)
cogList.append(server)

# Flip
fliptime = Fliptime.Fliptime(bot, settings)
cogList.append(fliptime)

# Remind
remind = Remind.Remind(bot, settings)
cogList.append(remind)

# Faces
face = Face.Face(bot, settings)
cogList.append(face)

# Cats
cats = Cats.Cats(bot, settings)
cogList.append(cats)

# EightBall
eightball = EightBall.EightBall(bot)
cogList.append(eightball)

# Calc
calc = Calc.Calc(bot)
cogList.append(calc)

# Time
atime = Time.Time(bot, settings)
cogList.append(atime)

# LMG(B)(DDG)TFY
search = Search.Search(bot, corpSiteAuth)
cogList.append(search)

# Eat something...
eat = Eat.Eat(bot)
cogList.append(eat)

# Ascii
askey = Ascii.Ascii(bot)
cogList.append(askey)

# Profile
prof = Profile.Profile(bot, settings)
cogList.append(prof)

# Promote/Demote
prom = Promote.Promote(bot, settings)
cogList.append(prom)

# MessageXp
messageXp = MessageXp.MessageXp(bot, settings)
cogList.append(messageXp)

# Welcome
welcome = Welcome.Welcome(bot, settings)
cogList.append(welcome)

# Server Stats
serverstats = ServerStats.ServerStats(bot, settings)
cogList.append(serverstats)

# Strike
strike = Strike.Strike(bot, settings)
cogList.append(strike)

# Debugging
debugging = Debugging.Debugging(bot, settings, debug)
cogList.append(debugging)

# CardsAgainstHumanity
if os.path.exists(deckFile):
	cah = CardsAgainstHumanity.CardsAgainstHumanity(bot)
	cogList.append(cah)

# Cleverbot
chatterbot = ChatterBot.ChatterBot(bot, settings, prefix)
cogList.append(chatterbot)

# Help - Must be last
#help = Help.Help(bot, cogList)
#cogList.append(help)


# Main bot events
@bot.event
async def on_ready():
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	# Let cogs ready up
	respond = None
	for cog in cogList:
		try:
			await cog.onready()
		except AttributeError:
			# Onto the next
			continue
	

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
		state.playlist = []
		state.repeat = False
		await state.voice.disconnect()
	except:
		pass

@bot.event
async def on_member_remove(member):
	server = member.server
	settings.removeUser(member, server)
	for cog in cogList:
		try:
			check = await cog.onleave(member, server)
		except AttributeError:
			# Onto the next
			continue

@bot.event
async def on_server_join(server):
	settings.checkServer(server)
	owner = server.owner
	# Let's message hello in the main chat - then pm the owner
	msg = 'Hello everyone! Thanks for inviting me to your server!\n\nFeel free to put me to work.\n\nYou can get a list of my commands by typing `{}help` either in chat or in PM.'.format(prefix)
	await bot.send_message(server, msg)
	msg = 'Hey there - I\'m new here!\n\nWhenever you have a chance, maybe take the time to set me up by typing `{}setup` in the main chat.  Thanks!'.format(prefix)
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

	rules = settings.getServerStat(server, "Rules")
	
	for cog in cogList:
		try:
			check = await cog.onjoin(member, server)
		except AttributeError:
			# Onto the next
			continue

	help = 'Type `{}help` for a list of available user commands.'.format(prefix)

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
	
	# Check for cogs that accept updates
	pm = None
	for cog in cogList:
		try:
			await cog.status(after)
		except AttributeError:
			# Onto the next
			continue
		

@bot.event
async def on_message(message):
	if not message.server:
		# This wasn't said in a server, process commands, then return
		await bot.process_commands(message)
		return

	try:
		message.author.roles
	except AttributeError:
		# Not a User
		await bot.process_commands(message)
		return

	# Admin Override - always allow admin commands
	#if message.author.permissions_in(message.channel).administrator:
		#await bot.process_commands(message)
		#return
	
	# Check if we need to ignore or delete the message
	# or respond or replace
	ignore = delete = False
	respond = None
	for cog in cogList:
		try:
			check = await cog.message(message)
		except AttributeError:
			# Onto the next
			continue
		try:
			if check['Delete']:
				delete = True
		except KeyError:
			pass
		try:
			if check['Ignore']:
				ignore = True
		except KeyError:
			pass
		try:
			respond = check['Respond']
		except KeyError:
			pass

	if respond:
		# We have something to say
		await bot.send_message(message.channel, respond)
	if delete:
		# We need to delete the message - top priority
		await bot.delete_message(message)

	if not ignore:
		# We're processing commands here
		await bot.process_commands(message)

@bot.event
async def on_command(command, ctx):
	for cog in cogList:
		try:
			await cog.oncommand(command, ctx)
		except AttributeError:
			# Onto the next
			continue

@bot.event
async def on_command_completion(command, ctx):
	for cog in cogList:
		try:
			await cog.oncommandcompletion(command, ctx)
		except AttributeError:
			# Onto the next
			continue
		
@bot.event
async def on_message_edit(before, message):
	# Run through the on_message commands, but on edits.
	if not message.server:
		# This wasn't said in a server, return
		return

	try:
		message.author.roles
	except AttributeError:
		# Not a User
		return
	
	# Check if we need to ignore or delete the message
	# or respond or replace
	ignore = delete = False
	respond = None
	for cog in cogList:
		try:
			check = await cog.message(message)
		except AttributeError:
			# Onto the next
			continue
		try:
			if check['Delete']:
				delete = True
		except KeyError:
			pass
		try:
			if check['Ignore']:
				ignore = True
		except KeyError:
			pass
		try:
			respond = check['Respond']
		except KeyError:
			pass

	if respond:
		# We have something to say
		await bot.send_message(message.channel, respond)
	if delete:
		# We need to delete the message - top priority
		await bot.delete_message(message)
	
	

# Add our cogs 
# bot.add_cog(Music(bot))

# Module and Class are named the same, must use Settings.Settings to call
i = 0
for cog in cogList:
	i += 1
	bot.add_cog(cog)

print("{} Cog(s) Loaded.".format(i))

# await bot.connect()
# bot.login(token)
bot.run(token)
