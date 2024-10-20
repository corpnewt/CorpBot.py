import asyncio, discord, time
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, Settings, ReadableTime, DisplayName, Message, Nullify, PickList

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
		# Remove tabs, newlines, and carriage returns and strip leading/trailing spaces from the name
		name = None if name is None else name.replace("\n"," ").replace("\r","").replace("\t"," ").strip()
		if name is None or link is None:
			msg = 'Usage: `{}addprofile "[profile name]" [link]`'.format(ctx.prefix)
			return await ctx.send(msg)
		itemList = self.settings.getUserStat(ctx.author, ctx.guild, "Profiles")
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

		itemList = self.settings.getUserStat(ctx.author, ctx.guild, "Profiles")
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
				# We got a member - let's check for a profile
				itemList = self.settings.getUserStat(mem_from_name, ctx.guild, "Profiles", [])
				item = next((x for x in itemList if x["Name"].lower() == profile_str.lower()),None)
				if item: return (mem_from_name,item)
		# Check if there is no member specified
		itemList = self.settings.getUserStat(ctx.author, ctx.guild, "Profiles", [])
		item = next((x for x in itemList if x["Name"].lower() == name.lower()),None)
		if item: return (ctx.author,item)
		return None

	async def _get_profile_reply(self,ctx,name=None,raw=False):
		if not name:
			msg = "Usage: `{}{}profile [member] [profile name]`".format(ctx.prefix, "raw" if raw else "")
			return await ctx.send(msg)
		item = self._get_profile(ctx,name)
		if item is None:
			return await ctx.send("Sorry, I couldn't find that user/profile.")
		member,item = item
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
		itemList = self.settings.getUserStat(member, ctx.guild, "Profiles")
		if not itemList or itemList == []:
			msg = '*{}* has no profiles set!  They can add some with the `{}addprofile "[profile name]" [link]` command!'.format(DisplayName.name(ctx.author), ctx.prefix)
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
