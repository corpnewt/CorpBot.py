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
	
class IntelArk(commands.Cog):
    
	def __init__(self, bot):
		self.bot = bot
		self.fields = {
			"ProcessorNumber": "Processor Name",
			"ProcessorBrandName": "Processor Brand String",
			"BornOnDate": "Release Date",
			"ClockSpeed": "Base Clock",
			"ClockSpeedMax": "Max Clock",
			"CoreCount": "Cores",
			"ThreadCount": "Threads",
			"MaxMem": "Max Memory",
			"MaxTDP": "Max TDP",
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

		if text == None:
			await Message.EmbedText(**args).send(ctx)
			return

		# Strip single quotes
		text = text.replace("'","")
		if not len(text):
			await Message.EmbedText(**args).send(ctx)
			return

		# message = await Message.EmbedText(title="Intel Ark Search",description="Gathering info...",color=ctx.author,footer="Powered by http://ark.intel.com").send(ctx)

		args["description"] = "Gathering info..."
		message = await Message.EmbedText(**args).send(ctx)

		search_url = "https://odata.intel.com/API/v1_0/Products/Processors()?&$filter=substringof(%27{}%27,ProductName)&$format=json&$top=5".format(urllib.parse.quote(text))
		try:
			# Get the response
			response = await DL.async_json(search_url)
			response = response["d"]
		except:
			response = []
		# Check if we got nothing
		if not len(response):
			args["description"] = "No results returned for `{}`.".format(text.replace("`","").replace("\\",""))
			await Message.EmbedText(**args).edit(ctx, message)
			return
		elif len(response) == 1:
			# Set it to the first item
			response = response[0]
		# Check if we got more than one result (either not exact, or like 4790 vs 4790k)
		elif len(response) > 1:
			# Check the top result - and if the ProcessorNumber == our search term - we good
			proc_num = response[0].get("ProcessorNumber","")
			if proc_num.lower().strip() == text.lower().strip():
				# found it
				response = response[0]
			else:
				# Not exact - let's give options
				index, message = await PickList.Picker(
					message=message,
					title="Multiple Matches Returned For `{}`:".format(text.replace("`","").replace("\\","")),
					list=[x["ProcessorNumber"] for x in response],
					ctx=ctx
				).pick()
				if index < 0:
					args["description"] = "Search cancelled."
					await Message.EmbedText(**args).edit(ctx, message)
					return
				# Got something
				response = response[index]
		# At this point - we should have a single response
		# Let's format and display.
		fields = [{"name":self.fields[x], "value":response.get(x,None), "inline":True} for x in self.fields]
		await Message.Embed(
			thumbnail=response.get("BrandBadge",None),
			pm_after=12,
			title=response.get("ProductName","Intel Ark Search"),
			fields=fields,
			url=response.get("Link",None),
			footer="Powered by http://ark.intel.com",
			color=ctx.author
			).edit(ctx, message)
