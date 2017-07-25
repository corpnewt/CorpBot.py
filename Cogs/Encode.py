import asyncio
import discord
from   discord.ext import commands
import base64
import binascii
import re
from   Cogs import Nullify

class Encode:

	# Init with the bot reference
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions").lower() == "yes":
			return Nullify.clean(msg)
		else:
			return msg

	# Helper methods
	def _to_bytes(self, in_string):
		return in_string.encode('utf-8')
	
	def _to_string(self, in_bytes):
			return in_bytes.decode('utf-8')

	# Check hex value
	def _check_hex(self, hex_string):
		if hex_string.lower().startswith("0x"):
			hex_string = hex_string[2:]
		hex_string = re.sub(r'[^0-9A-Fa-f]+', '', hex_string)
		return hex_string

	# To base64 methods
	def _ascii_to_base64(self, ascii_string):
		ascii_bytes = self._to_bytes(ascii_string)
		base_64     = base64.b64encode(ascii_bytes)
		return self._to_string(base_64)

	def _hex_to_base64(self, hex_string):
		hex_string    = self._check_hex(hex_string)
		hex_s_bytes   = self._to_bytes(hex_string)
		hex_bytes     = binascii.unhexlify(hex_s_bytes)
		base64_bytes  = base64.b64encode(hex_bytes)
		return self._to_string(base64_bytes)

	# To ascii methods
	def _hex_to_ascii(self, hex_string):
		hex_string  = self._check_hex(hex_string)
		hex_bytes   = self._to_bytes(hex_string)
		ascii_bytes = binascii.unhexlify(hex_bytes)
		return self._to_string(ascii_bytes)

	def _base64_to_ascii(self, base64_string):
		base64_bytes  = self._to_bytes(base64_string)
		ascii_bytes   = base64.b64decode(base64_bytes)
		return self._to_string(ascii_bytes)

	# To hex methods
	def _ascii_to_hex(self, ascii_string):
		ascii_bytes = self._to_bytes(ascii_string)
		hex_bytes   = binascii.hexlify(ascii_bytes)
		return self._to_string(hex_bytes)

	def _base64_to_hex(self, base64_string):
		b64_string = self._to_bytes(base64_string)
		base64_bytes = base64.b64decode(b64_string)
		hex_bytes    = binascii.hexlify(base64_bytes)
		return self._to_string(hex_bytes)

	@commands.command(pass_context=True)
	async def encode(self, ctx, value = None , from_type = None, *, to_type = None):
		"""Data converter from string <--> hex <--> base64."""

		if value == None or from_type == None or to_type == None:
			msg = 'Usage: `{}encode "[value]" [from_type] [to_type]`\nTypes include ascii, hex, and base64.'.format(ctx.prefix)
			await ctx.send(msg)
			return

		types = [ "base64", "hex", "ascii" ]

		if not from_type.lower() in types:
			await ctx.send("Invalid *from* type!")
			return

		if not to_type.lower() in types:
			await ctx.send("Invalid *to* type!")
			return

		if from_type.lower() == to_type.lower():
			await ctx.send("*Poof!* Your encoding was done before it started!")
			return

		try:
			if from_type.lower() == "base64":
				if to_type.lower() == "hex":
					await ctx.send(self.suppressed(ctx.guild, self._base64_to_hex(value)))
					return
				elif to_type.lower() == "ascii":
					await ctx.send(self.suppressed(ctx.guild, self._base64_to_ascii(value)))
					return
			elif from_type.lower() == "hex":
				if to_type.lower() == "ascii":
					await ctx.send(self.suppressed(ctx.guild, self._hex_to_ascii(value)))
					return
				elif to_type.lower() == "base64":
					await ctx.send(self.suppressed(ctx.guild, self._hex_to_base64(value)))
					return
			elif from_type.lower() == "ascii":
				if to_type.lower() == "hex":
					await ctx.send(self.suppressed(ctx.guild, self._ascii_to_hex(value)))
					return
				elif to_type.lower() == "base64":
					await ctx.send(self.suppressed(ctx.guild, self._ascii_to_base64(value)))
					return
		except Exception:
			await ctx.send("I couldn't make that conversion!")
			return		
	
