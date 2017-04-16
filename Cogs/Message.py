import asyncio
import discord
import textwrap
from   discord.ext import commands

async def say(bot, msg, target, characters : int = 2000, maxMessage = 5):
    """A helper function to get the bot to cut his text into chunks."""
    if not bot or not msg or not target:
        return False

    textList = textwrap.wrap(msg, characters, break_long_words=True, replace_whitespace=False)

    if not len(textList):
        return False
    
    messageCount = 0
    for message in textList:
        if messageCount >= maxMessage:
            await bot.send_message(target, "Looks like I've got *a lot more* to say about this - but I won't bore you with the details.")
            break
        await bot.send_message(target, message)
        messageCount += 1
    
    return True