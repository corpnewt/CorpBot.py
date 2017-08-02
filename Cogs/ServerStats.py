import asyncio
import discord
from   datetime    import datetime
from   operator    import itemgetter
from   discord.ext import commands
from   Cogs        import Nullify
from   Cogs        import DisplayName

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
    async def serverinfo(self, ctx):
        """Lists some info about the current server."""
        server_embed = discord.Embed(color=ctx.author.color)
        server_embed.title = ctx.guild.name
        server_embed.description = "Created at " + ctx.guild.created_at.strftime("%Y-%m-%d %I:%M %p") + " UTC"
        online_members = 0
        for member in ctx.guild.members:
            if not str(member.status).lower() == "offline":
                online_members += 1
        server_embed.add_field(name="Members", value="{:,}/{:,}".format(online_members, len(ctx.guild.members)), inline=True)
        server_embed.add_field(name="Roles", value=str(len(ctx.guild.roles)), inline=True)
        chandesc = "{:,} text, {:,} voice".format(len(ctx.guild.text_channels), len(ctx.guild.voice_channels))
        server_embed.add_field(name="Channels", value=chandesc, inline=True)
        server_embed.add_field(name="Default Channel", value=ctx.guild.default_channel.mention, inline=True)
        server_embed.add_field(name="Default Role", value=ctx.guild.default_role, inline=True)
        server_embed.add_field(name="Owner", value=ctx.guild.owner.mention, inline=True)
        server_embed.add_field(name="AFK Channel", value=ctx.guild.afk_channel, inline=True)
        server_embed.add_field(name="Verification", value=ctx.guild.verification_level, inline=True)
        server_embed.add_field(name="Voice Region", value=ctx.guild.region, inline=True)
        server_embed.add_field(name="Considered Large", value=ctx.guild.large, inline=True)
        emojitext = ""
        emojicount = 0
        for emoji in ctx.guild.emojis:
            emojiMention = "<:"+emoji.name+":"+str(emoji.id)+">"
            test = emojitext + emojiMention
            if len(test) > 1024:
                # TOOO BIIIIIIIIG
                emojicount += 1
                if emojicount == 1:
                    ename = "Emojis ({:,} total)".format(len(ctx.guild.emojis))
                else:
                    ename = "Emojis (Continued)"
                server_embed.add_field(name=ename, value=emojitext, inline=True)
                emojitext=emojiMention
            else:
                emojitext = emojitext + emojiMention

        if len(emojitext):
            if emojicount == 0:
                emojiname = "Emojis ({} total)".format(len(ctx.guild.emojis))
            else:
                emojiname = "Emojis (Continued)"
            server_embed.add_field(name=emojiname, value=emojitext, inline=True)


        if len(ctx.guild.icon_url):
            server_embed.set_thumbnail(url=ctx.guild.icon_url)
        else:
            # No Icon
            server_embed.set_thumbnail(url=ctx.author.default_avatar_url)
        server_embed.set_footer(text="Server ID: {}".format(ctx.guild.id))
        await ctx.channel.send(embed=server_embed)


    @commands.command(pass_context=True)
    async def sharedservers(self, ctx):
        """Lists how many servers you share with the bot."""

        count = 0
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id == ctx.author.id:
                    count += 1
        
        if count == 1:
            await ctx.send("You share *1* server with me. :blush:")
        else:
            await ctx.send("You share *{}* servers with me. :blush:".format(count))


    @commands.command(pass_context=True)
    async def listservers(self, ctx, number : int = 10):
        """Lists the servers I'm connected to - default is 10, max is 50."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
        userCount = 0
        serverCount = 0
        counted_users = []
        for server in self.bot.guilds:
            serverCount += 1
            userCount += len(server.members)
            for member in server.members:
                if not member.id in counted_users:
                    counted_users.append(member.id)
        await ctx.channel.send('There are *{:,} users* (*{:,}* unique) on the *{:,} servers* I am currently a part of!'.format(userCount, len(counted_users), serverCount))

    
    @commands.command(pass_context=True)
    async def firstjoins(self, ctx, number : int = 10):
        """Lists the first users to join - default is 10, max is 25."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
            msg += '{}. *{}* - *{}*\n'.format(i, DisplayName.name(DisplayName.memberForID(member['ID'], ctx.message.guild)), member['Joined'].strftime("%Y-%m-%d %I:%M %p"))
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
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
            msg += '{}. *{}* - *{}*\n'.format(i, DisplayName.name(DisplayName.memberForID(member['ID'], ctx.message.guild)), member['Joined'].strftime("%Y-%m-%d %I:%M %p"))
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
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
            if member['Members'] == 1:
                msg += '{}. *{}* - *{}* - *(1 member)*\n'.format(i, member['Name'], member['Joined'].strftime("%Y-%m-%d %I:%M %p"))
            else:
                msg += '{}. *{}* - *{}* - *({} members)*\n'.format(i, member['Name'], member['Joined'].strftime("%Y-%m-%d %I:%M %p"), member['Members'])
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
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
            if member['Members'] == 1:
                msg += '{}. *{}* - *{}* - *(1 member)*\n'.format(i, member['Name'], member['Joined'].strftime("%Y-%m-%d %I:%M %p"))
            else:
                msg += '{}. *{}* - *{}* - *({} members)*\n'.format(i, member['Name'], member['Joined'].strftime("%Y-%m-%d %I:%M %p"), member['Members'])
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
