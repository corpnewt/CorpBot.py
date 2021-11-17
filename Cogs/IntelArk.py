import asyncio
import discord
from   discord.ext import commands
from   Cogs import Message
from   Cogs import DL
from   Cogs import PickList
import urllib
import requests

def setup(bot):
	# Add the bot
	bot.add_cog(IntelArk(bot))
	
class IntelArk(commands.Cog):
    
	def __init__(self, bot):
		self.bot = bot
		self.fields = {
			'CodeNameText': 'Codename',
			'ProcessorNumber': 'Name',
			'CoreCount': '# of Cores',
			'ThreadCount': '# of Threads',
			'ClockSpeed': 'Base Clock Speed',
			'ClockSpeedMax': 'Max Clock Speed',
			'MaxTDP': 'TDP',
			'MaxMem': 'Max Memory',
			'ProcessorGraphicsModelId': 'iGPU',
			'InstructionSet': 'Instruction Set',
			'InstructionSetExtensions': 'Extensions'
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
		
		text = self.simplified_name(text)

		# message = await Message.EmbedText(title="Intel Ark Search",description="Gathering info...",color=ctx.author,footer="Powered by http://ark.intel.com").send(ctx)

		args["description"] = "Gathering info..."
		message = await Message.EmbedText(**args).send(ctx)

		try:
			# Query the ARK, and try to return a response
			response = await self.iark_search(text)
		except:
			response = []

		# Check if we got nothing
		if not len(response):
			args["description"] = "No results returned for `{}`.".format(text.replace("`","").replace("\\",""))
			await Message.EmbedText(**args).edit(ctx, message)
			return

		elif len(response) == 1:
			# Set it to the first item
			response = await self.get_match_data(response[0])

		# Check if we got more than one result (either not exact, or like 4790 vs 4790k)
		elif len(response) > 1:
			# Allow the user to choose which one they meant.
			index, message = await PickList.Picker(
				message=message,
				title="Multiple Matches Returned For `{}`:".format(text.replace("`","").replace("\\","")),
				list=[x["label"] for x in response],
				ctx=ctx
			).pick()

			if index < 0:
				args["description"] = "Search cancelled."
				await Message.EmbedText(**args).edit(ctx, message)
				return

			# Got something
			response = await self.get_match_data(response[index])

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

	async def get_match_data(self, match):
		"""Returns the data of a matched entry."""

		text = await DL.async_text('https://ark.intel.com{0}'.format(match.get('prodUrl', '')))
		lines = text.split('\n')
		data = {}

		for line_index in range(len(lines)):
			for key, value in self.fields.items():
				"""
				Grabs the image URL of the current item, if possible.

				For example, we might have an element like this:

					<img ptype="processors" alt="Intel® Core™2 Duo Processor P8600 " 
					src="https://www.intel.com/content/dam/www/global/ark/badges/34530_128.gif/jcr:content/renditions/_64.gif" 
					onerror="ValidateImage(this);" 
					onload="checkImgSize(this);" 
					width="" 
					height=""
					>

				From here, we'd want to isolate what's inside of `src="*"`;
				In order to achieve this, we can simply divide the string into a list.
				
					lines[line_index].split('src="')

				Which will yield something like:

					->  [  
							'<img ptype="processors" alt="Intel® Core™2 Duo Processor P8600 "',     
							'https://www.intel.com/content/dam/www/global/ark/badges/34530_128.gif/jcr:content/renditions/_64.gif" onerror="ValidateImage(this);" onload="checkImgSize(this);" width="" height="">'
						]

				From here, we can select the second element, as it contains the URL we're looking for, and split by `"`.

					lines[line_index].split('src="')[1].split('"')

				Which will yield something like:

					->  [
							'https://www.intel.com/content/dam/www/global/ark/badges/34530_128.gif/jcr:content/renditions/_64.gif',
							' onerror=', 
							'ValidateImage(this);', 
							' onload=', 
							'checkImgSize(this);', 
							' width=', 
							'', 
							' height=', 
							'', 
							'>'
						]

				From here, we can simply select the first element, which is the URL.
				"""
				if 'ptype="processors"' in lines[line_index].lower():
					data['BrandBadge'] = lines[line_index].split('src="')[1].split('"')[0]

				if 'data-key="{}"'.format(key.lower()) in lines[line_index].lower():
					if 'codename' in key.lower():
						data[key] = lines[line_index + 1].strip().split('>')[1].split('<')[0].replace('Products formerly', '').strip()
						continue
					data[key] = lines[line_index + 1].strip().replace("</span>", "")

		return data


	async def quick_search(self, search_term):
		try:
			# Credits to https://github.com/xiongnemo/arksearch (a fork of major/arksearch) for this.
			url = (
				"https://ark.intel.com/libs/apps/intel/arksearch/autocomplete?"
				+ "_charset_=UTF-8"
				+ "&locale=en_us"
				+ "&currentPageUrl=https%3A%2F%2Fark.intel.com%2Fcontent%2Fwww%2Fus%2Fen%2Fark.html"
				+ "&input_query={0}"
			)

			res = await DL.async_json(url.format(search_term))
			return res
		except Exception as e:
			return []

	async def iark_search(self, search_term):
		results = await self.quick_search(self.simplified_name(search_term))

		return results

	def simplified_name(self, search_term):
		replace_dict = {
			"(R)": "®",
			"(TM)": "™",
			"(C)": "©",
			"(P)": "℗",
			"(G)": "℠",
			"CPU": "",
			"@": "",
		}

		for key, val in replace_dict.items():
			if key in search_term:
				search_term = search_term.replace(key, val)

		sanitised_term = ""
		sanitised = search_term.split(' ')

		if len(sanitised) == 1:
			return search_term
		elif len(sanitised) == 2:
			return "-".join(sanitised)

		for i in range(len(sanitised)):
			if i == (len(sanitised) - 2):
				sanitised_term += sanitised[i] + '-' + sanitised[i + 1]
				break
		
			sanitised_term += sanitised[i] + ' '

		return sanitised_term