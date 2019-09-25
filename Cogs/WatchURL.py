import asyncio, discord, re
from   discord.ext import commands
from   Cogs import PickList, Message

def setup(bot):
	# Add the bot
	settings = bot.get_cog("Settings")
	bot.add_cog(WatchURL(bot,settings))
	
class WatchURL(commands.Cog):
    
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		# Regex for extracting urls from strings
		self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")
		self.limit = 200 # Set to 0 or less for unlimited

	def is_bot_admin(self, ctx):
		# Checks if the passed user is bot admin
		return ctx.author.permissions_in(ctx.channel).administrator or next((role for role in ctx.author.roles for check in self.settings.getServerStat(ctx.guild, "AdminArray", []) if str(role.id) == str(check["ID"])),False)

	@commands.Cog.listener()
	async def on_message(self, message):
		if not message.guild:
			return
		if not self.settings.getServerStat(message.guild,"URLWatchListAllowBots",False) and message.author.bot:
			return # We're not listening for bots
		url_list = self.settings.getServerStat(message.guild,"URLWatchList",[])
		if not url_list:
			return
		# Check if we have a link
		matches = re.finditer(self.regex, message.content)
		valid_matches = list(set([match.group(0) for match in matches for x in url_list if x.lower() in match.group(0).lower()]))
		if not len(valid_matches):
			return
		matched = self.settings.getServerStat(message.guild,"URLWatchListMatches",[])
		for match in valid_matches:
			matched.insert(0,{"from":message.author.id,"url":match,"link":"https://discordapp.com/channels/{}/{}/{}".format(message.guild.id, message.channel.id, message.id)})
		# Ensure we're not over the limit if one is set
		if self.limit > 0:
			while len(matched) > self.limit:
				matched.pop()
		self.settings.setServerStat(message.guild,"URLWatchListMatches",matched)

	@commands.command()
	async def clearwatchedurls(self, ctx):
		"""Clears all URLs to watch for (bot-admin only)."""
		if not self.is_bot_admin(ctx):
			return await ctx.send("You do not have sufficient privileges to access this command.")
		self.settings.setServerStat(ctx.guild,"URLWatchList",[])
		await Message.EmbedText(description="No longer watching for any URLs!",title="Watched URLs",color=ctx.author).send(ctx)

	@commands.command()
	async def clearwatchurlmatches(self, ctx):
		"""Clears all URL watch list matches (bot-admin only)."""
		if not self.is_bot_admin(ctx):
			return await ctx.send("You do not have sufficient privileges to access this command.")
		self.settings.setServerStat(ctx.guild,"URLWatchListMatches",[])
		await Message.EmbedText(description="All matches cleared!",title="Watched URLs",color=ctx.author).send(ctx)

	@commands.command()
	async def listwatchurls(self, ctx):
		"""Lists the URLs to watch for in passed messages."""
		url_list = self.settings.getServerStat(ctx.guild,"URLWatchList",[])
		msg = "\n".join(url_list) if len(url_list) else "There are no URLs being watched for."
		await Message.EmbedText(description=msg,title="Watched URLs",color=ctx.author).send(ctx)
	
	@commands.command()
	async def addwatchurl(self, ctx, url = None):
		"""Adds a new URL to watch for (bot-admin only)."""
		if not self.is_bot_admin(ctx):
			return await ctx.send("You do not have sufficient privileges to access this command.")
		url_list = self.settings.getServerStat(ctx.guild,"URLWatchList",[])
		if url.lower() in url_list:
			return await Message.EmbedText(description="That URL is already being watched!",title="Watched URLs Error",color=ctx.author).send(ctx)
		url_list.append(url.lower())
		self.settings.setServerStat(ctx.guild,"URLWatchList",url_list)
		await Message.EmbedText(description="{} is now being watched!".format(url.lower()),title="Watched URLs",color=ctx.author).send(ctx)
		
	@commands.command()
	async def delwatchurl(self, ctx, url = None):
		"""Removes a URL from the watch list (bot-admin only)."""
		if not self.is_bot_admin(ctx):
			return await ctx.send("You do not have sufficient privileges to access this command.")
		url_list = self.settings.getServerStat(ctx.guild,"URLWatchList",[])
		if not url.lower() in url_list:
			return await Message.EmbedText(description="That URL is not being watched!",title="Watched URLs Error",color=ctx.author).send(ctx)
		url_list.remove(url.lower())
		self.settings.setServerStat(ctx.guild,"URLWatchList",url_list)
		await Message.EmbedText(description="{} is no longer being watched!".format(url.lower()),title="Watched URLs",color=ctx.author).send(ctx)

	@commands.command()
	async def watchboturls(self, ctx, *, yes_no = None):
		"""Sets whether we watch for URLs from other bots (bot-admin only - disabled by default)."""
		if not self.is_bot_admin(ctx):
			return await ctx.send("You do not have sufficient privileges to access this command.")
		setting_name = "Watch bot URLs"
		setting_val  = "URLWatchListAllowBots"
		current = self.settings.getServerStat(ctx.guild, setting_val, False)
		if yes_no == None:
			msg = "{} currently *{}.*".format(setting_name,"enabled" if current else "disabled")
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			msg = "{} {} *enabled*.".format(setting_name,"remains" if current else "is now")
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			msg = "{} {} *disabled*.".format(setting_name,"remains" if not current else "is now")
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)
	
	@commands.command()
	async def lasturls(self, ctx):
		"""Shows up to the last 200 URLs sent that matched the URL watch lists in order of most recent to least."""
		url_matches = self.settings.getServerStat(ctx.guild,"URLWatchListMatches",[])
		if not url_matches:
			return await Message.EmbedText(description="I haven't seen any matches yet.",title="Watched URL Matches",color=ctx.author).send(ctx)
		# Let's create our list now
		entries = [{"name":"{}. {}".format(y+1,x["url"]),"value":"└─ From <@!{}> - [Link]({})".format(x["from"],x["link"])} for y,x in enumerate(url_matches)]
		await PickList.PagePicker(title="Watched URL Matches",list=entries,ctx=ctx).pick()
