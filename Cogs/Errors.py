import asyncio
import discord
import sys
import traceback
from   discord.ext import commands
from   discord import errors
from   Cogs import Message

def setup(bot):
	bot.add_cog(Errors())

class Errors:

	def __init__(self):
		pass

	@asyncio.coroutine
	async def on_command_error(self, context, exception):
		if type(exception) is commands.CommandInvokeError and type(exception.original) is discord.Forbidden:
			await Message.EmbedText(
					title="⚠ Forbidden Error",
					color=context.author,
					description="Looks like I tried to do something I don't have permissions for!\nIf `{}{}` is role-based - make sure that my role is above the affected role(s).".format(context.prefix, context.command.name)
				).send(context)
			return
		cog = context.cog
		if cog:
			attr = '_{0.__class__.__name__}__error'.format(cog)
			if hasattr(cog, attr):
				return

		print('Ignoring exception in command {}:'.format(context.command), file=sys.stderr)
		traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

