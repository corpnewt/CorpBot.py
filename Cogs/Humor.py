import asyncio
import discord
import random
from   discord.ext import commands

# This module is for random funny things I guess...

class Humor:

	def __init__(self, bot):
		self.bot = bot

	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}

	@commands.command(pass_context=True)
	async def fart(self, ctx):
		"""PrincessZoey :P"""
		fartList = ["Poot", "Prrrrt", "Thhbbthbbbthhh", "Plllleerrrrffff", "Toot", "Blaaaaahnk", "Squerk"]
		randnum = random.randint(0, len(fartList)-1)
		msg = '{}'.format(fartList[randnum])
		await self.bot.send_message(ctx.message.channel, msg)

	@commands.command(pass_context=True)
	async def shart(self, ctx):
	"""PrincessZoey was here <3"""
	shartList = ["Oops not again!", "Son of a biscuit eating whore", "Really? God Damnit"]
	randnum = random.randinit(0, len(fartList)-1)
	msg = '{}'.format(fartList[randnum])
	await self.bot.send_message(ctx.message.channel, msg)
