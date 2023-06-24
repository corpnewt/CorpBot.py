import asyncio, discord, base64, binascii, re, math, shutil, tempfile, os, random
from   discord.ext import commands
from   Cogs import Utils, DL, Message, Nullify
from   PIL import Image

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
		self.types = (
			# Decimal types
			"decimal",
			"dec",
			"d",
			"integer",
			"int",
			"i",
			# Base64 types
			"base64",
			"b64",
			"b",
			# Binary types
			"binary",
			"bin",
			# Ascii/text types
			"ascii",
			"a",
			"text",
			"t",
			"string",
			"str",
			"s",
			# Hex types
			"hexadecimal",
			"hex",
			"h",
			"bhex",
			"lhex"
		)
		self.display_types = ("(d)ecimal/(i)nteger","(b)ase64","(bin)ary","(a)scii/(t)ext/(s)tring","(h)ex/bhex/lhex")
		global Utils
		Utils = self.bot.get_cog("Utils")

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
		if not path is None and os.path.exists(path):
			shutil.rmtree(os.path.dirname(path), ignore_errors=True)

	# Helper methods
	def _to_bytes(self, in_string):
		return in_string.encode('utf-8')
	
	def _to_string(self, in_bytes, split_hex = 0):
		out_str = in_bytes.decode("utf-8")
		if split_hex>0: # Break into chunks of split_hex size
			out_str = " ".join((out_str[0+i:split_hex+i] for i in range(0, len(out_str), split_hex))).upper()
		return out_str

	# Check hex value
	def _check_hex(self, hex_string):
		# Remove 0x/0X
		hex_string = hex_string.replace("0x", "").replace("0X", "")
		hex_string = re.sub(r'[^0-9A-Fa-f]+', '', hex_string)
		return hex_string

	def _convert_value(self, val, from_type, to_type):
		# Normalize case
		from_type = from_type.lower()
		to_type = to_type.lower()
		# Ensure types are valid
		if (not from_type in self.types \
		and not from_type.startswith("bin")) \
		or (not to_type in self.types \
		and not to_type.startswith("bin")):
			raise Exception("Invalid from or to type")
		# Resolve the value to hex bytes
		if from_type.startswith(("d","i")):
			val_hex = "{:x}".format(int(val))
			val_adj = binascii.unhexlify("0"*(len(val_hex)%2)+val_hex)
		elif from_type.startswith("bin"):
			val_hex = "{:x}".format(int("".join([x for x in val if x in "01"]),2))
			val_adj = binascii.unhexlify("0"*(len(val_hex)%2)+val_hex)
		elif from_type.startswith("b") and not from_type=="bhex":
			if len(val)%4: # Pad with =
				val += "="*(4-len(val)%4)
			val_adj = base64.b64decode(val.encode())
		elif from_type.startswith(("a","t","s")):
			val_adj = binascii.hexlify(val.encode())
			val_adj = val.encode()
		elif from_type == "lhex": # Little-endian
			val = self._check_hex(val)
			val = "0"*(len(val)%2)+val
			hex_rev = "".join(["".join(x) for x in [val[i:i + 2] for i in range(0,len(val),2)][::-1]])
			val_adj = binascii.unhexlify(hex_rev)
		else: # Assume bhex/hex
			val = self._check_hex(val)
			val_adj = binascii.unhexlify("0"*(len(val)%2)+val)
		# At this point - everything is converted to hex bytes - let's convert
		out = None
		if to_type.startswith(("d","i")):
			out = str(int(binascii.hexlify(val_adj).decode(),16))
		elif to_type.startswith("bin"):
			out = "{:b}".format(int(binascii.hexlify(val_adj).decode(),16))
			# Get our chunk/pad size - use 8 as a fallback
			pad = 8
			if to_type.startswith("binary"):
				try: pad = abs(int(to_type[6:]))
				except: pass
			else:
				try: pad = abs(int(to_type[3:]))
				except: pass
			# Can't have a 0 pad
			if pad <= 0: pad = 8
			# Pad if needed
			if len(out)%pad:
				out = "0"*(pad-len(out)%pad)+out
			# Split into chunks
			out = "{}".format(" ".join((out[0+i:pad+i] for i in range(0,len(out),pad))))
		elif to_type.startswith("b") and not to_type=="bhex":
			out = base64.b64encode(val_adj).decode()
		elif to_type.startswith(("a","t","s")):
			out = val_adj.decode()
		elif to_type == "lhex": # Little-endian
			out = binascii.hexlify(val_adj).decode().upper() # Get the hex values as a string
			pad_val = "0"*(len(out)%2)+out
			out = "".join(["".join(x) for x in [pad_val[i:i + 2] for i in range(0,len(pad_val),2)][::-1]]).upper()
		else:
			out = binascii.hexlify(val_adj).decode().upper()
			if from_type.startswith(("d","i","bin")): # No need to pad to an even length - but prepend 0x
				out = "0x"+hex(int(out,16))[2:].upper()
			else:
				if len(out)%2: # Not from a decimal, and an odd length - prepend 0
					out = "0"+out
				# Also split into chunks of 8 for readability
				out = " ".join((out[0+i:8+i] for i in range(0,len(out),8)))
		return out

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
		if len(base64_string) % 4: base64_string+="="*(4-(len(base64_string)%4))
		base64_bytes  = self._to_bytes(base64_string)
		ascii_bytes   = base64.b64decode(base64_bytes)
		return self._to_string(ascii_bytes)

	# To hex methods
	def _ascii_to_hex(self, ascii_string):
		ascii_bytes = self._to_bytes(ascii_string)
		hex_bytes   = binascii.hexlify(ascii_bytes)
		return self._to_string(hex_bytes,split_hex=8)

	def _base64_to_hex(self, base64_string):
		if len(base64_string) % 4: base64_string+="="*(4-(len(base64_string)%4))
		b64_string   = self._to_bytes(base64_string)
		base64_bytes = base64.b64decode(b64_string)
		hex_bytes    = binascii.hexlify(base64_bytes)
		return self._to_string(hex_bytes,split_hex=8)

	def _rgb_to_hex(self, r, g, b):
		return "#{:02x}{:02x}{:02x}".format(r,g,b).upper()

	def _hex_to_rgb(self, _hex):
		_hex = _hex.lower().replace("#", "").replace("0x","")
		l_hex = len(_hex)
		return tuple(int(_hex[i:i + l_hex // 3], 16) for i in range(0, l_hex, l_hex // 3))

	def _hex_to_cmyk(self, _hex):
		return self._rgb_to_cmyk(*self._hex_to_rgb(_hex))

	def _cmyk_to_hex(self, c, m, y, k):
		return self._rgb_to_hex(*self._cmyk_to_rgb(c,m,y,k))

	def _cmyk_to_rgb(self, c, m, y, k):
		c, m, y, k = [float(x)/100.0 for x in tuple([c, m, y, k])]
		return tuple([round(255.0 - ((min(1.0, x * (1.0 - k) + k)) * 255.0)) for x in tuple([c, m, y])])

	def _rgb_to_cmyk(self, r, g, b):
		c, m, y = [1 - x/255 for x in tuple([r, g, b])]
		min_cmy = min(c, m, y)
		return tuple([0,0,0,100]) if all(x == 0 for x in [r, g, b]) else tuple([round(x*100) for x in [(x - min_cmy) / (1 - min_cmy) for x in tuple([c, m, y])] + [min_cmy]])

	def _hex_int_to_tuple(self, _hex):
		return (_hex >> 16 & 0xFF, _hex >> 8 & 0xFF, _hex & 0xFF)

	@commands.command()
	async def color(self, ctx, *, value = None):
		"""
		View info on a rgb, hex or cmyk color and their
		values in other formats

		Example usage:
		color #3399cc
		color rgb(3, 4, 5)
		color cmyk(1, 2, 3, 4)
		color 0xFF00FF
		"""
		if not value: return await ctx.send("Usage: `{}color [value]`".format(ctx.prefix))
		# Let's replace commas, and parethesis with spaces, then split on whitespace
		values = value.replace(","," ").replace("("," ").replace(")"," ").replace("%"," ").split()
		color_values  = []
		for x in values:
			if x.lower().startswith(("0x","#")) or any((y in x.lower() for y in "abcdef")):
				# We likely have a hex value
				try: color_values.append(int(x.lower().replace("#","").replace("0x",""),16))
				except: pass # Bad value - ignore
			else:
				# Try to convert it to an int
				try: color_values.append(int(x))
				except: pass # Bad value - ignore
		original_type = "hex" if len(color_values) == 1 else "rgb" if len(color_values) == 3 else "cmyk" if len(color_values) == 4 else None
		if original_type is None: return await ctx.send("Incorrect number of color values!  Hex takes 1, RGB takes 3, CMYK takes 4.")
		# Verify values
		max_val = int("FFFFFF",16) if original_type == "hex" else 255 if original_type == "rgb" else 100
		if not all((0 <= x <= max_val for x in color_values)):
			return await ctx.send("Value out of range!  Valid ranges are from `#000000` to `#FFFFFF` for Hex, `0` to `255` for RGB, and `0` to `100` for CMYK.")
		# Organize the data into the Message format expectations
		if original_type == "hex":
			hex_value = "#"+hex(color_values[0]).replace("0x","").rjust(6,"0").upper()
			title = "Color {}".format(hex_value)
			color = color_values[0]
			fields = [
				{"name":"RGB","value":"rgb({}, {}, {})".format(*self._hex_to_rgb(hex_value))},
				{"name":"CMYK","value":"cmyk({}, {}, {}, {})".format(*self._hex_to_cmyk(hex_value))}
				]
		elif original_type == "rgb":
			title = "Color rgb({}, {}, {})".format(*color_values)
			color = int(self._rgb_to_hex(*color_values).replace("#",""),16)
			fields = [
				{"name":"Hex","value":self._rgb_to_hex(*color_values)},
				{"name":"CMYK","value":"cmyk({}, {}, {}, {})".format(*self._rgb_to_cmyk(*color_values))}
			]
		else:
			title = "Color cmyk({}, {}, {}, {})".format(*color_values)
			color = int(self._cmyk_to_hex(*color_values).replace("#",""),16)
			fields = [
				{"name":"Hex","value":self._cmyk_to_hex(*color_values)},
				{"name":"RGB","value":"rgb({}, {}, {})".format(*self._cmyk_to_rgb(*color_values))}
			]
		# Create the image
		file_path = "images/colornow.png"
		try:
			image = Image.new(mode="RGB",size=(512,256),color=self._hex_int_to_tuple(color))
			image.save(file_path)
			await Message.Embed(title=title,color=self._hex_int_to_tuple(color),fields=fields,file=file_path).send(ctx)
		except:
			pass
		if os.path.exists(file_path):
			os.remove(file_path)

	@commands.command()
	async def randomcolor(self, ctx):
		"""Selects a random color."""
		# Pick a random color
		hex_value = "#{}".format("".join([random.choice("0123456789ABCDEF") for x in range(6)]))
		title = "Color {}".format(hex_value)
		color = int(hex_value.replace("#",""),16)
		fields = [
			{"name":"RGB","value":"rgb({}, {}, {})".format(*self._hex_to_rgb(hex_value))},
			{"name":"CMYK","value":"cmyk({}, {}, {}, {})".format(*self._hex_to_cmyk(hex_value))}
		]
		# Create the image
		file_path = "images/colornow.png"
		try:
			image = Image.new(mode="RGB",size=(512,256),color=self._hex_int_to_tuple(color))
			image.save(file_path)
			await Message.Embed(title=title,color=self._hex_int_to_tuple(color),fields=fields,file=file_path).send(ctx)
		except:
			pass
		if os.path.exists(file_path):
			os.remove(file_path)

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

	@commands.command()
	async def slide(self, ctx, *, input_hex = None):
		"""Calculates your slide value for Clover based on an input address (in hex)."""
		if input_hex is None and len(ctx.message.attachments) == 0: # No info passed - bail!
			return await ctx.send("Usage: `{}slide [hex address]`".format(ctx.prefix))
		# Check for urls
		matches = [] if input_hex is None else list(re.finditer(self.regex, input_hex))
		slide_url = ctx.message.attachments[0].url if input_hex is None else None if not len(matches) else matches[0].group(0)
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
			if slide >= 256 or x["start"] == 0: continue # Out of range
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
	
	@commands.command()
	async def hexswap(self, ctx, *, input_hex = None):
		"""Byte swaps the passed hex value."""
		if input_hex is None:
			return await ctx.send("Usage: `{}hexswap [input_hex]`".format(ctx.prefix))
		input_hex = self._check_hex(input_hex)
		if not len(input_hex):
			return await ctx.send("Malformed hex - try again.")
		# Normalize hex into pairs
		input_hex = list("0"*(len(input_hex)%2)+input_hex)
		hex_pairs = [input_hex[i:i + 2] for i in range(0, len(input_hex), 2)]
		hex_rev = hex_pairs[::-1]
		hex_str = "".join(["".join(x) for x in hex_rev])
		await ctx.send(hex_str.upper())
		
	@commands.command()
	async def hexdec(self, ctx, *, input_hex = None):
		"""Converts hex to decimal."""
		if input_hex is None:
			return await ctx.send("Usage: `{}hexdec [input_hex]`".format(ctx.prefix))
		
		input_hex = self._check_hex(input_hex)
		if not len(input_hex):
			return await ctx.send("Malformed hex - try again.")
		
		try:
			dec = int(input_hex, 16)
		except Exception:
			return await ctx.send("I couldn't make that conversion!")

		await ctx.send(dec)

	@commands.command()
	async def dechex(self, ctx, *, input_dec = None):
		"""Converts an int to hex."""
		if input_dec is None:
			return await ctx.send("Usage: `{}dechex [input_dec]`".format(ctx.prefix))

		try:
			input_dec = int(input_dec)
		except Exception:
			return await ctx.send("Input must be an integer.")
		min_length = 2
		hex_str = "{:x}".format(input_dec).upper()
		hex_str = "0"*(len(hex_str)%min_length)+hex_str
		await ctx.send("0x"+hex_str)


	@commands.command()
	async def strbin(self, ctx, *, input_string = None):
		"""Converts the input string to its binary representation."""
		if input_string is None:
			return await ctx.send("Usage: `{}strbin [input_string]`".format(ctx.prefix))
		msg = ''.join('{:08b}'.format(ord(c)) for c in input_string)
		# Format into blocks:
		# - First split into chunks of 8
		msg_list = re.findall('........?', msg)
		# Now we format!
		msg = "```\n"
		msg += " ".join(msg_list)
		msg += "```"	
		if len(msg) > 1993:
			return await ctx.send("Well... that was *a lot* of 1s and 0s.  Maybe try a smaller string... Discord won't let me send all that.")
		await ctx.send(msg)

	@commands.command()
	async def binstr(self, ctx, *, input_binary = None):
		"""Converts the input binary to its string representation."""
		if input_binary is None:
			return await ctx.send("Usage: `{}binstr [input_binary]`".format(ctx.prefix))
		# Clean the string
		new_bin = ""
		for char in input_binary:
			if char == "0" or char == "1":
				new_bin += char
		if not len(new_bin):
			return await ctx.send("Usage: `{}binstr [input_binary]`".format(ctx.prefix))
		msg = ''.join(chr(int(new_bin[i:i+8], 2)) for i in range(0, len(new_bin), 8))
		await ctx.send(Nullify.escape_all(msg))

	@commands.command()
	async def binint(self, ctx, *, input_binary = None):
		"""Converts the input binary to its integer representation."""
		if input_binary is None:
			return await ctx.send("Usage: `{}binint [input_binary]`".format(ctx.prefix))
		try:
			msg = int(input_binary, 2)
		except Exception:
			msg = "I couldn't make that conversion!"
		await ctx.send(msg)

	@commands.command()
	async def intbin(self, ctx, *, input_int = None):
		"""Converts the input integer to its binary representation."""
		if input_int is None:
			return await ctx.send("Usage: `{}intbin [input_int]`".format(ctx.prefix))
		try:
			input_int = int(input_int)
		except Exception:
			return await ctx.send("Input must be an integer.")

		await ctx.send("{:08b}".format(input_int))

	'''@commands.command()
	async def encode(self, ctx, from_type = None , to_type = None, *, value = None):
		"""Data converter from ascii <--> hex <--> base64."""

		if value is None or from_type is None or to_type is None:
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
					await ctx.send(Nullify.escape_all(self._base64_to_hex(value)))
					return
				elif to_type.lower() == "ascii":
					await ctx.send(Nullify.escape_all(self._base64_to_ascii(value)))
					return
			elif from_type.lower() == "hex":
				if to_type.lower() == "ascii":
					await ctx.send(Nullify.escape_all(self._hex_to_ascii(value)))
					return
				elif to_type.lower() == "base64":
					await ctx.send(Nullify.escape_all(self._hex_to_base64(value)))
					return
			elif from_type.lower() == "ascii":
				if to_type.lower() == "hex":
					await ctx.send(Nullify.escape_all(self._ascii_to_hex(value)))
					return
				elif to_type.lower() == "base64":
					await ctx.send(Nullify.escape_all(self._ascii_to_base64(value)))
					return
		except Exception:
			await ctx.send("I couldn't make that conversion!")
			return	'''	
	
	@commands.command()
	async def encode(self, ctx, from_type = None, to_type = None, *, value = None):
		"""Data converter that supports hex, decimal, binary, base64, and ascii."""

		if any((x is None for x in (value,from_type,to_type))):
			return await ctx.send(
				'Usage: `{}encode [from_type] [to_type] [value]`\nAvailable types include:\n- {}'.format(ctx.prefix,"\n- ".join(self.display_types))
			)
		
		if not from_type.lower() in self.types and not from_type.lower().startswith("bin"):
			return await ctx.send("Invalid *from* type!\nAvailable types include:\n- {}".format("\n- ".join(self.display_types)))

		if not to_type.lower() in self.types and not to_type.lower().startswith("bin"):
			return await ctx.send("Invalid *to* type!\nAvailable types include:\n- {}".format("\n- ".join(self.display_types)))

		if from_type.lower() == to_type.lower():
			return await ctx.send("*Poof!* Your encoding was done before it started!")
			
		try:
			return await ctx.send(Nullify.escape_all(self._convert_value(value,from_type,to_type)))
		except Exception as e:
			return await ctx.send(Nullify.escape_all("I couldn't make that conversion:\n{}".format(e)))
