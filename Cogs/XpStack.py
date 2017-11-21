import asyncio
import discord
import random
import math
from   datetime import datetime
from   discord.ext import commands
from   operator import itemgetter
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import CheckRoles
from   Cogs import Message

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(XpStack(bot, settings))

# This is the xp module.  It's likely to be retarded.

class XpStack:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.xp_save_count = 10

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg
		
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
	async def clearallxp(self, ctx):
		"""Clears all xp transactions from the transaction list for all servers (owner-only)."""
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
		for guild in self.bot.guilds:
			self.settings.setServerStat(guild, "XP Array", [])
		
		await ctx.send("All xp transactions from the transaction list for all servers cleared!")
		
	@commands.command(pass_context=True)
	async def setxpcount(self, ctx, count = None):
		"""Sets the number of xp transactions to keep (default is 10)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if count == None:
			# Reset to default
			self.settings.setServerStat(ctx.guild, "XP Count", self.xp_save_count)
			await ctx.send("Reset the xp count to the default of {}.".format(self.xp_save_count))
			return

		try:
			count = int(count)
		except Exception:
			await ctx.send("Count must be an integer.")
			return

		if count < 0:
			await ctx.send("Count must be at least 0.")
			return
		
		if count > 100:
			count = 100

		self.settings.setServerStat(ctx.guild, "XP Count", count)
		await ctx.send("Set the xp count to {}.".format(count))

	@commands.command(pass_context=True)
	async def xpcount(self, ctx, count = None):
		"""Returns the number of xp transactions to keep (default is 10)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		num = self.settings.getServerStat(ctx.guild, "XP Count")
		if num == None:
			num = self.xp_save_count
		
		await ctx.send("The current number of xp transactions to save is {}.".format(num))
		

	@commands.command(pass_context=True)
	async def clearxp(self, ctx):
		"""Clears the xp transaction list (bot-admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return
		
		xp_array = self.settings.getServerStat(ctx.guild, "XP Array")
		if xp_array == None:
			xp_array = []
		
		self.settings.setServerStat(ctx.guild, "XP Array", [])
		if len(xp_array) == 1:
			await ctx.send("Cleared 1 entry from the xp transactions list.")
		else:
			await ctx.send("Cleared {} entries from the xp transactions list.".format(len(xp_array)))

		
	@commands.command(pass_context=True)
	async def checkxp(self, ctx):
		"""Displays the last xp transactions (bot-admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return
		
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		xp_array = self.settings.getServerStat(ctx.guild, "XP Array")
		if xp_array == None:
			xp_array = []

		if not len(xp_array):
			await ctx.send("No recent XP transactions in *{}*.".format(self.suppressed(ctx.guild, ctx.guild.name)))
			return

		count = 0
		
		# msg = "__Recent XP Transactions in *{}*:__\n\n".format(self.suppressed(ctx.guild, ctx.guild.name))
		
		help_embed = discord.Embed(color=ctx.author.color)
		title = "Recent XP Transactions in {}".format(ctx.guild.name)
		help_embed.title = title
		
		to_pm = len(xp_array) > 25
		page_count = 1
		page_total = math.ceil(len(xp_array)/25)
		
		if page_total > 1:
			help_embed.title = title + " (Page {:,} of {:,})".format(page_count, page_total)
		for i in range(len(xp_array)):
			i = xp_array[len(xp_array)-1-i]
			# Add the field
			to_user = DisplayName.memberForID(i["To"], ctx.guild)
			if to_user == None:
				to_user = DisplayName.roleForID(i["To"], ctx.guild)
				if to_user == None:
					to_user = "ID: " + str(i["To"])
			from_user = DisplayName.memberForID(i["From"], ctx.guild)
			if from_user == None:
				from_user = DisplayName.roleForID(i["From"], ctx.guild)
				if from_user == None:
					from_user = "ID: " + str(i["From"])
			
			# Build the name of the field
			f_name = "{} -- to --> {}".format(from_user, to_user)
			# Make sure the field names are 256 chars max
			f_name = (f_name[:253]+"...") if len(f_name) > 256 else f_name
			
			# Get the xp amount and time
			f_value = "\* {} xp\n\* {}".format(i["Amount"], i["Time"])
			# Make sure it's 1024 chars max
			f_value = (f_value[:1021]+"...") if len(f_value) > 1024 else f_value
			
			# Add the field
			help_embed.add_field(name=f_name, value=f_value, inline=False)
			# 25 field max - send the embed if we get there
			if len(help_embed.fields) >= 25:
				if page_total == page_count:
					help_embed.set_footer(text="Requested by " + str(ctx.author))
				await self._send_embed(ctx, help_embed, to_pm)
				help_embed.clear_fields()
				page_count += 1
				if page_total > 1:
					help_embed.title = title + " (Page {:,} of {:,})".format(page_count, page_total)
		
		if len(help_embed.fields):
			help_embed.set_footer(text="Requested by " + str(ctx.author))
			await self._send_embed(ctx, help_embed, to_pm)


	# Catch custom xp event
	@asyncio.coroutine
	async def on_xp(self, to_user, from_user, amount):
		server = from_user.guild
		num = self.settings.getServerStat(server, "XP Count")
		if num == None:
			num = self.xp_save_count
		'''if type(to_user) is discord.Role:
			#to_name = to_user.name + " role"
		else:
			to_name = "{}#{}".format(to_user.name, to_user.discriminator)'''
		to_name = to_user.id
		f_name = from_user.id
		#f_name = "{}#{}".format(from_user.name, from_user.discriminator)
		# Add new xp transaction
		xp_transaction = { "To": to_name, "From": f_name, "Time": datetime.today().strftime("%Y-%m-%d %H.%M"), "Amount": amount }
		xp_array = self.settings.getServerStat(server, "XP Array")
		if xp_array == None:
			xp_array = []
		xp_array.append(xp_transaction)
		while len(xp_array) > num:
			xp_array.pop(0)
		self.settings.setServerStat(server, "XP Array", xp_array)
