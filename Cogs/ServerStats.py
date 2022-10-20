import asyncio, discord
from   discord.ext import commands
from   Cogs        import Nullify, DisplayName, Message, PickList

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(ServerStats(bot, settings))

class ServerStats(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    async def message(self, message):
        # Check the message and see if we should allow it - always yes.
        # This module doesn't need to cancel messages.

        # Don't count your own, Pooter
        if not message.author.id == self.bot.user.id:
            server = message.guild
            messages = int(self.settings.getServerStat(server, "TotalMessages"))
            if messages == None:
                messages = 0
            messages += 1
            self.settings.setServerStat(server, "TotalMessages", messages)
            
        return { 'Ignore' : False, 'Delete' : False}

    @commands.command()
    async def listbots(self, ctx, *, guild_name = None):
        """Lists up to the first 20 bots of the current or passed server."""
        # Check if we passed another guild
        guild = None
        if guild_name == None:
            guild = ctx.guild
        else:
            for g in self.bot.guilds:
                if g.name.lower() == guild_name.lower():
                    guild = g
                    break
                if str(g.id) == str(guild_name):
                    guild = g
                    break
        if guild == None:
            # We didn't find it
            await ctx.send("I couldn't find that guild...")
            return
        bot_list = [x for x in guild.members if x.bot]
        if not len(bot_list):
            # No bots - should... never... happen.
            await Message.EmbedText(title=guild.name, description="This server has no bots.", color=ctx.author).send(ctx)
        else:
            # Got some bots!
            fields = [{"name":"{:,}. {}#{} ({})".format(i,x.name,x.discriminator,x.id),"value":x.mention,"inline":False} for i,x in enumerate(bot_list,1)]
            header = "__**Showing {:,} bot{}:**__".format(len(bot_list), "" if len(bot_list) == 1 else "s")
            return await PickList.PagePicker(
                title="Bots in {} ({:,} total)".format(guild.name,len(bot_list)),
                list=fields,
                ctx=ctx
            ).pick()

    @commands.command()
    async def serverinfo(self, ctx, *, guild_name = None):
        """Lists some info about the current or passed server."""
        
        # Check if we passed another guild
        guild = None
        if guild_name == None:
            guild = ctx.guild
        else:
            for g in self.bot.guilds:
                if g.name.lower() == guild_name.lower():
                    guild = g
                    break
                if str(g.id) == str(guild_name):
                    guild = g
                    break
        if guild == None:
            # We didn't find it
            await ctx.send("I couldn't find that guild...")
            return
        
        server_embed = discord.Embed(color=ctx.author.color)
        server_embed.title = guild.name
        
        # Get localized user time
        created = "Unknown"
        if guild.created_at:
            ts = int(guild.created_at.timestamp())
            created = "<t:{}> (<t:{}:R>)".format(ts,ts)
        server_embed.description = "Created: {}".format(created)
        online_members = 0
        bot_member     = 0
        bot_online     = 0
        for member in guild.members:
            if member.bot:
                bot_member += 1
                if not member.status == discord.Status.offline:
                        bot_online += 1
                continue
            if not member.status == discord.Status.offline:
                online_members += 1
        # bot_percent = "{:,g}%".format((bot_member/len(guild.members))*100)
        user_string = "{:,}/{:,} online ({:,g}%)".format(
                online_members,
                len(guild.members) - bot_member,
                round((online_members/(len(guild.members) - bot_member) * 100), 2)
        )
        b_string = "bot" if bot_member == 1 else "bots"
        user_string += "\n{:,}/{:,} {} online ({:,g}%)".format(
                bot_online,
                bot_member,
                b_string,
                round((bot_online/bot_member)*100, 2)
        )
        #server_embed.add_field(name="Members", value="{:,}/{:,} online ({:.2f}%)\n{:,} {} ({}%)".format(online_members, len(guild.members), bot_percent), inline=True)
        server_embed.add_field(name="Members ({:,} total)".format(len(guild.members)), value=user_string, inline=True)
        server_embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        chandesc = "{:,} text, {:,} voice".format(len(guild.text_channels), len(guild.voice_channels))
        server_embed.add_field(name="Channels", value=chandesc, inline=True)
        server_embed.add_field(name="Default Role", value=guild.default_role, inline=True)
        server_embed.add_field(name="Owner", value=guild.owner.name + "#" + guild.owner.discriminator, inline=True)
        server_embed.add_field(name="AFK Channel", value=guild.afk_channel, inline=True)
        server_embed.add_field(name="Verification", value=str(guild.verification_level).capitalize(), inline=True)
        # server_embed.add_field(name="Voice Region", value=guild.region, inline=True)
        server_embed.add_field(name="Considered Large", value=guild.large, inline=True)
        server_embed.add_field(name="Shard ID", value="{}/{}".format(guild.shard_id+1, self.bot.shard_count), inline=True)
        server_embed.add_field(name="Nitro Boosts",value="{} (level {})".format(guild.premium_subscription_count,guild.premium_tier))
        # Find out where in our join position this server is
        joinedList = []
        popList    = []
        for g in self.bot.guilds:
            joinedList.append({ 'ID' : g.id, 'Joined' : g.me.joined_at })
            popList.append({ 'ID' : g.id, 'Population' : len(g.members) })
        
        # sort the guilds by join date
        joinedList = sorted(joinedList, key=lambda x:x["Joined"].timestamp() if x["Joined"] != None else -1)
        popList = sorted(popList, key=lambda x:x['Population'], reverse=True)
        
        check_item = { "ID" : guild.id, "Joined" : guild.me.joined_at }
        total = len(joinedList)
        position = joinedList.index(check_item) + 1
        server_embed.add_field(name="Join Position", value="{:,} of {:,}".format(position, total), inline=True)
        
        # Get our population position
        check_item = { "ID" : guild.id, "Population" : len(guild.members) }
        total = len(popList)
        position = popList.index(check_item) + 1
        server_embed.add_field(name="Population Rank", value="{:,} of {:,}".format(position, total), inline=True)
        
        emojitext = ""
        emojifields = []
        disabledemojis = 0
        twitchemojis = 0
        for i,emoji in enumerate(guild.emojis):
            if not emoji.available:
                disabledemojis += 1
                continue
            if emoji.managed:
                twitchemojis += 1
                continue
            emojiMention = "<{}:{}:{}>".format("a" if emoji.animated else "",emoji.name,emoji.id)
            test = emojitext + emojiMention
            if len(test) > 1024:
                # TOOO BIIIIIIIIG
                emojifields.append(emojitext)
                emojitext=emojiMention
            else:
                emojitext = emojitext + emojiMention
        
        if len(emojitext): emojifields.append(emojitext) # Add any leftovers
        if twitchemojis:   emojifields.append("{:,} managed".format(twitchemojis))
        if disabledemojis: emojifields.append("{:,} unavailable".format(disabledemojis)) # Add the disabled if any

        server_embed.set_thumbnail(url=Utils.get_guild_icon(guild))
        server_embed.set_footer(text="Server ID: {}".format(guild.id))
        # Let's send all the embeds we need finishing off with extra emojis as needed
        for i,e in enumerate(emojifields):
            name = "Disabled Emojis" if e.lower().endswith("unavailable") else "Twitch Emojis" if e.lower().endswith("managed") else "Emojis ({} of {})".format(i+1,len(emojifields))
            server_embed.add_field(name=name,value=e,inline=True)
            if len(server_embed) > 6000: # too big
                server_embed.remove_field(len(server_embed.fields)-1)
                await ctx.send(embed=server_embed)
                server_embed = discord.Embed(color=ctx.author.color)
                server_embed.title = guild.name
                server_embed.set_thumbnail(url=Utils.get_guild_icon(guild))
                server_embed.set_footer(text="Server ID: {}".format(guild.id))
                server_embed.description = "Continued Emojis:"
                server_embed.add_field(name=name,value=e,inline=True)
        if len(server_embed.fields):
            await ctx.send(embed=server_embed)


    @commands.command()
    async def sharedservers(self, ctx, *, member = None):
        """Lists how many servers you share with the bot."""
        if member == None:
            member = ctx.author
        
        if type(member) is str:
            member_check = DisplayName.memberForName(member, ctx.guild)
            if not member_check:
                msg = "I couldn't find *{}* on this server...".format(Nullify.escape_all(member))
                await ctx.send(msg)
                return
            member = member_check

        if member.id == self.bot.user.id:
            return await ctx.send("I'm on *{:,}* server{}. :blush:".format(len(self.bot.guilds),"" if len(self.bot.guilds)==1 else "s"))
        
        count = 0
        for guild in self.bot.guilds:
            for mem in guild.members:
                if mem.id == member.id:
                    count += 1
        if ctx.author.id == member.id:
            targ = "You share"
        else:
            targ = "*{}* shares".format(DisplayName.name(member))

        await ctx.send("{} *{:,}* server{} with me. :blush:".format(targ,count,"" if count==1 else "s"))

    @commands.command()
    async def listservers(self, ctx):
        """Lists the servers I'm connected to."""
        our_list = []
        for guild in self.bot.guilds:
            our_list.append(
                {
                    "name":"{}".format(guild.name),
                    "value":"{:,} member{} ({})".format(len(guild.members),"" if len(guild.members)==1 else "s",guild.id),
                    "users":len(guild.members)
                }
            )
        return await PickList.PagePicker(title="Servers I'm On ({} total)".format(len(self.bot.guilds)),ctx=ctx,list=[{"name":"{}. {}".format(y+1,x["name"]),"value":x["value"]} for y,x in enumerate(our_list)]).pick()

    @commands.command()
    async def topservers(self, ctx):
        """Lists the top servers I'm connected to ordered by population."""
        our_list = []
        for guild in self.bot.guilds:
            our_list.append(
                {
                    "name":"{}".format(guild.name),
                    "value":"{:,} member{} ({})".format(len(guild.members),"" if len(guild.members)==1 else "s",guild.id),
                    "users":len(guild.members)
                }
            )
        our_list = sorted(our_list, key=lambda x:x["users"],reverse=True)
        return await PickList.PagePicker(title="Top Servers By Population ({} total)".format(len(self.bot.guilds)),ctx=ctx,list=[{"name":"{}. {}".format(y+1,x["name"]),"value":x["value"]} for y,x in enumerate(our_list)]).pick()

    @commands.command()
    async def bottomservers(self, ctx):
        """Lists the bottom servers I'm connected to ordered by population."""
        our_list = []
        for guild in self.bot.guilds:
            our_list.append(
                {
                    "name":"{}".format(guild.name),
                    "value":"{:,} member{} ({})".format(len(guild.members),"" if len(guild.members)==1 else "s",guild.id),
                    "users":len(guild.members)
                }
            )
        our_list = sorted(our_list, key=lambda x:x["users"])
        return await PickList.PagePicker(title="Bottom Servers By Population ({} total)".format(len(self.bot.guilds)),ctx=ctx,list=[{"name":"{}. {}".format(y+1,x["name"]),"value":x["value"]} for y,x in enumerate(our_list)]).pick()

    @commands.command()
    async def users(self, ctx):
        """Lists the total number of users on all servers I'm connected to."""
        message = await Message.EmbedText(title="Counting users...", color=ctx.message.author).send(ctx)
        # Let's try to do this more efficiently
        users         = [x for x in self.bot.get_all_members() if not x.bot]
        users_online  = [x for x in users if x.status != discord.Status.offline]
        unique_users  = set([x.id for x in users])
        bots          = [x for x in self.bot.get_all_members() if x.bot]
        bots_online   = [x for x in bots if x.status != discord.Status.offline]
        unique_bots   = set([x.id for x in bots])
        await Message.Embed(
            title="Member Stats",
            description="Current User Information",
            fields=[
                { "name" : "Servers", "value" : "└─ {:,}".format(len(self.bot.guilds)), "inline" : False },
                { "name" : "Users", "value" : "└─ {:,}/{:,} online ({:,g}%) - {:,} unique ({:,g}%)".format(
                    len(users_online),
                    len(users),
                    round((len(users_online)/len(users))*100, 2),
                    len(unique_users),
                    round((len(unique_users)/len(users))*100, 2)
                ),"inline" : False},
                { "name" : "Bots", "value" : "└─ {:,}/{:,} online ({:,g}%) - {:,} unique ({:,g}%)".format(
                    len(bots_online),
                    len(bots),
                    round((len(bots_online)/len(bots))*100, 2),
                    len(unique_bots),
                    round(len(unique_bots)/len(bots)*100, 2)
                ), "inline" : False},
                { "name" : "Total", "value" : "└─ {:,}/{:,} online ({:,g}%)".format(
                    len(users_online)+len(bots_online),
                    len(users)+len(bots),
                    round(((len(users_online)+len(bots_online))/(len(users)+len(bots)))*100, 2)
                ), "inline" : False}
            ],
            color=ctx.message.author).edit(ctx, message)
    
    @commands.command()
    async def joinpos(self, ctx, *, member = None):
        """Tells when a user joined compared to other users."""
        if member == None:
            member = ctx.author
        
        if type(member) is str:
            member_check = DisplayName.memberForName(member, ctx.guild)
            if not member_check:
                msg = "I couldn't find *{}* on this server...".format(Nullify.escape_all(member))
                await ctx.send(msg)
                return
            member = member_check

        joinedList = []
        for mem in ctx.message.guild.members:
            joinedList.append({ 'ID' : mem.id, 'Joined' : mem.joined_at })
        
        # sort the users by join date
        joinedList = sorted(joinedList, key=lambda x:x["Joined"].timestamp() if x["Joined"] != None else -1)

        check_item = { "ID" : member.id, "Joined" : member.joined_at }

        total = len(joinedList)
        position = joinedList.index(check_item) + 1

        before = ""
        after  = ""
        
        msg = "*{}'s* join position is **{:,}**.".format(DisplayName.name(member), position, total)
        if position-1 == 1:
            # We have previous members
            before = "**1** user"
        elif position-1 > 1:
            before = "**{:,}** users".format(position-1)
        if total-position == 1:
            # There were users after as well
            after = "**1** user"
        elif total-position > 1:
            after = "**{:,}** users".format(total-position)
        # Build the string!
        if len(before) and len(after):
            # Got both
            msg += "\n\n{} joined before, and {} after.".format(before, after)
        elif len(before):
            # Just got before
            msg += "\n\n{} joined before.".format(before)
        elif len(after):
            # Just after
            msg += "\n\n{} joined after.".format(after)
        await ctx.send(msg)

    @commands.command()
    async def joinedatpos(self, ctx, *, position):
        """Lists the user that joined at the passed position."""
        try:
            position = int(position)-1
            assert -1<position<len(ctx.guild.members) 
        except:
            return await ctx.send("Position must be an int between 1 and {:,}".format(len(ctx.guild.members)))
        joinedList = [{"member":mem,"joined":mem.joined_at} for mem in ctx.guild.members]
        # sort the users by join date
        joinedList = sorted(joinedList, key=lambda x:x["joined"].timestamp() if x["joined"] != None else -1)
        join = joinedList[position]
        msg = "*{}* joined at position **{:,}**.".format(DisplayName.name(join["member"]),position+1)
        await ctx.send(msg)

    @commands.command()
    async def firstjoins(self, ctx):
        """Lists the first users to join."""
        our_list = []
        # offset = self.settings.getGlobalUserStat(ctx.author,"TimeZone",self.settings.getGlobalUserStat(ctx.author,"UTCOffset",None))
        for member in ctx.guild.members:
            join = "Unknown"
            if member.joined_at:
                ts = int(member.joined_at.timestamp())
                join = "<t:{}> (<t:{}:R>)".format(ts,ts)
            name = "{}#{}".format(member.name,member.discriminator)
            if member.nick:
                name = "{} ({})".format(member.nick,name)
            our_list.append(
                {
                    "name":name,
                    "value":join,
                    "date":member.joined_at
                }
            )
        our_list = sorted(our_list, key=lambda x:x["date"].timestamp() if x["date"] != None else -1)
        return await PickList.PagePicker(title="First Members to Join {} ({:,} total)".format(ctx.guild.name,len(ctx.guild.members)),ctx=ctx,list=[{"name":"{}. {}".format(y+1,x["name"]),"value":x["value"]} for y,x in enumerate(our_list)]).pick()

    @commands.command()
    async def recentjoins(self, ctx):
        """Lists the most recent users to join."""
        our_list = []
        for member in ctx.guild.members:
            join = "Unknown"
            if member.joined_at:
                ts = int(member.joined_at.timestamp())
                join = "<t:{}> (<t:{}:R>)".format(ts,ts)
            name = "{}#{}".format(member.name,member.discriminator)
            if member.nick:
                name = "{} ({})".format(member.nick,name)
            our_list.append(
                {
                    "name":name,
                    "value":join,
                    "date":member.joined_at
                }
            )
        our_list = sorted(our_list, key=lambda x:x["date"].timestamp() if x["date"] != None else -1, reverse=True)
        return await PickList.PagePicker(title="Most Recent Members to Join {} ({:,} total)".format(ctx.guild.name,len(ctx.guild.members)),ctx=ctx,list=[{"name":"{}. {}".format(y+1,x["name"]),"value":x["value"]} for y,x in enumerate(our_list)]).pick()
        
    @commands.command()
    async def firstservers(self, ctx):
        """Lists the first servers I've joined."""
        our_list = []
        # offset = self.settings.getGlobalUserStat(ctx.author, "TimeZone",self.settings.getGlobalUserStat(ctx.author,"UTCOffset",None))
        for guild in self.bot.guilds:
            bot = guild.me
            join = "Unknown"
            if bot.joined_at:
                ts = int(bot.joined_at.timestamp())
                join = "<t:{}> (<t:{}:R>)".format(ts,ts)
            our_list.append(
                {
                    "name":"{} ({:,} member{})".format(guild.name,len(guild.members),"" if len(guild.members)==1 else "s"),
                    "value":"`{}`\n".format(guild.id)+join,
                    "date":bot.joined_at
                }
            )
        our_list = sorted(our_list, key=lambda x:x["date"].timestamp() if x["date"] != None else -1)
        return await PickList.PagePicker(title="First Servers I Joined ({:,} total)".format(len(self.bot.guilds)),ctx=ctx,list=[{"name":"{}. {}".format(y+1,x["name"]),"value":x["value"]} for y,x in enumerate(our_list)]).pick()

    @commands.command()
    async def recentservers(self, ctx):
        """Lists the most recent users to join - default is 10, max is 25."""
        our_list = []
        # offset = self.settings.getGlobalUserStat(ctx.author,"TimeZone",self.settings.getGlobalUserStat(ctx.author,"UTCOffset",None))
        for guild in self.bot.guilds:
            bot = guild.me
            join = "Unknown"
            if bot.joined_at:
                ts = int(bot.joined_at.timestamp())
                join = "<t:{}> (<t:{}:R>)".format(ts,ts)
            our_list.append(
                {
                    "name":"{} ({:,} member{})".format(guild.name,len(guild.members),"" if len(guild.members)==1 else "s"),
                    "value":"`{}`\n".format(guild.id)+join,
                    "date":bot.joined_at
                }
            )
        our_list = sorted(our_list, key=lambda x:x["date"].timestamp() if x["date"] != None else -1, reverse=True)
        return await PickList.PagePicker(title="Most Recent Servers I Joined ({:,} total)".format(len(self.bot.guilds)),ctx=ctx,list=[{"name":"{}. {}".format(y+1,x["name"]),"value":x["value"]} for y,x in enumerate(our_list)]).pick()

    @commands.command()
    async def messages(self, ctx):
        """Lists the number of messages I've seen on this sever so far. (only applies after this module's inception, and if I'm online)"""
        messages = int(self.settings.getServerStat(ctx.message.guild, "TotalMessages"))
        messages -= 1
        self.settings.setServerStat(ctx.message.guild, "TotalMessages", messages)
        if messages == None:
            messages = 0
        if messages == 1:
            await ctx.channel.send('So far, I\'ve witnessed *{:,} message!*'.format(messages))
        else:
            await ctx.channel.send('So far, I\'ve witnessed *{:,} messages!*'.format(messages))

    @commands.command()
    async def allmessages(self, ctx):
        """Lists the number of messages I've seen on all severs so far. (only applies after this module's inception, and if I'm online)"""
        messages = 0
        for guild in self.bot.guilds:
            temp = 0 if self.settings.getServerStat(guild, "TotalMessages") is None else self.settings.getServerStat(guild, "TotalMessages")
            messages += int(temp)
        messages -= 1
        if messages == 1:
            await ctx.channel.send('So far, I\'ve witnessed *{:,} message across all servers!*'.format(messages))
        else:
            await ctx.channel.send('So far, I\'ve witnessed *{:,} messages across all servers!*'.format(messages))
        # Set our message count locally -1
        messages = int(self.settings.getServerStat(ctx.message.guild, "TotalMessages"))
        messages -= 1
        self.settings.setServerStat(ctx.message.guild, "TotalMessages", messages)
