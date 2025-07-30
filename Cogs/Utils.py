import asyncio, discord, re
from   discord.ext import commands
from   Cogs import Nullify
try:
	from discord.enums import MessageReferenceType
except ImportError:
	MessageReferenceType = None

# bot = None
# url_regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")

def setup(bot):
	# This module isn't actually a cog - but it is a place
	# we can call "a trash fire"
	bot.add_cog(Utils(bot))

class Utils(commands.Cog):
	def __init__(self,bot):
		self.bot = bot
		self.url_regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")

	def suppressed(self,ctx,msg,force=False):
		# Checks if the passed server is suppressing user/role mentions and adjust the msg accordingly
		guild = ctx if isinstance(ctx,discord.Guild) else ctx.guild if hasattr(ctx,"guild") else None
		if not guild: return msg
		settings = self.bot.get_cog("Settings")
		if not settings: return msg
		return Nullify.clean(msg, ctx=guild) if (force or settings.getServerStat(guild, "SuppressMentions", True)) else msg

	def is_owner(self,ctx,member=None):
		# Checks if the user in the passed context is an owner
		settings = self.bot.get_cog("Settings")
		if not settings: return False
		member = ctx.author if not member else member
		return settings.isOwner(member)

	def is_admin(self,ctx,member=None,guild=None):
		# Checks if the user in the passed context is admin
		member = member or ctx.author
		channel = next((c for c in guild.channels),None) if guild else ctx.channel
		if not channel: return False
		if hasattr(channel,"permissions_for"):
			return channel.permissions_for(member).administrator
		return member.permissions_in(channel).administrator

	def is_bot_admin_only(self,ctx,member=None,guild=None):
		# Checks only if we're bot admin
		settings = self.bot.get_cog("Settings")
		if not settings: return False
		member = member or ctx.author
		guild  = guild  or ctx.guild
		if not member or not guild: return False
		if not hasattr(member,"roles"): return False # No roles to iterate - can't be bot admin
		return any(role for role in member.roles for check in settings.getServerStat(guild, "AdminArray", []) if str(role.id) == str(check["ID"]))

	def is_bot_admin(self,ctx,member=None,guild=None):
		# Checks if the user in the passed context is admin or bot admin
		return self.is_admin(ctx,member,guild=guild) or self.is_bot_admin_only(ctx,member,guild=guild)

	async def is_owner_reply(self,ctx,member=None,not_claimed="I have not been claimed, *yet*.",not_owner="You are not the *true* owner of me.  Only the rightful owner can use this command."):
		# Auto-replies if the user isn't an owner
		are_we = self.is_owner(ctx,member)
		if are_we is None: await ctx.send(not_claimed)
		elif are_we == False: await ctx.send(not_owner)
		return are_we

	async def is_admin_reply(self,ctx,member=None,message="You do not have sufficient privileges to access this command.",message_when=False):
		# Auto-replies if the user doesn't have admin privs
		are_we = self.is_admin(ctx,member)
		if are_we == message_when: await ctx.send(message)
		return are_we

	async def is_bot_admin_only_reply(self,ctx,member=None,message="You do not have sufficient privileges to access this command.",message_when=False):
		# Auto-replies if the user doesn't have admin or bot admin privs
		are_we = self.is_bot_admin_only(ctx,member)
		if are_we == message_when: await ctx.send(message)
		return are_we

	async def is_bot_admin_reply(self,ctx,member=None,message="You do not have sufficient privileges to access this command.",message_when=False):
		# Auto-replies if the user doesn't have admin or bot admin privs
		are_we = self.is_bot_admin(ctx,member)
		if are_we == message_when: await ctx.send(message)
		return are_we

	def yes_no_setting(self,ctx,display_name,setting_name,yes_no=None,default=None,is_global=False):
		# Get or set a true/false value and return the resulting message
		guild = ctx if isinstance(ctx,discord.Guild) else ctx.guild if isinstance(ctx,discord.ext.commands.Context) else None
		if not guild and not is_global: return "I can't get a guild from here :("
		settings = self.bot.get_cog("Settings")
		if not settings: return "Something is wrong with my settings module :("
		current = settings.getGlobalStat(setting_name, default) if is_global else settings.getServerStat(guild, setting_name, default)
		if yes_no is None:
			# Output what we have
			return "{} currently *{}*.".format(display_name,"enabled" if current else "disabled")
		elif yes_no.lower() in ( "1", "yes", "on", "true", "enabled", "enable" ):
			yes_no = True
			msg = "{} {} *enabled*.".format(display_name,"remains" if current else "is now")
		elif yes_no.lower() in ( "0", "no", "off", "false", "disabled", "disable" ):
			yes_no = False
			msg = "{} {} *disabled*.".format(display_name,"is now" if current else "remains")
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == current:
			if is_global: settings.setGlobalStat(setting_name, yes_no)
			else: settings.setServerStat(ctx.guild, setting_name, yes_no)
		return msg

	def get_urls(self,message):
		# Returns a list of valid urls from a passed message/context/string
		message = message.content if isinstance(message,discord.Message) else message.message.content if isinstance(message,discord.ext.commands.Context) else str(message)
		return [x.group(0) for x in re.finditer(self.url_regex,message)]

	def truncate_string(self,value=None,limit=128,suffix="...",replace_newlines=True,complete_codeblocks=True):
		if not isinstance(value,str) : return value
		# Truncates the string to the max chars passed
		if replace_newlines:
			new_val = [line+"\n" if complete_codeblocks and line.startswith("```") and line[3:].isalpha() else line for line in value.split("\n")]
			value = " ".join(new_val)
		if len(value)>limit: # We need to truncate
			# Start with a truncated value
			value = value[:limit]
			# Check if we need to complete an orphaned codeblock
			if complete_codeblocks and value.count("```") % 2:
				suffix += "```"
			if len(value) <= len(suffix):
				# Skip the suffix - too short to truncate
				suffix = ""
			value = value[:-len(suffix)]+suffix
		return value

	def get_avatar(self,member,server=True):
		# Check for the old syntax
		if hasattr(member,"avatar_url"):
			return next((x for x in (member.avatar_url,member.default_avatar_url) if x),None)
		# Check for new - and leverage the display_avatar first
		if server:
			return member.display_avatar.url
		return next((x.url for x in (member.avatar,member.display_avatar) if x),None)

	def get_default_avatar(self):
		# Check for the old syntax
		if hasattr(self.bot.user,"default_avatar_url"):
			return self.bot.user.default_avatar_url
		# Use the new
		return self.bot.user.default_avatar.url

	def get_guild_icon(self,guild):
		# Returns the icon for the passed guild - or the default avatar if none exists
		if hasattr(guild,"icon_url") and guild.icon_url:
			return guild.icon_url
		elif getattr(guild,"icon",None):
			return guild.icon.url
		return self.get_default_avatar()

	async def get_message_content(self,message,ctx=None,strip_prefix=True):
		# Returns the adjusted content of a message - stripping any command
		# call prefix if needed
		if not isinstance(message,discord.Message): return ""
		if not ctx:
			ctx = await self.bot.get_context(message)
		if not ctx or not ctx.command or not strip_prefix:
			return message.content
		# We have a command - check names and aliases
		for check in [ctx.command.name]+list(ctx.command.aliases):
			check_str = ctx.prefix+check
			if message.content.startswith(check_str):
				return message.content[len(check_str):].strip()
		# If we got here, nothing was found - return the original content
		return message.content

	async def get_replied_to(self,message,ctx=None,current_depth=1,max_depth=5):
		# Returns the replied-to message first by checking the cache, then
		# by fetching it.
		if not isinstance(message,discord.Message): return None
		if current_depth >= max_depth: return message
		if not message.reference: return None
		replied_to = self.bot.get_message(message.reference.message_id)
		if not replied_to: # Not in the cache, try to retrieve it
			if not ctx: # First retrieve the context if needed
				ctx = await self.bot.get_context(message)
			replied_to = await ctx.channel.fetch_message(message.reference.message_id)
		# Check for forwarding here - and recurse
		if getattr(getattr(replied_to,"reference",None),"type","") == getattr(MessageReferenceType,"forward",None):
			# Forwarded - return the result of another check
			return await self.get_replied_to(replied_to,current_depth=current_depth+1,max_depth=max_depth)
		return replied_to

	async def get_message_from_url(self,message_url,ctx=None):
		# Attempts to resolve the passed URL to the message object using the passed
		# context as needed.
		try:
			guild_id,channel_id,message_id = message_url.split("/")[-3:]
			message = self.bot.get_message(int(message_id))
			if message: return message
			# Resolve the originating channel
			if guild_id == "@me":
				if not ctx: return None # Need context to resolve to the author
				channel = ctx.author
			else:
				channel = self.bot.get_channel(int(channel_id))
			message = await channel.fetch_message(int(message_id))
			assert message # Force a failure if the message wasn't found
			return message
		except:
			pass
		# Nothing resolved - bail
		return None
