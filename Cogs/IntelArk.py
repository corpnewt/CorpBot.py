from   discord.ext import commands
from   Cogs import Message
from   Cogs import DL
from   Cogs import PickList
import re, urllib.parse

def setup(bot):
	# Add the bot
	bot.add_cog(IntelArk(bot))
	
class IntelArk(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.h = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

	@commands.command(aliases=["intelark"])
	async def iark(self, ctx, *, text : str = None):
		"""Search for Intel CPU info."""

		args = {
			"title":"Intel Search",
			"description":'Usage: `{}iark [cpu model]`'.format(ctx.prefix),
			"footer":"Powered by https://www.intel.com",
			"color":ctx.author
		}

		if text is None: return await Message.Embed(**args).send(ctx)
		original_text = text # Retain the original text sent by the user

		# Strip single quotes
		text = text.replace("'","")
		if not len(text):
			return await Message.Embed(**args).send(ctx)

		args["description"] = "Gathering info..."
		message = await Message.Embed(**args).send(ctx)

		try:
			# Query the ARK, and try to return a response
			response = await self.quick_search(text)
		except:
			response = []

		# Check if we got nothing
		if not len(response):
			args["description"] = "No results returned for `{}`.".format(original_text.replace("`","").replace("\\",""))
			return await Message.Embed(**args).edit(ctx, message)

		index = 0 # Default to the first
		# Check if we got more than one result (either not exact, or like 4790 vs 4790k)
		if len(response) > 1:
			response = response[:10] # Only accept a max of 10
			# Allow the user to choose which one they meant.
			index, message = await PickList.Picker(
				message=message,
				title="Multiple Matches Returned For `{}`:".format(original_text.replace("`","").replace("\\","")),
				list=[x["label"] for x in response],
				ctx=ctx
			).pick()

			if index < 0:
				args["description"] = "Search cancelled."
				return await Message.Embed(**args).edit(ctx, message)

		# Got something
		try:
			response = await self.get_match_data(response[index])
		except:
			response = {}
		
		# Verify if we got something
		if not response.get("list"):
			try: # Maybe we got a product line - or something other than a specific CPU?
				args["title"] = response["title"]
				args["url"] = response["url"]
				args["description"] = "Could not retrieve specific data for this search.\nPlease follow the title link (or click [here]({})) to open your search results in your browser.".format(response["Link"])
			except: # Fall back on a generic error
				args["description"] = "Something went wrong getting search data!"
			return await Message.Embed(**args).edit(ctx, message)

		# Fill out the rest of the values
		args["ctx"] = ctx
		args["max"] = 18
		args["message"] = message
		args["description"] = None
		for key in response:
			args[key] = response[key]
		# Display the content
		await PickList.PagePicker(**args).pick()
	
	def clean_search(self, search_term, xeon_check=False, strip_prefix=False):
		# Clean up the search terms to prevent some issues with Intel.com
		# getting a bit confused.  This mostly shows up with Xeons and the
		# newer Ultra CPUs if some query elements are retained.
		#
		# Strip non-ASCII chars
		search_term = re.sub(
			r"[^\x00-\x7F]+",
			"",
			search_term
		)
		if re.search(r"(?i)\b(\w\d(\-|\s))?(\w*\d+\w*){3,}\b",search_term):
			# Got a model number in there - make sure we strip
			# the branding like Processor, Core, Ultra, CPU, etc
			search_term = re.sub(
				r"(?i)\b(?!(K|M|G|T)Hz)(core[\-\s]?2|[^\d\s]{2,})\b",
				"",
				search_term
			)
		# Make sure we use spaces for Xeon models
		if xeon_check and re.search(r"(?i)e\d\-[a-z\d]{4,}",search_term):
			search_term = search_term.replace("-"," ")
		# Strip out the iX-#### prefix if needed
		if strip_prefix:
			search_term = re.sub(
				r"(?i)[a-z]\d\-",
				"",
				search_term
			)
		# Ensure we don't have erroneous spaces
		search_term = re.sub(
			r"\s+",
			" ",
			search_term
		)
		# Check for X.XGHz and convert to X.XX GHz
		for m in re.finditer(r"(?i)\b(\d+(\.\d)?){1,}\s?((K|M|G|T)?Hz)\b",search_term):
			m = m.group()
			try:
				# Get the numbers and suffix
				val = m[:-3].strip()
				suf = m[-3:].strip()
				# Make sure the number is padded if need be
				if "." in val and len(val.split(".")[-1]) < 2:
					val = val+"0" # Pad with a 0
				search_term = search_term.replace(m,"{} {}Hz".format(val,suf[0].upper()))
			except:
				pass
		return search_term.strip()

	async def get_match_data(self, match):
		"""Returns the data of a matched entry."""

		if not "prodUrl" in match: return
		data = {
			"url":match["prodUrl"],
			"title":match.get("label","Intel Search")
		}
		text = await DL.async_text(data["url"])
		
		current_key = None
		data["list"] = []
		for line in text.split("<h3>Essentials</h3>")[-1].split("\n"):
			if '<div class="disclaimer">' in line:
				break # Got to the end
			if "<span>" in line and current_key is None:
				# Got a new key
				if "t<sub>junction</sub>" in line.lower():
					# Special handling to avoid dropping "junction"
					current_key = "Tjunction Max"
				elif "t<sub>case</sub>" in line.lower():
					# Special handling to avoid dropping "case"
					current_key = "Tcase Max"
				else:
					current_key = line.split("<span>")[1].split("<")[0].strip()
				continue
			if current_key is None:
				# We don't have a key yet - skip until we do
				continue
			if "<span>" in line or "</a>" in line:
				# We have a current key, and what seems to be the results - save them
				if "</a>" in line and "<a href=" in line:
					# It's got a link in it - let's rip that out as well
					url = line.split('<a href="')[1].split('"')[0] # Get the URL referenced
					if url.startswith("/"):
						# It's referencing a local value - prepend
						url = "https://www.intel.com"+url
					val = "[{}]({})".format(
						line.split('">')[1].split("<")[0], # Get the name of the value
						url
					)
				else:
					val = line.split(">")[1].split("<")[0]
				data["list"].append({
					"name":current_key,
					"value":val.strip(),
					"inline":True
				})
				current_key = None # Reset the key
		# Try to pull the thumbnail as well
		# Omit this for now - it seems there's some inconsistencies, and trouble loading
		'''try:
			data["thumbnail"] = "https://www.intel.com/content/dam/www/central-libraries/"+text.split("/content/dam/www/central-libraries/")[-1].split('"')[0]
		except:
			pass'''
		return data

	async def quick_search(self, search_term):
		try:
			search_term = self.clean_search(search_term)
			if not search_term:
				return []
			search_term_stripped = self.clean_search(search_term,xeon_check=True,strip_prefix=True)
			url = "https://www.intel.com/content/www/us/en/search.html?ws=text#q={}&sort=relevancy".format(
				urllib.parse.quote(search_term.strip())
			)
			res = await DL.async_text(url)

			# Let's split the resulting HTML at ighfToken: ' to get our token
			token = res.split("ighfToken: '")[1].split("'")[0]
			# Let's force a coveo search
			# Build a simple query
			post_data = {
				"q":search_term,
				"aq":"@localecode==en_US"
			}
			# Build a new set of headers with the access token
			search_headers = {}
			for x in self.h:
				# Shallow copy our current headers
				search_headers[x] = self.h[x]
			# Add the authorization
			search_headers["Authorization"] = "Bearer {}".format(token)
			# Run the actual coveo search
			search_data = await DL.async_post_json(
				"https://platform.cloud.coveo.com/rest/search/v2",
				post_data,
				search_headers
			)

			if not search_data or not search_data.get("results"):
				return []
			# Let's iterate the results
			results = []
			for result in search_data["results"]:
				title = result.get("title","").lower()
				filen = result.get("raw",{}).get("filename","").lower()
				uri   = result.get("uri","").split("?")[0] # Strip modifiers to the URL
				if "processor" in title and not "family" in title and "/products/sku/" in uri:
					if uri.endswith("/ordering.html"):
						uri = uri[:-len("/ordering.html")]+"/specifications.html"
					if any(x.get("prodUrl") == uri for x in results):
						continue # Skip duplicates
					label = result.get("title",uri.split("/")[-1])
					# Check if it's exact - and avoid returning multiple results when not needed
					if self.clean_search(label,strip_prefix=True).lower() == search_term_stripped.lower():
						return [{"label":label,"prodUrl":uri}]
					results.append({
						"label":label,
						"prodUrl":uri
					})
			return sorted(results,key=lambda x:x["label"])
		except Exception as e:
			return []
