import asyncio
import discord
import random
import math
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import Nullify
from   Cogs import DisplayName

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

		if com == None:
			# No command or cog - let's send the coglist
			embed_list = { "title" : "Current Categories", "fields" : [] }
			command_list = []
			for cog in sorted(self.bot.cogs):
				if not len(self.bot.get_cog_commands(cog)):
					# Skip empty cogs
					continue
				# Make sure there are non-hidden commands here
				cog_commands = self.bot.get_cog_commands(cog)
				hidden = True
				for command in cog_commands:
					if not command.hidden:
						# At least one that's not hidden
						hidden = False
						break
				if hidden:
					continue
				# Add the name of each cog in the list
				new_dict = { "name" : cog }
				if len(self.bot.get_cog_commands(cog)) == 1:
					new_dict["value"] = "└─ 1 command"
				else:
					new_dict["value"] = "└─ {:,} commands".format(len(self.bot.get_cog_commands(cog)))
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
				embed_list = {"title" : cog, "fields" : [] }
				for command in cog_commands:
					# Make sure there are non-hidden commands here
					if command.hidden:
						continue
					command_help = self._get_help(command, 80)
					embed_list["fields"].append({ "name" : prefix + command.signature, "value" : "└─ " + command_help, "inline" : False })
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
					embed_list = {"title" : cog, "fields" : [] }
					embed_list["fields"].append({ "name" : prefix + command.signature, "value" : command.help, "inline" : False })
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


	@commands.command(pass_context=True)
	async def help(self, ctx, *, command = None):
		"""Lists the bot's commands and cogs.
		You can pass a command or cog to this to get more info (case-sensitive)."""
		
		result = await self._get_info(ctx, command)

		if result == None:
			await ctx.send("No command called *\"{}\"* found.  Remember that commands and cogs are case-sensitive.".format(Nullify.clean(command)))
			return

		# Build the embed
		if type(ctx.author) is discord.Member:
			help_embed = discord.Embed(color=ctx.author.color)
		else:
			# No default color - pick a random
			colors = [ 
				discord.Color.teal(),
				discord.Color.dark_teal(),
				discord.Color.green(),
				discord.Color.dark_green(),
				discord.Color.blue(),
				discord.Color.dark_blue(),
				discord.Color.purple(),
				discord.Color.dark_purple(),
				discord.Color.magenta(),
				discord.Color.dark_magenta(),
				discord.Color.gold(),
				discord.Color.dark_gold(),
				discord.Color.orange(),
				discord.Color.dark_orange(),
				discord.Color.red(),
				discord.Color.dark_red(),
				discord.Color.lighter_grey(),
				discord.Color.dark_grey(),
				discord.Color.light_grey(),
				discord.Color.darker_grey(),
				discord.Color.blurple(),
				discord.Color.greyple()
				]
			help_embed = discord.Embed(color=random.choice(colors))
		help_embed.title = result["title"]

		to_pm = len(result["fields"]) > 10
		page_count = 1
		page_total = math.ceil(len(result["fields"])/25)
		if page_total > 1:
			help_embed.title = result["title"] + " (Page {:,} of {:,})".format(page_count, page_total)
		for embed in result["fields"]:
			help_embed.add_field(name=embed["name"], value=embed["value"], inline=embed["inline"])
			# 25 field max - send the embed if we get there
			if len(help_embed.fields) >= 25:
				if page_total == page_count:
					help_embed.set_footer(text=self.bot.description + " - Type \"{}help command\" for more info on a command. \n".format(self._get_prefix(ctx)))
				await self._send_embed(ctx, help_embed, to_pm)
				help_embed.clear_fields()
				page_count += 1
				if page_total > 1:
					help_embed.title = result["title"] + " (Page {:,} of {:,})".format(page_count, page_total)
		
		if len(help_embed.fields):
			help_embed.set_footer(text=self.bot.description + " - Type \"{}help command\" for more info on a command. \n".format(self._get_prefix(ctx)))
			await self._send_embed(ctx, help_embed, to_pm)
				

			
