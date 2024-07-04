import discord, time, re
from discord.ext import commands
from datetime import timedelta
from Cogs import Utils, DisplayName, Message, Nullify, PickList

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

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or not message.content or message.author.bot:
            # We need a guild, some message contents, and for the author to be a person
            return
        # Check if we have an admin/bot-admin author and bail - they should be trusted
        ctx = await self.bot.get_context(message)
        if Utils.is_bot_admin(ctx):
            return
        spam_rules = self.settings.getServerStat(message.guild,"SpamRules",[])
        if not spam_rules: # Not set up, bail
            return
        # Let's ensure they're ordered by severity
        spam_rules.sort(key=lambda x:x.get("time_out",0),reverse=True)
        # Figure out the farthest message back we need to be aware of
        timestamp = time.time()
        max_time  = max(spam_rules, key=lambda x:x.get("time_frame",-1)).get("time_frame")
        if max_time is None:
            return # broken somehow
        author_messages = self.settings.getUserStat(message.author,message.guild,"MessageHashes",[])
        valid_messages  = [x for x in author_messages if timestamp-x.get("timestamp",-1) <= max_time]
        message_check = {"hash":hash(message.content),"timestamp":timestamp,"channel":message.channel.id}
        # Walk the valid messages and check our rules
        for rule in spam_rules:
            # Spam rules are a dict with the following:
            # "time_frame" : number of seconds old (float) a message can be to consider it
            # "channels"   : minimum number of channels they have to span
            # "messages"   : minimum number of messages they have to send
            # "time_out"   : number of seconds (float) to time the user out for spamming
            # "same"       : bool that denotes if the messages considered have to be the same
            # "in_a_row"   : bool that denotes if the messages have to be the same, and sent in a row
            #
            # Verify we have what we need and then parse the messages in this rule's context
            if not (isinstance(rule.get("messages"),int) and rule["messages"] > 1):
                # Something is not right - we need *at least* the message count
                continue
            time_frame = rule.get("time_frame",0)
            if not isinstance(time_frame,(float,int)) or time_frame <= 0:
                # Botched time frame - bail on this rule
                continue
            time_out = rule.get("time_out",0)
            if not isinstance(time_out,(float,int)) or time_out <= 0:
                # Botched time out - bail on this rule
                continue
            check_channels = isinstance(rule.get("channels"),int) and rule["channels"] > 0
            rule_messages = []
            rule_channels = []
            # Walk them in reverse - from newest to oldest
            for m in valid_messages[::-1]:
                if timestamp-m.get("timestamp",-1) > time_frame:
                    break # Assume everything this message and after will be older
                if rule.get("same"):
                    if rule.get("in_a_row"):
                        if m.get("hash") != message_check.get("hash",False):
                            break # Bail on the first non-match
                        rule_messages.append(m)
                    elif m.get("hash") == message_check.get("hash",False):
                        rule_messages.append(m)
                else:
                    # They don't have to be the same - just verifying timestamps
                    rule_messages.append(m)
                # Add the channel if we haven't seen it before
                if check_channels and m.get("channel") and not m["channel"] in rule_channels:
                    rule_channels.append(m["channel"])
            # Add our message and channel as needed
            rule_messages.append(message_check)
            if check_channels and not message.channel.id in rule_channels:
                rule_channels.append(message.channel.id)
            # Check the channel count
            if check_channels and len(rule_channels) < rule.get("channels",0):
                # Watching channel count - but we didn't exceed it
                continue
            # Check the message count
            if rule.get("messages") and len(rule_messages) < rule["messages"]:
                # Watching message count - but didn't exceed it
                continue
            # At this point - we're spamming per this rule - we should attempt to
            # time the user out, then delete the message that tripped the filter
            # Build our reason string
            reason = "Spam: Sent {:,}{} message{}{}{} within {:,} second{}".format(
                len(rule_messages),
                " identical" if rule.get("same") else "",
                "" if len(rule_messages) == 1 else "s",
                " in a row" if rule.get("same") and rule.get("in_a_row") else "",
                "" if not check_channels else " in {:,} channel{}".format(
                    len(rule_channels),
                    "" if len(rule_channels) == 1 else "s"
                ),
                time_frame,
                "" if time_frame == 1 else "s"
            )
            try: await message.author.timeout_for(timedelta(seconds=time_out),reason=reason)
            except: pass
            try: await message.delete()
            except: pass
            # Leave the loop - we had a match
            break
        # Ensure we update our message hashes
        self.settings.setUserStat(message.author,message.guild,"MessageHashes",valid_messages+[message_check])

    @commands.command(aliases=["spamlist","spam"])
    async def listspam(self, ctx):
        """Lists the spam filter rules (bot-admin only)."""

        if not await Utils.is_bot_admin_reply(ctx): return
        spam_rules = self.settings.getServerStat(ctx.guild,"SpamRules",[])
        if not spam_rules:
            return await ctx.send("No spam filter rules setup!  You can use the `{}addspam` command to add some.".format(ctx.prefix))
        entries = []
        # Walk the entries in order of time_out severity
        for i,rule in enumerate(sorted(spam_rules,key=lambda x:x.get("time_out",0),reverse=True),start=1):
            name = "{}. {:,} second time-out:".format(i,rule.get("time_out",0))
            val  = "**Trigger:** {:,}{} message{} sent{}{} within {:,} second{}\n**Args:** `{}`".format(
                rule.get("messages",0),
                " identical" if rule.get("same") else "",
                "" if rule.get("messages",0) == 1 else "s",
                " in a row" if rule.get("same") and rule.get("in_a_row") else "",
                "" if not rule.get("channels",0) else " in {:,} or more channel{}".format(
                    rule["channels"],
                    "" if rule["channels"] == 1 else "s"
                ),
                rule.get("time_frame",0),
                "" if rule.get("time_frame",0) == 1 else "s",
                "-messages {} -channels {} -timeframe {} -timeout {}{}".format(
                    rule.get("messages",-1),
                    rule.get("channels",-1),
                    rule.get("time_frame",-1),
                    rule.get("time_out",-1),
                    " -inarow" if rule.get("in_a_row") else " -same" if rule.get("same") else ""
                )
            )
            entries.append({"name":name,"value":val})
        return await PickList.PagePicker(title="Current Spam Filters ({:,} total)".format(len(entries)),list=entries,ctx=ctx).pick()

    @commands.command(aliases=["spamclear"])
    async def clearspam(self, ctx):
        """Clears all spam filter rules (bot-admin only)."""

        if not await Utils.is_bot_admin_reply(ctx): return
        self.settings.setServerStat(ctx.guild,"SpamRules",[])
        await ctx.send("All spam filter rules have been cleared!")

    @commands.command(aliases=["removespam","spamrem","spamremove"])
    async def remspam(self, ctx, rule_index = None):
        """Removes the spam filter rule at the passed index (bot-admin only)."""

        if not await Utils.is_bot_admin_reply(ctx): return
        spam_rules = self.settings.getServerStat(ctx.guild,"SpamRules",[])
        if not spam_rules:
            return await ctx.send("No spam filter rules setup!  You can use the `{}addspam` command to add some.".format(ctx.prefix))
        try:
            rule_index = int(rule_index)
            assert 0 < rule_index <= len(spam_rules)
        except:
            return await ctx.send("You need to pass a valid integer from 1 to {:,}.\nYou can get a numbered list with `{}listspam`".format(len(spam_rules),ctx.prefix))
        # Got our index - let's sort by severity and then remove it
        spam_rules.sort(key=lambda x:x.get("time_out",0),reverse=True)
        del spam_rules[rule_index-1]
        self.settings.setServerStat(ctx.guild,"SpamRules",spam_rules)
        await ctx.send("Spam filter rule removed!")
    
    @commands.command(aliases=["spamadd","newspam","spamnew"])
    async def addspam(self, ctx, *, rule = None):
        """Adds a new spam filter rule (bot-admin only).
        Rules can be a space delimited list of the following:

        -messages #    (# = the number of messages for the rule to consider; 2-50)
        -channels #    (# = the number of channels for the rule to consider; 1-50)
        -timeframe #   (# = the number of seconds for the rule to consider; > 0)
        -timeout #     (# = the number of seconds to time the user out for spamming; > 0)
        -same          (only consider messages that have the same hash)
        -inarow        (only consider messages taht have the same hash in a row; implies -same)

        e.g. To create a spam filter rule that watches for a user sending 2 or more idential
        messages in a row across 2 or more channels within 5 seconds - resulting in them being
        timed out for 5 minutes, we can use the following:

        $addspam -messages 2 -channels 2 -timeframe 5 -timeout 300 -inarow"""

        if not await Utils.is_bot_admin_reply(ctx): return
        if rule is None:
            return await ctx.send("Usage: `{}addspam -messages # -channels # -timeframe # -timeout # -same/-inarow`".format(ctx.prefix))
        # Set up some regex arg parsing
        match_dict = {
            "messages"  : re.compile(r"(?i)-?m(ess(age|ages)?)?"),
            "channels"  : re.compile(r"(?i)-?(c(h|han|hannels?)?)"),
            "time_frame": re.compile(r"(?i)-?(tf|time-?f(rame)?)"),
            "time_out"  : re.compile(r"(?i)-?(to|time-?o(ut)?)"),
            "same"      : re.compile(r"(?i)-?s(ame)?"),
            "in_a_row"  : re.compile(r"(?i)-?i(ar|n-?a-?row)?")
        }
        # Get the arg order for those that don't *require* the switches
        arg_order = list(match_dict)[:-2]
        # Set up placeholders
        arg_dict = {
            "messages"  : 0,
            "channels"  : 1,
            "time_frame": 0,
            "time_out"  : 0,
            "same"      : False,
            "in_a_row"  : False
        }
        # Walk our args
        last_arg = None
        for i,arg in enumerate(rule.split(),start=1):
            if not arg: continue # Skip empty args, if any
            # Check if it's a float/int
            arg_float = arg_int = None
            try:
                arg_float = float(arg)
                arg_int = int(arg_float)
            except:
                pass
            # If we got a float/int value, check if we have a last_arg
            # and if so - use that.  If not - use the next in the order
            if arg_float is not None:
                try:
                    resolved = last_arg or arg_order[0]
                except IndexError:
                    # We got something we didn't expect
                    return await ctx.send("Could not parse '{}' at {}".format(Nullify.escape_all(arg),i))
            else:
                # Resolve it to either an arg match - or in-order as needed
                resolved = next((x for x in match_dict if match_dict[x].fullmatch(arg)),None)
                if not resolved:
                    return await ctx.send("Unknown argument '{}' at {}".format(Nullify.escape_all(arg),i))
            last_arg = None
            # Make sure we have a valid value for the arg
            if resolved == "same":
                arg_dict["same"] = True
            elif resolved == "in_a_row":
                arg_dict["same"] = arg_dict["in_a_row"] = True
            elif arg_float is None:
                # No value - just the arg - set it and continue
                last_arg = resolved
            else:
                # We got a value - let's set it, clear last_arg, and
                # remove resolved from our arg_order
                arg_dict[resolved] = arg_float if resolved == "time_frame" else arg_int
                try: arg_order.remove(resolved)
                except: pass
        if not 2 <= arg_dict["messages"] <= 50:
            return await ctx.send("`-messages` must be an integer from 2 to 50")
        if not 1 <= arg_dict["channels"] <= 50:
            return await ctx.send("`-channels` must be an integer from 1 to 50")
        if arg_dict["time_frame"] <= 0:
            return await ctx.send("`-timeframe` must be greater than 0")
        if arg_dict["time_out"] <= 0:
            return await ctx.send("`-timeout` must be greater than 0")
        spam_rules = self.settings.getServerStat(ctx.guild,"SpamRules",[])
        # Let's see if we have the same requirements in another rule - and just replace it
        spam_rules_checked = [x for x in spam_rules if not all((x.get(y)==arg_dict[y] for y in ("messages","channels","time_frame","same","in_a_row")))]
        self.settings.setServerStat(ctx.guild,"SpamRules",spam_rules_checked+[arg_dict])
        if len(spam_rules) != len(spam_rules_checked):
            await ctx.send("Spam filter rule updated!")
        else:
            await ctx.send("Spam filter rule added!")

    @commands.command()
    async def listlock(self, ctx):
        """Lists the channels and categories configured for lockdown (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        lockdown,channels = self._get_lockdown(ctx)
        if not await self._check_lockdown(lockdown,ctx): return
        desc = "\n".join([self._get_mention(x) for x in channels])
        with open("lock.txt","wb") as f:
            f.write(desc.encode("utf-8"))
        await PickList.PagePicker(
            title="Current Lockdown List - {:,} Total".format(len(lockdown)),
            description=desc,
            color=ctx.author,
            footer=self.key,
            ctx=ctx
        ).pick()

    @commands.command()
    async def listlockall(self, ctx):
        """Lists all channels and categories and their lockdown/sync status (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        lockdown = self.settings.getServerStat(ctx.guild,"LockdownList",[])
        desc = "\n".join([self._get_mention(x,lockdown_list=lockdown,show_lock=True) for x in self._order(ctx,ctx.guild.channels,only_id=False)])
        await PickList.PagePicker(
            title="All Channel Lockdown Status - {:,} Total".format(len(ctx.guild.channels)),
            description=desc,
            color=ctx.author,
            footer=self.key_long,
            ctx=ctx
        ).pick()

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
        await PickList.PagePicker(
            title="{:,} New Entr{} Added to Lockdown List".format(len(resolved),"y" if len(resolved)==1 else "ies"),
            description=desc,
            color=ctx.author,
            footer=self.key,
            ctx=ctx
        ).pick()

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
        await PickList.PagePicker(
            title="{:,} New Entr{} Added to Lockdown List".format(len(new_lockdown),"y" if len(new_lockdown)==1 else "ies"),
            description=desc,
            color=ctx.author,
            footer=self.key,
            ctx=ctx
        ).pick()

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
        await PickList.PagePicker(
            title="{:,} New Entr{} Removed from Lockdown List".format(len(resolved),"y" if len(resolved)==1 else "ies"),
            description=desc,
            color=ctx.author,
            footer=self.key,
            ctx=ctx
        ).pick()

    @commands.command()
    async def remlockall(self, ctx):
        """Removes all channels and categories from the lockdown list (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return
        lockdown,channels = self._get_lockdown(ctx)
        if not await self._check_lockdown(lockdown,ctx): return
        self.settings.setServerStat(ctx.guild,"LockdownList",[])
        desc = "\n".join([self._get_mention(x) for x in channels])
        await PickList.PagePicker(
            title="{:,} New Entr{} Removed from Lockdown List".format(len(lockdown),"y" if len(lockdown)==1 else "ies"),
            description=desc,
            color=ctx.author,
            footer=self.key,
            ctx=ctx
        ).pick()

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

    async def _anti_raid_respond(self, member, response = "kick", reason = "Anti-raid active"):
        if response.lower() == "mute":
            mute = self.bot.get_cog("Mute")
            if mute: await mute._mute(member, member.guild)
        else:
            action = member.guild.ban if response.lower() == "ban" else member.guild.kick
            try: await action(member, reason=reason)
            except: pass

    @commands.Cog.listener()	
    async def on_member_join(self, member):
        name_filters = self.settings.getServerStat(member.guild, "NameFilters", {})
        # See if the new join matches any of the name filters
        r = 0
        r_levels = (None,"mute","kick","ban")
        for trigger in name_filters:
            match = re.fullmatch(trigger, member.name)
            if not match: continue
            # Retain the highest level
            try: trigger_level = r_levels.index(name_filters[trigger].lower())
            except: continue # Unknown response
            if trigger_level < r: continue # Not a more severe punishment - bypass
            r = trigger_level # Set it as we incremented punishment
        # Check if we have a punishment, and send it along
        if r_levels[r]: await self._anti_raid_respond(member,response=r_levels[r],reason="Name filter match")
        if not self.settings.getServerStat(member.guild, "AntiRaidEnabled", False): return # Not enabled, ignore
        ar_response = self.settings.getServerStat(member.guild, "AntiRaidResponse", "kick")
        if self.settings.getServerStat(member.guild, "AntiRaidActive", False):
            # Currently in anti-raid mode, find out what to do with the new join
            ar_cooldown = self.settings.getServerStat(member.guild, "AntiRaidCooldown", 600) # 10 minute default
            ar_lastjoin = self.settings.getServerStat(member.guild, "AntiRaidLastJoin", 0)
            if time.time() - ar_lastjoin >= ar_cooldown: # No longer watching - disable anti-raid
                self.settings.setServerStat(member.guild, "AntiRaidActive", False)
            else: # Gather our response to the new user and put it into effect
                await self._anti_raid_respond(member,response=ar_response)
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
                                try: await c.send("{} - Anti-raid has been enabled!".format(m.mention),allowed_mentions=discord.AllowedMentions.all())
                                except: pass
            self.settings.setServerStat(member.guild, "AntiRaidLastJoin", time.time())
            for m_id,t in ar_joins:
                # Resolve the ids and react accordingly
                m = member.guild.get_member(m_id)
                if m: await self._anti_raid_respond(m,response=ar_response)

    @commands.command()
    async def addnamefilter(self, ctx, action = None, *, regex = None):
        """Adds a new action (kick|ban|mute) and regex name filter (bot-admin only).
        
        Example:  $addnamefilter ban (?i)baduser.*
        
        This would look for a user joining with a name that starts with "baduser" (case-insensitive) and ban them.
        """

        if not await Utils.is_bot_admin_reply(ctx): return
        if not action or not regex or not action.lower() in ("kick","ban","mute"): return await ctx.send("Usage: `{}addnamefilter action regex`".format(ctx.prefix))
        # Ensure the regex is valid
        try: re.compile(regex)
        except Exception as e: return await ctx.send(Nullify.escape_all(str(e)))
        # Save the trigger and response
        name_filters = self.settings.getServerStat(ctx.guild, "NameFilters", {})
        context = "Updated" if regex in name_filters else "Added new"
        name_filters[regex] = action
        self.settings.setServerStat(ctx.guild, "NameFilters", name_filters)
        return await ctx.send("{} name filter!".format(context))

    @commands.command()
    async def namefilters(self, ctx):
        """Lists the name filters and their actions (bot-admin only)."""
        
        if not await Utils.is_bot_admin_reply(ctx): return
        name_filters = self.settings.getServerStat(ctx.guild, "NameFilters", {})
        if not name_filters: return await ctx.send("No name filters setup!  You can use the `{}addnamefilter` command to add some.".format(ctx.prefix))
        entries = [{"name":"{}. ".format(i)+Nullify.escape_all(x),"value":name_filters[x].capitalize()} for i,x in enumerate(name_filters,start=1)]
        return await PickList.PagePicker(title="Current Name Filters",list=entries,ctx=ctx).pick()

    @commands.command()
    async def remnamefilter(self, ctx, *, name_filter_number = None):
        """Removes the passed name filter (bot-admin only)."""
        
        if not await Utils.is_bot_admin_reply(ctx): return
        if not name_filter_number: return await ctx.send("Usage: `{}remnamefilter name_filter_number`\nYou can get a numbered list with `{}namefilters`".format(ctx.prefix,ctx.prefix))
        name_filters = self.settings.getServerStat(ctx.guild, "NameFilters", {})
        if not name_filters: return await ctx.send("No name filters setup!  You can use the `{}addnamefilter` command to add some.".format(ctx.prefix))
        # Make sure we got a number, and it's within our list range
        try:
            name_filter_number = int(name_filter_number)
            assert 0 < name_filter_number <= len(name_filters)
        except:
            return await ctx.send("You need to pass a valid number from 1 to {:,}.\nYou can get a numbered list with `{}namefilters`".format(len(name_filters),ctx.prefix))
        # Remove it, save, and report
        name_filters.pop(list(name_filters)[name_filter_number-1],None)
        self.settings.setServerStat(ctx.guild, "NameFilters", name_filters)
        return await ctx.send("Name filter removed!")

    @commands.command()
    async def clearnamefilters(self, ctx):
        """Removes all name filters (bot-admin only)."""

        if not await Utils.is_bot_admin_reply(ctx): return
        self.settings.setServerStat(ctx.guild, "NameFilters", {})
        return await ctx.send("All name filters removed!")

    @commands.command()
    async def antiraid(self, ctx, *, on_off = None, join_number = None, join_seconds = None, kick_ban_mute = None, cooldown_minutes = None):
        """Sets up the anti-raid module (bot-admin only).
        Options:

            on_off:           Enables or disables anti-raid detection
            join_number:      The number of members that need to join within the threshold to enable anti-raid (2-100)
            join_seconds:     The seconds threshold for the number of members specified in join_number to enable anti-raid (1-600)
            kick_ban_mute:    The response the bot should take for all members that join during anti-raid (including those in the threshold)
            cooldown_minutes: The number of minutes with no joins before anti-raid is disabled (1-100)
        
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
        if on_off.split()[0].lower() in ("off", "no", "disable", "disabled", "false"):
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
        if not on_off.lower() in ("on", "yes", "enable", "enabled", "true"):
            return await ctx.send(usage)
        # We're enabling - qualify the rest of the values
        if not 2 <= join_number <= 100:
            return await ctx.send("`join_number` must be between 2-100.")
        if not 1 <= join_seconds <= 600:
            return await ctx.send("`join_seconds` must be between 1-600.")
        if not 1 <= cooldown_minutes <= 100:
            return await ctx.send("`cooldown_minutes` must be between 1-100.")
        if not kick_ban_mute.lower() in ("kick","ban","mute"):
            return await ctx.send("Unknown `kick_ban_mute` value - can only be `kick`, `ban`, or `mute`.")
        # Values should be qualified - let's save them
        self.settings.setServerStat(ctx.guild, "AntiRaidEnabled", True)
        self.settings.setServerStat(ctx.guild, "AntiRaidMax", join_number)
        self.settings.setServerStat(ctx.guild, "AntiRaidTime", join_seconds)
        self.settings.setServerStat(ctx.guild, "AntiRaidResponse", kick_ban_mute.lower())
        self.settings.setServerStat(ctx.guild, "AntiRaidCooldown", cooldown_minutes*60)
        self.settings.setServerStat(ctx.guild, "AntiRaidActive", False)
        await ctx.send("Anti-raid protection enabled with the following settings:\n\nIf {:,} members join within {:,} second{}, I will {} all new members until {} minute{} elapsed without joins.".format(
            join_number,
            join_seconds,
            "" if join_seconds==1 else "s",
            kick_ban_mute.lower(),
            cooldown_minutes,
            " has" if cooldown_minutes==1 else "s have"
        )) 

    @commands.command()
    async def antiraidping(self, ctx, user_or_role = None, channel = None):
        """Sets up what user or role to ping and in what channel when anti-raid is activated.  Can be disabled by passing "off" to this command (bot-admin only)."""

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
            return await ctx.send("Anti-raid activity will mention {} and be announced in {}!".format(Nullify.escape_all(user_role.display_name) if isinstance(user_role, discord.Member) else Nullify.escape_all(user_role.name),chan.mention))
        if channel == None:
            if user_or_role.lower() in ("no","off","disable","disabled","none","false"): # Disable the ping
                self.settings.setServerStat(ctx.guild, "AntiRaidPing", None)
                self.settings.setServerStat(ctx.guild, "AntiRaidChannel", None)
                return await ctx.send("Anti-raid activity will not mention any user or role!")
            # If we got here, we just got some unsupported values, send the usage
            return await ctx.send("Usage: `{}antiraidping user_or_role channel`".format(ctx.prefix))
        # We're setting it up - let's check the user first, then role, then channel
        ur = DisplayName.memberForName(user_or_role, ctx.guild)
        if not ur: ur = DisplayName.roleForName(user_or_role, ctx.guild)
        if not ur: return await ctx.send("I couldn't find that user or role.")
        ch = DisplayName.channelForName(channel, ctx.guild)
        if not ch: return await ctx.send("I couldn't find that channel.")
        # Got them! - Save and report
        self.settings.setServerStat(ctx.guild, "AntiRaidPing", ur.id)
        self.settings.setServerStat(ctx.guild, "AntiRaidChannel", ch.id)
        return await ctx.send("Anti-raid activity will mention {} and be announced in {}!".format(Nullify.escape_all(ur.display_name) if isinstance(ur, discord.Member) else Nullify.escape_all(ur.name),ch.mention))
