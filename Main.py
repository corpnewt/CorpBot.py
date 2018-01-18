import asyncio
import discord
import time
import sys
import os
import random
import subprocess
import traceback
from   discord.ext import commands
from   discord import errors
from   Cogs import DisplayName

# Let's load our prefix file
prefix = '$'
if os.path.exists('prefix.txt'):
	with open('prefix.txt') as f:
		prefix = f.read()
	if not prefix:
		prefix = '$'


async def get_prefix(bot, message):
	# Check commands against some things and do stuff or whatever...
	try:
		# Set the settings var up
		settings = bot.get_cog("Settings")
		serverPrefix = settings.getServerStat(message.guild, "Prefix")
	except Exception:
		serverPrefix = None

	if not serverPrefix:
		# No custom prefix - use the default
		serverPrefix = prefix
	return (serverPrefix, "<@!{}> ".format(bot.user.id), "<@{}> ".format(bot.user.id))

# This should be the main soul of the bot - everything should load from here
bot = commands.Bot(command_prefix=get_prefix, pm_help=None, description='A bot that does stuff.... probably')
# Initialize some things
jsonFile = "Settings.json"
deckFile = "deck.json"
corpSiteAuth = "corpSiteAuth.txt"
# Open our token
with open('token.txt', 'r') as f:
	token = f.read().strip()

# Main bot events
@bot.event
async def on_ready():
	print('Logged in as:\n{0} (ID: {0.id})\n'.format(bot.user))
	print("Invite Link:\nhttps://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8\n".format(bot.user.id))
	
	# Load extensions - Bypassed for now
	# _load_extensions()
	
	# Let's try to use the CogManager class to load things
	bot.load_extension("Cogs.CogManager")
	cg_man = bot.get_cog("CogManager")
	
	# Load up the rest of the extensions
	cog_loaded, cog_count = cg_man._load_extension()
	
	# Set the settings var up
	settings = bot.get_cog("Settings")
	
	# Output the load counts
	if cog_count == 1:
		print("Loaded {} of {} cog.".format(cog_loaded, cog_count))
	else:
		print("Loaded {} of {} cogs.".format(cog_loaded, cog_count))

	# Return the dict key or None if it doesn't exist
	# Also deletes said key
	return_channel = settings.serverDict.pop("ReturnChannel", None)

	if not return_channel == None:
		message_to = bot.get_channel(return_channel)
		if message_to == None:
			# No channel
			return
		return_options = [
			"I'm back!",
			"I have returned!",
			"Guess who's back?",
			"Fear not!  I have returned!",
			"I'm alive!"
		]
		await message_to.send(random.choice(return_options))

'''@bot.event
async def on_command_error(context, exception):
	if type(exception) is commands.CommandInvokeError:
		print("Command invoke error")
		print(exception.original)
		print(type(exception.original))
		if type(exception.original) is discord.Forbidden:
			print("Can't do that yo")
			return
	cog = context.cog
	if cog:
		attr = '_{0.__class__.__name__}__error'.format(cog)
		if hasattr(cog, attr):
			return

	print('Ignoring exception in command {}:'.format(context.command), file=sys.stderr)
	traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)'''

'''@bot.event
async def on_error(event_method, *args, **kwargs):
	exc_str = "Ignoring exception in {}:\n    ".format(event_method)
	exc_str += "{}: {}".format(sys.exc_info()[0].__name__, sys.exc_info()[1])
	#print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
	#traceback.print_exc()
	print(exc_str)'''
	
@bot.event
async def on_voice_state_update(user, beforeState, afterState):
	return

@bot.event
async def on_typing(channel, user, when):
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			await cog.ontyping(channel, user, when)
		except AttributeError:
			continue

@bot.event
async def on_member_remove(member):
	server = member.guild
	# Set the settings var up
	settings = bot.get_cog("Settings")
	settings.removeUser(member, server)
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			await cog.onleave(member, server)
		except AttributeError:
			# Onto the next
			continue

@bot.event
async def on_member_ban(guild, member):
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			await cog.onban(guild, member)
		except AttributeError:
			# Onto the next
			continue

@bot.event
async def on_member_unban(member, server):
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			await cog.onunban(member, server)
		except AttributeError:
			# Onto the next
			continue

@bot.event
async def on_guild_join(server):
	didLeave = False
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			if await cog.onserverjoin(server):
				didLeave = True
		except AttributeError:
			# Onto the next
			continue
	if didLeave:
		return
	# Set the settings var up
	settings = bot.get_cog("Settings")
	settings.checkServer(server)
	owner = server.owner
	# Let's message hello in the main chat - then pm the owner
	msg = 'Hello there! Thanks for having me on your server! ({})\n\nFeel free to put me to work.\n\nYou can get a list of my commands by typing `{}help` either in chat or in PM.\n\n'.format(server.name, prefix)
	msg += 'Whenever you have a chance, maybe take the time to set me up by typing `{}setup` in the main chat.  Thanks!'.format(prefix)
	try:
		await owner.send(msg)
	except Exception:
		pass

@bot.event
async def on_guild_remove(server):
	# Set the settings var up
	settings = bot.get_cog("Settings")
	settings.removeServer(server)

@bot.event
async def on_channel_delete(channel):
	# Set the settings var up
	settings = bot.get_cog("Settings")
	settings.removeChannelID(channel.id, channel.guild)

@bot.event
async def on_member_join(member):
	server = member.guild
	# Set the settings var up
	settings = bot.get_cog("Settings")
	# Initialize the user
	settings.checkUser(member, server)

	rules = settings.getServerStat(server, "Rules")
	
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			await cog.onjoin(member, server)
		except AttributeError:
			# Onto the next
			continue

@bot.event
async def on_member_update(before, after):	
	# Check for cogs that accept updates
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			await cog.member_update(before, after)
		except AttributeError:
			# Onto the next
			continue

@bot.event
async def on_message(message):
	# Post the context too
	context = await bot.get_context(message)
	bot.dispatch("message_context", context, message)

	if not message.guild:
		# This wasn't said in a server, process commands, then return
		await bot.process_commands(message)
		return

	if message.author.bot:
		# We don't need other bots controlling things we do.
		return

	try:
		message.author.roles
	except AttributeError:
		# Not a User
		await bot.process_commands(message)
		return
	
	# Check if we need to ignore or delete the message
	# or respond or replace
	ignore, delete, react = False, False, False
	respond = None
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			check = await cog.message(message)
		except AttributeError:
			# Onto the next
			continue
		# Make sure we have things formatted right
		if not type(check) is dict:
			check = {}
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
		try:
			react = check['Reaction']
		except KeyError:
			pass

	if delete:
		# We need to delete the message - top priority
		await message.delete()

	if not ignore:
		# We're processing commands here
		if respond:
			# We have something to say
			await message.channel.send(respond)
		if react:
			# We have something to react with
			for r in react:
				await message.add_reaction(r)
		await bot.process_commands(message)

@bot.event
async def on_command(command):
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			await cog.oncommand(command)
		except AttributeError:
			# Onto the next
			continue

@bot.event
async def on_command_completion(command):
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			await cog.oncommandcompletion(command)
		except AttributeError:
			# Onto the next
			continue

'''@bot.event
async def on_command_error(ctx, error):
	# if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
	if not isinstance(error, (commands.CommandNotFound)):
		await ctx.send("{}: {}".format(type(error).__name__, error))
		formatted_help = await bot.formatter.format_help_for(ctx, ctx.command)
		for page in formatted_help:
			await ctx.send(page)
	#print("".join(traceback.format_exception(etype=type(error),value=error,tb=error.__traceback__)))
	if traceback.print_tb(error.__traceback__):
		print(traceback.print_tb(error.__traceback__))'''

@bot.event
async def on_message_delete(message):
	# Run through the on_message commands, but on deletes.
	if not message.guild:
		# This wasn't in a server, return
		return
	try:
		message.author.roles
	except AttributeError:
		# Not a User
		return
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			await cog.message_delete(message)
		except AttributeError:
			# Onto the next
			continue

		
@bot.event
async def on_message_edit(before, message):
	# Run through the on_message commands, but on edits.
	if not message.guild:
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
	for cog in bot.cogs:
		cog = bot.get_cog(cog)
		try:
			check = await cog.message_edit(before, message)
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
		await message.channel.send(respond)
	if delete:
		# We need to delete the message - top priority
		await message.delete()

# Run the bot
bot.run(token)
