import functools, string, googletrans
from Cogs import DisplayName, Message, PickList
from discord.ext import commands

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Translate(bot, settings))

# Requires the mtranslate module be installed

class Translate(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.translator = googletrans.Translator(service_urls=["translate.googleapis.com"])
        self.langcodes = googletrans.LANGCODES
        self.languages = googletrans.LANGUAGES
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    @commands.command(pass_context=True)
    async def langlist(self, ctx):
        """Lists available languages."""
        description = ""
        for lang in googletrans.LANGCODES:
            description += "**{}** - {}\n".format(string.capwords(lang), googletrans.LANGCODES[lang])
        await PickList.PagePicker(
            title="Language List",
            description=description,
            color=ctx.author,
            ctx=ctx
        ).pick()

    @commands.command(pass_context=True)
    async def detectlang(self, ctx, *, text):
        """Reports the detected language and certainty of the passed text."""
        if text == None: return await ctx.send("Usage: `{}detectlang [text to identify]`".format(ctx.prefix))
        lang_detect = await self.bot.loop.run_in_executor(None, self.translator.detect, text)
        await Message.EmbedText(
            title="Detected Language",
            description="Detected **{}** ({}) with {:.0%} confidence.".format(
                string.capwords(googletrans.LANGUAGES.get(lang_detect.lang.lower(),"Martian?")),
                lang_detect.lang.lower(),
                lang_detect.confidence
            ),
            color=ctx.author
        ).send(ctx)

    @commands.command(pass_context=True)
    async def tr(self, ctx, *, translate = None):
        """Translate some stuff!  Takes a phrase, the from language identifier and the to language identifier (optional).
        To see a number of potential language identifiers, use the langlist command.

        Example Translation:
        $tr Hello there, how are you? en es

        Would translate from English to Spanish resulting in:
        ¿Hola como estás?

        If you do not specify the from language, Google translate will attempt to automatically determine it.
        If you do not specify the to language, it will default to English."""

        usage = "Usage: `{}tr [words] [from code (optional)] [to code (optional)]`".format(ctx.prefix)
        if translate == None: return await ctx.send(usage)

        word_list = translate.split(" ")
        if len(word_list) < 1: return await ctx.send(usage)

        to_lang = word_list[-1] if word_list[-1] in self.langcodes.values() else None  # check for to_lang
        if to_lang: word_list.pop()  # Remove the last word from the list, i.e. the to_lang
        else: to_lang = "en"  # Default to english

        # there cannot be a from_lang if there is no to_lang, which means there should be at least 3 words
        from_lang = word_list[-1] if len(word_list) >= 2 and word_list[-1] in self.langcodes.values() else None
        if from_lang:
            word_list.pop()  # remove the last word from the list, i.e. the from_lang (since the to_lang has been removed already)


        # Get the from language name from the passed code
        if from_lang: from_lang_name = self.languages.get(from_lang.lower(), None)
        else: from_lang_name = None

        # Get the to language name from the passed code
        if to_lang: to_lang_name = self.languages.get(to_lang.lower(), None)
        else: to_lang_name = None

        if not to_lang_name:  # No dice on the language :(
            return await Message.EmbedText(
                title="Something went wrong...",
                description="I couldn't find that language!",
                color=ctx.author
            ).send(ctx)

        # Get our words joined with spaces
        to_translate = " ".join(word_list) if word_list else ""

        if from_lang_name:
            result = self.translator.translate(text=to_translate, src=from_lang, dest=to_lang)
        else:
            # We'll leave Google Translate to figure out the source language if we don't have it
            result = self.translator.translate(text=to_translate, dest=to_lang)

        # Explore the results!
        if not result.text:
            return await Message.EmbedText(
                title="Something went wrong...",
                description="I wasn't able to translate that!",
                color=ctx.author
            ).send(ctx)

        if result.text == to_translate:
            # We got back what we put in...
            return await Message.EmbedText(
                title="Something went wrong...",
                description="The text returned from Google was the same as the text put in.  Either the translation failed - or you were translating from/to the same language ({src} -> {src})".format(
                    src=result.src
                ),
                color=ctx.author
            ).send(ctx)

        # Get the language names from the codes, and make them title case
        footer = "{} --> {}".format(
            self.languages.get(result.src.lower(), "Unknown").title(),
            self.languages.get(result.dest.lower(), "Unknown").title()
        )
        embed = Message.Embed(
            title="{}, your translation is:".format(DisplayName.name(ctx.author)),
            force_pm=True,
            color=ctx.author,
            description=result.text,
            footer=footer
        )
        if result.pronunciation:
            # If we have a pronunciation, add it to the embed!
            embed.add_field(name="Pronunciation", value=result.pronunciation, inline=False)

        await embed.send(ctx)
