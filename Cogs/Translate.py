import asyncio
import discord
from   Cogs import Nullify
from   Cogs import DisplayName
from   discord.ext import commands
import json
import os
import mtranslate

# Requires the mtranslate module be installed

class Translate:
            
    def __init__(self, bot, settings, language_file = "Languages.json"):
        self.bot = bot
        self.settings = settings

        if os.path.exists(language_file):
            f = open(language_file,'r')
            filedata = f.read()
            f.close()
            self.languages = json.loads(filedata)
        else:
            self.languages = []
            print("No {}!".format(language_file))

    @commands.command(pass_context=True)
    async def langlist(self, ctx):
        """Lists available languages."""
        if not len(self.languages):
            await ctx.send("I can't seem to find any languages :(")
            return

        # Pm languages to author
        await ctx.send("I'll pm them to you.")
        msg = "Languages:\n\n"
        for lang in self.languages:
            msg += lang["Name"] + "\n"
        await ctx.author.send(msg)

    @commands.command(pass_context=True)
    async def tr(self, ctx, *, translate = None):
        """Translate some stuff!"""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.guild, "SuppressMentions").lower() == "yes":
            suppress = True
        else:
            suppress = False

        usage = "Usage: `{}tr [words] [language]`".format(ctx.prefix)
        if translate == None:
            await ctx.send(usage)
            return

        word_list = translate.split(" ")

        if len(word_list) < 2:
            await ctx.send(usage)
            return

        lang = word_list[len(word_list)-1]
        trans = " ".join(word_list[:-1])

        lang_code = None

        for item in self.languages:
            if item["Name"].lower() == lang.lower():
                lang_code = item["Code"]
                break
        if not lang_code and len(word_list) > 2:
            # Maybe simplified/traditional chinese or other 2 word lang
            lang = " ".join(word_list[len(word_list)-2:])
            trans = " ".join(word_list[:-2])
            for item in self.languages:
                if item["Name"].lower() == lang.lower():
                    lang_code = item["Code"]
                    break
        
        if not lang_code:
            await ctx.send("I couldn't find that language!")
            return

        result = mtranslate.translate(trans, lang_code, "auto")
        
        if not result:
            await ctx.send("I wasn't able to translate that!")
            return

        # Check for suppress
        if suppress:
            result = Nullify.clean(result)

        await ctx.send("*{}*, your translation is:\n\n{}".format(DisplayName.name(ctx.author), result))
