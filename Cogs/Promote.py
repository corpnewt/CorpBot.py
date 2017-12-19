import asyncio
import discord
import datetime
import random
from   discord.ext import commands
from   operator import itemgetter
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import Xp

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Promote(bot, settings))

# This module is for auto promoting/demoting of roles - admin only

class Promote:

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    async def _can_run(self, ctx):
        # Check if we're admin - and if not, check if bot admins can run this
        # and if we're bot admin
        if ctx.author.permissions_in(ctx.channel).administrator:
            return True
        if not self.settings.getServerStat(ctx.guild, "BotAdminAsAdmin"):
            return False
        checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
        for role in ctx.author.roles:
            for aRole in checkAdmin:
                # Get the role that corresponds to the id
                if str(aRole['ID']) == str(role.id):
                    return True
        return False

    @commands.command(pass_context=True)
    async def promote(self, ctx, *, member = None):
        """Auto-adds the required xp to promote the passed user to the next role (admin only)."""

        author  = ctx.message.author
        server  = ctx.message.guild
        channel = ctx.message.channel

        # Only allow admins to change server stats
        if not await self._can_run(ctx):
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False
        
        usage = 'Usage: `{}promote [member]`'.format(ctx.prefix)

        if member == None:
            await ctx.channel.send(usage)
            return

        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                if suppress:
                    msg = Nullify.clean(msg)
                await ctx.channel.send(msg)
                return

        # Get user's xp
        xp = int(self.settings.getUserStat(member, server, "XP"))

        # Get the role list
        promoArray = self.getSortedRoles(server)
        currentRole = self.getCurrentRoleIndex(member, server)
        nextRole = currentRole + 1
        if nextRole >= len(promoArray):
            msg = 'There are no higher roles to promote *{}* into.'.format(DisplayName.name(member))
        else:
            newRole  = DisplayName.roleForID(promoArray[nextRole]['ID'], server)
            neededXp = int(promoArray[nextRole]['XP'])-xp
            self.settings.incrementStat(member, server, "XP", neededXp)
            # Start at the bottom role and add all roles up to newRole
            addRoles = []
            for i in range(0, nextRole+1):
                addRole  = DisplayName.roleForID(promoArray[i]['ID'], server)
                if addRole:
                    if not addRole in member.roles:
                        addRoles.append(addRole)
            # await member.add_roles(*addRoles)
            # Use role manager instead
            self.settings.role.add_roles(member, addRoles)
            if not newRole:
                # Promotion role doesn't exist
                msg = 'It looks like **{}** is no longer on this server.  *{}* was still given *{} xp* - but I am unable to promote them to a non-existent role.  Consider revising your xp roles.'.format(promoArray[nextRole]['Name'], DisplayName.name(member), neededXp)
            else:
                msg = '*{}* was given *{} xp* and promoted to **{}**!'.format(DisplayName.name(member), neededXp, newRole.name)
        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await channel.send(msg)

    @commands.command(pass_context=True)
    async def promoteto(self, ctx, *, member = None, role = None):
        """Auto-adds the required xp to promote the passed user to the passed role (admin only)."""

        author  = ctx.message.author
        server  = ctx.message.guild
        channel = ctx.message.channel

        # Only allow admins to change server stats
        if not await self._can_run(ctx):
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False
        
        usage = 'Usage: `{}promoteto [member] [role]`'.format(ctx.prefix)

        if member == None:
            await ctx.channel.send(usage)
            return

        if role == None:
            # Either a role wasn't set - or it's the last section
            if type(member) is str:
                # It' a string - the hope continues
                # Let's search for a name at the beginning - and a role at the end
                parts = member.split()
                memFromName = None
                for j in range(len(parts)):
                    # Reverse search direction
                    i = len(parts)-1-j
                    # Name = 0 up to i joined by space
                    nameStr = ' '.join(parts[0:i+1])
                    # Role = end of name -> end of parts joined by space
                    roleStr = ' '.join(parts[i+1:])
                    memFromName = DisplayName.memberForName(nameStr, ctx.message.guild)
                    if memFromName:
                        # We got a member - let's check for a role
                        roleFromName = DisplayName.roleForName(roleStr, ctx.message.guild)
                            
                        if not roleFromName == None:
                            # We got a member and a role - break
                            role = roleFromName
                            break
                if memFromName == None:
                    # Never found a member at all
                    msg = 'I couldn\'t find *{}* on the server.'.format(member)
                    # Check for suppress
                    if suppress:
                        msg = Nullify.clean(msg)
                    await ctx.channel.send(msg)
                    return
                if roleFromName == None:
                    # We couldn't find one or the other
                    await ctx.channel.send(usage)
                    return

                member = memFromName

        # Get user's xp
        xp = int(self.settings.getUserStat(member, server, "XP"))

        # Get the role list
        promoArray = self.getSortedRoles(server)
        nextRole = self.getIndexForRole(role, server)
        currentRole = self.getCurrentRoleIndex(member, server)
        vowels = 'aeiou'

        if nextRole == None:
            msg = '**{}** doesn\'t appear to be in the xp role list - consider adding it with the `{}addxprole [role] [xp amount]` command.'.format(role.name, ctx.prefix)
            # Check for suppress
            if suppress:
                msg = Nullify.clean(msg)
            await channel.send(msg)
            return
        
        if currentRole == nextRole:
            # We are already the target role
            if role.name[:1].lower() in vowels:
                msg = '*{}* is already an **{}**.'.format(DisplayName.name(member), role.name)
            else:
                msg = '*{}* is already a **{}**.'.format(DisplayName.name(member), role.name)
            # Check for suppress
            if suppress:
                msg = Nullify.clean(msg)
            await channel.send(msg)
            return
        elif currentRole > nextRole:
            # We are a higher role than the target
            msg = '*{}* already has **{}** in their collection of roles.'.format(DisplayName.name(member), role.name)
            # Check for suppress
            if suppress:
                msg = Nullify.clean(msg)
            await channel.send(msg)
            return

        if nextRole >= len(promoArray):
            msg = 'There are no higher roles to promote *{}* into.'.format(DisplayName.name(member))
        else:
            newRole  = DisplayName.roleForID(promoArray[nextRole]['ID'], server)
            neededXp = int(promoArray[nextRole]['XP'])-xp
            self.settings.incrementStat(member, server, "XP", neededXp)
            # Start at the bottom role and add all roles up to newRole
            addRoles = []
            for i in range(0, nextRole+1):
                addRole  = DisplayName.roleForID(promoArray[i]['ID'], server)
                if addRole:
                    if not addRole in member.roles:
                        addRoles.append(addRole)
            # await member.add_roles(*addRoles)
            # Use role manager instead
            self.settings.role.add_roles(member, addRoles)
            if not newRole:
                # Promotion role doesn't exist
                msg = 'It looks like **{}** is no longer on this server.  *{}* was still given *{} xp* - but I am unable to promote them to a non-existent role.  Consider revising your xp roles.'.format(promoArray[nextRole]['Name'], DisplayName.name(member), neededXp)
            else:
                msg = '*{}* was given *{} xp* and promoted to **{}**!'.format(DisplayName.name(member), neededXp, newRole.name)
        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await channel.send(msg)

    @commands.command(pass_context=True)
    async def demote(self, ctx, *, member = None):
        """Auto-removes the required xp to demote the passed user to the previous role (admin only)."""

        author  = ctx.message.author
        server  = ctx.message.guild
        channel = ctx.message.channel

        # Only allow admins to change server stats
        if not await self._can_run(ctx):
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False
        
        usage = 'Usage: `{}demote [member]`'.format(ctx.prefix)

        if member == None:
            await ctx.channel.send(usage)
            return

        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                if suppress:
                    msg = Nullify.clean(msg)
                await ctx.channel.send(msg)
                return

        # Get user's xp
        xp = int(self.settings.getUserStat(member, server, "XP"))

        # Get the role list
        promoArray = self.getSortedRoles(server)
        currentRole = self.getCurrentRoleIndex(member, server)
        nextRole = currentRole - 1
        if nextRole == -1:
            # We're removing the user from all roles
            neededXp = int(promoArray[0]['XP'])-xp-1
            self.settings.incrementStat(member, server, "XP", neededXp)
            remRoles = []
            for i in range(0, len(promoArray)):
                remRole  = DisplayName.roleForID(promoArray[i]['ID'], server)
                if remRole:
                    if remRole in member.roles:
                        remRoles.append(remRole)
            # await member.remove_roles(*remRoles)
            # Use role manager instead
            self.settings.role.rem_roles(member, remRoles)
            msg = '*{} xp* was taken from *{}* and they were demoted out of the xp system!'.format(neededXp*-1, DisplayName.name(member))
        elif nextRole < -1:
            msg = 'There are no lower roles to demote *{}* into.'.format(DisplayName.name(member))
        else:
            newRole  = DisplayName.roleForID(promoArray[nextRole]['ID'], server)
            neededXp = int(promoArray[nextRole]['XP'])-xp
            self.settings.incrementStat(member, server, "XP", neededXp)
            # Start at the currentRole and remove that and all roles above
            remRoles = []
            for i in range(currentRole, len(promoArray)):
                remRole  = DisplayName.roleForID(promoArray[i]['ID'], server)
                if remRole:
                    if remRole in member.roles:
                        remRoles.append(remRole)
            # await member.remove_roles(*remRoles)
            # Use role manager instead
            self.settings.role.rem_roles(member, remRoles)
            if not newRole:
                # Promotion role doesn't exist
                msg = 'It looks like **{}** is no longer on this server.  *{} xp* was still taken from *{}* - but I am unable to demote them to a non-existent role.  Consider revising your xp roles.'.format(promoArray[nextRole]['Name'], neededXp*-1, DisplayName.name(member))
            else:
                msg = '*{} xp* was taken from *{}* and they were demoted to **{}**!'.format(neededXp*-1, DisplayName.name(member), newRole.name)
        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await channel.send(msg)


    @commands.command(pass_context=True)
    async def demoteto(self, ctx, *, member = None, role = None):
        """Auto-removes the required xp to demote the passed user to the passed role (admin only)."""

        author  = ctx.message.author
        server  = ctx.message.guild
        channel = ctx.message.channel

        # Only allow admins to change server stats
        if not await self._can_run(ctx):
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False
        
        usage = 'Usage: `{}demoteto [member] [role]`'.format(ctx.prefix)

        if member == None:
            await ctx.channel.send(usage)
            return

        if role == None:
            # Either a role wasn't set - or it's the last section
            if type(member) is str:
                # It' a string - the hope continues
                # Let's search for a name at the beginning - and a role at the end
                parts = member.split()
                memFromName = None
                for j in range(len(parts)):
                    # Reverse search direction
                    i = len(parts)-1-j
                    # Name = 0 up to i joined by space
                    nameStr = ' '.join(parts[0:i+1])
                    # Role = end of name -> end of parts joined by space
                    roleStr = ' '.join(parts[i+1:])
                    memFromName = DisplayName.memberForName(nameStr, ctx.message.guild)
                    if memFromName:
                        # We got a member - let's check for a role
                        roleFromName = DisplayName.roleForName(roleStr, ctx.message.guild)
                            
                        if not roleFromName == None:
                            # We got a member and a role - break
                            role = roleFromName
                            break
                if memFromName == None:
                    # Never found a member at all
                    msg = 'I couldn\'t find *{}* on the server.'.format(member)
                    # Check for suppress
                    if suppress:
                        msg = Nullify.clean(msg)
                    await ctx.channel.send(msg)
                    return
                if roleFromName == None:
                    # We couldn't find one or the other
                    await ctx.channel.send(usage)
                    return

                member = memFromName

        # Get user's xp
        xp = int(self.settings.getUserStat(member, server, "XP"))

        # Get the role list
        promoArray = self.getSortedRoles(server)
        nextRole = self.getIndexForRole(role, server)
        currentRole = self.getCurrentRoleIndex(member, server)
        vowels = 'aeiou'
        
        if nextRole == None:
            msg = '**{}** doesn\'t appear to be in the xp role list - consider adding it with the `{}addxprole [role] [xp amount]` command.'.format(role.name, ctx.prefix)
            # Check for suppress
            if suppress:
                msg = Nullify.clean(msg)
            await channel.send(msg)
            return

        if currentRole == nextRole:
            # We are already the target role
            if role.name[:1].lower() in vowels:
                msg = '*{}* is already an **{}**.'.format(DisplayName.name(member), role.name)
            else:
                msg = '*{}* is already a **{}**.'.format(DisplayName.name(member), role.name)
            # Check for suppress
            if suppress:
                msg = Nullify.clean(msg)
            await channel.send(msg)
            return
        elif currentRole < nextRole:
            # We are a higher role than the target
            msg = 'I can\'t demote *{}* to a higher role.'.format(DisplayName.name(member))
            # Check for suppress
            if suppress:
                msg = Nullify.clean(msg)
            await channel.send(msg)
            return

        newRole  = DisplayName.roleForID(promoArray[nextRole]['ID'], server)
        neededXp = int(promoArray[nextRole]['XP'])-xp
        self.settings.incrementStat(member, server, "XP", neededXp)
        # Start at the currentRole and remove that and all roles above
        remRoles = []
        for i in range(currentRole, len(promoArray)):
            remRole  = DisplayName.roleForID(promoArray[i]['ID'], server)
            if remRole:
                if remRole in member.roles:
                    # Only add the ones we have
                    remRoles.append(remRole)
        # await member.remove_roles(*remRoles)
        # Use role manager instead
        self.settings.role.rem_roles(member, remRoles)
        if not newRole:
            # Promotion role doesn't exist
            msg = 'It looks like **{}** is no longer on this server.  *{} xp* was still taken from *{}* - but I am unable to demote them to a non-existent role.  Consider revising your xp roles.'.format(promoArray[nextRole]['Name'], neededXp*-1, DisplayName.name(member))
        else:
            msg = '*{} xp* was taken from *{}* and they were demoted to **{}**!'.format(neededXp*-1, DisplayName.name(member), newRole.name)
        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await channel.send(msg)


    def getCurrentRoleIndex(self, member, server):
        # Helper method to get the role index the user *should* have
        # Get user's xp
        xp = int(self.settings.getUserStat(member, server, "XP"))
        promoSorted = self.getSortedRoles(server)
        if not promoSorted:
            return 0
        index = 0
        topIndex = -1
        for role in promoSorted:
            if int(role['XP']) <= xp:
                topIndex = index
            index += 1
        return topIndex

    def getIndexForRole(self, role, server):
        # Helper method to get the sorted index for an xp role
        # Returns None if not found
        promoSorted = self.getSortedRoles(server)
        if not promoSorted:
            return 0
        index = 0
        found = False
        for arole in promoSorted:
            if str(arole['ID']) == str(role.id):
                # Found it - break
                found = True
                break
            index += 1
        if found:
            return index
        return None


    def getSortedRoles(self, server):
        # Get the role list
        promoArray = self.settings.getServerStat(server, "PromotionArray")
        # promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
        promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
        if len(promoSorted):
            return promoSorted
        else:
            return None