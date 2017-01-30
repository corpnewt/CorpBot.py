import asyncio
import discord
import random
import urllib
import requests
import json
from   discord.ext import commands
from Cogs import Message

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

	@commands.command(pass_context=True)
	async def memetemps(self, ctx):
		"""Get Meme Templates"""
		url = "https://api.imgflip.com/get_memes"
		r = requests.get(url)
		result_json = json.loads(r.text)
		templates = result_json["data"]["memes"]

		templates_string = "**Meme Templates**\n"
		for template in templates:
			templates_string += "* [`{}` - `{}`]\n".format(template["id"], template["name"])
		
		await Message.say(self.bot, templates_string, ctx.message.author)

	@commands.command(pass_context=True)
	async def meme(self, ctx, template_id = None, text_zero = None, text_one = None):
		"""Generate Meme"""

		if template_id == None or text_zero == None or text_one == None:
			msg = "Usage: `{}meme [template_id] [text#1] [text#2]`\n\n Meme Templates can be found using `$memetemps`".format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		url = "https://api.imgflip.com/caption_image"
		payload = {'template_id': template_id, 'username':'CorpBot', 'password': 'pooter123', 'text0': text_zero, 'text1': text_one }
		r = requests.post(url, data=payload)
		result_json = json.loads(r.text)
		result = result_json["data"]["url"]
		await self.bot.send_message(ctx.message.channel, result)