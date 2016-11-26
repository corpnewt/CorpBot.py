import asyncio
import discord
import textwrap
from   discord.ext import commands

async def say(bot, msg, target, characters : int = 2000):
    """A helper function to get the bot to cut his text into chunks."""
    if not bot or not msg or not target:
        return False

    textList = textwrap.wrap(msg, characters, break_long_words=True, replace_whitespace=False)

    if not len(textList):
        return False
    
    for message in textList:
        await bot.send_message(target, message)
    
    return True