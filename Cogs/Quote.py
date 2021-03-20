import asyncio, discord
from   discord.ext import commands
from   Cogs import Utils, DisplayName, Message

def setup(bot):
	# Add the bot
	settings = bot.get_cog("Settings")
	bot.add_cog(Quote(bot, settings))

class Quote(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	@commands.Cog.listener()
	async def on_reaction_add(self, reaction, member):
		# Catch reactions and see if they match our list
		if not type(member) is discord.Member:
			# Not in a server
			return

		# Check if the reaction is added by the bot
		if member.id == self.bot.user.id:
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
		ctx = await self.bot.get_context(reaction.message)
		if em.count > 1:
			# Our reaction is already here
			if not r_admin:
				# We're not worried about admin stuffs
				# and someone already quoted
				return
			# Check for admin/bot-admin
			if not Utils.is_bot_admin(ctx,member=member):
				# We ARE worried about admin - and we're not admin... skip
				return
			# Iterate through those that reacted and see if any are admin
			r_users = await reaction.users().flatten()
			for r_user in r_users:
				if r_user == member:
					continue
				if Utils.is_bot_admin(ctx,member=r_user):
					# An admin already quoted - skip
					return
		else:
			# This is the first reaction
			# Check for admin/bot-admin
			if r_admin and not Utils.is_bot_admin(ctx,member=member):
				return

		r_channel = member.guild.get_channel(int(r_channel))
		if r_channel == None:
			# Not a valid channel
			return

		if not len(reaction.message.content) and not len(reaction.message.attachments):
			# Only quote actual text or attachments - no embeds
			return
		
		# Initialize our message and image field
		msg = reaction.message.content if len(reaction.message.content) else ""
		image = None
		if len(reaction.message.attachments):
			# We have some attachments to work through
			attach_text = ""
			for a in reaction.message.attachments:
				# Add each attachment by name as a link to its own url
				attach_text += "[{}]({}), ".format(a.filename, a.url)
				if image == None and a.filename.lower().endswith((".jpg",".jpeg",".png",".gif")):
					# We got the first image in the attachment list - set it
					image = a.url
			# Remove the last ", "
			attach_text = attach_text[:-2]
			msg += "\n\n" + attach_text
		if len(reaction.message.embeds) and image == None:
			# We have embeds to look at too, and we haven't set an image yet
			for e in reaction.message.embeds:
				d = e.to_dict()
				i = d.get("thumbnail",d.get("video",d.get("image",{}))).get("url",None)
				if not i: continue
				image = i
				break

		# Build an embed!
		e = {
			"author" : reaction.message.author,
			"image" : image,
			"pm_after" : -1, # Don't pm quotes
			"description" : msg + "\n\nSent by {} in {} | {} | {} UTC".format(
				reaction.message.author.mention,
				reaction.message.channel.mention,
				"[Link](https://discord.com/channels/{}/{}/{})".format(reaction.message.guild.id, reaction.message.channel.id, reaction.message.id),
				reaction.message.created_at.strftime("%I:%M %p")
			),
			"color" : reaction.message.author,
			"footer" : "Quoted by {}#{}".format(member.name, member.discriminator)
		}
		await Message.EmbedText(**e).send(r_channel)


	@commands.command(pass_context=True)
	async def setquotechannel(self, ctx, channel = None):
		"""Sets the channel for quoted messages or disables it if no channel sent (admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		if channel == None:
			self.settings.setServerStat(ctx.guild, "QuoteChannel", None)
			msg = 'Quote channel *disabled*.'
			return await ctx.send(msg)
		channel = DisplayName.channelForName(channel, ctx.guild, "text")
		if channel == None:
			return await ctx.send("I couldn't find that channel :(")
		self.settings.setServerStat(ctx.guild, "QuoteChannel", channel.id)
		
		msg = 'Quote channel set to {}'.format(channel.mention)
		await ctx.send(msg)
	

	@commands.command(pass_context=True)
	async def quotechannel(self, ctx):
		"""Prints the current quote channel."""
		qChan = self.settings.getServerStat(ctx.guild, "QuoteChannel")
		if not qChan:
			return await ctx.send("Quoting is currently *disabled*.")
		channel = DisplayName.channelForName(str(qChan), ctx.guild, "text")
		if channel:
			return await ctx.send("The current quote channel is {}".format(channel.mention))
		await ctx.send("Channel id: *{}* no longer exists on this server.  Consider updating this setting!".format(qChan))


	@commands.command(pass_context=True)
	async def clearquotereaction(self, ctx):
		"""Clears the trigger reaction for quoting messages (admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		self.settings.setServerStat(ctx.guild, "QuoteReaction", None)
		await ctx.send("Quote reaction *cleared*.")


	@commands.command(pass_context=True)
	async def setquotereaction(self, ctx):
		"""Sets the trigger reaction for quoting messages (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		message = await ctx.send("Please react to this message with the desired quote reaction.")
		# Backup then clear - so we don't trigger quoting during this
		backup_reaction = self.settings.getServerStat(ctx.guild, "QuoteReaction")
		self.settings.setServerStat(ctx.guild, "QuoteReaction", None)
		# Now we would wait...
		def check(reaction, user):
			return reaction.message.id == message.id and user == ctx.author
		try:
			reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
		except:
			# Didn't get a reaction
			self.settings.setServerStat(ctx.guild, "QuoteReaction", backup_reaction)
			return await message.edit(content="Looks like we ran out of time - run `{}setquotereaction` to try again.".format(ctx.prefix))

		# Got it!
		self.settings.setServerStat(ctx.guild, "QuoteReaction", str(reaction.emoji))

		await message.edit(content="Quote reaction set to {}".format(str(reaction.emoji)))


	@commands.command(pass_context=True)
	async def getquotereaction(self, ctx):
		"""Displays the quote reaction if there is one."""
		r = self.settings.getServerStat(ctx.guild, "QuoteReaction")
		await ctx.send("No quote reaction set." if not r else "Current quote reaction is {}".format(r))


	@commands.command(pass_context=True)
	async def quoteadminonly(self, ctx, *, yes_no = None):
		"""Sets whether only admins/bot-admins can quote or not (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Admin-only quotes","QuoteAdminOnly",yes_no))
