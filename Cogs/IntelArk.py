import asyncio
import discord
from   discord.ext import commands
from   Cogs import Message
from   Cogs import DL
from   Cogs import PickList
import urllib

def setup(bot):
	# Add the bot
	bot.add_cog(IntelArk(bot))
	
class IntelArk:
    
	def __init__(self, bot):
		self.bot = bot
		self.fields = {
			"ProcessorNumber": "Processor Name",
			"ProcessorBrandName": "Processor Brand String",
			"BornOnData": "Release Date",
			"ClockSpeed": "Base Clock",
			"ClockSpeedMax": "Max Clock",
			"CoreCount": "Cores",
			"ThreadCount": "Threads",
			"MaxMem": "Max Memory",
			"GraphicsModel": "Onboard Graphics",
			"InstructionSet": "Instruction Set",
			"InstructionSetExtensions": "Extensions"
		}

	@commands.command(pass_context=True, no_pm=True)
	async def iark(self, ctx, *, text : str = None):
		"""Search Ark for Intel CPU info."""

		args = {
			"title":"Intel Ark Search",
			"description":'Usage: `{}iark [cpu model]`'.format(ctx.prefix),
			"footer":"Powered by http://ark.intel.com",
			"color":ctx.author
		}

		if isinstance(ctx.channel, discord.DMChannel):
			args["description"] = "Please search in the main channel."
			await Message.EmbedText(**args).send(ctx)
			return

		if text == None:
			await Message.EmbedText(**args).send(ctx)
			return

		# message = await Message.EmbedText(title="Intel Ark Search",description="Gathering info...",color=ctx.author,footer="Powered by http://ark.intel.com").send(ctx)

		args["description"] = "Gathering info..."
		message = await Message.EmbedText(**args).send(ctx)

		# Process the search terms
		search_url = "https://ark.intel.com/search/AutoComplete?term={}".format(urllib.parse.quote(text))
		try:
			# Get the response
			response = await DL.async_json(search_url)
		except:
			response = []

		# Strip out those without a category
		response = [x for x in response if x.get("category","") != ""]
		if not len(response):
			args["description"] = "No results returned for `{}`.".format(text.replace("`",""))
			await Message.EmbedText(**args).edit(ctx, message)
			return

		# Let's see if we have one match that reeeeeaaallly matches
		# We're going to split the label at Processor, and again at ( to try to isolate
		if len(response) > 1:
			got = None
			for x in response:
				try:
					if "Core" in x["label"]:
						# Core [model] Processor
						match_string = x["label"].split("Core™ ")[1].split(" Processor")[0].lower()
					else:
						# Processor [model] (...
						match_string = x["label"].split("Processor ")[1].split(" (")[0].lower()
					if match_string == text.lower() or match_string.split("-")[1].lower() == text.lower():
						# Exact match!
						got = x
						break
				except:
					# Probably incorrect formatting - bail
					pass
			response = [got] if got else response

		# Set to our first match
		if len(response) > 1:
			# Trim to a max of 5
			if len(response) > 5:
				response = response[0:5]
			index, message = await PickList.Picker(
				message=message,
				title="Multiple Matches Returned For `{}`:".format(text.replace("`","")),
				list=[x["label"] for x in response],
				ctx=ctx
			).pick()
			if index < 0:
				args["description"] = "Search cancelled."
				await Message.EmbedText(**args).edit(ctx, message)
				return
			# Got something
			response = response[index]
			args["description"] = "Gathering info for `{}`...".format(response["label"])
			message = await Message.EmbedText(**args).edit(ctx, message)
		else:
			response = response[0]
		
		# Get the product id - if it exists
		if "id" in response:
			# Gather a new query
			prod_url = "https://odata.intel.com/API/v1_0/Products/Processors()?&$filter={}&$format=json".format(urllib.parse.quote("ProductId eq "+str(response["id"])))
			try:
				# Get the product info
				res = await DL.async_json(prod_url)
				# Grab the first result
				response = res["d"][0]
			except:
				pass
		
		if not any([x for x in self.fields if x in response]):
			# None of our fields match - return no results error
			args["description"] = "No results returned for `{}`.".format(text.replace("`",""))
			await Message.EmbedText(**args).edit(ctx, message)
			return

		# Setup for embed
		fields = [{"name":self.fields[x], "value":response.get(x,None), "inline":True} for x in self.fields]

		await Message.Embed(
			thumbnail=response.get("BrandBadge",None),
			pm_after=11,
			title=response.get("ProductName","Intel Ark Search"),
			fields=fields,
			url=response.get("Link",None),
			footer="Powered by http://ark.intel.com",
			color=ctx.author
			).edit(ctx, message)
