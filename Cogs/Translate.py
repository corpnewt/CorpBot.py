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
        """Translate some stuff!  Takes a phrase, the from language identifier (optional), and the to language identifier.
        To see a number of potential language identifiers, use the langlist command.
        
        Example Translation:
        $tr Hello there, how are you? en es
        
        Would translate from English to Spanish resulting in:
        ¿Hola como estás?
        
        If you do not specify the from language, Google translate will attempt to automatically determine it."""

        usage = "Usage: `{}tr [words] [from code (optional)] [to code]`".format(ctx.prefix)
        if translate == None: return await ctx.send(usage)

        word_list = translate.split(" ")

        if len(word_list) < 2: return await ctx.send(usage)

        to_lang   = word_list[len(word_list)-1]
        from_lang = word_list[len(word_list)-2] if len(word_list) >= 3 else ""

        # Get the from language name from the passed code
        from_lang_name = googletrans.LANGUAGES.get(from_lang.lower(),None)
        # Get the to language name from the passed code
        to_lang_name   = googletrans.LANGUAGES.get(to_lang.lower(),None)
        if not to_lang_name: # No dice on the language :(
            return await Message.EmbedText(
                    title="Something went wrong...",
                    description="I couldn't find that language!",
                    color=ctx.author
                ).send(ctx)
        # Get all but our language codes joined with spaces
        trans = " ".join(word_list[:-2] if from_lang_name else word_list[:-1])
        # If our from_lang_name is None, we need to auto-detect it
        if not from_lang_name:
            from_output = await self.bot.loop.run_in_executor(None, self.translator.detect, trans)
            from_lang = from_output.lang
            from_lang_name = googletrans.LANGUAGES.get(from_lang,"Unknown")
        # Let's actually translate now
        result_output = await self.bot.loop.run_in_executor(None, functools.partial(self.translator.translate, trans, dest=to_lang, src=from_lang))
        result = result_output.text
        
        # Explore the results!
        if not result:
            await Message.EmbedText(
                title="Something went wrong...",
                description="I wasn't able to translate that!",
                color=ctx.author
            ).send(ctx)
            return
        
        if result == trans:
            # We got back what we put in...
            await Message.EmbedText(
                title="Something went wrong...",
                description="The text returned from Google was the same as the text put in.  Either the translation failed - or you were translating from/to the same language (en -> en)",
                color=ctx.author
            ).send(ctx)
            return

        await Message.EmbedText(
            title="{}, your translation is:".format(DisplayName.name(ctx.author)),
            force_pm=True,
            color=ctx.author,
            description=result,
            footer="{} --> {} - Powered by Google Translate".format(string.capwords(from_lang_name), string.capwords(to_lang_name))
        ).send(ctx)
