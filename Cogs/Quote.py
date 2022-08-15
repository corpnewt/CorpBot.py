from datetime import datetime, timezone
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
	async def on_raw_reaction_add(self, payload):
		# Make sure we're in a guild, then gather member info
		if not payload.guild_id: return
		guild = self.bot.get_guild(payload.guild_id)
		if not guild: return
		member = guild.get_member(payload.user_id)
		if not member or member.bot: return
		# Make sure we're in the right channel
		r_channel = self.settings.getServerStat(member.guild, "QuoteChannel")
		if not r_channel: return # Not setup, or wrong channel
		# Gather the reaction - and make sure it's the same
		r = self.settings.getServerStat(member.guild, "QuoteReaction")
		if not r or str(payload.emoji) != r: return # Not setup, or wrong reaction
		r_admin = self.settings.getServerStat(member.guild, "QuoteAdminOnly")
		r_qv = 1 if r_admin else self.settings.getServerStat(member.guild,"QuoteVotes",1)
		# Get the original message
		channel = guild.get_channel(payload.channel_id)
		try: message = await channel.fetch_message(payload.message_id)
		except: return # Failed to get the message
		reaction = next((x for x in message.reactions if str(x) == str(r)),None)
		if not reaction: return # Broken for no reason?
		# Gather the context and evaluate
		ctx = await self.bot.get_context(message)
		# Let's look at who has already reacted aside from us - and if any are admin.
		r_users = [x for x in await reaction.users().flatten() if x!=member]
		if any((Utils.is_bot_admin(ctx,member=x) for x in r_users)):
			return # Already quoted - as at least one user was bot-admin
		bot_admin = Utils.is_bot_admin(ctx,member=member)
		# Check bot-admin stuffs first
		if r_admin and not bot_admin:
			return # We're not, and we need to be
		# Check if we're bot admin - but there were already enough users to quote
		# or if the reaction count isn't exact.
		if (bot_admin and len(r_users)>=r_qv) or (not bot_admin and reaction.count!=r_qv): return
		# If we got here - we've passed.
		r_channel = member.guild.get_channel(int(r_channel))
		if r_channel is None:
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
				if image is None and a.filename.lower().endswith((".jpg",".jpeg",".png",".gif")):
					# We got the first image in the attachment list - set it
					image = a.url
			# Remove the last ", "
			attach_text = attach_text[:-2]
			msg += "\n\n" + attach_text
		if len(reaction.message.embeds) and image is None:
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
			"pm_after_fields" : -1, # Don't pm quotes
			"description" : msg + "\n\nSent by {} in {} | {} | {}".format(
				reaction.message.author.mention,
				reaction.message.channel.mention,
				"[Link](https://discord.com/channels/{}/{}/{})".format(reaction.message.guild.id, reaction.message.channel.id, reaction.message.id),
				"<t:{}>".format(int(datetime.timestamp(reaction.message.created_at.replace(tzinfo=timezone.utc)))) #reaction.message.created_at.strftime("%I:%M %p")
			),
			"color" : reaction.message.author,
			"footer" : "Quoted by {}#{} ({})".format(member.name, member.discriminator, member.id)
		}
		await Message.EmbedText(**e).send(r_channel)


	@commands.command(aliases=["quotev","qv"])
	async def quotevote(self, ctx, quote_votes = None):
		"""Gets or sets the number of votes/reactions needed for non admin/bot-admin users to quote a message (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		if quote_votes is None: # We're querying the current value
			qv = self.settings.getServerStat(ctx.guild,"QuoteVotes",1)
			if not isinstance(qv,int):
				qv = 1
				self.settings.setServerStat(ctx.guild,"QuoteVotes",1)
			return await ctx.send("Quote votes currently set to {:,}.".format(qv))
		# We're setting a value - make sure it's an int, and at least 1
		try:
			qv = int(quote_votes)
			assert qv > 0
		except:
			return await ctx.send("Quote votes must be an integer of at least 1.")
		# Set the value.
		self.settings.setServerStat(ctx.guild,"QuoteVotes",qv)
		await ctx.send("Quote votes set to {:,}.".format(qv))

	@commands.command(aliases=["sqc","setquotec","setqc"])
	async def setquotechannel(self, ctx, channel = None):
		"""Sets the channel for quoted messages or disables it if no channel sent (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		if channel is None:
			self.settings.setServerStat(ctx.guild, "QuoteChannel", None)
			msg = 'Quote channel *disabled*.'
			return await ctx.send(msg)
		channel = DisplayName.channelForName(channel, ctx.guild, "text")
		if channel is None:
			return await ctx.send("I couldn't find that channel :(")
		self.settings.setServerStat(ctx.guild, "QuoteChannel", channel.id)
		
		msg = 'Quote channel set to {}'.format(channel.mention)
		await ctx.send(msg)
	

	@commands.command(aliases=["quotechannel","gqc","qc","getquotec"])
	async def getquotechannel(self, ctx):
		"""Prints the current quote channel."""
		qChan = self.settings.getServerStat(ctx.guild, "QuoteChannel")
		if not qChan:
			return await ctx.send("Quoting is currently *disabled*.")
		channel = DisplayName.channelForName(str(qChan), ctx.guild, "text")
		if channel:
			return await ctx.send("The current quote channel is {}".format(channel.mention))
		await ctx.send("Channel id: *{}* no longer exists on this server.  Consider updating this setting!".format(qChan))


	@commands.command(aliases=["clearqr","clearquoter","cqr"])
	async def clearquotereaction(self, ctx):
		"""Clears the trigger reaction for quoting messages (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		self.settings.setServerStat(ctx.guild, "QuoteReaction", None)
		await ctx.send("Quote reaction *cleared*.")


	@commands.command(aliases=["sqr","setquoter","setqr"])
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


	@commands.command(aliases=["gqr","getquoter","getqr"])
	async def getquotereaction(self, ctx):
		"""Displays the quote reaction if there is one."""
		r = self.settings.getServerStat(ctx.guild, "QuoteReaction")
		await ctx.send("No quote reaction set." if not r else "Current quote reaction is {}".format(r))


	@commands.command(aliases=["qao","quoteao","quoteadmino"])
	async def quoteadminonly(self, ctx, *, yes_no = None):
		"""Sets whether only admins/bot-admins can quote or not (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Admin-only quotes","QuoteAdminOnly",yes_no))
