import asyncio, discord, time, parsedatetime
from discord.ext import commands
from datetime import datetime
from Cogs import Utils, DisplayName, ReadableTime

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Mute(bot, settings))

class Mute(commands.Cog):

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.loop_list = []
        self.mute_perms = ("send_messages","add_reactions","speak")
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    def _is_submodule(self, parent, child):
        return parent == child or child.startswith(parent + ".")

    @commands.Cog.listener()
    async def on_unloaded_extension(self, ext):
        # Called to shut things down
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        for task in self.loop_list:
            task.cancel()

    @commands.Cog.listener()
    async def on_loaded_extension(self, ext):
        # See if we were loaded
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        await self.bot.wait_until_ready()
        # Check all mutes and start timers
        print("Checking mutes...")
        t = time.time()
        for server in self.bot.guilds:
            muteList = self.settings.getServerStat(server, "MuteList")
            for entry in muteList:
                member = server.get_member(int(entry["ID"]))
                if member:
                    # We have a user! Check for a cooldown
                    cooldown = entry['Cooldown']
                    if cooldown == None:
                        continue
                    self.loop_list.append(self.bot.loop.create_task(self.checkMute(member, server, cooldown)))
        # Add a loop to remove expired mutes in the MuteList
        self.loop_list.append(self.bot.loop.create_task(self.mute_list_check()))
        print("Mutes checked - took {} seconds.".format(time.time() - t))       

    async def onjoin(self, member, server):
        # Check if the new member was muted when they left
        muteList = self.settings.getServerStat(server, "MuteList")
        for entry in muteList:
            if str(entry['ID']) == str(member.id):
                # Found them - mute them
                await self._mute(member, server, entry['Cooldown'])
            
    async def mute_list_check(self):
        while not self.bot.is_closed():
            # Iterate through the servers and check for roll-off mutes
            for guild in self.bot.guilds:
                mute_list = self.settings.getServerStat(guild, "MuteList")
                # Go through the id's and check for orphaned ones
                remove_mute = []
                for entry in mute_list:
                    if guild.get_member(int(entry["ID"])):
                        # Still on the server - ignore
                        continue
                    if entry["Cooldown"] == None:
                        # Perma-muted - let's see if we have a rolloff time
                        if not "Added" in entry:
                            # Old mute - set "Added" to now
                            entry["Added"] = int(time.time())
                            continue
                        # See if we're over 90 days and remove perma mute
                        if int(time.time())-int(entry["Added"]) > 3600*24*90:
                            remove_mute.append(entry)
                        continue
                    if int(entry["Cooldown"])-int(time.time()) > 0:
                        # Still going on
                        continue
                    # We can remove them
                    remove_mute.append(entry)
                if len(remove_mute) == 0:
                    # No one to remove
                    continue
                for entry in remove_mute:
                    mute_list.remove(entry)
                self.settings.setServerStat(guild, "MuteList", mute_list)
            # Check once per hour
            await asyncio.sleep(3600)
            
    def _remove_task(self, task):
        if task in self.loop_list:
            self.loop_list.remove(task)

    async def checkMute(self, member, server, cooldown):
        # Get the current task
        task = asyncio.Task.current_task()
        # Check if we have a cooldown left - and unmute accordingly
        timeleft = int(cooldown)-int(time.time())
        if timeleft > 0:
            # Time to wait yet - sleep
            await asyncio.sleep(timeleft)
        # We've waited it out - unmute if needed
        # But check if the mute time has changed
        cd = self.settings.getUserStat(member, server, "Cooldown")
        isMute = self.settings.getUserStat(member, server, "Muted", False)
        if cd == None:
            if isMute:
                # We're now muted permanently
                self._remove_task(task)
                return
        else:
            timeleft = int(cd)-int(time.time())
            if timeleft > 0:
                # Our cooldown changed - rework
                self.loop_list.append(self.bot.loop.create_task(self.checkMute(member, server, cd)))
                self._remove_task(task)
                return
        # Here - we either have surpassed our cooldown - or we're not muted anymore
        if isMute:
            await self._unmute(member, server)
            # pm = 'You have been **Unmuted**.\n\nYou can send messages on *{}* again.'.format(Utils.suppressed(server,server.name))
            # await member.send(pm)
        self._remove_task(task)

    async def _mute(self, member, server, cooldown = None, muted_by = None):
        # Mutes the specified user on the specified server
        # Check for a mute role - and verify it
        mute_role = self.settings.getServerStat(server,"MuteRole")
        if mute_role: # Got something - make sure it's real
            try: mute_role = server.get_role(int(mute_role))
            except: mute_role = None
        if mute_role: # We actually have a mute role here - let's apply it
            if not mute_role in member.roles: # Doesn't already have it
                self.settings.role.add_roles(member,[mute_role])
        else: # Need to mute the old-fashioned way
            await self._sync_perms(server, member)
        # Setup our info
        self.settings.setUserStat(member, server, "Muted", True)
        self.settings.setUserStat(member, server, "Cooldown", cooldown)
        muteList = self.settings.getServerStat(server, "MuteList")
        # check if we're already muted
        entry = next((x for x in muteList if str(x["ID"])==str(member.id)),False)
        if entry: entry["Cooldown"] = cooldown
        else: muteList.append({ 'ID': member.id, 'Cooldown': cooldown, 'Added' : int(time.time()) })
        # Save the results
        self.settings.setServerStat(server, "MuteList", muteList)
        # Set a timer if we have a cooldown
        if not cooldown == None: self.loop_list.append(self.bot.loop.create_task(self.checkMute(member, server, cooldown)))
        # Dispatch and event
        self.bot.dispatch("mute", member, server, cooldown, muted_by)

    async def _unmute(self, member, server):
        # Unmutes the specified user on the specified server
        # First we check for the mute role if possible - and then we
        # walk the channels looking for our custom overrides and remove those
        mute_role = self.settings.getServerStat(server,"MuteRole")
        if mute_role: # Got something - make sure it's real
            try: mute_role = server.get_role(int(mute_role))
            except: mute_role = None
        if mute_role: # We actually have a mute role here - let's remove it
            if mute_role in member.roles: # Already have it
                self.settings.role.rem_roles(member,[mute_role])
        # Let's walk all the channels and make sure we remove the overrides as needed
        await self._sync_perms(server, member, desync=True)
        # Setup and gather our info
        self.settings.setUserStat(member, server, "Muted", False)
        self.settings.setUserStat(member, server, "Cooldown", None)
        muteList = self.settings.getServerStat(server, "MuteList")
        # Set the list to all items except the one we're undoing
        muteList = [x for x in muteList if str(x["ID"]) != str(member.id)]
        # Save the results
        self.settings.setServerStat(server, "MuteList", muteList)
        # Dispatch the event for logging
        self.bot.dispatch("unmute", member, server)

    async def _ask_perms(self, ctx, mute_role, desync=False, show_count=True):
        # Helper that asks the user if they want to sync/desync the role perms
        # Let's build our question:
        question = ""
        if show_count:
            count = len([x for x in ctx.guild.members if mute_role in x.roles])
            question += "**There {} currently {} member{} with {}.**\n".format(
                "is" if count == "1" else "are",
                count,
                "" if count == 1 else "s",
                Utils.suppressed(ctx,mute_role.name)
            )
        question += "Would you like to {}sync **{}**'s permissions? (y/n)\nThis *{}* the following permissions in all channels:\n`{}`".format(
            "de" if desync else "",
            Utils.suppressed(ctx,mute_role.name),
            "enables" if desync else "disables",
            ", ".join(self.mute_perms)
        )
        check_sync = await ctx.send(question)
        def check_answer(message):
            return message.channel == ctx.channel and message.author == ctx.author and message.content.lower() in ["y","yes","true","n","no","false"]
        try: sync_response = await self.bot.wait_for('message', timeout=60, check=check_answer)
        except:
            await ctx.send("We're out of time - I'll leave the permissions untouched.")
            return None
        if sync_response.content.lower() in ["n","no","false"]:
            await ctx.send("Permissions for **{}** have been left untouched.".format(Utils.suppressed(ctx,mute_role.name)))
            return False
        # We want to adjust perms
        syncing_message = await ctx.send("{}yncing permissions for **{}**...".format("Des" if desync else "S", Utils.suppressed(ctx,mute_role.name)))
        await self._sync_perms(ctx,mute_role,desync)
        await syncing_message.edit(content="**{}** has been **{}ynced**.".format(Utils.suppressed(ctx,mute_role.name),"de" if desync else "s"))
        return True

    async def _sync_perms(self, ctx, mute_role, desync=False):
        # Helper to sync or desync the role based on the current context.
        guild = ctx if isinstance(ctx,discord.Guild) else ctx.guild if isinstance(ctx,discord.ext.commands.Context) else None
        if guild is None: return # Got sent some wonky values, I guess...
        for channel in guild.channels:
            if not isinstance(channel,(discord.TextChannel,discord.VoiceChannel)): continue
            if hasattr(channel,"permissions_synced"): # Implemented in 1.3.0 of discord.py
                if channel.permissions_synced: channel = channel.category # Get the category if we're synced
            overs = channel.overwrites_for(mute_role) # Get any overrides for the role
            # Check if we qualify in this channel to sync/desync
            if desync: perm_check  = any(x[0] in self.mute_perms and x[1] != None for x in overs)
            else: perm_check = not all([x==False for x in (overs.send_messages,overs.add_reactions,overs.speak)])
            if perm_check: # We qualify - set our perms as needed
                other_perms = any(x[0] not in self.mute_perms and x[1] != None for x in overs)
                overs.send_messages = overs.add_reactions = overs.speak = None if desync else False
                try: await channel.set_permissions(mute_role, overwrite=overs if other_perms or not desync else None)
                except: pass

    @commands.command(pass_context=True)
    async def setmuterole(self, ctx, *, role = None):
        """Sets the target role to apply when muting.  Passing nothing will disable the mute role and remove send_messages, add_reactions, and speak overrides (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        if role:
            target_role = DisplayName.roleForName(role, ctx.guild)
            if not target_role: return await ctx.send("That role doesn't exist - you can create a new mute role with `{}createmuterole [role_name]` though.".format(ctx.prefix))
        try: mute_role = ctx.guild.get_role(int(self.settings.getServerStat(ctx.guild,"MuteRole")))
        except: mute_role = None
        await ctx.send("Current mute role: **{}**".format(Utils.suppressed(ctx,mute_role.name)) if mute_role else "Currently, there is **no mute role** setup.")
        if role == None:
            if mute_role:
                await self._ask_perms(ctx,mute_role,desync=True,show_count=True)
            self.settings.setServerStat(ctx.guild,"MuteRole",None)
            return await ctx.send("Mute role **removed** - muting will now create overrides per channel!") if mute_role else None
        if mute_role:
            if mute_role == target_role:
                await ctx.send("Target mute role is **the same** as the current!")
                return await self._ask_perms(ctx,target_role,desync=False,show_count=True)
            await self._ask_perms(ctx,mute_role,desync=True,show_count=True)
        # Got a mute role - let's set the id
        await ctx.send("Target mute role: **{}**".format(Utils.suppressed(ctx,target_role.name)))
        self.settings.setServerStat(ctx.guild,"MuteRole",target_role.id)
        await self._ask_perms(ctx,target_role,desync=False,show_count=True)
        await ctx.send("The mute role has been set to **{}**!".format(Utils.suppressed(ctx,target_role.name)))

    @commands.command(pass_context=True)
    async def muterole(self, ctx):
        """Lists the target role to apply when muting (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        role = self.settings.getServerStat(ctx.guild,"MuteRole")
        if not role:
            return await ctx.send("There is no mute role setup.  You can set one with `{}setmuterole [role]` - or have me create one with `{}createmuterole [role_name]`".format(ctx.prefix,ctx.prefix))
        try: mute_role = ctx.guild.get_role(int(role))
        except: mute_role = None
        if not mute_role: return await ctx.send("The prior mute role (ID: `{}`) no longer exists.  You can set one with `{}setmuterole [role]` - or have me create one with `{}createmuterole [role_name]`".format(role,ctx.prefix,ctx.prefix))
        await ctx.send("Muted users will be given **{}**.".format(Utils.suppressed(ctx,mute_role.name)))

    @commands.command(pass_context=True)
    async def createmuterole(self, ctx, *, role_name = None):
        """Sets the target role to apply when muting (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        mute_role = DisplayName.roleForName(role_name, ctx.guild)
        if mute_role: # Already exists - let's update the settings
            self.settings.setServerStat(ctx.guild,"MuteRole",mute_role.id)
            return await ctx.send("The mute role has been set to the __existing__ **{}** role!".format(Utils.suppressed(ctx,mute_role.name)))
        # Create a role with the proper overrides
        message = await ctx.send("Creating **{}** role...".format(Utils.suppressed(ctx,role_name)))
        try: mute_role = await ctx.guild.create_role(name=role_name,reason="Mute role created by {}#{}".format(ctx.author.name,ctx.author.discriminator))
        except Exception as e: return await message.edit(content="Role create failed with error:\n```\n{}\n```".format(e))
        # Walk the channels and set the perms for the role
        await message.edit(content="Updating permissions for **{}**...".format(Utils.suppressed(ctx,role_name)))
        for channel in ctx.guild.channels:
            if not isinstance(channel,(discord.TextChannel,discord.VoiceChannel)): continue
            if hasattr(channel,"permissions_synced"): # Implemented in 1.3.0 of discord.py
                if channel.permissions_synced: channel = channel.category # Get the category if we're synced
            overs = channel.overwrites_for(mute_role)
            if not all([x==False for x in (overs.send_messages,overs.add_reactions,overs.speak)]):
                # We haven't been muted completely here yet
                overs.send_messages = overs.add_reactions = overs.speak = False
                try: await channel.set_permissions(mute_role, overwrite=overs)
                except: pass
        # Save it in our settings
        self.settings.setServerStat(ctx.guild,"MuteRole",mute_role.id)
        await message.edit(content="Muted users will be given **{}**.".format(Utils.suppressed(ctx,mute_role.name)))

    @commands.command(pass_context=True)
    async def syncmuterole(self, ctx):
        """Ensures that the mute role has the send_messages, add_reactions, and speak overrides disabled in all channels (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        role = self.settings.getServerStat(ctx.guild,"MuteRole")
        if not role:
            return await ctx.send("There is no mute role setup.  You can set one with `{}setmuterole [role]` - or have me create one with `{}createmuterole [role_name]`".format(ctx.prefix,ctx.prefix))
        try: mute_role = ctx.guild.get_role(int(role))
        except: mute_role = None
        if not mute_role: return await ctx.send("The prior mute role (ID: `{}`) no longer exists.  You can set one with `{}setmuterole [role]` - or have me create one with `{}createmuterole [role_name]`".format(role,ctx.prefix,ctx.prefix))
        # Have a valid mute role here - let's sync the perms
        message = await ctx.send("Syncing permissions for **{}**...".format(Utils.suppressed(ctx,mute_role.name)))
        await self._sync_perms(ctx,mute_role)
        await message.edit(content="**{}** has been synced for muting.".format(Utils.suppressed(ctx,mute_role.name)))

    @commands.command(pass_context=True)
    async def desyncmuterole(self, ctx):
        """Removes send_messages, add_reactions, and speak overrides from the mute role - helpful if you plan to repurpose the existing mute role (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        role = self.settings.getServerStat(ctx.guild,"MuteRole")
        if not role:
            return await ctx.send("There is no mute role setup.  You can set one with `{}setmuterole [role]` - or have me create one with `{}createmuterole [role_name]`".format(ctx.prefix,ctx.prefix))
        try: mute_role = ctx.guild.get_role(int(role))
        except: mute_role = None
        if not mute_role: return await ctx.send("The prior mute role (ID: `{}`) no longer exists.  You can set one with `{}setmuterole [role]` - or have me create one with `{}createmuterole [role_name]`".format(role,ctx.prefix,ctx.prefix))
        # Have a valid mute role here - let's desync our perms
        message = await ctx.send("Syncing permissions for **{}**...".format(Utils.suppressed(ctx,mute_role.name)))
        await self._sync_perms(ctx,mute_role,True)
        await message.edit(content="**{}** has been **desynced**.  It will **__no longer work__** for muting!".format(Utils.suppressed(ctx,mute_role.name)))

    @commands.command(pass_context=True)
    async def mute(self, ctx, *, member = None, cooldown = None):
        """Prevents a member from sending messages in chat or speaking in voice (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        if member == None:
            msg = 'Usage: `{}mute [member] [cooldown]`'.format(ctx.prefix)
            return await ctx.send(msg)
        # Let's search for a name at the beginning - and a time at the end
        parts = member.split()
        for j in range(len(parts)):
            # Reverse search direction
            i = len(parts)-1-j
            memFromName = None
            endTime     = None
            # Name = 0 up to i joined by space
            nameStr = ' '.join(parts[0:i+1])
            # Time = end of name -> end of parts joined by space
            timeStr = ' '.join(parts[i+1:])
            memFromName = DisplayName.memberForName(nameStr, ctx.guild)
            if memFromName:
                # We got a member - let's check for time
                # Get current time - and end time
                try:
                    # Get current time - and end time
                    currentTime = int(time.time())
                    cal         = parsedatetime.Calendar()
                    time_struct, parse_status = cal.parse(timeStr)
                    start       = datetime(*time_struct[:6])
                    end         = time.mktime(start.timetuple())
                    # Get the time from now to end time
                    endTime = end-currentTime
                except:
                    pass
                if not endTime == None:
                    # We got a member and a time - break
                    break
        if memFromName == None:
            # We couldn't find one or the other
            msg = 'Usage: `{}mute [member] [cooldown]`'.format(ctx.prefix)
            return await ctx.send(msg)
        cooldown = None if endTime == 0 else endTime
        member   = memFromName
        # Check if we're muting ourself
        if member is ctx.author:
            msg = 'It would be easier for me if you just *stayed quiet all by yourself...*'
            return await ctx.send(msg)
        # Check if we're muting the bot
        if member.id == self.bot.user.id:
            msg = 'How about we don\'t, and *pretend* we did...'
            return await ctx.send(msg)
        # Check if member is admin or bot admin
        if await Utils.is_bot_admin_reply(ctx,member=member,message="You can't mute other admins or bot-admins.",message_when=True): return
        # Set cooldown - or clear it
        if type(cooldown) is int or type(cooldown) is float:
            if cooldown < 0:
                msg = 'Cooldown cannot be a negative number!'
                return await ctx.send(msg)
            currentTime = int(time.time())
            cooldownFinal = currentTime+cooldown
        else:
            cooldownFinal = None
        # Check if we're using the old mute and suggest the quicker version
        try: role = ctx.guild.get_role(int(self.settings.getServerStat(ctx.guild,"MuteRole")))
        except: role = None
        mess = await ctx.send("Muting...{}".format(
            "" if role else " You can set up a mute role with `{}setmuterole [role]` or `{}createmuterole [role_name]` for a **much faster** muting experience.".format(ctx.prefix,ctx.prefix)
            ))
        # Do the actual muting
        await self._mute(member, ctx.guild, cooldownFinal, ctx.author)
        if cooldown:
            mins = "minutes"
            checkRead = ReadableTime.getReadableTimeBetween(currentTime, cooldownFinal)
            msg = '*{}* has been **Muted** for *{}*.'.format(DisplayName.name(member), checkRead)
            # pm  = 'You have been **Muted** by *{}* for *{}*.\n\nYou will not be able to send messages on *{}* until either that time has passed, or you have been **Unmuted**.'.format(DisplayName.name(ctx.author), checkRead, Utils.suppressed(ctx, ctx.guild.name))
        else:
            msg = '*{}* has been **Muted** *until further notice*.'.format(DisplayName.name(member))
            # pm  = 'You have been **Muted** by *{}* *until further notice*.\n\nYou will not be able to send messages on *{}* until you have been **Unmuted**.'.format(DisplayName.name(ctx.author), Utils.suppressed(ctx, ctx.guild.name))
        await mess.edit(content=Utils.suppressed(ctx,msg))
        '''try:
            await member.send(pm)
        except Exception:
            pass'''

    @commands.command(pass_context=True)
    async def unmute(self, ctx, *, member = None):
        """Allows a muted member to send messages in chat (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        if member == None:
            msg = 'Usage: `{}unmute [member]`'.format(ctx.prefix)
            return await ctx.send(msg)
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                return await ctx.send(Utils.suppressed(ctx,msg))
        mess = await ctx.send("Unmuting...")
        await self._unmute(member, ctx.guild)
        pm = "You have been **Unmuted** by *{}*.\n\nYou can send messages on *{}* again.".format(DisplayName.name(ctx.author), Utils.suppressed(ctx, ctx.guild.name))
        msg = '*{}* has been **Unmuted**.'.format(DisplayName.name(member))
        await mess.edit(content=msg)
        try:
            await member.send(pm)
        except Exception:
            pass

    @commands.command(pass_context=True)
    async def ismuted(self, ctx, *, member = None):
        """Says whether a member is muted in chat."""
        if member == None:
            msg = 'Usage: `{}ismuted [member]`'.format(ctx.prefix)
            return await ctx.send(msg)
        memberName = member
        member = DisplayName.memberForName(memberName, ctx.guild)
        if not member:
            msg = 'I couldn\'t find *{}*...'.format(memberName)
            return await ctx.send(Utils.suppressed(ctx,msg))
        # Check if we have a muted role
        try: mute_role = ctx.guild.get_role(int(self.settings.getServerStat(ctx.guild,"MuteRole")))
        except: mute_role = None
        item = next((x for x in self.settings.getServerStat(ctx.guild,"MuteList",[]) if str(x["ID"])==str(member.id)),None)
        if mute_role and mute_role in member.roles:
            # We're muted using the role - let's get the cooldown if any
            if not item or item["Cooldown"] == None:
                # No cooldown - let's just give the bad news...
                return await ctx.send("*{}* is **muted**.".format(DisplayName.name(member)))
            # We're still muted - but have a cooldown
            return await ctx.send("*{}* is **muted**.\n*{}* remain.".format(
                DisplayName.name(member),
                ReadableTime.getReadableTimeBetween(int(time.time()), item["Cooldown"])
            ))
        muted_channels = 0
        # Walk the channels we may be muted in
        for channel in ctx.guild.channels:
            if not isinstance(channel,(discord.TextChannel,discord.VoiceChannel)): continue
            if hasattr(channel,"permissions_synced"): # Implemented in 1.3.0 of discord.py
                if channel.permissions_synced: channel = channel.category # Get the category if we're synced
            overs = channel.overwrites_for(member) # Get any overrides for the user
            # Check if we match any of the mute overrides - and if we have any others
            if any(x[0] in self.mute_perms and x[1] != None for x in overs):
                muted_channels += 1
        # Tell the user if the target is muted
        if muted_channels:
            if not item or item["Cooldown"] == None:
                # No cooldown - let's just give the bad news...
                return await ctx.send("*{}* is **muted** in {} channel{}.".format(
                    DisplayName.name(member),
                    muted_channels,
                    "" if muted_channels == 1 else "s"
                ))
            # We're still muted - but have a cooldown
            return await ctx.send("*{}* is **muted** in {} channel{},\n*{}* remain.".format(
                DisplayName.name(member),
                muted_channels,    
                "" if muted_channels == 1 else "s",
                ReadableTime.getReadableTimeBetween(int(time.time()), item["Cooldown"])
            ))
        # Not muted - let em know
        await ctx.send("*{}* is **unmuted**.".format(DisplayName.name(member)))
