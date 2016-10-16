import asyncio
import discord
from discord.ext import commands
from discord import errors

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

# This should be the main soul of the bot - everything should load from here
bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'), description='A bot that does stuff.... probably')
# Initialize some things
jsonFile = "Settings.json"
# Open our token
with open('token.txt', 'r') as f:
	token = f.read()


# Create our cog classes
cogList = []

# Examples - there are 2 parts here, Example, and Music
example = Example.Example(bot)
music = Example.Music(bot)
cogList.append(example)
cogList.append(music)

# Settings
settings = Settings.Settings(bot, jsonFile)
cogList.append(settings)

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

humor = Humor.Humor(bot)
cogList.append(humor)

# Main bot events
@bot.event
async def on_ready():
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	settings.flushSettings()

@bot.event
async def on_member_join(member):
	server = member.server
	# Initialize the user
	settings.checkUser(member, server)
	fmt = 'Welcome *{}* to *{}*!'.format(member.name, server.name)
	await bot.send_message(server, fmt.format(member, server))
	# Scan through roles - find "Entry Level" and set them to that

	autoRole    = settings.getServerStat(server, "AutoRole")
	defaultRole = settings.getServerStat(server, "DefaultRole")
	rules       = settings.getServerStat(server, "Rules")
	
	if autoRole.lower() == "position":
		newRole = discord.utils.get(server.roles, position=int(defaultRole))
		await bot.add_roles(member, newRole)
		fmt = 'You\'ve been auto-assigned the role *{}*!'.format(newRole.name)
		await bot.send_message(server, fmt)
	elif autoRole.lower() == "id":
		newRole = discord.utils.get(server.roles, id=defaultRole)
		await bot.add_roles(member, newRole)
		fmt = 'You\'ve been auto-assigned the role *{}*!'.format(newRole.name)
		await bot.send_message(server, fmt)

	help = 'Type `$help` for a list of available user commands.'

	# PM User
	fmt = "*{}* Rules:\n{}\n\n{}".format(server.name, rules, help)
	await bot.send_message(member, fmt)

@bot.event
async def on_member_update(before, after):
	server = after.server
			
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
	if message.author.permissions_in(message.channel).administrator:
		await bot.process_commands(message)
		return
	
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