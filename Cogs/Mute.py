import asyncio, discord, time, parsedatetime, re
from discord.ext import commands
from datetime import datetime, timedelta
from Cogs import Utils, DisplayName, ReadableTime, PickList, Nullify, Message

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Mute(bot, settings))

class Mute(commands.Cog):

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.mention_re = re.compile(r"<?@?!?[0-9]{17,21}>?")
        self.time_check = re.compile(r"(?i)(\d+w(k|eek)?s?|\d+d(ay)?s?|\d+h(r|our)?s?|\d+m(inute|in)?s?|\d+s(econd|ec)?s?)+")
        self.loop_list = []
        self.mute_perms = ("send_messages","send_messages_in_threads","add_reactions","speak")
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    async def message(self,message):
        # Check for admin status
        ctx = await self.bot.get_context(message)
        if Utils.is_bot_admin(ctx) or not self.settings.getUserStat(message.author,message.guild,"Muted",False):
            return
        # We're not admin/bot-admin, and we've been muted - let's see if the server
        # requires we delete messages that sneak through
        if not self.settings.getServerStat(message.guild,"MuteAutoDelete",True):
            return
        # At this point - assume we're muted, and need to delete messages
        # Time to verify if we're past the mute time
        checkTime = self.settings.getUserStat(message.author, message.guild, "Cooldown")
        if checkTime: checkTime = int(checkTime)
        currentTime = int(time.time())
        if checkTime and currentTime >= checkTime:
            # We have passed the check time
            self.settings.setUserStat(message.author, message.guild, "Cooldown", None)
            self.settings.setUserStat(message.author, message.guild, "Muted", False)
            return
        # If we got here, we're still muted, and slipped past - ignore commands, and delete the message
        return {"Ignore":True,"Delete":True}

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
                    if cooldown is None:
                        continue
                    self.loop_list.append(self.bot.loop.create_task(self.checkMute(member, server, cooldown)))
        # Add a loop to remove expired mutes in the MuteList
        self.loop_list.append(self.bot.loop.create_task(self.mute_list_check()))
        print("Mutes checked - took {} seconds.".format(time.time() - t))       

    async def onjoin(self, member, server):
        # Check if the new member was muted when they left
        muteList = self.settings.getServerStat(server, "MuteList")
        entry = next((x for x in muteList if str(x["ID"])==str(member.id)),None)
        if not entry: return # Doesn't exist - skip
        # We had a mute - let's validate it
        if (entry["Cooldown"] is None and int(time.time())-entry.get("Added",int(time.time()))>3600*24*90) or (entry["Cooldown"] != None and int(entry["Cooldown"])-int(time.time())<=0):
            # Was a permamute and 90 days have expired - or was a timed mute, and the time has expired
            # Remove the mute from the mute list - and ignore
            muteList.remove(entry)
            self.settings.setServerStat(server,"MuteList",muteList)
            return
        # At this point - we still need to mute - so we'll just apply it
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
                    if entry["Cooldown"] is None:
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
        try:
            task = asyncio.Task.current_task()
        except AttributeError:
            task = asyncio.current_task()
        # Check if we have a cooldown left - and unmute accordingly
        timeleft = int(cooldown)-int(time.time())
        if timeleft > 0:
            # Time to wait yet - sleep
            await asyncio.sleep(timeleft)
        # We've waited it out - unmute if needed
        # But check if the mute time has changed
        cd = self.settings.getUserStat(member, server, "Cooldown")
        isMute = self.settings.getUserStat(member, server, "Muted", False)
        if cd is None:
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

    async def _mute(self, member, server, cooldown = None, muted_by = None, reason = None):
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
        if not cooldown is None: self.loop_list.append(self.bot.loop.create_task(self.checkMute(member, server, cooldown)))
        # Dispatch an event
        self.bot.dispatch("mute", member, server, cooldown, muted_by, reason)

    async def _unmute(self, member, server, unmuted_by = None, reason = None):
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
        self.bot.dispatch("unmute", member, server, unmuted_by, reason)

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
            if isinstance(channel,(discord.TextChannel,discord.VoiceChannel)) and hasattr(channel,"permissions_synced") and channel.permissions_synced:
                # This channel inherits its permissions from the category - let's skip it and just set that.
                continue
            overs = channel.overwrites_for(mute_role) # Get any overrides for the role
            # Check if we qualify in this channel to sync/desync
            if desync: perm_check = any(x[0] in self.mute_perms and x[1] != None for x in overs)
            else: perm_check = not all([getattr(overs,x,None)==False for x in self.mute_perms])
            if perm_check: # We qualify - set our perms as needed
                other_perms = any(x[0] not in self.mute_perms and x[1] != None for x in overs)
                for x in self.mute_perms:
                    setattr(overs,x,None if desync else False)
                try: await channel.set_permissions(mute_role, overwrite=overs if other_perms or not desync else None)
                except: pass

    @commands.command()
    async def setmuterole(self, ctx, *, role = None):
        """Sets the target role to apply when muting.  Passing nothing will disable the mute role and remove send_messages, add_reactions, and speak overrides (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        if role:
            target_role = DisplayName.roleForName(role, ctx.guild)
            if not target_role: return await ctx.send("That role doesn't exist - you can create a new mute role with `{}createmuterole [role_name]` though.".format(ctx.prefix))
        try: mute_role = ctx.guild.get_role(int(self.settings.getServerStat(ctx.guild,"MuteRole")))
        except: mute_role = None
        await ctx.send("Current mute role: **{}**".format(Utils.suppressed(ctx,mute_role.name)) if mute_role else "Currently, there is **no mute role** setup.")
        if role is None:
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

    @commands.command()
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

    @commands.command()
    async def createmuterole(self, ctx, *, role_name = None):
        """Sets the target role to apply when muting (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        if not role_name: return await ctx.send("Usage: `{}createmuterole [role_name]`".format(ctx.prefix))
        mute_role = DisplayName.roleForName(role_name, ctx.guild)
        if mute_role: # Already exists - let's update the settings
            self.settings.setServerStat(ctx.guild,"MuteRole",mute_role.id)
            return await ctx.send("The mute role has been set to the __existing__ **{}** role!".format(Utils.suppressed(ctx,mute_role.name)))
        # Create a role with the proper overrides
        message = await ctx.send("Creating **{}** role...".format(Utils.suppressed(ctx,role_name)))
        try: mute_role = await ctx.guild.create_role(name=role_name,reason="Mute role created by {}".format(ctx.author))
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

    @commands.command()
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

    @commands.command()
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

    @commands.command()
    async def muteautodelete(self, ctx, *, yes_no = None):
        """Enables/Disables auto-delete of any messages that slip by from muted users (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        await ctx.send(Utils.yes_no_setting(ctx,"Muted user auto-delete","MuteAutoDelete",yes_no=yes_no,default=True))

    async def mute_timeout(self, ctx, members_and_reason = None, command_name = "mute"):
        # Helper method to handle the lifting for mute and timeout
        if not await Utils.is_bot_admin_reply(ctx): return
        if not members_and_reason:
            return await ctx.send('Usage: `{}{} [space delimited member mention/id] {}[reason]`'.format(
                ctx.prefix,
                command_name,
                "" if command_name.lower() == "unmute" else "[duration] "
            ))
        is_admin = Utils.is_admin(ctx)
        def member_exception(m):
            # Helper to check if this member cannot be muted
            if not isinstance(m,discord.Member):
                # Only check members - discord.User isn't in the server,
                # so they have no reason to be excluded
                return False
            if m.id in (self.bot.user.id,ctx.author.id):
                # Can't mute the bot or ourselves
                return True
            if Utils.is_bot_admin(ctx,m):
                # Can't mute other bot-admins
                return True
            return False
        def get_seconds(time):
            # Helper to convert WwDdHhMmSs type time strings into a
            # total number of seconds
            allowed = {"w":604800,"d":86400,"h":3600,"m":60,"s":1}
            total_seconds = 0
            last_time = ""
            for char in time:
                # Check if we have a number
                if char.isdigit():
                    last_time += char
                    continue
                # Check if it's a valid suffix and we have a time so far
                if char.lower() in allowed and last_time:
                    total_seconds += int(last_time)*allowed[char.lower()]
                last_time = ""
            # Check if we have any left - and add it
            if last_time: total_seconds += int(last_time) # Assume seconds at this point
            return total_seconds
        # Split into a list of args
        args = members_and_reason.split()
        # Get our list of targets
        targets = []
        missed  = []
        unable  = []
        skipped = []
        reason  = ""
        cooldown_time = None # Default to None for later checks
        for index,item in enumerate(args):
            if self.mention_re.fullmatch(item): # Check if it's a mention
                # Resolve the member
                mem_id = int(re.sub(r'\W+', '', item))
                member = ctx.guild.get_member(mem_id)
                # If we have an invalid mention, save it to report later
                if member is None:
                    missed.append(str(mem_id))
                    continue
                # Let's check if we have a valid member and make sure it's not:
                # 1. The bot, 2. The command caller, 3. Another bot-admin/admin
                if command_name.lower() != "unmute" and member_exception(member):
                    unable.append(member.mention)
                    continue
                if not member in targets:
                    targets.append(member) # Only add them if we don't already have them
            else:
                # Not a member match - we're in the cooldown/reason portion now
                # Check if the next value is a time value
                try: mute_time_str = self.time_check.match(args[index]).group(0)
                except: mute_time_str = ""
                if mute_time_str:
                    # Got a mute time - let's get the seconds value
                    cooldown_time = get_seconds(mute_time_str)
                reason = " ".join(args[index if cooldown_time is None else index+1:])
                break
        reason = reason or "No reason provided."
        readable_time = "Until further notice" if not cooldown_time else ReadableTime.getReadableTimeBetween(time.time(), time.time()+cooldown_time)
        if not len(targets):
            msg = "**With reason:**\n{}{}{}".format(
                reason,
                "" if not len(missed) else "\n\n**Unmatched ID{}:**\n{}".format("" if len(missed) == 1 else "s", "\n".join(missed)),
                "" if not len(unable) else "\n\n**Unable to {}:**\n{}".format(command_name,"\n".join(unable))
            )
            return await Message.EmbedText(title="No valid members passed!",description=msg,color=ctx.author).send(ctx)
        if cooldown_time is not None and cooldown_time < 0:
            return await Message.EmbedText(title="Cooldown cannot be a negative number!",color=ctx.author).send(ctx)
        if command_name.lower() == "timeout" and cooldown_time is None:
            return await Message.EmbedText(title="Timeout requires a cooldown!",color=ctx.author).send(ctx)
        message = await Message.EmbedText(
            title="{}...".format(
                {
                    "mute":"Muting",
                    "timeout":"Timing Out",
                    "unmute":"Unmuting"
                }.get(command_name.lower(),"Muting")
            ),color=ctx.author
        ).send(ctx)
        canned = []
        cant   = []
        for target in targets:
            try:
                # Actually run our commands
                if command_name.lower() == "mute":
                    await self._mute(target, ctx.guild, None if not cooldown_time else time.time()+cooldown_time, ctx.author, reason)
                elif command_name.lower() == "timeout":
                    await target.timeout_for(timedelta(seconds=cooldown_time),reason="{}: {}".format(ctx.author,reason))
                elif command_name.lower() == "unmute":
                    if target.timed_out: # Remove the timeout first
                        await target.timeout(None,reason="{}: {}".format(ctx.author,reason))
                    await self._unmute(target, ctx.guild, ctx.author, reason)
                if not target in canned: # Avoid double adding
                    canned.append(target)
            except Exception as e:
                print(e)
                if not target in cant:
                    cant.append(target)
        # Make sure any that showed up in cant override those in canned
        canned = [x for x in canned if not x in cant]
        msg = ""
        if len(canned):
            msg += "**I was ABLE to {}:**\n{}\n\n".format(command_name,"\n".join([str(x) for x in canned]))
        if len(cant):
            msg += "**I was UNABLE to {}:**\n{}\n\n".format(command_name,"\n".join([str(x) for x in cant]))
        if command_name.lower() != "unmute":
            msg += "**Duration:**\n{}".format(readable_time)
        await Message.EmbedText(title="{} Results".format(command_name.capitalize()),description=msg).edit(ctx,message)

    @commands.command()
    async def mute(self, ctx, *, members = None, cooldown = None, reason = None):
        """Prevents the passed members from sending messages in chat or speaking in voice (bot-admin only).
        Cooldown expects WwXdHhMmSs format, where:
        w = weeks
        d = days
        h = hours
        m = minutes
        s = seconds
        Passing no cooldown results in a perma-mute.
        eg. To mute 3 users for 2 days, 10 hours for spamming, you could do:
            $mute @user1 @user2 @user3 2d10h spamming
        """
        await self.mute_timeout(ctx,members,"mute")

    @commands.command(aliases=["to"])
    async def timeout(self, ctx, *, members = None, cooldown = None, reason = None):
        """Alternative to $mute that uses discord's native timeout api (bot-admin only)."""
        await self.mute_timeout(ctx,members,"timeout")

    @commands.command()
    async def unmute(self, ctx, *, members = None, reason = None):
        """Allows the passed members to send messages in chat or speak in voice (bot-admin only)."""
        await self.mute_timeout(ctx,members,"unmute")

    def _get_mute_status(self, member, ctx, muted_list=None, mute_role=None, check_channels=False):
        # Helper to get the muted status of a passed member based on info passed
        # This command will get the MuteList if none is passed, but assumes that
        # that the calling function has already fetched the mute_role to avoid
        # multiple db calls where possible.
        #
        # Returns a tuple of:
        # (muted_bool, cooldown_timestamp, readable_cooldown, muted_role_bool, muted_in_channels)
        #
        # If not muted, will only return False - any function receiving
        # this info should check the return value before querying the rest.
        #
        if not ctx or not ctx.guild: # Can't be muted in dm
            return False
        if muted_list is None: # Resolve the mute list if not passed
            muted_list = self.settings.getServerStat(server,"MuteList",[])
        # Get the muted_list entry, if any
        muted_entry = next((x for x in muted_list if str(x["ID"])==str(member.id)),None)
        # Check if the member has the muted role
        if mute_role and mute_role in member.roles:
            # Get the cooldown if any
            if not muted_entry or muted_entry["Cooldown"] is None:
                # No cooldown - let's just give the bad news...
                return (True,None,"",True,None)
            # We're still muted - but have a cooldown
            return (True,muted_entry["Cooldown"],ReadableTime.getReadableTimeBetween(int(time.time()),muted_entry["Cooldown"]),True,None)
        if check_channels:
            # Not using a muted role - check if we have any channel overrides
            muted_channels = []
            # Walk the channels we may be muted in
            for channel in ctx.guild.channels:
                if not isinstance(channel,(discord.TextChannel,discord.VoiceChannel)): continue
                if hasattr(channel,"permissions_synced"): # Implemented in 1.3.0 of discord.py
                    if channel.permissions_synced: channel = channel.category # Get the category if we're synced
                overs = channel.overwrites_for(member) # Get any overrides for the user
                # Check if we match any of the mute overrides - and if we have any others
                if any(x[0] in self.mute_perms and x[1] != None for x in overs):
                    muted_channels.append(channel)
            # Tell the user if the target is muted
            if muted_channels:
                # Get the cooldown if any
                if not muted_entry or muted_entry["Cooldown"] is None:
                    # No cooldown - let's just give the bad news...
                    return (True,None,"",False,muted_channels)
                # We're still muted - but have a cooldown
                return (True,muted_entry["Cooldown"],ReadableTime.getReadableTimeBetween(int(time.time()),muted_entry["Cooldown"]),False,muted_channels)
        # Fall back to see if we're in the MuteList - even if there's no channel perms or mute role
        if muted_entry:
            if muted_entry["Cooldown"] is None:
                return (True,None,"",False,None)
            return (True,muted_entry["Cooldown"],ReadableTime.getReadableTimeBetween(int(time.time()),muted_entry["Cooldown"]),False,None)
        return False

    @commands.command(aliases=["muted","listmuted"])
    async def ismuted(self, ctx, *, member = None):
        """Says whether a member is muted in chat - pass no arguments to get a list of all muted members.  Channel override mutes are only checked if a member is passed."""
        if ctx.guild is None:
            return await ctx.send("Mutes do not apply in dm.")
        if member is None:
            member_list = ctx.guild.members # Check all
            title = "Currently Muted Members:"
        else:
            # Try to resolve the passed member
            member_list = [DisplayName.memberForName(member, ctx.guild)]
            title = "Mute Results for \"{}\":".format(Nullify.resolve_mentions(member,ctx=ctx))
            if not member_list[0]:
                return await PickList.PagePicker(
                    title=title,
                    description="I couldn't find that member...",
                    color=ctx.author,
                    ctx=ctx
                ).pick()
        # Check if we have a muted role
        try: mute_role = ctx.guild.get_role(int(self.settings.getServerStat(ctx.guild,"MuteRole")))
        except: mute_role = None
        muted_list = self.settings.getServerStat(ctx.guild,"MuteList",[])
        muted_members = []
        for m in member_list:
            mute_stat = self._get_mute_status(
                m,
                ctx,
                muted_list=muted_list,
                mute_role=mute_role,
                check_channels=member is not None
            )
            if not mute_stat and not m.timed_out: continue # Not muted.
            # Parse the output
            value = "`      ID:` `{}`".format(m.id)
            if mute_stat:
                value += "\n{}`Cooldown:` {}".format(
                    "" if not mute_stat[-1] else "` Mute Type:` Permission-based (in {:,} channel{})\n".format(len(mute_stat[-1]),"" if len(mute_stat[-1])==1 else "s"),
                    "Muted until further notice." if not mute_stat[2] else mute_stat[2] + " remain."
                )
            if m.timed_out:
                value += "\n` Timeout:` Member is currently timed out"
            muted_members.append({"name":"{}. {} ({})".format(len(muted_members)+1,DisplayName.name(m),m),"value":value})
        desc = None if muted_members else "{} is not currently muted.".format(member_list[0].mention) if member else "No members are currently muted."
        return await PickList.PagePicker(
            title=title,
            description=desc,
            list=muted_members,
            color=ctx.author,
            ctx=ctx
        ).pick()
