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
	async def pcpp(self, ctx, url = None, style = None):
		"""Convert a pcpartpicker.com link into markdown parts."""
		usage = "Usage: `{}pcpp [url] [style=normal, md, mdblock, bold, bolditalic]`".format(ctx.prefix)

		if not style:
			style = 'normal'
		
		if not url:
			await ctx.channel.send(usage)
			return
		
		output = PCPP.getMarkdown(url, style)
		if not output:
			await ctx.channel.send('Something went wrong!  Make sure you use a valid pcpartpicker link.')
			return

		await ctx.channel.send(output)
