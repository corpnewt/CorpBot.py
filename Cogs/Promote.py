import asyncio
import discord
from discord.ext import commands
from Cogs import Utils, DisplayName, Xp


def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Promote(bot, settings))

# This module is for auto promoting/demoting of roles - admin only


class Promote(commands.Cog):

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    async def _can_run(self, ctx, reply=True):
        # Check if we're admin - and if not, check if bot admins can run this
        # and if we're bot admin
        if Utils.is_admin(ctx):
            return True
        if self.settings.getServerStat(ctx.guild, "BotAdminAsAdmin", False) and Utils.is_bot_admin_only(ctx):
            return True
        if reply:
            await ctx.send("You do not have sufficient privileges to access this command.")
        return False

    @commands.command(pass_context=True)
    async def promote(self, ctx, *, member=None):
        """Auto-adds the required xp to promote the passed user to the next role (admin only)."""
        # Only allow admins to change server stats
        if not await self._can_run(ctx):
            return
        usage = 'Usage: `{}promote [member]`'.format(ctx.prefix)

        if member == None:
            return await ctx.send(usage)

        memberName = member
        member = DisplayName.memberForName(memberName, ctx.guild)
        if not member:
            msg = 'I couldn\'t find *{}*...'.format(memberName)
            return await ctx.send(Utils.suppressed(ctx, msg))

        # Get user's xp
        xp = int(self.settings.getUserStat(member, ctx.guild, "XP"))

        # Get the role list
        promoArray = self.getSortedRoles(ctx.guild)
        currentRole = self.getCurrentRoleIndex(member, ctx.guild)
        nextRole = currentRole + 1
        neededXp = 0
        if nextRole >= len(promoArray):
            msg = 'There are no higher roles to promote *{}* into.'.format(
                DisplayName.name(member))
        else:
            newRole = DisplayName.roleForID(
                promoArray[nextRole]['ID'], ctx.guild)
            neededXp = int(promoArray[nextRole]['XP'])-xp
            self.settings.incrementStat(member, ctx.guild, "XP", neededXp)
            # Start at the bottom role and add all roles up to newRole
            addRoles = []
            for i in range(0, nextRole+1):
                addRole = DisplayName.roleForID(promoArray[i]['ID'], ctx.guild)
                if addRole:
                    if not addRole in member.roles:
                        addRoles.append(addRole)
            # await member.add_roles(*addRoles)
            # Use role manager instead
            self.settings.role.add_roles(member, addRoles)
            if not newRole:
                # Promotion role doesn't exist
                msg = 'It looks like **{}** is no longer on this server.  *{}* was still given *{:,} xp* - but I am unable to promote them to a non-existent role.  Consider revising your xp roles.'.format(
                    promoArray[nextRole]['Name'], DisplayName.name(member), neededXp)
            else:
                msg = '*{}* was given *{:,} xp* and promoted to **{}**!'.format(
                    DisplayName.name(member), neededXp, newRole.name)
            self.bot.dispatch("xp", member, ctx.author, neededXp)
        await ctx.send(Utils.suppressed(ctx, msg))

    @commands.command(pass_context=True)
    async def promoteto(self, ctx, *, member=None, role=None):
        """Auto-adds the required xp to promote the passed user to the passed role (admin only)."""
        if not await self._can_run(ctx):
            return
        usage = 'Usage: `{}promoteto [member] [role]`'.format(ctx.prefix)

        if member == None:
            return await ctx.send(usage)

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
                    memFromName = DisplayName.memberForName(nameStr, ctx.guild)
                    if memFromName:
                        # We got a member - let's check for a role
                        roleFromName = DisplayName.roleForName(
                            roleStr, ctx.guild)

                        if not roleFromName == None:
                            # We got a member and a role - break
                            role = roleFromName
                            break
                if memFromName == None:
                    # Never found a member at all
                    msg = 'I couldn\'t find *{}* on the server.'.format(member)
                    return await ctx.send(Utils.suppressed(ctx, msg))
                if roleFromName == None:
                    # We couldn't find one or the other
                    return await ctx.send(usage)

                member = memFromName

        # Get user's xp
        xp = int(self.settings.getUserStat(member, ctx.guild, "XP"))

        # Get the role list
        promoArray = self.getSortedRoles(ctx.guild)
        nextRole = self.getIndexForRole(role, ctx.guild)
        currentRole = self.getCurrentRoleIndex(member, ctx.guild)
        vowels = 'aeiou'

        if nextRole == None:
            msg = '**{}** doesn\'t appear to be in the xp role list - consider adding it with the `{}addxprole [role] [xp amount]` command.'.format(
                role.name, ctx.prefix)
            return await ctx.send(Utils.suppressed(ctx, msg))

        if currentRole == nextRole:
            # We are already the target role
            if role.name[:1].lower() in vowels:
                msg = '*{}* is already an **{}**.'.format(
                    DisplayName.name(member), role.name)
            else:
                msg = '*{}* is already a **{}**.'.format(
                    DisplayName.name(member), role.name)
            return await ctx.send(Utils.suppressed(ctx, msg))
        elif currentRole > nextRole:
            # We are a higher role than the target
            msg = '*{}* already has **{}** in their collection of roles.'.format(
                DisplayName.name(member), role.name)
            return await ctx.send(Utils.suppressed(ctx, msg))

        if nextRole >= len(promoArray):
            msg = 'There are no higher roles to promote *{}* into.'.format(
                DisplayName.name(member))
        else:
            newRole = DisplayName.roleForID(
                promoArray[nextRole]['ID'], ctx.guild)
            neededXp = int(promoArray[nextRole]['XP'])-xp
            self.settings.incrementStat(member, ctx.guild, "XP", neededXp)
            # Start at the bottom role and add all roles up to newRole
            addRoles = []
            for i in range(0, nextRole+1):
                addRole = DisplayName.roleForID(promoArray[i]['ID'], ctx.guild)
                if addRole:
                    if not addRole in member.roles:
                        addRoles.append(addRole)
            # await member.add_roles(*addRoles)
            # Use role manager instead
            self.settings.role.add_roles(member, addRoles)
            if not newRole:
                # Promotion role doesn't exist
                msg = 'It looks like **{}** is no longer on this server.  *{}* was still given *{:,} xp* - but I am unable to promote them to a non-existent role.  Consider revising your xp roles.'.format(
                    promoArray[nextRole]['Name'], DisplayName.name(member), neededXp)
            else:
                msg = '*{}* was given *{:,} xp* and promoted to **{}**!'.format(
                    DisplayName.name(member), neededXp, newRole.name)
            self.bot.dispatch("xp", member, ctx.author, neededXp)
        return await ctx.send(Utils.suppressed(ctx, msg))

    @commands.command(pass_context=True)
    async def demote(self, ctx, *, member=None):
        """Auto-removes the required xp to demote the passed user to the previous role (admin only)."""
        if not await self._can_run(ctx):
            return
        usage = 'Usage: `{}demote [member]`'.format(ctx.prefix)

        if member == None:
            return await ctx.send(usage)

        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                return await ctx.send(Utils.suppressed(ctx, msg))

        # Get user's xp
        xp = int(self.settings.getUserStat(member, ctx.guild, "XP"))

        # Get the role list
        promoArray = self.getSortedRoles(ctx.guild)
        currentRole = self.getCurrentRoleIndex(member, ctx.guild)
        nextRole = currentRole - 1
        if nextRole == -1:
            # We're removing the user from all roles
            neededXp = int(promoArray[0]['XP'])-xp-1
            self.settings.incrementStat(member, ctx.guild, "XP", neededXp)
            remRoles = []
            for i in range(0, len(promoArray)):
                remRole = DisplayName.roleForID(promoArray[i]['ID'], ctx.guild)
                if remRole:
                    if remRole in member.roles:
                        remRoles.append(remRole)
            # await member.remove_roles(*remRoles)
            # Use role manager instead
            self.settings.role.rem_roles(member, remRoles)
            msg = '*{} xp* was taken from *{}* and they were demoted out of the xp system!'.format(
                neededXp*-1, DisplayName.name(member))
            self.bot.dispatch("xp", member, ctx.author, neededXp)
        elif nextRole < -1:
            msg = 'There are no lower roles to demote *{}* into.'.format(
                DisplayName.name(member))
        else:
            newRole = DisplayName.roleForID(
                promoArray[nextRole]['ID'], ctx.guild)
            neededXp = int(promoArray[nextRole]['XP'])-xp
            self.settings.incrementStat(member, ctx.guild, "XP", neededXp)
            # Start at the currentRole and remove that and all roles above
            remRoles = []
            for i in range(currentRole, len(promoArray)):
                remRole = DisplayName.roleForID(promoArray[i]['ID'], ctx.guild)
                if remRole:
                    if remRole in member.roles:
                        remRoles.append(remRole)
            # await member.remove_roles(*remRoles)
            # Use role manager instead
            self.settings.role.rem_roles(member, remRoles)
            if not newRole:
                # Promotion role doesn't exist
                msg = 'It looks like **{}** is no longer on this server.  *{:,} xp* was still taken from *{}* - but I am unable to demote them to a non-existent role.  Consider revising your xp roles.'.format(
                    promoArray[nextRole]['Name'], neededXp*-1, DisplayName.name(member))
            else:
                msg = '*{:,} xp* was taken from *{}* and they were demoted to **{}**!'.format(
                    neededXp*-1, DisplayName.name(member), newRole.name)
            self.bot.dispatch("xp", member, ctx.author, neededXp)
        return await ctx.send(Utils.suppressed(ctx, msg))

    @commands.command(pass_context=True)
    async def demoteto(self, ctx, *, member=None, role=None):
        """Auto-removes the required xp to demote the passed user to the passed role (admin only)."""
        if not await self._can_run(ctx):
            return
        usage = 'Usage: `{}demoteto [member] [role]`'.format(ctx.prefix)

        if member == None:
            return await ctx.send(usage)

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
                    memFromName = DisplayName.memberForName(
                        nameStr, ctx.message.guild)
                    if memFromName:
                        # We got a member - let's check for a role
                        roleFromName = DisplayName.roleForName(
                            roleStr, ctx.message.guild)

                        if not roleFromName == None:
                            # We got a member and a role - break
                            role = roleFromName
                            break
                if memFromName == None:
                    # Never found a member at all
                    msg = 'I couldn\'t find *{}* on the server.'.format(member)
                    return await ctx.send(Utils.suppressed(ctx, msg))
                if roleFromName == None:
                    # We couldn't find one or the other
                    return await ctx.send(usage)

                member = memFromName

        # Get user's xp
        xp = int(self.settings.getUserStat(member, ctx.guild, "XP"))

        # Get the role list
        promoArray = self.getSortedRoles(ctx.guild)
        nextRole = self.getIndexForRole(role, ctx.guild)
        currentRole = self.getCurrentRoleIndex(member, ctx.guild)
        vowels = 'aeiou'

        if nextRole == None:
            msg = '**{}** doesn\'t appear to be in the xp role list - consider adding it with the `{}addxprole [role] [xp amount]` command.'.format(
                role.name, ctx.prefix)
            return await ctx.send(Utils.suppressed(ctx, msg))

        if currentRole == nextRole:
            # We are already the target role
            if role.name[:1].lower() in vowels:
                msg = '*{}* is already an **{}**.'.format(
                    DisplayName.name(member), role.name)
            else:
                msg = '*{}* is already a **{}**.'.format(
                    DisplayName.name(member), role.name)
            return await ctx.send(Utils.suppressed(ctx, msg))
        elif currentRole < nextRole:
            # We are a higher role than the target
            msg = 'I can\'t demote *{}* to a higher role.'.format(
                DisplayName.name(member))
            return await ctx.send(Utils.suppressed(ctx, msg))

        newRole = DisplayName.roleForID(promoArray[nextRole]['ID'], ctx.guild)
        neededXp = int(promoArray[nextRole]['XP'])-xp
        self.settings.incrementStat(member, ctx.guild, "XP", neededXp)
        # Start at the currentRole and remove that and all roles above
        remRoles = []
        for i in range(currentRole, len(promoArray)):
            remRole = DisplayName.roleForID(promoArray[i]['ID'], ctx.guild)
            if remRole:
                if remRole in member.roles:
                    # Only add the ones we have
                    remRoles.append(remRole)
        # await member.remove_roles(*remRoles)
        # Use role manager instead
        self.settings.role.rem_roles(member, remRoles)
        if not newRole:
            # Promotion role doesn't exist
            msg = 'It looks like **{}** is no longer on this server.  *{:,} xp* was still taken from *{}* - but I am unable to demote them to a non-existent role.  Consider revising your xp roles.'.format(
                promoArray[nextRole]['Name'], neededXp*-1, DisplayName.name(member))
        else:
            msg = '*{:,} xp* was taken from *{}* and they were demoted to **{}**!'.format(
                neededXp*-1, DisplayName.name(member), newRole.name)
        self.bot.dispatch("xp", member, ctx.author, neededXp)
        return await ctx.send(Utils.suppressed(ctx, msg))

    def getCurrentRoleIndex(self, member, server):
        # Helper method to get the role index the user *should* have
        # Get user's xp
        xp = int(self.settings.getUserStat(member, server, "XP"))
        promoSorted = self.getSortedRoles(server)
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
        if not type(promoArray) is list:
            promoArray = []
        # promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
        promoSorted = sorted(promoArray, key=lambda x: int(x['XP']))
        return promoSorted
