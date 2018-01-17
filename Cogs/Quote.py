import asyncio
import discord
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Message

def setup(bot):
	# Add the bot
	settings = bot.get_cog("Settings")
	bot.add_cog(Quote(bot, settings))

class Quote:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	def _is_admin(self, member, channel):
		# Check for admin/bot-admin
			isAdmin = member.permissions_in(channel).administrator
			if not isAdmin:
				checkAdmin = self.settings.getServerStat(member.guild, "AdminArray")
				for role in member.roles:
					for aRole in checkAdmin:
						# Get the role that corresponds to the id
						if str(aRole['ID']) == str(role.id):
							isAdmin = True
			return isAdmin

	@asyncio.coroutine
	async def on_reaction_add(self, reaction, member):
		# Catch reactions and see if they match our list
		if not type(member) is discord.Member:
			# Not in a server
			return

		r =         self.settings.getServerStat(member.guild, "QuoteReaction")
		r_channel = self.settings.getServerStat(member.guild, "QuoteChannel")
		r_admin   = self.settings.getServerStat(member.guild, "QuoteAdminOnly")

		if r == None or r_channel == None:
			# Not setup
			return

		# Check reactions
		if not str(reaction.emoji) == r:
			# Our reaction isn't in there
			return

		em = None
		for reac in reaction.message.reactions:
			if str(reac) == str(r):
				em = reac

		if not em:
			# Broken for no reason?
			return

		if em.count > 1:
			# Our reaction is already here
			if not r_admin:
				# We're not worried about admin stuffs
				# and someone already quoted
				return
			# Check for admin/bot-admin
			if not self._is_admin(member, reaction.message.channel):
				# We ARE worried about admin - and we're not admin... skip
				return
			# Iterate through those that reacted and see if any are admin
			r_users = await reaction.users().flatten()
			for r_user in r_users:
				if r_user == member:
					continue
				if self._is_admin(r_user, reaction.message.channel):
					# An admin already quoted - skip
					return
		else:
			# This is the first reaction
			# Check for admin/bot-admin
			if r_admin and not self._is_admin(member, reaction.message.channel):
				return

		r_channel = member.guild.get_channel(int(r_channel))
		if r_channel == None:
			# Not a valid channel
			return

		if not len(reaction.message.content) and not len(reaction.message.attachments):
			# Only quote actual text or attachments - no embeds
			return
		
		# Initialize our message
		msg = reaction.message.content if len(reaction.message.content) else ""
		
		if len(reaction.message.attachments):
			# We have some attachments to work through
			attach_text = ""
			for a in reaction.message.attachments:
				# Add each attachment by name as a link to its own url
				attach_text += "[{}]({}), ".format(a.filename, a.url)
			# Remove the last ", "
			attach_text = attach_text[:-2]
			msg += "\n\n" + attach_text

		# Build an embed!
		e = {
			"author" : reaction.message.author,
			"pm_after" : -1, # Don't pm quotes
			"description" : msg,
			"image" : reaction.message.author.avatar_url,
			"color" : reaction.message.author,
			"footer" : "Quoted by {}#{} | #{} | {} UTC".format(member.name, member.discriminator, reaction.message.channel.name, reaction.message.created_at.strftime("%I:%M %p"))
		}
		await Message.EmbedText(**e).send(r_channel)


	@commands.command(pass_context=True)
	async def setquotechannel(self, ctx, channel = None):
		"""Sets the channel for quoted messages or disables it if no channel sent (admin only)."""
		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return
		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "QuoteChannel", None)
			msg = 'Quote channel *disabled*.'
			await ctx.channel.send(msg)
			return
		channel = DisplayName.channelForName(channel, ctx.guild, "text")
		if channel == None:
			await ctx.send("I couldn't find that channel :(")
			return
		self.settings.setServerStat(ctx.message.guild, "QuoteChannel", channel.id)
		
		msg = 'Quote channel set to {}'.format(channel.mention)
		await ctx.channel.send(msg)
	

	@commands.command(pass_context=True)
	async def quotechannel(self, ctx):
		"""Prints the current quote channel."""
		qChan = self.settings.getServerStat(ctx.guild, "QuoteChannel")
		if not qChan:
			await ctx.send("Quoting is currently *disabled*.")
			return
		channel = DisplayName.channelForName(str(qChan), ctx.guild, "text")
		if channel:
			await ctx.send("The current quote channel is {}".format(channel.mention))
			return
		await ctx.send("Channel id: *{}* no longer exists on this server.  Consider updating this setting!".format(qChan))


	@commands.command(pass_context=True)
	async def clearquotereaction(self, ctx):
		"""Clears the trigger reaction for quoting messages (admin only)."""
		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		self.settings.setServerStat(ctx.message.guild, "QuoteReaction", None)
		await ctx.send("Quote reaction *cleared*.")


	@commands.command(pass_context=True)
	async def setquotereaction(self, ctx):
		"""Sets the trigger reaction for quoting messages (bot-admin only)."""
		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		message = await ctx.send("Please react to this message with the desired quote reaction.")
		# Backup then clear - so we don't trigger quoting during this
		backup_reaction = self.settings.getServerStat(ctx.message.guild, "QuoteReaction")
		self.settings.setServerStat(ctx.message.guild, "QuoteReaction", None)
		# Now we would wait...
		def check(reaction, user):
			return reaction.message.id == message.id and user == ctx.author
		try:
			reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
		except:
			# Didn't get a reaction
			self.settings.setServerStat(ctx.message.guild, "QuoteReaction", backup_reaction)
			await message.edit(content="Looks like we ran out of time - run `{}setquotereaction` to try again.".format(ctx.prefix))
			return

		# Got it!
		self.settings.setServerStat(ctx.message.guild, "QuoteReaction", str(reaction.emoji))

		await message.edit(content="Quote reaction set to {}".format(str(reaction.emoji)))


	@commands.command(pass_context=True)
	async def getquotereaction(self, ctx):
		"""Displays the quote reaction if there is one."""
		r = self.settings.getServerStat(ctx.message.guild, "QuoteReaction")

		if r:
			await ctx.send("Current quote reaction is {}".format(r))
			return
		else:
			await ctx.send("No quote reaction set.")


	@commands.command(pass_context=True)
	async def quoteadminonly(self, ctx, *, yes_no = None):
		"""Sets whether only admins/bot-admins can quote or not (bot-admin only)."""

		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		setting_name = "Admin-only quotes"
		setting_val  = "QuoteAdminOnly"

		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)
