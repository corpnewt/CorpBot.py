import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify
import requests
import urllib
	
class Ascii:
    
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, no_pm=True)
	async def ascii(self, ctx, *, text : str):
		"""Adds two numbers together."""
		url = "http://artii.herokuapp.com/make?{}".format(urllib.parse.urlencode({'text':text}))
		print(url)
		get_request = self.bot.loop.run_in_executor(None, requests.get, url)
		response = await get_request
		await self.bot.say("```Markup\n {} ```".format(response.text))