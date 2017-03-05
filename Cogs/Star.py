import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify
import requests

class Star:
    
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, no_pm=True)
	async def randstar(self, ctx, *, text : str = None):
		r = requests.get('https://sydneyerickson.me/starapi/rand.php')
		await self.bot.say(r.content.decode("utf-8").replace(" ", "%20"))
