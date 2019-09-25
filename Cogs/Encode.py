import asyncio, discord, base64, binascii, re, math, shutil, tempfile, os
from   discord.ext import commands
from   Cogs import Nullify, DL

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Encode(bot, settings))

class Encode(commands.Cog):

	# Init with the bot reference
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg

	async def download(self, url):
		url = url.strip("<>")
		# Set up a temp directory
		dirpath = tempfile.mkdtemp()
		tempFileName = url.rsplit('/', 1)[-1]
		# Strip question mark
		tempFileName = tempFileName.split('?')[0]
		filePath = dirpath + "/" + tempFileName
		rImage = None
		try:
			rImage = await DL.async_dl(url)
		except:
			pass
		if not rImage:
			self.remove(dirpath)
			return None
		with open(filePath, 'wb') as f:
			f.write(rImage)
		# Check if the file exists
		if not os.path.exists(filePath):
			self.remove(dirpath)
			return None
		return filePath
		
	def remove(self, path):
		if not path == None and os.path.exists(path):
			shutil.rmtree(os.path.dirname(path), ignore_errors=True)

	# Helper methods
	def _to_bytes(self, in_string):
		return in_string.encode('utf-8')
	
	def _to_string(self, in_bytes):
		return in_bytes.decode('utf-8')

	# Check hex value
	def _check_hex(self, hex_string):
		# Remove 0x/0X
		hex_string = hex_string.replace("0x", "").replace("0X", "")
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

	def _rgb_to_hex(self, r, g, b):
		return '#%02x%02x%02x' % (r, g, b)

	def _hex_to_rgb(self, _hex):
		_hex = _hex.replace("#", "")
		l_hex = len(_hex)
		return tuple(int(_hex[i:i + l_hex // 3], 16) for i in range(0, l_hex, l_hex // 3))

	def _cmyk_to_rgb(self, c, m, y, k):
		c, m, y, k = [float(x)/100.0 for x in tuple([c, m, y, k])]
		return tuple([round(255.0 - ((min(1.0, x * (1.0 - k) + k)) * 255.0)) for x in tuple([c, m, y])])

	def _rgb_to_cmyk(self, r, g, b):
		c, m, y = [1 - x/255 for x in tuple([r, g, b])]
		min_cmy = min(c, m, y)
		return tuple([0,0,0,100]) if all(x == 0 for x in [r, g, b]) else tuple([round(x*100) for x in [(x - min_cmy) / (1 - min_cmy) for x in tuple([c, m, y])] + [min_cmy]])


	@commands.command()
	async def color(self, ctx, *, value = None):
		"""
		View info on a rgb, hex or cmyk color and their
		values in other formats

		Example usage:
		color #3399cc
		color rgb(3, 4, 5)
		"""
		if not value:
			await ctx.send("Usage: `{}color [value]`".format(ctx.prefix))
			return

		value = value.lower()
		
		if not any(value.startswith(x) for x in ["#", "rgb", "cmyk"]):
			await ctx.send("Invalid value color format, please choose from rgb, cmyk or hex")
			return

		error = False

		if value.startswith('rgb'):
			count = value.count('(') + value.count(')') + value.count(',')
			if count != 4:
				error = True

			number_list = value.lower().replace("rgb", "").replace("(", "").replace(")", "").replace(" ", "")
			try:
				r, g, b = map(int, number_list.split(','))

				if (r < 0 or r > 255) or (g < 0 or g > 255) or (b < 0 or b > 255):
					error = True

			except:
				error = True

			if error:
				await ctx.send("Invalid RGB color format!")
				return
			
			_hex = self._rgb_to_hex(r,g,b)
			c, m, y, k = self._rgb_to_cmyk(r, g, b)
			
			embed_color = int("0x{}".format(_hex.replace("#", '')), 16)
			embed = discord.Embed(color=embed_color)

			embed.title = "Color {}".format(value.replace(" ", ""))
			embed.add_field(name="Hex", value=_hex)
			embed.add_field(name="CMYK", value="cmyk({}, {}, {}, {})".format(c, m, y, k))
				
		elif value.startswith('#'):
			match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value)
			if not match:
				await ctx.send("Invalid Hex color format!")
				return

			embed_color = int("0x{}".format(value.replace('#', '')), 16)
			embed = discord.Embed(color=embed_color)
			r, g, b = self._hex_to_rgb(value)
			c, m, y, k = self._rgb_to_cmyk(r, g, b)

			embed.title = "Color {}".format(value.replace(" ", ""))
			embed.add_field(name="RGB", value="rgb({}, {}, {})".format(r, g, b))
			embed.add_field(name="CMYK", value="cmyk({}, {}, {}, {})".format(c, m, y, k))

		elif value.startswith('cmyk'):
			count = value.count('(') + value.count(')') + value.count(',')
			if count != 5:
				error = True

			number_list = value.lower().replace("cmyk", "").replace("(", "").replace(")", "").replace(" ", "")

			try:
				c, m, y, k = map(int, number_list.split(','))

				if (c < 0 or c > 255) or (m < 0 or m > 255) or (y < 0 or y > 255) or (k < 0 or k > 255):
					error = True

			except:
				error = True
			
			if error:
				await ctx.send("Invalid CMYK color format!")
				return
	
			r, g, b = self._cmyk_to_rgb(c, m, y, k)
			_hex = self._rgb_to_hex(r, g, b)

			embed_color = int("0x{}".format(_hex.replace("#", '')), 16)
			embed = discord.Embed(color=embed_color)

			embed.title = "Color {}".format(value.replace(" ", ""))
			embed.add_field(name="Hex", value=_hex)
			embed.add_field(name="RGB", value="rgb({}, {}, {})".format(r, g, b))

		await ctx.send(embed=embed)

	def get_slide(self, start_addr = 0):
		# Setup our temp vars
		m1 = int("0x100000",16)
		m2 = int("0x200000",16)
		
		slide = int(math.ceil(( start_addr - m1 ) / m2))
		return 0 if slide < 0 else slide

	def get_available(self, line_list = []):
		available = []
		for line in line_list:
			line_split = [x for x in line.split(" ") if len(x)]
			if not len(line_split):
				continue
			if len(line_split) == 1:
				# No spaces - let's make sure it's hex and add it
				try: available.append({"start":int(line_split[0],16)})
				except:	continue
			elif line_split[0].lower() == "available":
				# If our first item is "available", let's convert the others into ints
				new_line = []
				for x in line_split:
					new_line.extend(x.split("-"))
				if len(new_line) < 3:
					# Not enough info
					continue
				try:
					available.append({
						"start":int(new_line[1],16),
						"end":int(new_line[2],16),
						"size": (int(new_line[2],16)-int(new_line[1],16))/4096 if len(new_line) < 4 else int(new_line[3],16)
						})
				except:	continue
		return available

	@commands.command(pass_context=True)
	async def slide(self, ctx, *, input_hex = None):
		"""Calculates your slide value for Clover based on an input address (in hex)."""
		if input_hex == None and len(ctx.message.attachments) == 0: # No info passed - bail!
			return await ctx.send("Usage: `{}slide [hex address]`".format(ctx.prefix))
		# Check for urls
		matches = [] if input_hex == None else list(re.finditer(self.regex, input_hex))
		slide_url = ctx.message.attachments[0].url if input_hex == None else None if not len(matches) else matches[0].group(0)
		if slide_url:
			path = await self.download(slide_url)
			if not path: # It was just an attachment - bail
				return await ctx.send("Looks like I couldn't download that link...")
			# Got something - let's load it as text
			with open(path,"rb") as f:
				input_hex = f.read().decode("utf-8","ignore").replace("\x00","").replace("\r","")
			self.remove(path)
		# At this point - we might have a url, a table of data, or a single hex address
		# Let's split by newlines first, then by spaces
		available = self.get_available(input_hex.replace("`","").split("\n"))
		if not len(available):
			return await ctx.send("No available space was found in the passed values.")
		# Let's sort our available by their size - then walk the list until we find the
		# first valid slide
		available = sorted(available, key=lambda x:x.get("size",0),reverse=True)
		slides = []
		for x in available:
			slide = self.get_slide(x["start"])
			if slide < 256:
				# Got a good one - spit it out
				hex_str = "{:x}".format(x["start"]).upper()
				hex_str = "0"*(len(hex_str)%2)+hex_str
				slides.append(("0x"+hex_str,slide))
				# return await ctx.send("Slide value for starting address of 0x{}:\n```\nslide={}\n```".format(hex_str.upper(),slide))
		if not len(slides):
			# If we got here - we have no applicable slides
			return await ctx.send("No valid slide values were found for the passed info.")
		# Format the slides
		pad = max([len(x[0]) for x in slides])
		await ctx.send("**Applicable Slide Values:**\n```\n{}\n```".format("\n".join(["{}: slide={}".format(x[0].rjust(pad),x[1]) for x in slides])))
	
	@commands.command(pass_context=True)
	async def hexswap(self, ctx, *, input_hex = None):
		"""Byte swaps the passed hex value."""
		if input_hex == None:
			await ctx.send("Usage: `{}hexswap [input_hex]`".format(ctx.prefix))
			return
		input_hex = self._check_hex(input_hex)
		if not len(input_hex):
			await ctx.send("Malformed hex - try again.")
			return
		# Normalize hex into pairs
		input_hex = list("0"*(len(input_hex)%2)+input_hex)
		hex_pairs = [input_hex[i:i + 2] for i in range(0, len(input_hex), 2)]
		hex_rev = hex_pairs[::-1]
		hex_str = "".join(["".join(x) for x in hex_rev])
		await ctx.send(hex_str.upper())
		
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
		min_length = 2
		hex_str = "{:x}".format(input_dec).upper()
		hex_str = "0"*(len(hex_str)%min_length)+hex_str
		await ctx.send("0x"+hex_str)


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
	async def encode(self, ctx, from_type = None , to_type = None, *, value = None):
		"""Data converter from ascii <--> hex <--> base64."""

		if value == None or from_type == None or to_type == None:
			msg = 'Usage: `{}encode [from_type] [to_type] [value]`\nTypes include ascii, hex, and base64.'.format(ctx.prefix)
			await ctx.send(msg)
			return

		types = [ "base64", "hex", "ascii" ]
		
		# Allow first letters as well
		from_check = [x for x in types if x[0] == from_type.lower()]
		from_type = from_type if not len(from_check) else from_check[0]
		to_check = [x for x in types if x[0] == to_type.lower()]
		to_type = to_type if not len(to_check) else to_check[0]
		
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
	
