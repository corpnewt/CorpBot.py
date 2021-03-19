import asyncio, discord, time
from discord.ext import commands
from Cogs import Utils, DisplayName, Message

def setup(bot):
    bot.add_cog(Lockdown(bot, bot.get_cog("Settings")))

class Lockdown(commands.Cog):

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.lockdown_perms = ("send_messages","add_reactions","speak")
        global Utils, DisplayName
        self.key = "Key: 🔴=Locked 🟡=Partial Lock 🟢=Unlocked 🔄=Synced 🟦=Not Synced"
        self.key_long = self.key+" ✅=Configured 🟩=Not Configured"
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    def _get_lockdown(self, ctx):
        # Returns a tuple of (lockdown_ids, channel_objects)
        lockdown = self.settings.getServerStat(ctx.guild,"LockdownList",[])
        if not len(lockdown): return ([],None)
        orphaned,channels = self._verify_lockdown(ctx,lockdown)
        if len(orphaned): # Update the lockdown list to reflect changes
            lockdown = [x for x in lockdown if not x in orphaned]
            self.settings.setServerStat(ctx.guild,"LockdownList",lockdown)
        return (lockdown,channels)

    def _verify_lockdown(self, ctx, lockdown):
        # Returns a tuple of (orphaned_ids, channel_objects)
        channels = []
        orphaned = []
        if not isinstance(lockdown,(list,tuple)): lockdown = (lockdown,)
        for c in lockdown:
            channel = ctx.guild.get_channel(int(c))
            if not channel: orphaned.append(c)
            else: channels.append(channel)
        # Return the list sorted by discord's GUI position
        return (orphaned,self._order(ctx,channels))

    def _order(self,ctx,channels,only_id=True):
        ordered = []
        for cat,chan_list in ctx.guild.by_category():
            if cat and not cat.id in ordered: ordered.append(cat.id)
            ordered.extend([chan.id for chan in chan_list])
        return sorted(channels,key=lambda x:ordered.index(x.id))

    def _get_mention(self,channel,show_lock=False,lockdown_list=[]):
        # Returns a formatted mention for the passed channel - including
        # the number of synced channels if it's a category
        #
        # First we get the overrides for the default role to check if this channel is
        # locked, unlocked, or partially locked
        default_role = channel.guild.default_role
        overs = channel.overwrites_for(default_role)
        overs_check = (overs.send_messages,overs.add_reactions,overs.speak)
        lock = "🔴" if all([x==False for x in overs_check]) else "🟡" if any([x==False for x in overs_check]) else "🟢"
        lock_text = ""
        if show_lock: lock_text = "✅ " if channel.id in lockdown_list else "🟩 "
        if isinstance(channel,discord.CategoryChannel):
            synced = [x for x in channel.channels if x.permissions_synced] if hasattr(channel,"permissions_synced") else channel.channels
            return "{}{} {} ({:,}/{:,} synced)".format(
                lock_text,
                lock,
                channel.name,
                len(synced),
                len(channel.channels)
            )
        return "{}{} {}{}".format(lock_text,lock, "🔄 " if not hasattr(channel,"permissions_synced") or channel.permissions_synced else "🟦 " if channel.category else "", channel.mention)

    async def _check_lockdown(self, lockdown, ctx):
        # Helper to auto-reply if Lockdown is not configured
        if len(lockdown): return True
        await Message.EmbedText(
            title="Lockdown is not configured!",
            description="You can add channels/categories to the lockdown list with `{}addlock [channel list]`".format(ctx.prefix),
            color=ctx.author
        ).send(ctx)
        return False

    async def _perform_lockdown(self, ctx, target_channels, unlock=False):
        # Helper to lock or unlock channels based on the current context.
        guild = ctx if isinstance(ctx,discord.Guild) else ctx.guild if isinstance(ctx,discord.ext.commands.Context) else None
        if guild is None: return (0,0) # Got sent some wonky values, I guess...
        default_role = guild.default_role
        lockdown = [x for x in target_channels] # Duplicate the list to avoid removing from the original
        categories = channels = 0
        while len(lockdown):
            channel = lockdown.pop(0)
            # Increment counts
            if isinstance(channel,discord.CategoryChannel):
                categories += 1
                # Add all missing channels that do not have synced perms
                new_chans = [x for x in channel.channels if not x in lockdown and (not hasattr(channel,"permissions_synced") or not x.permissions_synced)]
                lockdown.extend(new_chans)
            else:
                channels += 1
                # Check if we even need to update perms based on syncing/category inclusion
                if channel.category and hasattr(channel,"permissions_synced") and channel.permissions_synced and channel.category in target_channels: continue
            overs = channel.overwrites_for(default_role) # Get any overrides for the role
            # Check if we qualify in this channel to (un)lockdown
            if unlock: perm_check  = any(x[0] in self.lockdown_perms and x[1] != None for x in overs)
            else: perm_check = not all([x==False for x in (overs.send_messages,overs.add_reactions,overs.speak)])
            if perm_check: # We qualify - set our perms as needed
                other_perms = any(x[0] not in self.lockdown_perms and x[1] != None for x in overs)
                overs.send_messages = overs.add_reactions = overs.speak = None if unlock else False
                try: await channel.set_permissions(default_role, overwrite=overs if other_perms or not unlock else None)
                except: pass
        return (categories,channels)

    @commands.command()
    async def listlock(self, ctx):
        """Lists the channels and categories configured for lockdown (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        lockdown,channels = self._get_lockdown(ctx)
        if not await self._check_lockdown(lockdown,ctx): return
        desc = "\n".join([self._get_mention(x) for x in channels])
        await Message.EmbedText(title="Current Lockdown List - {:,} Total".format(len(lockdown)),description=desc,color=ctx.author,footer=self.key).send(ctx)

    @commands.command()
    async def listlockall(self, ctx):
        """Lists all channels and categories and their lockdown/sync status (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        lockdown = self.settings.getServerStat(ctx.guild,"LockdownList",[])
        desc = "\n".join([self._get_mention(x,lockdown_list=lockdown,show_lock=True) for x in self._order(ctx,ctx.guild.channels,only_id=False)])
        await Message.EmbedText(title="All Channel Lockdown Status - {:,} Total".format(len(ctx.guild.channels)),description=desc,color=ctx.author,footer=self.key_long).send(ctx)

    @commands.command()
    async def addlock(self, ctx, *, channel_list = None):
        """Adds the passed space-delimited list of channels and categories to the lockdown list (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        lockdown,channels = self._get_lockdown(ctx)
        if not channel_list: return await ctx.send("Usage: `{}addlock [channel list]`".format(ctx.prefix))
        resolved = []
        resolved_id = []
        for channel in channel_list.split():
            c = DisplayName.channelForName(channel,ctx.guild)
            if c and not c.id in lockdown:
                resolved.append(c)
                resolved_id.append(c.id)
            # Also consider child channels as needed
            if isinstance(c,discord.CategoryChannel):
                for c_child in c.channels:
                    if not c_child.id in lockdown:
                        resolved.append(c_child)
                        resolved_id.append(c_child.id)
        if not len(resolved): return await ctx.send("No valid channels passed!\nUsage: `{}addlock [channel list]`".format(ctx.prefix))
        lockdown.extend(resolved_id)
        self.settings.setServerStat(ctx.guild,"LockdownList",lockdown)
        desc = "\n".join([self._get_mention(x) for x in resolved])
        await Message.EmbedText(title="{:,} New Entr{} Added to Lockdown List".format(len(resolved),"y" if len(resolved)==1 else "ies"),description=desc,color=ctx.author,footer=self.key).send(ctx)

    @commands.command()
    async def addlockall(self, ctx):
        """Adds all channels and categories to the lockdown list (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        orphaned,channels = self._verify_lockdown(ctx,[x.id for x in ctx.guild.channels])
        if not len(channels): return await ctx.send("No valid channels found!")
        lockdown = [x.id for x in channels]
        new_lockdown = [x for x in channels if not x.id in self.settings.getServerStat(ctx.guild,"LockdownList",[])]
        self.settings.setServerStat(ctx.guild,"LockdownList",lockdown)
        desc = "\n".join([self._get_mention(x) for x in new_lockdown])
        await Message.EmbedText(title="{:,} New Entr{} Added to Lockdown List".format(len(new_lockdown),"y" if len(new_lockdown)==1 else "ies"),description=desc,color=ctx.author,footer=self.key).send(ctx)

    @commands.command()
    async def remlock(self, ctx, *, channel_list = None):
        """Removes the passed space-delimited list of channels and categories from the lockdown list (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        lockdown,channels = self._get_lockdown(ctx)
        if not await self._check_lockdown(lockdown,ctx): return
        if not channel_list: return await ctx.send("Usage: `{}remlock [channel list]`".format(ctx.prefix))
        resolved = []
        resolved_id = []
        for channel in channel_list.split():
            c = DisplayName.channelForName(channel,ctx.guild)
            if c and c.id in lockdown:
                resolved.append(c)
                resolved_id.append(c.id)
            # Also consider child channels as needed
            if isinstance(c,discord.CategoryChannel):
                for c_child in c.channels:
                    if c_child and c_child.id in lockdown:
                        resolved.append(c_child)
                        resolved_id.append(c_child.id)
        if not len(resolved): return await ctx.send("No valid channels passed!\nUsage: `{}remlock [channel list]`".format(ctx.prefix))
        lockdown = [x for x in lockdown if not x in resolved_id]
        self.settings.setServerStat(ctx.guild,"LockdownList",lockdown)
        desc = "\n".join([self._get_mention(x) for x in resolved])
        await Message.EmbedText(title="{:,} Entr{} Removed from Lockdown List".format(len(resolved),"y" if len(resolved)==1 else "ies"),description=desc,color=ctx.author,footer=self.key).send(ctx)

    @commands.command()
    async def remlockall(self, ctx):
        """Removes all channels and categories from the lockdown list (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        lockdown,channels = self._get_lockdown(ctx)
        if not await self._check_lockdown(lockdown,ctx): return
        self.settings.setServerStat(ctx.guild,"LockdownList",[])
        desc = "\n".join([self._get_mention(x) for x in channels])
        await Message.EmbedText(title="{:,} Entr{} Removed from Lockdown List".format(len(lockdown),"y" if len(lockdown)==1 else "ies"),description=desc,color=ctx.author,footer=self.key).send(ctx)

    @commands.command()
    async def lockdown(self, ctx, target_channel = None):
        """Iterate through the channels in the lockdown list and revoke the send_message, add_reaction, and speak permissions for the everyone role (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        if target_channel:
            c = DisplayName.channelForName(target_channel,ctx.guild)
            if not c: return await ctx.send("The passed value is not a valid channel or category!")
            orphaned,channels = self._verify_lockdown(ctx,c.id)
            lockdown = channels
        else:
            lockdown,channels = self._get_lockdown(ctx)
            if not await self._check_lockdown(lockdown,ctx): return
        message = await Message.EmbedText(
            title="Lockdown",
            description="🔴 Locking down {:,} entr{}...".format(len(lockdown),"y" if len(lockdown)==1 else "ies"),
            color=ctx.author
        ).send(ctx)
        cats,chans = await self._perform_lockdown(ctx,channels)
        if cats==chans==0: return await Message.EmbedText(title="Lockdown",description="**LOCKDOWN FAILED!**").edit(ctx,message)
        await Message.EmbedText(
            title="Lockdown",
            description="🔴 Locked down {}{}.".format(
                "{:,} categor{}".format(cats,"y" if cats==1 else "ies") if cats else "",
                "" if not chans else "{}{:,} channel{}.".format(", " if cats else "",chans,"" if chans==1 else "s")
            )
        ).edit(ctx,message)

    @commands.command()
    async def unlockdown(self, ctx, target_channel = None):
        """Iterate through the channels in the lockdown list and clear the send_message, add_reaction, and speak permissions for the everyone role (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        if target_channel:
            c = DisplayName.channelForName(target_channel,ctx.guild)
            if not c: return await ctx.send("The passed value is not a valid channel or category!")
            orphaned,channels = self._verify_lockdown(ctx,c.id)
            lockdown = channels
        else:
            lockdown,channels = self._get_lockdown(ctx)
            if not await self._check_lockdown(lockdown,ctx): return
        message = await Message.EmbedText(
            title="Unlockdown",
            description="🟢 Unlocking {:,} entr{}...".format(len(lockdown),"y" if len(lockdown)==1 else "ies"),
            color=ctx.author
        ).send(ctx)
        cats,chans = await self._perform_lockdown(ctx,channels,unlock=True)
        if cats==chans==0: return await Message.EmbedText(title="Unlockdown",description="**UNLOCKDOWN FAILED!**").edit(ctx,message)
        await Message.EmbedText(
            title="Unlockdown",
            description="🟢 Unlocked {}{}.".format(
                "{:,} categor{}".format(cats,"y" if cats==1 else "ies") if cats else "",
                "" if not chans else "{}{:,} channel{}.".format(", " if cats else "",chans,"" if chans==1 else "s")
            )
        ).edit(ctx,message)

    async def _anti_raid_respond(self, member):
        response = self.settings.getServerStat(member.guild, "AntiRaidResponse", "kick") # kick, mute, ban
        if response.lower() == "mute":
            mute = self.bot.get_cog("Mute")
            if mute: await mute._mute(member, member.guild)
        elif response.lower() == "ban": await member.guild.ban(member, reason="Anti-raid active")
        else: await member.guild.kick(member, reason="Anti-raid active") # Assume kick if nothing specified

    @commands.Cog.listener()	
    async def on_member_join(self, member):
        if not self.settings.getServerStat(member.guild, "AntiRaidEnabled", False): return # Not enabled, ignore
        if self.settings.getServerStat(member.guild, "AntiRaidActive", False):
            # Currently in anti-raid mode, find out what to do with the new join
            ar_cooldown = self.settings.getServerStat(member.guild, "AntiRaidCooldown", 600) # 10 minute default
            ar_lastjoin = self.settings.getServerStat(member.guild, "AntiRaidLastJoin", 0)
            if time.time() - ar_lastjoin >= ar_cooldown: # No longer watching - disable anti-raid
                self.settings.setServerStat(member.guild, "AntiRaidActive", False)
            else: # Gather our response to the new user and put it into effect
                await self._anti_raid_respond(member)
            # Save the last join timestamp in the anti-raid list
            self.settings.setServerStat(member.guild, "AntiRaidLastJoin", time.time())
        # Gather the settings and go from there
        ar_joins = self.settings.getServerStat(member.guild, "AntiRaidJoins", [])
        ar_maxj  = self.settings.getServerStat(member.guild, "AntiRaidMax", 10)
        ar_time  = self.settings.getServerStat(member.guild, "AntiRaidTime", 10)
        ar_joins.insert(0,(member.id,time.time())) # Add (mem_id,timestamp) to the front of the list
        ar_joins = ar_joins[:ar_maxj] # Ensure the list is only as long as the max joins allowed
        self.settings.setServerStat(member.guild, "AntiRaidJoins", ar_joins) # Save the updated list
        if len(ar_joins) < ar_maxj: return # List isn't long enough to consider - bail
        # Compare the first and last join times to the threshold
        if ar_joins[0][1] - ar_joins[-1][1] <= ar_time: # Enable anti-raid!
            if not self.settings.getServerStat(member.guild, "AntiRaidActive", False):
                self.settings.setServerStat(member.guild, "AntiRaidActive", True)
                mention = self.settings.getServerStat(member.guild, "AntiRaidPing", None)
                if mention:
                    m = DisplayName.memberForName(mention, member.guild)
                    if not m: m = DisplayName.roleForName(mention, member.guild)
                    if m: # Got a member or role - let's get the channel
                        channel = self.settings.getServerStat(member.guild, "AntiRaidChannel", None)
                        if channel:
                            c = DisplayName.channelForName(channel, member.guild)
                            if c: # Got a member/role and a channel - try to post the ping
                                try: await c.send("{} - Anti-raid has been enabled!".format(m.mention))
                                except: pass
            self.settings.setServerStat(member.guild, "AntiRaidLastJoin", time.time())
            for m_id,t in ar_joins:
                # Resolve the ids and react accordingly
                m = member.guild.get_member(m_id)
                if m: await self._anti_raid_respond(m)

    @commands.command()
    async def antiraid(self, ctx, *, on_off = None, join_number = None, join_seconds = None, kick_ban_mute = None, cooldown_minutes = None):
        """Sets up the anti-raid module (bot-admin only).
        Options:

            on_off:           Enables or disables anti-raid detection
            join_number:      The number of members that need to join within the threshold to enable anti-raid (2-100)
            join_seconds:     The seconds threshold for the number of members specified in join_number to enable anti-raid (2-100)
            kick_ban_mute:    The response the bot should take for all members that join during anti-raid (including those in the threshold)
            cooldown_minutes: The number of minutes with no joins before anti-raid is disabled (2-100)
        
        Example:

            $antiraid on 10 8 kick 5

            This would result in anti-raid being active, and if 10 users join in 8 seconds, anti-raid will enable and auto-kick any users
            that join (including those that joined during the original 8 second threshold) until the 5 minute cooldown has elapsed with
            no new joins."""
        
        if not await Utils.is_bot_admin_reply(ctx): return
        usage = "Usage: `{}antiraid on_off join_number join_seconds kick_ban_mute cooldown_minutes`".format(ctx.prefix)
        if on_off == None: # Gather settings and report the current
            on_off = self.settings.getServerStat(ctx.guild, "AntiRaidEnabled", False)
            if not on_off: return await ctx.send("Anti-raid is currently disabled.")
            # Check if we're past the cooldown - and adjust accordingly
            cooldown_minutes = self.settings.getServerStat(ctx.guild, "AntiRaidCooldown", 600) # 10 minute default
            ar_lastjoin = self.settings.getServerStat(ctx.guild, "AntiRaidLastJoin", 0)
            if time.time() - ar_lastjoin >= cooldown_minutes: self.settings.setServerStat(ctx.guild, "AntiRaidActive", False) # No longer watching - disable anti-raid
            active = self.settings.getServerStat(ctx.guild, "AntiRaidActive", False)
            join_number = self.settings.getServerStat(ctx.guild, "AntiRaidMax", 10)
            join_seconds = self.settings.getServerStat(ctx.guild, "AntiRaidTime", 10)
            kick_ban_mute = self.settings.getServerStat(ctx.guild, "AntiRaidResponse", "kick")
            return await ctx.send("Anti-raid protection enabled and currently **{}** with settings:\n\nIf {:,} users join within {:,} seconds, then I will {} all new users until {} minutes have elapsed without joins.".format(
                "active" if active else "inactive",
                join_number,
                join_seconds,
                kick_ban_mute.lower(),
                int(cooldown_minutes/60)
            )) 
        if on_off.lower() in ("off", "no", "disable", "disabled", "false"):
            self.settings.setServerStat(ctx.guild, "AntiRaidEnabled", False)
            self.settings.setServerStat(ctx.guild, "AntiRaidJoins", [])
            self.settings.setServerStat(ctx.guild, "AntiRaidLastJoin", 0)
            return await ctx.send("Anti-raid is disabled!")
        try: # Split and convert as needed
            on_off, join_number, join_seconds, kick_ban_mute, cooldown_minutes = on_off.split()
            join_number, join_seconds, cooldown_minutes = int(join_number), int(join_seconds), int(cooldown_minutes)
        except:
            return await ctx.send(usage)
        # We should have adequate values here - let's ensure limits though
        if on_off.lower() in ("off", "no", "disable", "disabled", "false"):
            self.settings.setServerStat(ctx.guild, "AntiRaidEnabled", False)
            return await ctx.send("Anti-raid is disabled!")
        elif not on_off.lower() in ("on", "yes", "enable", "enabled", "true"):
            return await ctx.send(usage)
        # We're enabling - qualify the rest of the values
        if any((100 < x or 2 > x for x in (join_number, join_seconds, cooldown_minutes))):
            return await ctx.send("All numerical values must be between 2-100.")
        if not kick_ban_mute.lower() in ("kick","ban","mute"):
            return await ctx.send("Unknown kick_ban_mute value - can only be kick, ban, or mute.")
        # Values should be qualified - let's save them
        self.settings.setServerStat(ctx.guild, "AntiRaidEnabled", True)
        self.settings.setServerStat(ctx.guild, "AntiRaidMax", join_number)
        self.settings.setServerStat(ctx.guild, "AntiRaidTime", join_seconds)
        self.settings.setServerStat(ctx.guild, "AntiRaidResponse", kick_ban_mute.lower())
        self.settings.setServerStat(ctx.guild, "AntiRaidCooldown", cooldown_minutes*60)
        self.settings.setServerStat(ctx.guild, "AntiRaidActive", False)
        await ctx.send("Anti-raid protection enabled with the following settings:\n\nIf {:,} members join within {:,} seconds, I will {} all new members until {} minutes have elapsed without joins.".format(
            join_number,
            join_seconds,
            kick_ban_mute.lower(),
            cooldown_minutes
        )) 

    @commands.command()
    async def antiraidping(self, ctx, user_or_role = None, channel = None):
        """Sets up what user or role to ping and in what channel when anti-raid is activated (bot-admin only)."""

        if not await Utils.is_bot_admin_reply(ctx): return
        if user_or_role == None: # print the settings
            user_role = self.settings.getServerStat(ctx.guild, "AntiRaidPing", None)
            if user_role:
                u = DisplayName.memberForName(user_role, ctx.guild)
                if not u: u = DisplayName.roleForName(user_role, ctx.guild)
                user_role = u
            chan = self.settings.getServerStat(ctx.guild, "AntiRaidChannel", None)
            if chan: chan = DisplayName.channelForName(chan, ctx.guild)
            if not user_role or not chan: return await ctx.send("Anti-raid ping is not setup.")
            return await ctx.send("Anti-raid activity will mention {} and be announced in {}!".format(DisplayName.name(user_role),chan.mention))
        if channel == None: return await ctx.send("Usage: `{}antiraidping user_or_role channel`".format(ctx.prefix))
        # We're setting it up - let's check the user first, then role, then channel
        ur = DisplayName.memberForName(user_or_role, ctx.guild)
        if not ur: ur = DisplayName.roleForName(user_or_role, ctx.guild)
        if not ur: return await ctx.send("I couldn't find that user or role.")
        ch = DisplayName.channelForName(channel, ctx.guild)
        if not ch: return await ctx.send("I couldn't find that channel.")
        # Got them! - Save and report
        self.settings.setServerStat(ctx.guild, "AntiRaidPing", ur.id)
        self.settings.setServerStat(ctx.guild, "AntiRaidChannel", ch.id)
        return await ctx.send("Anti-raid activity will mention {} and be announced in {}!".format(DisplayName.name(ur),ch.mention))
