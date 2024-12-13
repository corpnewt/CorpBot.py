import asyncio, discord, time, shutil, os, tempfile, json
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, Settings, ReadableTime, DisplayName, Message, Nullify, PickList, DL

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Profile(bot, settings))

# This is the profiles module.

class Profile(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

		
	@commands.command(aliases=["newprofile"])
	async def addprofile(self, ctx, name = None, *, link = None):
		"""Add a profile to your profile list."""
		if not ctx.guild:
			return await ctx.send("Profiles cannot be set in dm!")
		# Remove tabs, newlines, and carriage returns and strip leading/trailing spaces from the name
		name = None if name is None else name.replace("\n"," ").replace("\r","").replace("\t"," ").strip()
		if name is None or link is None:
			msg = 'Usage: `{}addprofile "[profile name]" [link]`'.format(ctx.prefix)
			return await ctx.send(msg)
		itemList = self.settings.getUserStat(ctx.author, ctx.guild, "Profiles", [])
		if not itemList:
			itemList = []
		currentTime = int(time.time())
		item = next((x for x in itemList if x["Name"].lower() == name.lower()),None)
		if item:
			msg = Utils.suppressed(ctx,"{}'s {} profile was updated!".format(DisplayName.name(ctx.author),Nullify.escape_all(item["Name"])))
			item["URL"] = link
			item["Updated"] = currentTime
		else:
			itemList.append({"Name":name,"URL":link,"Created":currentTime})
			msg = Utils.suppressed(ctx,"{} added to {}'s profile list!".format(Nullify.escape_all(name),DisplayName.name(ctx.author)))
		self.settings.setUserStat(ctx.author, ctx.guild, "Profiles", itemList)
		await ctx.send(msg)
		
		
	@commands.command(aliases=["remprofile","delprofile","deleteprofile"])
	async def removeprofile(self, ctx, *, name = None):
		"""Remove a profile from your profile list."""
		name = None if name is None else name.replace("\n"," ").replace("\r","").replace("\t"," ").strip()
		if name is None:
			msg = 'Usage: `{}removeprofile [profile name]`'.format(ctx.prefix)
			return await ctx.send(msg)

		itemList = self.settings.getUserStat(ctx.author, ctx.guild, "Profiles", [])
		if not itemList or itemList == []:
			msg = '*{}* has no profiles set!  They can add some with the `{}addprofile "[profile name]" [link]` command!'.format(DisplayName.name(ctx.author), ctx.prefix)
			return await ctx.send(msg)
		item = next((x for x in itemList if x["Name"].lower() == name.lower()),None)
		if not item:
			return await ctx.send(Utils.suppressed(ctx,"{} not found in {}'s profile list!".format(Nullify.escape_all(name),DisplayName.name(ctx.author))))
		itemList.remove(item)
		self.settings.setUserStat(ctx.author, ctx.guild, "Profiles", itemList)
		await ctx.send(Utils.suppressed(ctx,"{} removed from {}'s profile list!".format(Nullify.escape_all(item["Name"]),DisplayName.name(ctx.author))))

	def _get_profile(self,ctx,name=None):
		parts = name.split()
		for j in range(len(parts)):
			# Reverse search direction
			i = len(parts)-1-j
			# Name = 0 up to i joined by space
			name_str    = ' '.join(parts[0:i+1])
			# Profile = end of name -> end of parts joined by space
			profile_str = ' '.join(parts[i+1:])
			mem_from_name = DisplayName.memberForName(name_str, ctx.guild)
			if mem_from_name:
				if not profile_str:
					continue # Skip member-only matches
				# We got a member - let's gather their profiles
				itemList = self.settings.getUserStat(mem_from_name, ctx.guild, "Profiles", [])
				if not itemList:
					continue # Nothing to check - skip
				# Check if the member passed is us - and see if it's part of the
				# profile name first
				if mem_from_name == ctx.author:
					item = next((x for x in itemList if x["Name"].lower() == name.lower()),None)
					if item:
						return (mem_from_name,item)
				# Not us, or not a match - check the profile string directly
				item = next((x for x in itemList if x["Name"].lower() == profile_str.lower()),None)
				if item:
					return (mem_from_name,item)
		# Check if the whole string is our profile
		itemList = self.settings.getUserStat(ctx.author, ctx.guild, "Profiles", [])
		item = next((x for x in itemList if x["Name"].lower() == name.lower()),None)
		if item:
			return (ctx.author,item)
		# If we got here, there were no matches
		return None

	async def _get_profile_reply(self,ctx,name=None,raw=False):
		if not name:
			msg = "Usage: `{}{}profile [member] [profile name]`".format(ctx.prefix, "raw" if raw else "")
			return await ctx.send(msg)
		item = self._get_profile(ctx,name)
		if item is None:
			return await ctx.send("Sorry, I couldn't find that user/profile.")
		member,item = item
		if item is None:
			# Just got a member - list their profiles
			return await self._list_profiles(ctx,member.id)
		msg = '*{}\'s {}{} Profile:*\n\n{}'.format(
			DisplayName.name(member),
			"Raw " if raw else "",
			Nullify.escape_all(item['Name']),
			discord.utils.escape_markdown(item['URL']) if raw else item['URL']
		)
		return await ctx.send(Utils.suppressed(ctx,msg))

	async def _list_profiles(self,ctx,member=None,raw=None):
		if not member:
			member = ctx.author
		else:
			newMember = DisplayName.memberForName(member, ctx.guild)
			if not newMember:
				# no member found by that name
				msg = 'I couldn\'t find *{}* on this server.'.format(member)
				return await ctx.send(Utils.suppressed(ctx,msg))
			member = newMember
		# We have a member here
		itemList = self.settings.getUserStat(member, ctx.guild, "Profiles", [])
		if not itemList or itemList == []:
			msg = '*{}* has no profiles set!  They can add some with the `{}addprofile "[profile name]" [link]` command!'.format(DisplayName.name(member), ctx.prefix)
			return await ctx.send(msg)
		itemList = sorted(itemList, key=itemgetter('Name'))
		title="{}'s {}Profiles ({:,} total)".format(
			DisplayName.name(member),
			"Raw " if raw else "",
			len(itemList)
		)
		items = []
		for i,x in enumerate(itemList,start=1):
			items.append(
				"{}. {}".format(
					i,
					discord.utils.escape_markdown(x["Name"]) if raw else x["Name"]
				)
			)
		return await PickList.PagePicker(
			title=title,
			description="\n".join(items),
			ctx=ctx
		).pick()

	@commands.command()
	async def profile(self, ctx, *, member = None, name = None):
		"""Retrieve a profile from the passed user's profile list."""
		await self._get_profile_reply(ctx,member)

	@commands.command()
	async def rawprofile(self, ctx, *, member = None, name = None):
		"""Retrieve a profile's raw markdown from the passed user's profile list."""
		await self._get_profile_reply(ctx,member,raw=True)

	@commands.command()
	async def profileinfo(self, ctx, *, member = None, name = None):
		"""Displays info about a profile from the passed user's profile list."""
		if not member:
			msg = 'Usage: `{}profileinfo [member] [profile name]`'.format(ctx.prefix)
			return await ctx.send(msg)
		item = self._get_profile(ctx,member)
		if item is None:
			return await ctx.send("Sorry, I couldn't find that user/profile.")
		member,item = item
		# We have a profile
		current_time = int(time.time())
		msg = '**{}:**\n'.format(item['Name'])
		msg += "Created: {} ago\n".format(ReadableTime.getReadableTimeBetween(item.get("Created",None), current_time, True)) if item.get("Created",None) else "Created: `UNKNOWN`\n"
		if item.get("Updated",None):
			msg += "Updated: {} ago\n".format(ReadableTime.getReadableTimeBetween(item["Updated"], current_time, True))
		return await ctx.send(Utils.suppressed(ctx,msg))

	@commands.command()
	async def profiles(self, ctx, *, member = None):
		"""List all profiles in the passed user's profile list."""
		await self._list_profiles(ctx,member)
		
	@commands.command()
	async def rawprofiles(self, ctx, *, member = None):
		"""List all profiles' raw markdown in the passed user's profile list."""
		await self._list_profiles(ctx,member,raw=True)

	@commands.command()
	async def clearprofiles(self, ctx):
		"""Removes all of your profiles."""
		itemList = self.settings.getUserStat(ctx.author, ctx.guild, "Profiles", [])
		self.settings.setUserStat(ctx.author, ctx.guild, "Profiles", [])
		return await ctx.send("{:,} profile{} removed!".format(
			len(itemList),
			"" if len(itemList) == 1 else "s"
		))

	@commands.command()
	async def saveprofiles(self, ctx):
		"""Saves your profiles to a json file and uploads."""
		itemList = self.settings.getUserStat(ctx.author, ctx.guild, "Profiles", [])
		if not itemList:
			msg = '*{}* has no profiles set!  They can add some with the `{}addprofile "[profile name]" [link]` command!'.format(DisplayName.name(ctx.author), ctx.prefix)
			return await ctx.send(msg)
		message = await ctx.send("Saving profiles and uploading...")
		temp = tempfile.mkdtemp()
		temp_json = os.path.join(temp,"Profiles.json")
		try:
			json.dump(itemList,open(temp_json,"w"),indent=2)
			await ctx.send(file=discord.File(temp_json))
		except:
			return await message.edit(content="Could not save or upload profiles :(")
		finally:
			shutil.rmtree(temp,ignore_errors=True)
		await message.edit(content="Uploaded Profiles.json! ({:,})".format(len(itemList)))
	
	@commands.command()
	async def loadprofiles(self, ctx, url = None):
		"""Loads the passed json attachment or URL into your profiles."""
		if url is None and len(ctx.message.attachments) == 0:
			return await ctx.send("Usage: `{}loadprofiles [url or attachment]`".format(ctx.prefix))
		if url is None:
			url = ctx.message.attachments[0].url
		message = await ctx.send("Downloading and parsing...")
		try:
			items = await DL.async_json(url.strip("<>"))
		except:
			return await message.edit(content="Could not serialize data :(")
		if not items:
			return await message.edit(content="Json data is empty :(")
		if not isinstance(items,list):
			return await message.edit(content="Malformed json data :(")
		if not all(("Name" in x and "URL" in x for x in items)):
			return await message.edit(content="Invalid profile data :(")
		itemList = self.settings.getUserStat(ctx.author, ctx.guild, "Profiles", [])
		if not isinstance(itemList,list): # Malformed - let's start it anew
			itemList = []
		# At this point - we should have a valid json file with our data - let's add it.
		currentTime = int(time.time())
		added = updated = 0
		for i in items:
			item = next((x for x in itemList if x["Name"].lower() == i["Name"].lower()),None)
			if item:
				updated += 1
				item["URL"]     = i["URL"]
				item['Updated'] = currentTime
			else:
				added += 1
				itemList.append({
					"Name":    i["Name"],
					"URL":     i["URL"],
					"Created": currentTime
				})
		self.settings.setUserStat(ctx.author, ctx.guild, "Profiles", itemList)
		if added and updated:
			msg = "Added {:,} new and updated {:,} existing profile{}!".format(
				added,updated,"" if updated == 1 else "s"
			)
		elif added:
			msg = "Added {:,} new profile{}!".format(added,"" if added == 1 else "s")
		else:
			msg = "Updated {:,} existing profile{}!".format(updated,"" if updated == 1 else "s")
		await message.edit(content=msg)