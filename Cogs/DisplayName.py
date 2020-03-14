import asyncio
import discord
import re
from   discord.ext import commands
from   Cogs import Nullify

# Stupid global vars because I didn't plan this
# out correctly... sigh...
bot = None

def setup(bot):
	# This module isn't actually a cog - but it is a place
    # we can start small fires and watch them burn the entire
    # house to the ground.
    bot.add_cog(DisplayName(bot))
    
    # global bot
    # bot = bot_start
    # return

class DisplayName(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    def clean_message(self, message, *, bot = None, server = None, nullify = True):
        # Searches for <@ > and <!@ > and gets the ids between
        # then resolves them to their user name if it can be determined
        
        if nullify:
            # Strip out @here and @everyone first
            zerospace = "​"
            message = message.replace("@everyone", "@{}everyone".format(zerospace)).replace("@here", "@{}here".format(zerospace))
        # Check for matches
        matches_re = re.finditer(r"\<[!&#\@]*[^<\@!&#]+[0-9]\>", message)
        matches = []
        matches = [x.group(0) for x in matches_re]
        if not len(matches):
            return message
        for match in matches:
            if server:
                # Have the server, bot doesn't matter
                # Let's do this right
                if "#" in match:
                    # It should be a channel
                    mem = self.channelForName(match, server)
                elif "&" in match:
                    # It should be a role
                    mem = self.roleForName(match, server)
                else:
                    # Guess it's a user
                    mem = self.memberForName(match, server)
                if not mem:
                    continue
                mem_name = self.name(mem)
            else:
                # Must have bot then
                memID = re.sub(r'\W+', '', match)
                mem = self.bot.get_user(int(memID))
                if mem == None:
                    continue
                mem_name = mem.name
            message = message.replace(match, mem_name)
        return message

    def name(self, member : discord.Member):
        # A helper function to return the member's display name
        nick = name = None
        try:
            nick = member.nick
        except AttributeError:
            pass
        try:
            name = member.name
        except AttributeError:
            pass
        if nick:
            return Nullify.clean(nick)
        if name:
            return Nullify.clean(name)
        return None

    def memberForID(self, checkid, server):
        if server == None:
            mems = self.bot.users
        else:
            mems = server.members
        try:
            checkid = int(checkid)
        except:
            return None
        for member in mems:
            if member.id == checkid:
                return member
        return None

    def memberForName(self, name, server):
        if server == None:
            # No server passed - this is likely happening
            # in dm - let's get a user as-is.
            mems = self.bot.users
        else:
            # We got a server - let's get that server's members
            mems = server.members
        # Check nick first - then name
        name = str(name)
        for member in mems:
            if not hasattr(member,"nick"):
                # No nick property - must be a user, bail
                break
            if member.nick:
                if member.nick.lower() == name.lower():
                    return member
        for member in mems:
            if member.name.lower() == name.lower():
                return member
        mem_parts = name.split("#")
        if len(mem_parts) == 2:
            # We likely have a name#descriminator
            try:
                mem_name = mem_parts[0]
                mem_disc = int(mem_parts[1])
            except:
                mem_name = mem_disc = None
            if mem_name:
                for member in mems:
                    if member.name.lower() == mem_name.lower() and int(member.discriminator) == mem_disc:
                        return member
        mem_id = re.sub(r'\W+', '', name)
        new_mem = self.memberForID(mem_id, server)
        if new_mem:
            return new_mem
        
        return None

    def channelForID(self, checkid, server, typeCheck = None):
        try:
            checkid = int(checkid)
        except:
            return None
        for channel in server.channels:
            if typeCheck:
                if typeCheck.lower() == "text" and not type(channel) is discord.TextChannel:
                    continue
                if typeCheck.lower() == "voice" and not type(channel) is discord.VoiceChannel:
                    continue
                if typeCheck.lower() == "category" and not type(channel) is discord.CategoryChannel:
                    continue
            if channel.id == checkid:
                return channel
        return None

    def channelForName(self, name, server, typeCheck = None):
        name = str(name)
        for channel in server.channels:
            if typeCheck:
                if typeCheck.lower() == "text" and not type(channel) is discord.TextChannel:
                    continue
                if typeCheck.lower() == "voice" and not type(channel) is discord.VoiceChannel:
                    continue
                if typeCheck.lower() == "category" and not type(channel) is discord.CategoryChannel:
                    continue
            if channel.name.lower() == name.lower():
                return channel
        chanID = re.sub(r'\W+', '', name)
        newChan = self.channelForID(chanID, server, typeCheck)
        if newChan:
            return newChan
        return None

    def roleForID(self, checkid, server):
        try:
            checkid = int(checkid)
        except:
            return None
        for role in server.roles:
            if role.id == checkid:
                return role
        return None

    def roleForName(self, name, server):
        name = str(name)
        # Adjust for "everyone"
        if name.lower() == "everyone":
            name = "@everyone"
        for role in server.roles:
            if role.name.lower() == name.lower():
                return role
        # No role yet - try ID
        roleID = ''.join(list(filter(str.isdigit, name)))
        newRole = self.roleForID(roleID, server)
        if newRole:
            return newRole
        return None

    def serverNick(self, user, server):
        for member in server.members:
            if member.id == user.id:
                return self.name(member)
        return None

    def checkNameForInt(self, name, server):
        name = str(name)
        theList = name.split()
        # We see if we have multiple parts split by a space
        if len(theList)<2:
            # Only one part - no int included (or not separated by space)
            # Check if member exists - and if not throw an error, if so, throw a diff error
            amember = self.memberForName(name, server)
            if amember:
                # We at least have a member
                return { "Member" : amember, "Int" : None }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, name)))
                newMem = self.memberForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Member" : newMem, "Int" : None }
                else:
                    # Nothing was right about this...
                    return { "Member" : None, "Int" : None }
        try:
            # Let's cast the last item as an int and catch any exceptions
            theInt = int(theList[len(theList)-1])
            newMemberName = " ".join(theList[:-1])
            amember = self.memberForName(newMemberName, server)
            if amember:
                return { "Member" : amember, "Int" : theInt }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, newMemberName)))
                newMem = self.memberForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Member" : newMem, "Int" : theInt }
                else:
                    # Nothing was right about this...
                    return { "Member" : None, "Int" : None }
        except ValueError:
            # Last section wasn't an int
            amember = self.memberForName(name, server)
            if amember:
                # Name was just a member - return
                return { "Member" : amember, "Int" : None }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, name)))
                newMem = self.memberForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Member" : newMem, "Int" : None }
                else:
                    # Nothing was right about this...
                    return { "Member" : None, "Int" : None }
        # Should never get here
        return None

    def checkRoleForInt(self, name, server):
        name = str(name)
        theList = name.split()
        # We see if we have multiple parts split by a space
        if len(theList)<2:
            # Only one part - no int included (or not separated by space)
            # Check if role exists - and if not throw an error, if so, throw a diff error
            amember = self.roleForName(name, server)
            if amember:
                # We at least have a member
                return { "Role" : amember, "Int" : None }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, name)))
                newMem = self.roleForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Role" : newMem, "Int" : None }
                else:
                    # Nothing was right about this...
                    return { "Role" : None, "Int" : None }
        try:
            # Let's cast the last item as an int and catch any exceptions
            theInt = int(theList[len(theList)-1])
            newMemberName = " ".join(theList[:-1])
            amember = self.roleForName(newMemberName, server)
            if amember:
                return { "Role" : amember, "Int" : theInt }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, newMemberName)))
                newMem = self.roleForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Role" : newMem, "Int" : theInt }
                else:
                    # Nothing was right about this...
                    return { "Role" : None, "Int" : None }
        except ValueError:
            # Last section wasn't an int
            amember = self.roleForName(name, server)
            if amember:
                # Name was just a role - return
                return { "Role" : amember, "Int" : None }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, name)))
                newMem = self.roleForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Role" : newMem, "Int" : None }
                else:
                    # Nothing was right about this...
                    return { "Role" : None, "Int" : None }
        # Should never get here
        return None
