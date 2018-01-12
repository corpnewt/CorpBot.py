import asyncio
import discord
import re
from   discord.ext import commands
from   Cogs import Nullify

def setup(bot):
	# This module isn't actually a cog
    return

def clean_message(message, *, bot = None, server = None, nullify = True):
    # Searches for <@ > and <!@ > and gets the ids between
    # then resolves them to their user name if it can be determined
    
    if nullify:
        # Strip out @here and @everyone first
        zerospace = "​"
        message = message.replace("@everyone", "@{}everyone".format(zerospace)).replace("@here", "@{}here".format(zerospace))
    if bot == None and server == None:
        # Not enough info
        return message
    matches_re = re.finditer(r"\<!?\@[^\<\@]+\>", message)
    matches = []
    matches = [x.group(0) for x in matches_re]
    if not len(matches):
        return message
    for match in matches:
        if server:
            # Have the server, bot doesn't matter
            mem = memberForName(match, server)
            if mem == None:
                continue
            mem_name = name(mem)
        else:
            # Must have bot then
            memID = re.sub(r'\W+', '', match)
            mem = bot.get_user(int(memID))
            if mem == None:
                continue
            mem_name = mem.name
        message = message.replace(match, mem_name)
    return message

def name(member : discord.Member):
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

def memberForID(checkid, server):
    try:
        checkid = int(checkid)
    except:
        return None
    for member in server.members:
        if member.id == checkid:
            return member
    return None

def memberForName(name, server):
    # Check nick first - then name
    name = str(name)
    for member in server.members:
        if member.nick:
            if member.nick.lower() == name.lower():
                return member
    for member in server.members:
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
            for member in server.members:
                if member.name.lower() == mem_name.lower() and int(member.discriminator) == mem_disc:
                    return member
    mem_id = re.sub(r'\W+', '', name)
    new_mem = memberForID(mem_id, server)
    if new_mem:
        return new_mem
    
    return None

def channelForID(checkid, server, typeCheck = None):
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
        if channel.id == checkid:
            return channel
    return None

def channelForName(name, server, typeCheck = None):
    name = str(name)
    for channel in server.channels:
        if typeCheck:
            if typeCheck.lower() == "text" and not type(channel) is discord.TextChannel:
                continue
            if typeCheck.lower() == "voice" and not type(channel) is discord.VoiceChannel:
                continue
        if channel.name.lower() == name.lower():
            return channel
    chanID = re.sub(r'\W+', '', name)
    newChan = channelForID(chanID, server, typeCheck)
    if newChan:
        return newChan
    return None

def roleForID(checkid, server):
    try:
        checkid = int(checkid)
    except:
        return None
    for role in server.roles:
        if role.id == checkid:
            return role
    return None

def roleForName(name, server):
    name = str(name)
    # Adjust for "everyone"
    if name.lower() == "everyone":
        name = "@everyone"
    for role in server.roles:
        if role.name.lower() == name.lower():
            return role
    # No role yet - try ID
    roleID = ''.join(list(filter(str.isdigit, name)))
    newRole = roleForID(roleID, server)
    if newRole:
        return newRole
    return None

def serverNick(user, server):
    for member in server.members:
        if member.id == user.id:
            return name(member)
    return None

def checkNameForInt(name, server):
    name = str(name)
    theList = name.split()
    # We see if we have multiple parts split by a space
    if len(theList)<2:
        # Only one part - no int included (or not separated by space)
        # Check if member exists - and if not throw an error, if so, throw a diff error
        amember = memberForName(name, server)
        if amember:
            # We at least have a member
            return { "Member" : amember, "Int" : None }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, name)))
            newMem = memberForID(memID, server)
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
        amember = memberForName(newMemberName, server)
        if amember:
            return { "Member" : amember, "Int" : theInt }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, newMemberName)))
            newMem = memberForID(memID, server)
            if newMem:
                # We FOUND it!
                return { "Member" : newMem, "Int" : theInt }
            else:
                # Nothing was right about this...
                return { "Member" : None, "Int" : None }
    except ValueError:
        # Last section wasn't an int
        amember = memberForName(name, server)
        if amember:
            # Name was just a member - return
            return { "Member" : amember, "Int" : None }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, name)))
            newMem = memberForID(memID, server)
            if newMem:
                # We FOUND it!
                return { "Member" : newMem, "Int" : None }
            else:
                # Nothing was right about this...
                return { "Member" : None, "Int" : None }
    # Should never get here
    return None

def checkRoleForInt(name, server):
    name = str(name)
    theList = name.split()
    # We see if we have multiple parts split by a space
    if len(theList)<2:
        # Only one part - no int included (or not separated by space)
        # Check if role exists - and if not throw an error, if so, throw a diff error
        amember = roleForName(name, server)
        if amember:
            # We at least have a member
            return { "Role" : amember, "Int" : None }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, name)))
            newMem = roleForID(memID, server)
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
        amember = roleForName(newMemberName, server)
        if amember:
            return { "Role" : amember, "Int" : theInt }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, newMemberName)))
            newMem = roleForID(memID, server)
            if newMem:
                # We FOUND it!
                return { "Role" : newMem, "Int" : theInt }
            else:
                # Nothing was right about this...
                return { "Role" : None, "Int" : None }
    except ValueError:
        # Last section wasn't an int
        amember = roleForName(name, server)
        if amember:
            # Name was just a role - return
            return { "Role" : amember, "Int" : None }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, name)))
            newMem = roleForID(memID, server)
            if newMem:
                # We FOUND it!
                return { "Role" : newMem, "Int" : None }
            else:
                # Nothing was right about this...
                return { "Role" : None, "Int" : None }
    # Should never get here
    return None
