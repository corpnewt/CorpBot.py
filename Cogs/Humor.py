import asyncio
import discord
import random
from   discord.ext import commands

# This module is for random funny things I guess...

class Humor:

	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(pass_context=True)
	async def fart(self, ctx):
		"""PrincessZoey :P"""
		fartList = ["Poot", "Prrrrt", "Thhbbthbbbthhh", "Plllleerrrrffff", "Toot", "Blaaaaahnk", "Squerk"]
		randnum = random.randint(0, len(fartList)-1)
		msg = '{}'.format(fartList[randnum])
		await self.bot.send_message(ctx.message.channel, msg)