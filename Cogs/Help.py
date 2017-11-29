import asyncio
import discord
import random
import math
import os
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import Nullify
from   Cogs import DisplayName
from   Cogs import Message
from   Cogs import FuzzySearch

def setup(bot):
	# Add the cog
	bot.remove_command("help")
	bot.add_cog(Help(bot))

# This is the Help module. It replaces the built-in help command

class Help:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		
	def _get_prefix(self, ctx):
		# Helper method to get the simplified prefix
		# Setup a clean prefix
		if ctx.guild:
			bot_member = ctx.guild.get_member(self.bot.user.id)
		else:
			bot_member = ctx.bot.user
		# Replace name and nickname mentions
		return ctx.prefix.replace(bot_member.mention, '@' + DisplayName.name(bot_member))

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	def _get_help(self, command, max_len = 0):
		# A helper method to return the command help - or a placeholder if none
		if max_len == 0:
			# Get the whole thing
			if command.help == None:
				return "Help not available..."
			else:
				return command.help
		else:
			if command.help == None:
				c_help = "Help not available..."
			else:
				c_help = command.help.split("\n")[0]
			return (c_help[:max_len-3]+"...") if len(c_help) > max_len else c_help

	async def _get_info(self, ctx, com = None):
		# Helper method to return a list of embed content
		# or None if no results

		prefix = self._get_prefix(ctx)

		# Setup the footer
		footer = "\nType `{}help command` for more info on a command. \n".format(prefix)
		footer += "You can also type `{}help category` for more info on a category.".format(prefix)

		# Get settings - and check them if they exist
		disabled_list = None
		settings = self.bot.get_cog("Settings")
		if settings and ctx.guild:
			disabled_list = settings.getServerStat(ctx.guild, "DisabledCommands")
		if disabled_list == None:
			disabled_list = []

		if com == None:
			# No command or cog - let's send the coglist
			embed_list = { "title" : "Current Categories", "fields" : [] }
			command_list = []
			for cog in sorted(self.bot.cogs):
				if not len(self.bot.get_cog_commands(cog)):
					# Skip empty cogs
					continue
				# Make sure there are non-hidden commands here
				visible = []
				disabled = 0
				for command in self.bot.get_cog_commands(cog):
					if not command.hidden:
						visible.append(command)
					if command.name in disabled_list:
						disabled += 1
				if not len(visible):
					continue
				# Add the name of each cog in the list
				if disabled == 0:
					new_dict = { "name" : cog }
				elif disabled == len(visible):
					new_dict = { "name" : "~~" + cog + "~~ (Disabled)" }
				else:
					new_dict = { "name" : cog + " ({} Disabled)".format(disabled) }
				if len(visible) == 1:
					new_dict["value"] = "`└─ 1 command`"
				else:
					new_dict["value"] = "`└─ {:,} commands`".format(len(visible))
				new_dict["inline"] = True
				embed_list["fields"].append(new_dict)
			return embed_list
		else:
			for cog in sorted(self.bot.cogs):
				if not cog == com:
					continue
				# Found the cog - let's build our text
				cog_commands = self.bot.get_cog_commands(cog)
				cog_commands = sorted(cog_commands, key=lambda x:x.name)
				# Get the extension
				the_cog = self.bot.get_cog(cog)
				embed_list = None
				for e in self.bot.extensions:
					b_ext = self.bot.extensions.get(e)
					if self._is_submodule(b_ext.__name__, the_cog.__module__):
						# It's a submodule
						embed_list = {"title" : "{} Cog - {}.py Extension". format(cog, e[5:]), "fields" : [] }
						break
				if not embed_list:
					embed_list = {"title" : cog, "fields" : [] }
				for command in cog_commands:
					# Make sure there are non-hidden commands here
					if command.hidden:
						continue
					command_help = self._get_help(command, 80)
					if command.name in disabled_list:
						name = "~~" + prefix + command.signature + "~~ (Disabled)"
					else:
						name = prefix + command.signature
					embed_list["fields"].append({ "name" : name, "value" : "`└─ " + command_help + "`", "inline" : False })
				# If all commands are hidden - pretend it doesn't exist
				if not len(embed_list["fields"]):
					return None
				return embed_list
			# If we're here, we didn't find the cog - check for the command
			for cog in self.bot.cogs:
				cog_commands = self.bot.get_cog_commands(cog)
				cog_commands = sorted(cog_commands, key=lambda x:x.name)
				for command in cog_commands:
					if not command.name == com:
						continue
					# Get the extension
					the_cog = self.bot.get_cog(cog)
					embed_list = None
					for e in self.bot.extensions:
						b_ext = self.bot.extensions.get(e)
						if self._is_submodule(b_ext.__name__, the_cog.__module__):
							# It's a submodule
							embed_list = {"title" : "{} Cog - {}.py Extension".format(cog, e[5:]), "fields" : [] }
							break
					if not embed_list:
						# embed_list = {"title" : cog, "fields" : [] }
						embed_list = { "title" : cog }
					# embed_list["fields"].append({ "name" : prefix + command.signature, "value" : command.help, "inline" : False })
					if command.name in disabled_list:
						embed_list["description"] = "~~**{}**~~ (Disabled)\n```\n{}```".format(prefix + command.signature, command.help)
					else:
						embed_list["description"] = "**{}**\n```\n{}```".format(prefix + command.signature, command.help) 
					return embed_list
		# At this point - we got nothing...
		return None

	async def _send_embed(self, ctx, embed, pm = False):
		# Helper method to send embeds to their proper location
		if pm == True and not ctx.channel == ctx.author.dm_channel:
			# More than 2 pages, try to dm
			try:
				await ctx.author.send(embed=embed)
				await ctx.message.add_reaction("📬")
			except discord.Forbidden:
				await ctx.send(embed=embed)
			return
		await ctx.send(embed=embed)

	@commands.command(pass_context=True, hidden=True)
	async def dumphelp(self, ctx, tab_indent_count = None):
		"""Dumps a timpestamped, formatted list of commands and descriptions into the same directory as the bot."""
		try:
			tab_indent_count = int(tab_indent_count)
		except:
			tab_indent_count = None
		if tab_indent_count == None or tab_indent_count < 0:
			tab_indent_count = 1

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		serverFile = 'HelpList-{}.txt'.format(timeStamp)
		message = await ctx.send('Saving help list to *{}*...'.format(serverFile))
		msg = ''
		prefix = self._get_prefix(ctx)
		
		# Get and format the help
		for cog in sorted(self.bot.cogs):
			cog_commands = sorted(self.bot.get_cog_commands(cog), key=lambda x:x.name)
			cog_string = ""
			# Get the extension
			the_cog = self.bot.get_cog(cog)
			# Make sure there are non-hidden commands here
			visible = []
			for command in self.bot.get_cog_commands(cog):
				if not command.hidden:
					visible.append(command)
			if not len(visible):
				# All hidden - skip
				continue
			cog_count = "1 command" if len(visible) == 1 else "{} commands".format(len(visible))
			for e in self.bot.extensions:
				b_ext = self.bot.extensions.get(e)
				if self._is_submodule(b_ext.__name__, the_cog.__module__):
					# It's a submodule
					cog_string += "{}{} Cog ({}) - {}.py Extension:\n".format(
						"	"*tab_indent_count,
						cog,
						cog_count,
						e[5:]
					)
					break
			if cog_string == "":
				cog_string += "{}{} Cog ({}):\n".format(
					"	"*tab_indent_count,
					cog,
					cog_count
				)
			for command in cog_commands:
				cog_string += "{}  {}\n".format("	"*tab_indent_count, prefix + command.signature)
				cog_string += "{}  {}└─ {}\n".format(
					"	"*tab_indent_count,
					" "*len(prefix),
					self._get_help(command, 80)
				)
			cog_string += "\n"
			msg += cog_string
		
		# Encode to binary
		# Trim the last 2 newlines
		msg = msg[:-2].encode("utf-8")
		with open(serverFile, "wb") as myfile:
			myfile.write(msg)

		await message.edit(content='Uploading *{}*...'.format(serverFile))
		await ctx.send(file=discord.File(serverFile))
		await message.edit(content='Uploaded *{}!*'.format(serverFile))
		os.remove(serverFile)

	@commands.command(pass_context=True)
	async def help(self, ctx, *, command = None):
		"""Lists the bot's commands and cogs.
		You can pass a command or cog to this to get more info (case-sensitive)."""
		
		result = await self._get_info(ctx, command)

		if result == None:
			# Get a list of all commands and modules and server up the 3 closest
			cog_name_list = []
			com_name_list = []
			
			for cog in self.bot.cogs:
				if not cog in cog_name_list:
					if not len(self.bot.get_cog_commands(cog)):
						# Skip empty cogs
						continue
				cog_commands = self.bot.get_cog_commands(cog)
				hid = True
				for comm in cog_commands:
					if comm.hidden:
						continue
					hid = False
					if not comm.name in com_name_list:
						com_name_list.append(comm.name)
				if not hid:
					cog_name_list.append(cog)
			
			# Get cog list:
			cog_match = FuzzySearch.search(command, cog_name_list)
			com_match = FuzzySearch.search(command, com_name_list)

			# Build the embed
			m = Message.Embed(force_pm=True)
			if type(ctx.author) is discord.Member:
				m.color = ctx.author.color
			m.title = "No command called \"{}\" found".format(Nullify.clean(command))
			if len(cog_match):
				cog_mess = ""
				for pot in cog_match:
					cog_mess += '└─ {}\n'.format(pot['Item'].replace('`', '\\`'))
				m.add_field(name="Close Cog Matches:", value=cog_mess)
			if len(com_match):
				com_mess = ""
				for pot in com_match:
					com_mess += '└─ {}\n'.format(pot['Item'].replace('`', '\\`'))
				m.add_field(name="Close Command Matches:", value=com_mess)
			m.footer = { "text" : "Remember that commands and cogs are case-sensitive.", "icon_url" : self.bot.user.avatar_url }
			await m.send(ctx)
			return
		m = Message.Embed(**result)
		m.force_pm = True
		# Build the embed
		if type(ctx.author) is discord.Member:
			m.color = ctx.author.color
		m.footer = self.bot.description + " - Type \"{}help command\" for more info on a command. \n".format(self._get_prefix(ctx))
		await m.send(ctx)
