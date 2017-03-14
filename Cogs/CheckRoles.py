import asyncio
import discord
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify

async def checkroles(user, channel, settings, bot, suppress : bool = False):
    # This method checks whether we need to promote, demote, or whatever
    # then performs the said action, and outputs.
    
    server = channel.server
    
    # Get our preliminary vars
    msg         = None
    xpPromote   = settings.getServerStat(server,     "XPPromote")
    xpDemote    = settings.getServerStat(server,     "XPDemote")
    userXP      = int(settings.getUserStat(user, server, "XP"))
    suppProm    = settings.getServerStat(server, "SuppressPromotions")
    suppDem     = settings.getServerStat(server, "SuppressDemotions")

    # Check if we're suppressing @here and @everyone mentions
    if settings.getServerStat(server, "SuppressMentions").lower() == "yes":
        suppressed = True
    else:
        suppressed = False

    changed = False
    promoArray = settings.getServerStat(server, "PromotionArray")
    promoArray = sorted(promoArray, key=lambda x:int(x['XP']))

    addRoles = []
    remRoles = []

    # Check promotions first
    if xpPromote.lower() == "yes":
        # This is, by far, the more functional way
        for role in promoArray:
            # Iterate through the roles, and add which we have xp for
            if int(role['XP']) <= userXP:
                # We *can* have this role, let's add it to a list
                addRole = DisplayName.roleForID(role['ID'], server)
                if addRole:
                    if not addRole in user.roles:
                        addRoles.append(addRole)
                        if not suppProm.lower() == "yes":
                            msg = '*{}* was promoted to **{}**!'.format(DisplayName.name(user), addRole.name)
                        changed = True

    # Allow independent promotion/demotion
    if xpDemote.lower() == "yes":
        for role in promoArray:
            # Iterate through the roles, and add which we have xp for
            if int(role['XP']) > userXP:
                # We *can* have this role, let's add it to a list
                remRole = DisplayName.roleForID(role['ID'], server)
                if remRole:
                    if remRole in user.roles:
                        remRoles.append(remRole)
                        if not suppDem.lower() == "yes":
                            msg = '*{}* was demoted from **{}**!'.format(DisplayName.name(user), remRole.name)
                        changed = True
    

    # Add and remove roles as needed
    if len(addRoles):
        try:
            await bot.add_roles(user, *addRoles)
        except Exception:
            pass
    if len(remRoles):
        try:
            await bot.remove_roles(user, *remRoles)
        except Exception:
            pass

    # Check if we have a message to display - and display it
    if msg and (not suppress):
        # Check for suppress
        if suppressed:
            msg = Nullify.clean(msg)
        await bot.send_message(channel, msg)
    return changed
