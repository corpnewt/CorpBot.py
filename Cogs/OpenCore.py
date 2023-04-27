import discord, asyncio, re, io, os, datetime
from   discord.ext import commands
from   Cogs import Settings, DL, PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(OpenCore(bot, settings))

class OpenCore(commands.Cog):

	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.tex = None
		self.tex_version = "?.?.?"
		self.is_current = False # Used for stopping loops
		self.wait_time = 21600 # Default of 6 hours (21600 seconds)
		global Utils
		Utils = self.bot.get_cog("Utils")

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.is_current = False

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.is_current = True
		self.bot.loop.create_task(self.update_tex())

	async def update_tex(self):
		print("Starting Configuration.tex update loop - repeats every {:,} second{}...".format(self.wait_time,"" if self.wait_time==1 else "s"))
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			if not self.is_current:
				# Bail if we're not the current instance
				return
			print("Updating Configuration.tex: {}".format(datetime.datetime.now().time().isoformat()))
			if not await self._dl_tex():
				print("Could not download Configuration.tex!")
				if self._load_local():
					print(" - Falling back on local copy!")
			await asyncio.sleep(self.wait_time)

	def _load_local(self):
		if not os.path.exists("Configuration.tex"): return False
		# Try to load it
		try:
			with open("Configuration.tex","r") as f:
				self.tex = f.read()
		except: return False
		# Retain the version
		try: self.tex_version = self.tex.split("Reference Manual (")[1].split(")")[0]
		except: self.tex_version = "?.?.?"
		return True

	async def _dl_tex(self):
		try: self.tex = await DL.async_text("https://github.com/acidanthera/OpenCorePkg/raw/master/Docs/Configuration.tex")
		except: return False
		# Save to a local file
		with open("Configuration.tex","w") as f:
			f.write(self.tex)
		# Retain the version
		try: self.tex_version = self.tex.split("Reference Manual (")[1].split(")")[0]
		except: self.tex_version = "?.?.?"
		return True

	@commands.command(aliases=["updatetex"])
	async def gettex(self, ctx):
		"""Forces an update of the in-memory Configuration.tex file (owner only)."""

		if not await Utils.is_owner_reply(ctx): return
		message = await ctx.send("Downloading Configuration.tex...")
		if await self._dl_tex():
			return await message.edit(content="Successfully updated Configuration.tex in memory.")
		return await message.edit(content="Failed to update Configuration.tex{}!".format(
			" - falling back on local copy" if self._load_local() else ""
		))

	@commands.command(aliases=["occonfig","configtex","ocsearch","configsearch","seachtex","tex"])
	async def octex(self, ctx, *, search_path = None):
		"""Searches the Configuration.tex file in memory for the passed path.  Must include the full path separated by spaces.

		eg.  $occ Kernel Quirks DisableIoMapper
		
		All keys are case-sensitive."""

		usage = "Usage: `{}occ [search_path]`".format(ctx.prefix)
		if not self.tex: return await ctx.send("It looks like I was unable to get the Configuration.tex :(")
		if search_path is None: return await ctx.send(usage)
		# Let's split up the search path and ensure we have a qualified path to give to the parser
		search_path = search_path.replace("-"," ").replace(">"," ").replace("/"," ")
		search_path = re.sub(" {2,}"," ",search_path)
		search_parts = search_path.split()
		if not search_parts: return await ctx.send(usage)

		search_results = self.tex_search(self.tex, search_parts)
		if not search_results: return await ctx.send("Nothing was found for that search :(  Remember that all keys are case-sensitive.")

		# We got something to show - let's build a page-picker
		return await PickList.PagePicker(
			title="Results For: "+" -> ".join(search_parts),
			description=search_results,
			timeout=300, # Allow 5 minutes before we stop watching the picker
			footer="From Configuration.tex for OpenCore v{}".format(self.tex_version),
			ctx=ctx
		).pick()

	### Helper methods adjusted from rusty_bits' config_tex_info.py from ProperTree's repo to search the Configuration.tex ###

	def tex_search(self, config_file, search_list, width = 80, valid_only = False, show_urls = False):
		result = self.parse_configuration_tex(self.tex, search_list, width, valid_only, show_urls)
		if not result:
			return None

		# First we strip out any backticks to avoid accidental markdown
		result = result.replace("`","'")
		# Translate '' into double quotes "
		result = result.replace("''",'"')

		style = "normal"
		in_escape = False
		esc_code = ""
		fixed_string = ""
		out = ""
		
		def dump_out(output,style):
			if not output: return output
			# Helper to bridge styles to markdown
			style_parser = {
				"bold": ("**","**"),
				"bold_mono": ("`","`"),
				"normal": ("",""),
				"mono": ("`","`"),
				"underline": ("__","__"),
				"reverse": ("",""),
				"url": ("",""),
				"italic": ("*","*")
			}
			header,footer = style_parser.get(style,("",""))
			return header+output+footer

		for c in result:
			# quick hack to decode the escape seqs ret from the parse
			# only including encodings needed for Configuration.tex and a
			# few others for now
			if in_escape:
				esc_code += c
				if c == "m":  # end of esc code
					# should be using these to turn font attributes on and off
					# but for now just have a style defined for current needs
					if esc_code == '[0m':
						style = "normal"
					if esc_code == "[10m": # switch to default family
						style = "normal"
					if esc_code == '[1m': # bold on
						if style == "mono":
							style = "bold_mono" # until a better method is found
						else:
							style = "bold"
					if esc_code == "[22m": # bold off
						if style == "bold_mono":
							style = "mono"
						else:
							style = "normal"
					if esc_code == '[3m': # italic on
						style = "italic"
					# [23m italic off
					if esc_code == "[4m": # underline on
						style = "underline"
					# [24m underline off
					if esc_code == '[11m': # switch to mono family
						style = "mono"
					if esc_code == '[7m': # reverse on
						style = "reverse"
					# [27m not reverse
					if esc_code == '[34m': # foreground blue
						if show_urls:
							style = "url"
						else:
							style = "mono"
					out = ""  # found valid esc - clear out
					esc_code = ""
					in_escape = False
				continue
			if c == '\x1b':
				# found end of one esc and start of another
				# dump formatted output to window
				# and start over
				fixed_string += dump_out(out, style)
				out = ""
				in_escape = True
				continue
			# Check for a newline and dump the output
			if c == "\n":
				fixed_string += dump_out(out, style)
				out = ""
			out += c
		if out:
			fixed_string +=  dump_out(out, style)
		# Strip more than one backtick in a row, or orphaned
		# back ticks surrounded by newlines
		fixed_string = re.sub("`{2,}","`",fixed_string)
		fixed_string = re.sub("\\n`\\n","",fixed_string)
		# Return the built string
		return fixed_string

	def parse_configuration_tex(self, config_file, search_list, width, valid_only, show_urls):
		# valid_only: True - return only the valid config.plist options for the search term &
		# return an empty list if no valid options found
		#     False: return whole text of section
		#
		# show_urls: True - return full url of links in the text
		#     False - return only link text with no url
		config = io.StringIO(self.tex)

		result = []
		search_len = len(search_list)
		if search_len == 0:  # we shouldn't get here, but just in case
			return result

		search_terms = ["\\section{"]
		search_terms[0] += search_list[0]
		text_search = search_list[search_len - 1] # ultimately looking for last item

		# set the search terms based on selected position
		if search_len == 1:
			# we're done
			pass
		elif search_len == 2:
			search_terms.append("\\subsection{Properties")
			search_terms.append("texttt{" + text_search + "}\\")
		elif search_len == 3:
			if search_list[0] == "NVRAM": # look for value in Introduction
				search_terms.append("\\subsection{Introduction")
				search_terms.append("texttt{" + text_search + "}")
			else:
				search_terms.append(
					"\\subsection{" + search_list[1] + " Properties")
				search_terms.append("texttt{" + text_search + "}\\")
		elif search_len == 4:
			item_zero = search_list[0]
			sub_search = "\\subsection{"
			if item_zero == "NVRAM": # look for UUID:term in Introduction
				sub_search = "\\subsection{Introduction"
				text_search = search_list[2]
				text_search += ":"
				text_search += search_list[3]
				text_search += "}"
			elif item_zero == "DeviceProperties": # look in Common
				sub_search += "Common"
				text_search += "}"
			elif item_zero == "Misc": # Entry Properties or subsub
				if len(search_list[2]) < 3:
					sub_search += "Entry Properties"
				else:
					sub_search = "\\subsubsection{"
					sub_search += search_list[1]
				text_search += "}"
			else:
				sub_search += search_list[1]
				sub_search += " Properties"
				text_search += "}\\"
			search_terms.append(sub_search)
			search_terms.append("texttt{" + text_search)
		elif search_len == 5:
			sub_search = "\\subsubsection{"
			sub_search += search_list[1]
			search_terms.append(sub_search)
			search_terms.append("texttt{" + text_search)

		# move down the Configuration.tex to the section we want
		for i in range(0, len(search_terms)):
			while True:
				line = config.readline()
				if not line:
					return result
				if search_terms[i] in line:
					break

		align = False
		itemize = 0
		not_first_item = False
		in_listing = False
		enum = 0
		columns = 0
		lines_between_valid = 0
		last_line_ended_in_colon = False
		last_line_had_forced_return = False
		last_line_ended_in_return = False
		last_line_was_blank = False

		while True:
			# track document state & preprocess line before parsing
			line = config.readline()
			if not line:
				break
			line = line.strip()
			if line.startswith("%"): # skip comments
				continue
			if "\\subsection{Introduction}" in line:
				continue
			if "\\begin{tabular}" in line:
				result.append("\x1b[11m")
				for c in line:
					if c == "c":
						columns += 1
				continue
			if "\\begin(align*}" in line:
				align = True
				continue
			if "\\end{align*}}" in line:
				align = False
				continue
			if "\\begin{itemize}" in line:
				itemize += 1
				continue
			if "\\begin{enumerate}" in line:
				enum += 1
				continue
			if "\\begin{lstlisting}" in line:
				in_listing = True
				result.append("\n\x1b[11m")
				continue
			if "\\begin{" in line: # ignore other begins
				continue
			if "\\mbox" in line:
				continue
			if "\\end{tabular}" in line:
				result.append("\x1b[10m")
				columns = 0
				continue
			if "\\end{itemize}" in line:
				itemize -= 1
				if itemize == 0 and enum == 0:
					not_first_item = False
				continue
			if "\\end{enumerate}" in line:
				enum = 0
				if itemize == 0:
					not_first_item = False
				continue
			if "\\end{lstlisting}" in line:
				in_listing = False
				result.append("\x1b[10m\n")
				continue
			if "\\end{" in line: # ignore other ends
				continue
			if "\\item" in line:
				if itemize == 0 and enum == 0:
					break # skip line, not itemizing, shouldn't get here
				else:
					if not_first_item or not last_line_ended_in_return:
						# newline before this item
						result.append("\n")
					not_first_item = True
					if itemize == 0: # in enum
						if search_len == 1: # first level enumerate, use numeric
							replace_str = str(enum) + "."
						else: # use alpha
							replace_str = "(" + chr(96 + enum) + ")"
						line = line.replace("\\item", replace_str)
						enum += 1
					elif itemize == 1: # first level item
						line = line.replace("\\item", u"\u2022")
					else:
						line = line.replace("\\item", "-")
					# fix indenting
					line = "    "*itemize + line
					if enum != 0:
						line = "    " + line
			else:
				if itemize > 0 or enum > 0: # inside multi line item
					if last_line_had_forced_return:
						line = "    "*itemize + line
						line = "       " + line # indent
			if "section{" in line: # stop when next section is found
	# let's try only checking for "section{" instead of 3 checks
	#        if "\\section{" in line or "\\subsection{" in line or "\\subsubsection{" in line:
				# reached end of current section
				break

			if line.strip() == "": # blank line, need linefeed, maybe two, maybe none
				if last_line_ended_in_colon:
					parsed_line = "\n"
				else:
					if last_line_was_blank:  # skip this blank line
						continue
					else:
						parsed_line = "\n\n"
				last_line_was_blank = True
			else:
				last_line_was_blank = False
				parsed_line = self.parse_line(line, columns, width,
										align, valid_only, show_urls)
				if len(parsed_line) == 0:
					continue
				# post process line
				last_line_had_forced_return = False
				last_line_ended_in_colon = False
				if parsed_line.endswith("\n"):
					last_line_had_forced_return = True
				elif parsed_line.endswith(":"):
					parsed_line += "\n"
					if not_first_item:
						# treat as forced return instead
						last_line_had_forced_return = True
					else:
						last_line_ended_in_colon = True
				else:
					parsed_line += " "  # add space for next word

			if parsed_line.endswith("\n"):
				# slightly different use than last_line_had_forced_return
				last_line_ended_in_return = True
			else:
				last_line_ended_in_return = False
			if valid_only: # we only want to return valid plist options for the field
				if itemize > 0:
					if "---" in line:
						if lines_between_valid < 10:
							result.append(parsed_line)
				else:
					if len(result) > 0:
						lines_between_valid += 1
			else:
				result.append(parsed_line)
				if in_listing:
					result.append("\n")
		# Join the result into a single string and remove
		# leading, trailing, and excessive newlines
		# result = re.sub(r"\n{2,}",r"\n\n","".join(result))
		# return result.strip("\n")

		# leave all excess internal newlines for now for easier debugging
		return "".join(result).strip("\n")

		# return re.sub("\n{2,}", "\n\n", "".join(result)).strip("\n")


	def parse_line(self, line, columns, width, align, valid_only, show_urls):
		ret = ""
		build_key = False
		key = ""
		col_width = 0
		if columns > 0:
			col_width = int(width / (columns + 1))
		ignore = False
		col_contents_len = 0
		line = line.rstrip()
		for c in line:
			if build_key:
				if c in "{[":
					build_key = False
					if not valid_only:
						if key == "text":
							ret += "\x1b[0m"
						elif key == "textit":
							ret += "\x1b[3m"
						elif key == "textbf":
							ret += "\x1b[1m"
						elif key == "emph":
							ret += "\x1b[3m"
						elif key == "texttt":
							ret += "\x1b[11m"
						elif key == "href":
							if show_urls:
								ret += "\x1b[34m"
							else:
								ignore = True
						else:
							ignore = True
					if key != "href":
						key = ""
				elif c in " ,()\\0123456789$&":
					build_key = False
					ret += self.special_char(key)
					col_contents_len += 1
					if c in ",()0123456789$":
						ret += c
					if c == "\\":
						if len(key) > 0:
							build_key = True
					key = ""
				elif c in "_^#":
					build_key = False
					ret += c
					col_contents_len += 1
					key = ""
				else:
					key += c
			else:
				if c == "\\":
					build_key = True
				elif c in "}]":
					if not ignore:
						if not valid_only:
							if columns > 0:
								ret += "\x1b[22m"
							else:
								ret += "\x1b[0m"
							if key == "href":
								# ret += " "
								key = ""
							elif c == "]":
								ret += "]"
					ignore = False
				elif c == "{":
					if not valid_only:
						ret += "\x1b[11m"
				elif c == "&":
					if columns > 0:
						pad = col_width - col_contents_len - 1
						if pad > 0:
							ret += " "*pad
						col_contents_len = 0
						ret += "|"
					else:
						if not align:
							ret += "&"
				else:
					if not ignore:
						ret += c
						col_contents_len += 1

		if len(key) > 0:
			ret += self.special_char(key)

		if not valid_only:
			if key == "tightlist":
				ret = ""
			else:
				if key == "hline":
					ret = "-"*(width-4)
					ret += "\n"
			if line.endswith("\\\\"):
				ret += "\n"
		return ret


	def special_char(self, key):
		if key == "kappa":
			return u"\u03f0"
		elif key == "lambda":
			return u"\u03bb"
		elif key == "mu":
			return u"\u03bc"
		elif key == "alpha":
			return u"\u03b1"
		elif key == "beta":
			return u"\u03b2"
		elif key == "gamma":
			return u"\u03b3"
		elif key == "leq":
			return u"\u2264"
		elif key == "cdot":
			return u"\u00b7"
		elif key == "in":
			return u"\u220a"
		elif key == "infty":
			return u"\u221e"
		elif key == "textbackslash":
			return "\\"
		elif key == "hline":
			return u"\u200b"
		else:
			return " "
