import asyncio
import discord
import time

class Mute:

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings


    async def onready(self):
        # Check all reminders - and start timers
        for server in self.bot.servers:
            for member in server.members:
                isMute = self.settings.getUserStat(member, server, "Muted")
                if isMute.lower() == "yes":
                    # We're muted
                    cooldown = self.settings.getUserStat(member, server, "Cooldown")
                    if cooldown == None:
                        continue
                    self.bot.loop.create_task(self.checkMute(member, server, cooldown))


    async def checkMute(self, member, server, cooldown):
        # Check if we have a cooldown left - and unmute accordingly
        timeleft = int(cooldown)-int(time.time())
        if timeleft > 0:
            # Time to wait yet - sleep
            await asyncio.sleep(timeleft)

        # We've waited it out - unmute if needed
        # But check if the mute time has changed
        cd = self.settings.getUserStat(member, server, "Cooldown")
        isMute = self.settings.getUserStat(member, server, "Muted")
        if cd == None:
            if isMute.lower() == 'yes':
                # We're now muted permanently
                return
        else:
            timeleft = int(cd)-int(time.time())
            if timeleft > 0:
                # Our cooldown changed - rework
                self.bot.loop.create_task(self.checkMute(member, server, cd))
                return

        # Here - we either have surpassed our cooldown - or we're not muted anymore
        isMute = self.settings.getUserStat(member, server, "Muted")
        if isMute.lower() == "yes":
            await self.unmute(member, server)
            pm = 'You have been **Unmuted**.\n\nYou can send messages on *{}* again.'.format(server.name)
            await self.bot.send_message(member, pm)


    async def mute(self, member, server, cooldown = None):
        # Mutes the specified user on the specified server
        for channel in server.channels:
            if not channel.type is discord.ChannelType.text:
                continue
            perms = member.permissions_in(channel)
            if perms.read_messages:
                overs = channel.overwrites_for(member)
                if not overs.send_messages == False:
                    # We haven't been muted here yet
                    overs.send_messages = False
                    overs.add_reactions = False
                    try:
                        await self.bot.edit_channel_permissions(channel, member, overs)
                    except Exception:
                        continue
        
        self.settings.setUserStat(member, server, "Muted", "Yes")
        self.settings.setUserStat(member, server, "Cooldown", cooldown)

        if not cooldown == None:
            # We have a cooldown - set a timer
            self.bot.loop.create_task(self.checkMute(member, server, cooldown))


    async def unmute(self, member, server):
        # Unmutes the specified user on the specified server
        for channel in server.channels:
                if not channel.type is discord.ChannelType.text:
                    continue
                perms = member.permissions_in(channel)
                if perms.read_messages:
                    overs = channel.overwrites_for(member)
                    otherPerms = False
                    for perm in overs:
                        if not perm[1] == None and not str(perm[0]) == 'send_messages' and not str(perm[0]) == 'add_reactions':
                            otherPerms = True
                    if overs.send_messages == False:
                        # We haven't been muted here yet
                        if otherPerms:
                            # We have other overwrites - preserve those
                            overs.send_messages = None
                            overs.add_reactions = None
                            try:
                                await self.bot.edit_channel_permissions(channel, member, overs)
                            except Exception:
                                continue
                        else:
                            # No other overwrites - delete custom perms
                            try:
                                await self.bot.delete_channel_permissions(channel, member)
                            except Exception:
                                continue