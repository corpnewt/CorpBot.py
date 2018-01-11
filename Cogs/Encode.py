import asyncio
import discord
from   discord.ext import commands
import base64
import binascii
import re
from   Cogs import Nullify

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Encode(bot, settings))

class Encode:

	# Init with the bot reference
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
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
	async def slide(self, ctx, input_hex = None):
		"""Calculates your slide value for Clover based on an input address (in hex)."""
		try:
			# We're accepting strings here - convert
			start_addr = int(input_hex, 16)
		except:
			await ctx.send("Malformed input hex - try again.")
			return
		# Setup our temp vars
		first_str = "0x100000"
		first = int(first_str, 16)
		secon_str = "0x200000"
		secon = int(secon_str, 16)
		
		slide_float = ( start_addr - first ) / secon
		
		if slide_float > int(slide_float):
			# has a > 0 decimal - round up
			slide_float = int(slide_float) + 1
			
		await ctx.send("```\nslide={}\n```".format(slide_float))
	
	@commands.command(pass_context=True)
	async def hexdec(self, ctx, *, input_hex = None):
		"""Converts hex to decimal."""
		if input_hex == None:
			await ctx.send("Usage: `{}hexdec [input_hex]`".format(ctx.prefix))
			return
		
		input_hex = self._check_hex(input_hex)
		if not len(input_hex):
			await ctx.send("Malformed hex - try again.")
			return
		
		try:
			dec = int(input_hex, 16)
		except Exception:
			await ctx.send("I couldn't make that conversion!")
			return	

		await ctx.send(dec)

	@commands.command(pass_context=True)
	async def dechex(self, ctx, *, input_dec = None):
		"""Converts an int to hex."""
		if input_dec == None:
			await ctx.send("Usage: `{}dechex [input_dec]`".format(ctx.prefix))
			return

		try:
			input_dec = int(input_dec)
		except Exception:
			await ctx.send("Input must be an integer.")
			return

		await ctx.send("0x" + "{:x}".format(input_dec).upper())


	@commands.command(pass_context=True)
	async def strbin(self, ctx, *, input_string = None):
		"""Converts the input string to its binary representation."""
		if input_string == None:
			await ctx.send("Usage: `{}strbin [input_string]`".format(ctx.prefix))
			return
		msg = ''.join('{:08b}'.format(ord(c)) for c in input_string)
		# Format into blocks:
		# - First split into chunks of 8
		msg_list = re.findall('........?', msg)
		# Now we format!
		msg = "```\n"
		msg += " ".join(msg_list)
		msg += "```"	
		if len(msg) > 1993:
			await ctx.send("Well... that was *a lot* of 1s and 0s.  Maybe try a smaller string... Discord won't let me send all that.")
			return
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def binstr(self, ctx, *, input_binary = None):
		"""Converts the input binary to its string representation."""
		if input_binary == None:
			await ctx.send("Usage: `{}binstr [input_binary]`".format(ctx.prefix))
			return
		# Clean the string
		new_bin = ""
		for char in input_binary:
			if char is "0" or char is "1":
				new_bin += char
		if not len(new_bin):
			await ctx.send("Usage: `{}binstr [input_binary]`".format(ctx.prefix))
			return
		msg = ''.join(chr(int(new_bin[i:i+8], 2)) for i in range(0, len(new_bin), 8))
		await ctx.send(self.suppressed(ctx.guild, msg))

	@commands.command(pass_context=True)
	async def binint(self, ctx, *, input_binary = None):
		"""Converts the input binary to its integer representation."""
		if input_binary == None:
			await ctx.send("Usage: `{}binint [input_binary]`".format(ctx.prefix))
			return
		try:
			msg = int(input_binary, 2)
		except Exception:
			msg = "I couldn't make that conversion!"
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def intbin(self, ctx, *, input_int = None):
		"""Converts the input integer to its binary representation."""
		if input_int == None:
			await ctx.send("Usage: `{}intbin [input_int]`".format(ctx.prefix))
			return
		try:
			input_int = int(input_int)
		except Exception:
			await ctx.send("Input must be an integer.")
			return

		await ctx.send("{:08b}".format(input_int))

	

	@commands.command(pass_context=True)
	async def encode(self, ctx, value = None , from_type = None, *, to_type = None):
		"""Data converter from ascii <--> hex <--> base64."""

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
	
