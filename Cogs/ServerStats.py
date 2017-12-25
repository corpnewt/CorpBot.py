import asyncio
import discord
from   datetime    import datetime
from   operator    import itemgetter
from   discord.ext import commands
from   Cogs        import Nullify
from   Cogs        import DisplayName
from   Cogs        import UserTime
from   Cogs        import Message

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(ServerStats(bot, settings))

class ServerStats:

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

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

    @commands.command(pass_context=True)
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
        local_time = UserTime.getUserTime(ctx.author, self.settings, guild.created_at)
        time_str = "{} {}".format(local_time['time'], local_time['zone'])
        
        server_embed.description = "Created at {}".format(time_str)
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
        server_embed.add_field(name="Verification", value=guild.verification_level, inline=True)
        server_embed.add_field(name="Voice Region", value=guild.region, inline=True)
        server_embed.add_field(name="Considered Large", value=guild.large, inline=True)
	# Find out where in our join position this server is
        joinedList = []
        popList    = []
        for g in self.bot.guilds:
            joinedList.append({ 'ID' : g.id, 'Joined' : g.me.joined_at })
            popList.append({ 'ID' : g.id, 'Population' : len(g.members) })
        
        # sort the guilds by join date
        joinedList = sorted(joinedList, key=lambda x:x['Joined'])
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
        emojicount = 0
        for emoji in guild.emojis:
            if emoji.animated:
                emojiMention = "<a:"+emoji.name+":"+str(emoji.id)+">"
            else:
                emojiMention = "<:"+emoji.name+":"+str(emoji.id)+">"
            test = emojitext + emojiMention
            if len(test) > 1024:
                # TOOO BIIIIIIIIG
                emojicount += 1
                if emojicount == 1:
                    ename = "Emojis ({:,} total)".format(len(guild.emojis))
                else:
                    ename = "Emojis (Continued)"
                server_embed.add_field(name=ename, value=emojitext, inline=True)
                emojitext=emojiMention
            else:
                emojitext = emojitext + emojiMention

        if len(emojitext):
            if emojicount == 0:
                emojiname = "Emojis ({} total)".format(len(guild.emojis))
            else:
                emojiname = "Emojis (Continued)"
            server_embed.add_field(name=emojiname, value=emojitext, inline=True)


        if len(guild.icon_url):
            server_embed.set_thumbnail(url=guild.icon_url)
        else:
            # No Icon
            server_embed.set_thumbnail(url=ctx.author.default_avatar_url)
        server_embed.set_footer(text="Server ID: {}".format(guild.id))
        await ctx.channel.send(embed=server_embed)


    @commands.command(pass_context=True)
    async def sharedservers(self, ctx, *, member = None):
        """Lists how many servers you share with the bot."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        if member == None:
            member = ctx.author
        
        if type(member) is str:
            member_check = DisplayName.memberForName(member, ctx.guild)
            if not member_check:
                msg = "I couldn't find *{}* on this server...".format(member)
                if suppress:
                    msg = Nullify.clean(msg)
                await ctx.send(msg)
                return
            member = member_check

        if member.id == self.bot.user.id:
            count = len(self.bot.guilds)
            if count == 1:
                await ctx.send("I'm on *1* server. :blush:")
            else:
                await ctx.send("I'm on *{}* servers. :blush:".format(count))
            return


        count = 0
        for guild in self.bot.guilds:
            for mem in guild.members:
                if mem.id == member.id:
                    count += 1
        if ctx.author.id == member.id:
            targ = "You share"
        else:
            targ = "*{}* shares".format(DisplayName.name(member))

        if count == 1:
            await ctx.send("{} *1* server with me. :blush:".format(targ))
        else:
            await ctx.send("{} *{}* servers with me. :blush:".format(targ, count))


    @commands.command(pass_context=True)
    async def listservers(self, ctx, number : int = 10):
        """Lists the servers I'm connected to - default is 10, max is 50."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        if number > 50:
            number = 50
        if number < 1:
            await ctx.channel.send('Oookay - look!  No servers!  Just like you wanted!')
            return
        i = 1
        msg = '__**Servers I\'m On:**__\n\n'
        for server in self.bot.guilds:
            if i > number:
                break
            msg += '{}. *{}*\n'.format(i, server.name)
            i += 1
        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def topservers(self, ctx, number : int = 10):
        """Lists the top servers I'm connected to ordered by population - default is 10, max is 50."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        if number > 50:
            number = 50
        if number < 1:
            await ctx.channel.send('Oookay - look!  No servers!  Just like you wanted!')
            return
        serverList = []
        for server in self.bot.guilds:
            memberCount = 0
            for member in server.members:
                memberCount += 1
            serverList.append({ 'Name' : server.name, 'Users' : memberCount })

        # sort the servers by population
        serverList = sorted(serverList, key=lambda x:int(x['Users']), reverse=True)

        if number > len(serverList):
            number = len(serverList)

        i = 1
        msg = ''
        for server in serverList:
            if i > number:
                break
            msg += '{}. *{}* - *{:,}* members\n'.format(i, server['Name'], server['Users'])
            i += 1

        if number < len(serverList):
            msg = '__**Top {} of {} Servers:**__\n\n'.format(number, len(serverList))+msg
        else:
            msg = '__**Top {} Servers:**__\n\n'.format(len(serverList))+msg
        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def bottomservers(self, ctx, number : int = 10):
        """Lists the bottom servers I'm connected to ordered by population - default is 10, max is 50."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        if number > 50:
            number = 50
        if number < 1:
            await ctx.channel.send('Oookay - look!  No servers!  Just like you wanted!')
            return
        serverList = []
        for server in self.bot.guilds:
            serverList.append({ 'Name' : server.name, 'Users' : len(server.members) })

        # sort the servers by population
        serverList = sorted(serverList, key=lambda x:int(x['Users']))

        if number > len(serverList):
            number = len(serverList)

        i = 1
        msg = ''
        for server in serverList:
            if i > number:
                break
            msg += '{}. *{}* - *{:,}* members\n'.format(i, server['Name'], server['Users'])
            i += 1

        if number < len(serverList):
            msg = '__**Bottom {} of {} Servers:**__\n\n'.format(number, len(serverList))+msg
        else:
            msg = '__**Bottom {} Servers:**__\n\n'.format(len(serverList))+msg
        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await ctx.channel.send(msg)


    @commands.command(pass_context=True)
    async def users(self, ctx):
        """Lists the total number of users on all servers I'm connected to."""
        
        message = await Message.EmbedText(title="Counting users...", color=ctx.message.author).send(ctx)
        servers = members = membersOnline = bots = botsOnline = 0
        counted_users = []
        counted_bots  = []
        for server in self.bot.guilds:
            servers += 1
            for member in server.members:
                if member.bot:
                    bots += 1
                    if not member.id in counted_bots:
                        counted_bots.append(member.id)
                    if not member.status == discord.Status.offline:
                        botsOnline += 1
                else:
                    members += 1
                    if not member.id in counted_users:
                        counted_users.append(member.id)
                    if not member.status == discord.Status.offline:
                        membersOnline += 1
        await Message.Embed(
            title="Member Stats",
            description="Current User Information".format(server.name),
            fields=[
                { "name" : "Servers", "value" : "└─ {:,}".format(servers), "inline" : False },
                { "name" : "Users", "value" : "└─ {:,}/{:,} online ({:,g}%) - {:,} unique ({:,g}%)".format(membersOnline, members, round((membersOnline/members)*100, 2), len(counted_users), round((len(counted_users)/members)*100, 2)), "inline" : False},
                { "name" : "Bots", "value" : "└─ {:,}/{:,} online ({:,g}%) - {:,} unique ({:,g}%)".format(botsOnline, bots, round((botsOnline/bots)*100, 2), len(counted_bots), round(len(counted_bots)/bots*100, 2)), "inline" : False},
                { "name" : "Total", "value" : "└─ {:,}/{:,} online ({:,g}%)".format(membersOnline + botsOnline, members+bots, round(((membersOnline + botsOnline)/(members+bots))*100, 2)), "inline" : False}
            ],
            color=ctx.message.author).edit(ctx, message)
        
        '''userCount = 0
        serverCount = 0
        counted_users = []
        message = await ctx.send("Counting users...")
        for server in self.bot.guilds:
            serverCount += 1
            userCount += len(server.members)
            for member in server.members:
                if not member.id in counted_users:
                    counted_users.append(member.id)
        await message.edit(content='There are *{:,} users* (*{:,}* unique) on the *{:,} servers* I am currently a part of!'.format(userCount, len(counted_users), serverCount))'''

	
    @commands.command(pass_context=True)
    async def joinpos(self, ctx, *, member = None):
        """Tells when a user joined compared to other users."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        if member == None:
            member = ctx.author
        
        if type(member) is str:
            member_check = DisplayName.memberForName(member, ctx.guild)
            if not member_check:
                msg = "I couldn't find *{}* on this server...".format(member)
                if suppress:
                    msg = Nullify.clean(msg)
                await ctx.send(msg)
                return
            member = member_check

        joinedList = []
        for mem in ctx.message.guild.members:
            joinedList.append({ 'ID' : mem.id, 'Joined' : mem.joined_at })
        
        # sort the users by join date
        joinedList = sorted(joinedList, key=lambda x:x['Joined'])

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


    @commands.command(pass_context=True)
    async def firstjoins(self, ctx, number : int = 10):
        """Lists the first users to join - default is 10, max is 25."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        if number > 25:
            number = 25
        if number < 1:
            await ctx.channel.send('Oookay - look!  No users!  Just like you wanted!')
            return

        joinedList = []
        for member in ctx.message.guild.members:
            joinedList.append({ 'ID' : member.id, 'Joined' : member.joined_at })
        
        # sort the users by join date
        joinedList = sorted(joinedList, key=lambda x:x['Joined'])

        i = 1
        msg = ''
        for member in joinedList:
            if i > number:
                break
            # Get localized user time
            local_time = UserTime.getUserTime(ctx.author, self.settings, member['Joined'])
            time_str = "{} {}".format(local_time['time'], local_time['zone'])
            msg += '{}. *{}* - *{}*\n'.format(i, DisplayName.name(DisplayName.memberForID(member['ID'], ctx.message.guild)), time_str)
            i += 1
        
        if number < len(joinedList):
            msg = '__**First {} of {} Members to Join:**__\n\n'.format(number, len(joinedList))+msg
        else:
            msg = '__**First {} Members to Join:**__\n\n'.format(len(joinedList))+msg

        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def recentjoins(self, ctx, number : int = 10):
        """Lists the most recent users to join - default is 10, max is 25."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        if number > 25:
            number = 25
        if number < 1:
            await ctx.channel.send('Oookay - look!  No users!  Just like you wanted!')
            return

        joinedList = []
        for member in ctx.message.guild.members:
            joinedList.append({ 'ID' : member.id, 'Joined' : member.joined_at })
        
        # sort the users by join date
        joinedList = sorted(joinedList, key=lambda x:x['Joined'], reverse=True)

        i = 1
        msg = ''
        for member in joinedList:
            if i > number:
                break
            # Get localized user time
            local_time = UserTime.getUserTime(ctx.author, self.settings, member['Joined'])
            time_str = "{} {}".format(local_time['time'], local_time['zone'])
            msg += '{}. *{}* - *{}*\n'.format(i, DisplayName.name(DisplayName.memberForID(member['ID'], ctx.message.guild)), time_str)
            i += 1
        
        if number < len(joinedList):
            msg = '__**Last {} of {} Members to Join:**__\n\n'.format(number, len(joinedList))+msg
        else:
            msg = '__**Last {} Members to Join:**__\n\n'.format(len(joinedList))+msg

        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await ctx.channel.send(msg)
        
    @commands.command(pass_context=True)
    async def firstservers(self, ctx, number : int = 10):
        """Lists the first servers I've joined - default is 10, max is 25."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        if number > 25:
            number = 25
        if number < 1:
            await ctx.channel.send('Oookay - look!  No servers!  Just like you wanted!')
            return

        joinedList = []
        for guild in self.bot.guilds:
            botmember = DisplayName.memberForID(self.bot.user.id, guild)
            joinedList.append({ 'Name' : guild.name, 'Joined' : botmember.joined_at, 'Members': len(guild.members) })
        
        # sort the servers by join date
        joinedList = sorted(joinedList, key=lambda x:x['Joined'])

        i = 1
        msg = ''
        for member in joinedList:
            if i > number:
                break
            # Get localized user time
            local_time = UserTime.getUserTime(ctx.author, self.settings, member['Joined'])
            time_str = "{} {}".format(local_time['time'], local_time['zone'])
            if member['Members'] == 1:
                msg += '{}. *{}* - *{}* - *(1 member)*\n'.format(i, member['Name'], time_str)
            else:
                msg += '{}. *{}* - *{}* - *({} members)*\n'.format(i, member['Name'], time_str, member['Members'])
            i += 1
        
        if number < len(joinedList):
            msg = '__**First {} of {} Servers I Joined:**__\n\n'.format(number, len(joinedList))+msg
        else:
            msg = '__**First {} Servers I Joined:**__\n\n'.format(len(joinedList))+msg

        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def recentservers(self, ctx, number : int = 10):
        """Lists the most recent users to join - default is 10, max is 25."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        if number > 25:
            number = 25
        if number < 1:
            await ctx.channel.send('Oookay - look!  No servers!  Just like you wanted!')
            return

        joinedList = []
        for guild in self.bot.guilds:
            botmember = DisplayName.memberForID(self.bot.user.id, guild)
            joinedList.append({ 'Name' : guild.name, 'Joined' : botmember.joined_at, 'Members': len(guild.members) })
        
        # sort the servers by join date
        joinedList = sorted(joinedList, key=lambda x:x['Joined'], reverse=True)

        i = 1
        msg = ''
        for member in joinedList:
            if i > number:
                break
            # Get localized user time
            local_time = UserTime.getUserTime(ctx.author, self.settings, member['Joined'])
            time_str = "{} {}".format(local_time['time'], local_time['zone'])
            if member['Members'] == 1:
                msg += '{}. *{}* - *{}* - *(1 member)*\n'.format(i, member['Name'], time_str)
            else:
                msg += '{}. *{}* - *{}* - *({} members)*\n'.format(i, member['Name'], time_str, member['Members'])
            i += 1
        
        if number < len(joinedList):
            msg = '__**Last {} of {} Servers I Joined:**__\n\n'.format(number, len(joinedList))+msg
        else:
            msg = '__**Last {} Servers I Joined:**__\n\n'.format(len(joinedList))+msg

        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
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

    @commands.command(pass_context=True)
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
