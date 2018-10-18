# Hey there! Sorru, I couldn't find any other way to contact you... I'm still very new to github and it is still very confusing...
# Anyway, I seem to have an issue with this part of your code. I merged this with my already existing commands and also added the Settings.py
# But every time I try to use this code I get and error (Starting at line 45). I hope you can tell me what I am doing wrong!


	@commands.command(pass_context=True)
	async def broadcast(self, ctx, *, message : str = None):
		"""Broadcasts a message to all connected servers.  Can only be done by the owner."""

		channel = ctx.message.channel
		author  = ctx.message.author

		if message == None:
			await channel.send(usage)
			return

		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return
		
		for server in self.bot.guilds:
			# Get the default channel
			targetChan = server.get_channel(server.id)
			targetChanID = self.settings.getServerStat(server, "DefaultChannel")
			if len(str(targetChanID)):
				# We *should* have a channel
				tChan = self.bot.get_channel(int(targetChanID))
				if tChan:
					# We *do* have one
					targetChan = tChan
			try:
				await targetChan.send(message)
			except Exception:
				pass
			
			
# ERROR_HERE
 File "C:\Users\niels\AppData\Local\Programs\Python\Python37-32\lib\site-packages\discord\ext\commands\core.py", line 61, in wrapped
    ret = await coro(*args, **kwargs)
  File "C:\Users\niels\Downloads\discord_bot.py-master\discord_bot.py-master\cogs\admin.py", line 271, in broadcast
    isOwner = self.settings.isOwner(ctx.author)
AttributeError: 'Admin' object has no attribute 'settings'
