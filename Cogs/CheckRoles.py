import asyncio
import discord
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
    # This module isn't actually a cog
    return

async def checkroles(user, channel, settings, bot, suppress : bool = False):
    # This method checks whether we need to promote, demote, or whatever
    # then performs the said action, and outputs.
    
    if type(channel) is discord.Guild:
        server = channel
        channel = None
    else:
        server = channel.guild
    
    # Get our preliminary vars
    msg         = None
    xpPromote   = settings.getServerStat(server,     "XPPromote")
    xpDemote    = settings.getServerStat(server,     "XPDemote")
    userXP      = int(settings.getUserStat(user, server, "XP"))
    suppProm    = settings.getServerStat(server, "SuppressPromotions")
    suppDem     = settings.getServerStat(server, "SuppressDemotions")
    onlyOne     = settings.getServerStat(server, "OnlyOneRole")

    # Check if we're suppressing @here and @everyone mentions
    if settings.getServerStat(server, "SuppressMentions"):
        suppressed = True
    else:
        suppressed = False

    changed = False
    promoArray = settings.getServerStat(server, "PromotionArray")
    promoArray = sorted(promoArray, key=lambda x:int(x['XP']))

    addRoles = []
    remRoles = []

    # Final checks for singular role-holding.  Will find a better system at
    # some point - probably...
    if onlyOne:
        # Only one role allowed, make sure we don't have the rest
        # Get the role we're supposed to be at
        current_role = None
        is_higher    = False
        target_role  = None
        for role in promoArray:
            test_role = DisplayName.roleForID(role['ID'], server)
            # Check if it's a real role
            if not test_role:
                continue
            if int(role["XP"]) > userXP:
                # We don't have xp for this role
                # Set it if we already have it though
                if test_role in user.roles:
                    current_role = test_role
                    is_higher = True
            else:
                # We've got the resources for it
                target_role = test_role
                # Set it if we already have it though
                if test_role in user.roles:
                    current_role = test_role

        # Remove all roles except current
        if current_role == target_role:
            for role in promoArray:
                test_role = DisplayName.roleForID(role['ID'], server)
                if test_role != target_role and test_role in user.roles:
                    changed = True
                    remRoles.append(test_role)
        else:
            # Demote if needed
            if is_higher:
                if xpDemote:
                    # We can remove roles above - but keep the last one
                    msg = '*{}* was demoted from **{}**!'.format(DisplayName.name(user), current_role.name)
                    for role in promoArray:
                        test_role = DisplayName.roleForID(role['ID'], server)
                        if test_role != target_role and test_role in user.roles:
                            remRoles.append(test_role)
                    addRoles.append(target_role)
                    changed = True
                else:
                    # We're not demoting - but let's add only the current role to the list
                    for role in promoArray:
                        test_role = DisplayName.roleForID(role['ID'], server)
                        if test_role != current_role and test_role in user.roles:
                            remRoles.append(test_role)
                            changed = True
            # Promote if needed
            else:
                if xpPromote:
                    # Remove all roles below
                    msg = '*{}* was promoted to **{}**!'.format(DisplayName.name(user), target_role.name)
                    for role in promoArray:
                        test_role = DisplayName.roleForID(role['ID'], server)
                        if test_role != target_role and test_role in user.roles:
                            remRoles.append(test_role)
                    addRoles.append(target_role)
                    changed = True
                else:
                    # We're not promoting - but let's add only the current role to the list
                    for role in promoArray:
                        test_role = DisplayName.roleForID(role['ID'], server)
                        if test_role != current_role and test_role in user.roles:
                            remRoles.append(test_role)
                            changed = True

    else:
        # Check promotions first
        if xpPromote:
            # This is, by far, the more functional way
            for role in promoArray:
                # Iterate through the roles, and add which we have xp for
                if int(role['XP']) <= userXP:
                    # We *can* have this role, let's add it to a list
                    addRole = DisplayName.roleForID(role['ID'], server)
                    if addRole:
                        if not addRole in user.roles:
                            addRoles.append(addRole)
                            if not suppProm:
                                msg = '*{}* was promoted to **{}**!'.format(DisplayName.name(user), addRole.name)
                            changed = True
        # Allow independent promotion/demotion
        if xpDemote:
            for role in promoArray:
                # Iterate through the roles, and add which we have xp for
                if int(role['XP']) > userXP:
                    # We *can* have this role, let's add it to a list
                    remRole = DisplayName.roleForID(role['ID'], server)
                    if remRole:
                        if remRole in user.roles:
                            remRoles.append(remRole)
                            if not suppDem:
                                msg = '*{}* was demoted from **{}**!'.format(DisplayName.name(user), remRole.name)
                            changed = True

    # Add and remove roles as needed
    if len(addRoles) or len(remRoles):
        settings.role.change_roles(user, add_roles=addRoles, rem_roles=remRoles)

    # Check if we have a message to display - and display it
    if msg and channel and (not suppress):
        # Check for suppress
        if suppressed:
            msg = Nullify.clean(msg)
        await channel.send(msg)
    return changed
