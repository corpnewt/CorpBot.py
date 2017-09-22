import asyncio
import discord
import time
from Cogs import DisplayName
from Cogs import Nullify

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Mute(bot, settings))

class Mute:

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.loop_list = []

    def _is_submodule(self, parent, child):
        return parent == child or child.startswith(parent + ".")

    @asyncio.coroutine
    async def on_unloaded_extension(self, ext):
        # Called to shut things down
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        for task in self.loop_list:
            task.cancel()

    @asyncio.coroutine
    async def on_loaded_extension(self, ext):
        # See if we were loaded
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        # Check all mutes and start timers
        for server in self.bot.guilds:
            muteList = self.settings.getServerStat(server, "MuteList")
            for entry in muteList:
                member = DisplayName.memberForID(entry['ID'], server)
                if member:
                    # We have a user! Check for a cooldown
                    cooldown = entry['Cooldown']
                    if cooldown == None:
                        continue
                    self.loop_list.append(self.bot.loop.create_task(self.checkMute(member, server, cooldown)))
                    
        
    def suppressed(self, guild, msg):
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(guild, "SuppressMentions").lower() == "yes":
            return Nullify.clean(msg)
        else:
            return msg

    async def onjoin(self, member, server):
        # Check if the new member was muted when they left
        muteList = self.settings.getServerStat(server, "MuteList")
        for entry in muteList:
            if str(entry['ID']) == str(member.id):
                # Found them - mute them
                await self.mute(member, server, entry['Cooldown'])

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
            pm = 'You have been **Unmuted**.\n\nYou can send messages on *{}* again.'.format(self.suppressed(server, server.name))
            await member.send(pm)


    async def mute(self, member, server, cooldown = None):
        # Mutes the specified user on the specified server
        for channel in server.channels:
            if not type(channel) is discord.TextChannel:
                continue
            perms = member.permissions_in(channel)
            if perms.read_messages:
                overs = channel.overwrites_for(member)
                if not overs.send_messages == False:
                    # We haven't been muted here yet
                    overs.send_messages = False
                    overs.add_reactions = False
                    try:
                        await channel.set_permissions(member, overwrite=overs)
                    except Exception:
                        continue
        
        self.settings.setUserStat(member, server, "Muted", "Yes")
        self.settings.setUserStat(member, server, "Cooldown", cooldown)

        muteList = self.settings.getServerStat(server, "MuteList")
        
        # check if we're already muted
        found = False
        for entry in muteList:
            if str(entry['ID']) == str(member.id):
                # Set the cooldown
                found = True
                entry['Cooldown'] = cooldown
                break
        if not found:
            muteList.append({ 'ID': member.id, 'Cooldown': cooldown })
        
        if not cooldown == None:
            # We have a cooldown - set a timer
            self.bot.loop.create_task(self.checkMute(member, server, cooldown))


    async def unmute(self, member, server):
        # Unmutes the specified user on the specified server
        for channel in server.channels:
                if not type(channel) is discord.TextChannel:
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
                                await channel.set_permissions(member, overwrite=overs)
                            except Exception:
                                continue
                        else:
                            # No other overwrites - delete custom perms
                            try:
                                await channel.set_permissions(member, overwrite=None)
                            except Exception:
                                continue
        self.settings.setUserStat(member, server, "Muted", "No")
        self.settings.setUserStat(member, server, "Cooldown", None)

        muteList = self.settings.getServerStat(server, "MuteList")
        for entry in muteList:
            if str(entry['ID']) == str(member.id):
                # Found them - remove from the mutelist
                muteList.remove(entry)
