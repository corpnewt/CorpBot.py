import asyncio
import discord
import random
from   datetime    import datetime
from   discord.ext import commands
from   Cogs        import DisplayName
from   Cogs        import Nullify


def setup(bot):
	settings = bot.get_cog("Settings")
	bot.add_cog(Spooktober(bot, settings))

class Spooktober(commands.Cog):
	
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	async def message(self, message):
		if datetime.today().month == 10 and datetime.today().day == 31:
			if not self.settings.getServerStat(message.guild, "Spooking"):
				# We have this turned off - bail
				return
			# it is the day of ultimate sp00p, sp00p all the messages
			if "spook" in message.content.lower():
				await message.add_reaction("🎃")
	
	@commands.command(pass_context=True)
	async def spooking(self, ctx, *, yes_no = None):
		"""Enables/Disables reacting 🎃 to every message on Halloween"""
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

		setting_name = "Spooking"
		setting_val  = "Spooking"

		current = self.settings.getServerStat(ctx.guild, setting_val)
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
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)