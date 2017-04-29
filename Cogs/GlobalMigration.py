import asyncio
import discord
import os
import time
from   datetime import datetime
from   discord.ext import commands

# This is the RateLimit module. It keeps users from being able to spam commands

class GlobalMigration:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings


	@commands.command(pass_context=True, hidden=True)
	async def migrate(self, ctx, setting = None):
		"""Migrates a local setting to global (owner only)."""
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

		if not setting:
			msg = "You need a setting to migrate."
			await ctx.channel.send(msg)
			return

		for member in ctx.guild.members:
			# Check this guild first
			if self.settings.getGlobalUserStat(member, setting):
				# Already set - continue
				continue
			tempStat = self.settings.getUserStat(member, ctx.guild, setting)
			self.settings.setGlobalUserStat(member, setting, tempStat)

		for guild in self.bot.guilds:
			if guild is ctx.guild:
				continue
			for member in guild.members:
				if self.settings.getGlobalUserStat(member, setting):
					# Already set - continue
					continue
				tempStat = self.settings.getUserStat(member, guild, setting)
				self.settings.setGlobalUserStat(member, setting, tempStat)

		msg = "Stat migrated!"
		await ctx.channel.send(msg)