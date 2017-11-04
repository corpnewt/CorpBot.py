import asyncio
import discord
import time
import parsedatetime
from   datetime import datetime
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import ReadableTime
from   Cogs import Nullify
from   Cogs import Mute

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	mute     = bot.get_cog("Mute")
	bot.add_cog(VoteKick(bot, settings, mute))

class VoteKick:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, muter):
		self.bot = bot
		self.settings = settings
		self.check_time = 10
		self.muter = muter
		self.loop_list = []

	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@asyncio.coroutine
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		for task in self.loop_list:
			task.cancel()

	@asyncio.coroutine
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Set our check loop
		self.loop_list.append(self.bot.loop.create_task(self.checkVotes()))

	async def checkVotes(self):
		while not self.bot.is_closed():
			await asyncio.sleep(self.check_time)
			for guild in self.bot.guilds:
				expire_time  = self.settings.getServerStat(guild, "VotesResetTime")
				vote_mute    = self.settings.getServerStat(guild, "VotesToMute")
				vote_mention = self.settings.getServerStat(guild, "VotesToMention")
				if expire_time == 0:
					# Never expire
					continue
				vote_list = self.settings.getServerStat(guild, "VoteKickArray")
				vote_rem = []
				for kicks in vote_list:
					# Should be a dict like this:
					# { "ID" : 123456789, "Kicks" : [ { "ID" : 123456789, "Added" : 123456789 } ] }
					remove_list = []
					for kick in kicks["Kicks"]:
						if (kick["Added"] + expire_time) <= time.time():
							remove_list.append(kick)
					for rem in remove_list:
						kicks["Kicks"].remove(rem)
					if not len(kicks["Kicks"]):
						# We removed them all - add to remove list
						vote_rem.append(kicks)
					else:
						# We still have some - let's check our values
						if len(kicks["Kicks"]) < vote_mute:
							kicks["Muted"] = False
						if len(kicks["Kicks"]) < vote_mention:
							kicks["Mentioned"] = False
				for rem in vote_rem:
					vote_list.remove(rem)
				self.settings.setServerStat(guild, "VoteKickArray", vote_list)

	@commands.command(pass_context=True)
	async def vkinfo(self, ctx):
		"""Lists the vote-kick info."""

		mute_votes = self.settings.getServerStat(ctx.guild, "VotesToMute")
		ment_votes = self.settings.getServerStat(ctx.guild, "VotesToMention")
		mute_time  = self.settings.getServerStat(ctx.guild, "VotesMuteTime")
		ment_chan  = self.settings.getServerStat(ctx.guild, "VoteKickChannel")
		vote_ment  = self.settings.getServerStat(ctx.guild, "VoteKickMention")
		vote_rest  = self.settings.getServerStat(ctx.guild, "VotesResetTime")
		vote_list  = self.settings.getServerStat(ctx.guild, "VoteKickArray")
		vote_anon  = self.settings.getServerStat(ctx.guild, "VoteKickAnon")

		msg = "__**Current Vote-Kick Settings For {}:**__\n```\n".format(Nullify.clean(ctx.guild.name))

		msg += "   Votes To Mute: {}\n".format(mute_votes)
		msg += "       Muted For: {}\n".format(ReadableTime.getReadableTimeBetween(0, mute_time))
		msg += "Votes to Mention: {}\n".format(ment_votes)
		if vote_ment:
			role_check = DisplayName.roleForName(vote_ment, ctx.guild)
			if not role_check:
				user_check = DisplayName.memberForName(vote_ment, ctx.guild)
				if not user_check:
					msg += "         Mention: None\n"
				else:
					msg += "         Mention: {}\n".format(user_check)
			else:
				msg += "         Mention: {} (role)\n".format(role_check)
		else:
			msg += "         Mention: None\n"
				
		m_channel = self.bot.get_channel(ment_chan)
		if m_channel:
			msg += "      Mention in: #{}\n".format(m_channel.name)
		else:
			msg += "      Mention in: None\n"
		if vote_rest == 0:
			msg += "      Vote reset: Permanent\n"
		elif vote_rest == 1:
			msg += "      Vote reset: After 1 second\n"
		else:
			msg += "      Vote reset: After {}\n".format(ReadableTime.getReadableTimeBetween(0, vote_rest))
		votes = 0
		for user in vote_list:
			votes += len(user["Kicks"])
		msg += " Anonymous votes: {}\n".format(vote_anon)
		msg += "    Active votes: {}\n```".format(votes)

		# Check if mention and mute are disabled
		if (ment_votes == 0 or ment_chan == None or ment_chan == None) and (mute_votes == 0 or mute_time == 0):
			msg += "\nSystem **not** configured fully."

		await ctx.send(msg)



	@commands.command(pass_context=True)
	async def vkmention(self, ctx):
		"""Gets which user or role is mentioned when enough votes against a user are reached."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
		
		current_id = self.settings.getServerStat(ctx.guild, "VoteKickMention")
		if not current_id:
			await ctx.send("There is no user or role set to mention.")
			return
		current_role = DisplayName.roleForName(current_id, ctx.guild)
		if current_role:
			await ctx.send("The current role to mention is *{}*.".format(Nullify.clean(current_role.name)))
			return
		current_user = DisplayName.memberForName(current_id, ctx.guild)
		if current_user:
			await ctx.send("The current user to mention is *{}*.".format(Nullify.clean(DisplayName.name(current_user))))
			return
		await ctx.send("The current id ({}) does not match any users or roles - please consider updating this setting.".format(current_id))

	@commands.command(pass_context=True)
	async def setvkmention(self, ctx, *, user_or_role = None):
		"""Sets which user or role is mentioned when enough votes against a user are reached."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if user_or_role == None:
			self.settings.setServerStat(ctx.guild, "VoteKickMention", None)
			await ctx.send("Removed the vote kick mention!")
			return

		check_role = DisplayName.roleForName(user_or_role, ctx.guild)
		if check_role:
			self.settings.setServerStat(ctx.guild, "VoteKickMention", check_role.id)
			await ctx.send("Vote kick will now mention the *{}* role.".format(Nullify.clean(check_role.name)))
			return
		check_user = DisplayName.memberForName(user_or_role, ctx.guild)
		if check_user:
			self.settings.setServerStat(ctx.guild, "VoteKickMention", check_user.id)
			await ctx.send("Vote kick will now mention *{}.*".format(Nullify.clean(DisplayName.name(check_user))))
			return
		await ctx.send("I couldn't find *{}*...".format(Nullify.clean(user_or_role)))

	@commands.command(pass_context=True)
	async def vktomute(self, ctx, *, number_of_votes = None):
		"""Sets the number of votes before a user is muted.  Anything less than 1 will disable, and nothing will output the current setting."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if number_of_votes == None:
			# Output the current setting
			current = self.settings.getServerStat(ctx.guild, "VotesToMute")
			if current == 1:
				await ctx.send("A user needs 1 vote to be muted.")
			elif current < 1:
				await ctx.send("This system is currently disabled.")
			else:
				await ctx.send("A user needs {} votes to be muted.".format(current))
			return

		try:
			number_of_votes = int(number_of_votes)
		except Exception:
			await ctx.send("Number of votes must be an integer.")
			return
		if number_of_votes < 0:
			number_of_votes = 0
		
		if number_of_votes == 0:
			self.settings.setServerStat(ctx.guild, "VotesToMute", 0)
			await ctx.send("Number of votes to mute disabled.")
		else:
			self.settings.setServerStat(ctx.guild, "VotesToMute", number_of_votes)
			await ctx.send("Number of votes to mute set to {}.".format(number_of_votes))

	@commands.command(pass_context=True)
	async def vktomention(self, ctx, *, number_of_votes = None):
		"""Sets the number of votes before the selected role or user is mentioned.  Anything less than 1 will disable, and nothing will output the current setting.
		You will also want to make sure you have a role/user to mention - and a channel in which to mention them setup."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if number_of_votes == None:
			# Output the current setting
			current = self.settings.getServerStat(ctx.guild, "VotesToMention")
			if current == 1:
				await ctx.send("A user needs 1 vote for the mention to trigger.")
			elif current < 1:
				await ctx.send("This system is currently disabled.")
			else:
				await ctx.send("A user needs {} votes for the mention to trigger.".format(current))
			return

		try:
			number_of_votes = int(number_of_votes)
		except Exception:
			await ctx.send("Number of votes must be an integer.")
			return
		if number_of_votes < 0:
			number_of_votes = 0
		
		if number_of_votes == 0:
			self.settings.setServerStat(ctx.guild, "VotesToMention", 0)
			await ctx.send("Number of votes to mention disabled.")
		else:
			self.settings.setServerStat(ctx.guild, "VotesToMention", number_of_votes)
			await ctx.send("Number of votes to mention set to {}.".format(number_of_votes))

	@commands.command(pass_context=True)
	async def vkchannel(self, ctx):
		"""Gets which channel then mention posts to when enough votes against a user are reached."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
		
		current_id = self.settings.getServerStat(ctx.guild, "VoteKickChannel")
		if not current_id:
			await ctx.send("There is no channel set to post to.")
			return
		current_channel = self.bot.get_channel(current_id)
		if current_channel:
			await ctx.send("The current channel to post in is *{}*.".format(current_channel.mention))
			return
		await ctx.send("The current id ({}) does not match any channels - please consider updating this setting.".format(current_id))


	@commands.command(pass_context=True)
	async def setvkchannel(self, ctx, *, channel = None):
		"""Sets which channel then mention posts to when enough votes against a user are reached."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if channel == None:
			self.settings.setServerStat(ctx.guild, "VoteKickChannel", None)
			await ctx.send("Removed the vote kick channel.")
			return

		check_channel = DisplayName.channelForName(channel, ctx.guild, "text")
		if check_channel:
			self.settings.setServerStat(ctx.guild, "VoteKickChannel", check_channel.id)
			await ctx.send("Vote kick will now be mentioned in *{}.*".format(check_channel.mention))
			return
		await ctx.send("I couldn't find *{}*...".format(Nullify.clean(channel)))

	@commands.command(pass_context=True)
	async def vkmutetime(self, ctx, *, the_time = None):
		"""Sets the number of time a user is muted when the mute votes are reached - 0 or less will disable the system."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if the_time == None:
			# Output the current setting
			current = self.settings.getServerStat(ctx.guild, "VotesMuteTime")
			if current < 1:
				await ctx.send("This system is currently disabled.")
			else:
				await ctx.send("Mute time is currently set to {}.".format(ReadableTime.getReadableTimeBetween(0, current)))
			return

		seconds = None
		try:
			# Get current time - and end time
			currentTime = int(time.time())
			cal         = parsedatetime.Calendar()
			time_struct, parse_status = cal.parse(the_time)
			start       = datetime(*time_struct[:6])
			end         = time.mktime(start.timetuple())

			# Get the time from now to end time
			seconds = end-currentTime
		except Exception:
			pass
		
		if seconds == None:
			await ctx.send("Hmmm - I couldn't figure out what time frame you wanted...")
			return

		if seconds < 0:
			seconds = 0
		
		if seconds == 0:
			self.settings.setServerStat(ctx.guild, "VotesMuteTime", 0)
			await ctx.send("Mute time disabled.")
		else:
			self.settings.setServerStat(ctx.guild, "VotesMuteTime", seconds)
			await ctx.send("Mute time set to {}.".format(ReadableTime.getReadableTimeBetween(0, seconds)))

	@commands.command(pass_context=True)
	async def vkexpiretime(self, ctx, *, the_time = None):
		"""Sets the amount of time before a vote expires.  0 or less will make them permanent."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if the_time == None:
			# Output the current setting
			current = self.settings.getServerStat(ctx.guild, "VotesResetTime")
			if current < 1:
				await ctx.send("Votes never expire.")
			else:
				await ctx.send("Votes will expire after {}.".format(ReadableTime.getReadableTimeBetween(0, current)))
			return

		seconds = None
		try:
			# Get current time - and end time
			currentTime = int(time.time())
			cal         = parsedatetime.Calendar()
			time_struct, parse_status = cal.parse(the_time)
			start       = datetime(*time_struct[:6])
			end         = time.mktime(start.timetuple())

			# Get the time from now to end time
			seconds = end-currentTime
		except Exception:
			pass
		
		if seconds == None:
			await ctx.send("Hmmm - I couldn't figure out what time frame you wanted...")
			return

		if seconds < 0:
			seconds = 0
		
		if seconds == 0:
			self.settings.setServerStat(ctx.guild, "VotesResetTime", 0)
			await ctx.send("Votes will never expire.")
		else:
			self.settings.setServerStat(ctx.guild, "VotesResetTime", seconds)
			await ctx.send("Votes will expire after {}.".format(ReadableTime.getReadableTimeBetween(0, seconds)))

	@commands.command(pass_context=True)
	async def vkanon(self, ctx, *, yes_no = None):
		"""Sets whether vote messages are removed after voting (bot-admin only; always off by default)."""

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

		setting_name = "Vote kick anon"
		setting_val  = "VoteKickAnon"

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

	@commands.command(pass_context=True)
	async def vk(self, ctx, *, user = None):
		"""Places your vote to have the passed user kicked."""
		# Should be a dict like this:
		# { "ID" : 123456789, "Kicks" : [ { "ID" : 123456789, "Added" : 123456789 } ] }
		if user == None:
			await ctx.send("Usage:  `{}vk [user]`".format(ctx.prefix))
			return

		mute_votes = self.settings.getServerStat(ctx.guild, "VotesToMute")
		ment_votes = self.settings.getServerStat(ctx.guild, "VotesToMention")
		mute_time  = self.settings.getServerStat(ctx.guild, "VotesMuteTime")
		ment_chan  = self.settings.getServerStat(ctx.guild, "VoteKickChannel")
		vote_ment  = self.settings.getServerStat(ctx.guild, "VoteKickMention")
		vote_anon  = self.settings.getServerStat(ctx.guild, "VoteKickAnon")
		
		if vote_anon:
			await ctx.message.delete()

		# Check if mention and mute are disabled
		if (ment_votes == 0 or ment_chan == None or ment_chan == None) and (mute_votes == 0 or mute_time == 0):
			await ctx.send('This function is not setup yet.')
			return
		

		check_user = DisplayName.memberForName(user, ctx.guild)
		if not check_user:
			await ctx.send("I couldn't find *{}*...".format(Nullify.clean(user)))
			return
		
		# Check if we're trying to kick ourselves
		if check_user.id == ctx.author.id:
			await ctx.send("You should probably find a way to be okay with yourself.  Kicking yourself will get you nowhere.")
			return

		# Check if we're trying to kick an admin
		isAdmin = check_user.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in check_user.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if isAdmin:
			await ctx.channel.send('You cannot vote to kick the admins.  Please work out any issues you may have with them in a civil manner.')
			return

		vote_list = self.settings.getServerStat(ctx.guild, "VoteKickArray")
		for member in vote_list:
			if member["ID"] == check_user.id:
				# They're in the list - let's see if you've already voted for them
				for vote in member["Kicks"]:
					if vote["ID"] == ctx.author.id:
						await ctx.send("You've already voted to kick that member.  You cannot vote against them again while your vote is still active.")
						return
				# We haven't voted for them yet - add our vote
				member["Kicks"].append({ "ID" : ctx.author.id, "Added" : time.time() })
				await ctx.send("Vote kick added for *{}!*".format(DisplayName.name(check_user)))
				await self._check_votes(ctx, check_user)
				return
		# Never found the member
		vote_list.append({ 
			"ID" : check_user.id,
			"Muted" : False,
			"Mentioned" : False,
			"Kicks" : [ { "ID" : ctx.author.id, "Added" : time.time() } ]
			})
		await ctx.send("Vote kick added for *{}!*".format(DisplayName.name(check_user)))
		await self._check_votes(ctx, check_user)

	@commands.command(pass_context=True)
	async def vkclear(self, ctx, *, user = None):
		"""Clears the votes against the passed user (bot-admin only)."""
		# Check if we're trying to kick an admin
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if user == None:
			await ctx.send("Usage: `{}vkclear [user]`".format(ctx.prefix))
			return

		check_user = DisplayName.memberForName(user, ctx.guild)
		if not check_user:
			await ctx.send("I couldn't find *{}*...".format(Nullify.clean(user)))
			return

		vote_list = self.settings.getServerStat(ctx.guild, "VoteKickArray")
		for member in vote_list:
			if member["ID"] == check_user.id:
				vote_list.remove(member)
				await ctx.send("All votes against *{}* have been removed.".format(DisplayName.name(check_user)))
				return
		await ctx.send("*{}* has no votes against them - nothing to clear.".format(DisplayName.name(check_user)))


	@commands.command(pass_context=True)
	async def vks(self, ctx, *, user = None):
		"""Lists the vote count of the passed user (bot-admin only) or the author if no user was passed."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Default to author if not admin/bot-admin
		if not isAdmin:
			user = None

		if user == None:
			user = ctx.author.mention

		check_user = DisplayName.memberForName(user, ctx.guild)
		if not check_user:
			await ctx.send("I couldn't find *{}*...".format(Nullify.clean(user)))
			return

		vote_list = self.settings.getServerStat(ctx.guild, "VoteKickArray")
		for member in vote_list:
			if member["ID"] == check_user.id:
				if len(member["Kicks"]) == 1:
					await ctx.send("*{}* has 1 vote against them.".format(DisplayName.name(check_user)))
				else:
					await ctx.send("*{}* has {} votes against them.".format(DisplayName.name(check_user), len(member["Kicks"])))
				return
		await ctx.send("*{}* has 0 votes against them.".format(DisplayName.name(check_user)))


	


	async def _check_votes(self, ctx, member = None):
		# A helper function that checks if a user needs to be punished for a vote level
		guild = ctx.guild
		vote_list    = self.settings.getServerStat(guild, "VoteKickArray")
		vote_mute    = self.settings.getServerStat(guild, "VotesToMute")
		mute_time    = self.settings.getServerStat(guild, "VotesMuteTime")
		vote_mention = self.settings.getServerStat(guild, "VotesToMention")
		mention_id   = self.settings.getServerStat(guild, "VoteKickMention")
		m_target     = DisplayName.roleForName(mention_id, guild)
		if not m_target:
			m_target = DisplayName.memberForName(mention_id, guild)
		channel_id   = self.settings.getServerStat(guild, "VoteKickChannel")
		m_channel    = self.bot.get_channel(channel_id)

		for user in vote_list:
			if member != None and member.id != user["ID"]:
				# skip this user
				continue
			# Check the user
			# Check mutes
			if vote_mute > 0 and len(user["Kicks"]) >= vote_mute and user["Muted"] == False:
				if mute_time == 0:
					# Disabled
					continue
				cd = self.settings.getUserStat(member, guild, "Cooldown")
				isMute = self.settings.getUserStat(member, guild, "Muted")
				if cd == None:
					if isMute.lower() == 'yes':
						# We're now muted permanently
						continue
				# Check our cooldowns
				elif cd >= (time.time() + mute_time):
					# Cooldown is higher as is - ignore
					continue
				# We need to mute				
				await self.muter.mute(member, ctx.message.guild, time.time() + mute_time)
				user["Muted"] = True
				await ctx.send("*{}* has been muted for {}.".format(DisplayName.name(member), ReadableTime.getReadableTimeBetween(0, mute_time)))
			# Check for mention
			if vote_mention > 0 and len(user["Kicks"]) >= vote_mention and user["Mentioned"] == False:
				if not m_channel or not m_target:
					continue
				kick_words = "1 user"
				if not len(user["Kicks"]) == 1:
					kick_words = "{} users".format(len(user["Kicks"]))
				user["Mentioned"] = True
				await m_channel.send("{} - *{}* has had {} vote to kick them.".format(m_target.mention, member.mention, kick_words))
