import asyncio
import discord
import time
import argparse
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import PCPP

# This is the Uptime module. It keeps track of how long the bot's been up

class Hw:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def pcpp(self, ctx, url = None, style = None, escape = None):
		"""Convert a pcpartpicker.com link into markdown parts. Available styles: normal, md, mdblock, bold, and bolditalic."""
		usage = "Usage: `{}pcpp [url] [style=normal, md, mdblock, bold, bolditalic] [escape=yes/no (optional)]`".format(ctx.prefix)

		if not style:
			style = 'normal'
		
		if not url:
			await ctx.channel.send(usage)
			return

		if escape == None:
			escape = 'no'
		escape = escape.lower()

		if escape == 'yes' or escape == 'true' or escape == 'on':
			escape = True
		else:
			escape = False
		
		output = PCPP.getMarkdown(url, style, escape)
		if not output:
			msg = 'Something went wrong!  Make sure you use a valid pcpartpicker link.'
			await ctx.channel.send(msg)
			return
		if len(output) > 2000:
			msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
			msg += '/nMaybe see if you can prune up that list and try again?'
			await ctx.channel.send(msg)
			return
			
		await ctx.channel.send(output)
