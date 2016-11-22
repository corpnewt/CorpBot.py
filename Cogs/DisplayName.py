import asyncio
import discord
from   discord.ext import commands

def name(member : discord.Member):
    # A helper function to return the member's display name
    if member.nick:
        return member.nick
    elif member.name:
        return member.name
    else:
        return None