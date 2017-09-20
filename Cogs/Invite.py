import asyncio
import discord
from   discord.ext import commands
from   Cogs import DisplayName

def setup(bot):
	# Add the bot
	bot.add_cog(Invite(bot))

class Invite:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def invite(self, ctx):
		"""Outputs a url you can use to invite me to your server."""
		myInvite = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(permissions=8))
		await ctx.channel.send('Invite me to *your* server with this link: \n\n<{}>'.format(myInvite))