import functools, string, googletrans
from Cogs import DisplayName, Message, PickList, FuzzySearch
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
        self.langcodes = googletrans.LANGCODES
        self.languages = googletrans.LANGUAGES

    @commands.command(aliases=["listlang","llist","listl"])
    async def langlist(self, ctx, search=None):
        """Lists available languages - can optionally take a search term and will list the 3 closest results."""
        if search:
            code_search = FuzzySearch.search(search.lower(), googletrans.LANGCODES)
            lang_search = FuzzySearch.search(search.lower(), googletrans.LANGUAGES)
            full_match  = next((x["Item"] for x in code_search+lang_search if x.get("Ratio") == 1),None)
            if full_match: # Got an exact match - build an embed
                if full_match in googletrans.LANGCODES:
                    name,code,t = string.capwords(full_match),googletrans.LANGCODES[full_match],"Language Name"
                else:
                    name,code,t = string.capwords(googletrans.LANGUAGES[full_match]),full_match,"Language Code"
                return await Message.Embed(
                    title="Search Results For \"{}\"".format(search),
                    description="Exact {} Match:\n\n`{}` - {}".format(t,code,name),
                    color=ctx.author,
                    ).send(ctx)
            # Got close matches
            desc = "No exact language matches for \"{}\"".format(search)
            fields = []
            if len(code_search):
                lang_mess = "\n".join(["└─ `{}` - {}".format(
                    googletrans.LANGCODES[x["Item"]],
                    string.capwords(x["Item"])
                ) for x in code_search])
                fields.append({"name":"Close Language Name Matches:","value":lang_mess})
            if len(lang_search):
                lang_mess = "\n".join(["└─ `{}` - {}".format(
                    x["Item"],
                    string.capwords(googletrans.LANGUAGES[x["Item"]])
                ) for x in lang_search])
                fields.append({"name":"Close Language Code Matches:","value":lang_mess})
            return await Message.Embed(title="Search Results For \"{}\"".format(search),description=desc,fields=fields).send(ctx)
        description = ""
        for lang in googletrans.LANGCODES:
            description += "`{}` - {}\n".format(googletrans.LANGCODES[lang],string.capwords(lang))
        await PickList.PagePicker(
            title="Language List",
            description=description,
            color=ctx.author,
            ctx=ctx
        ).pick()

    @commands.command()
    async def detectlang(self, ctx, *, text):
        """Reports the detected language and certainty of the passed text."""
        if text is None: return await ctx.send("Usage: `{}detectlang [text to identify]`".format(ctx.prefix))
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

    def _unpack(self,value):
        if isinstance(value,list):
            while True:
                if any((isinstance(x,list) for x in value)): value = sum(value,[])
                else: break
            if value: value = value[0]
        return value

    @commands.command(name="translate", aliases=["tr"], )
    async def translate(self, ctx, *, translate=None):
        """Translate some stuff!  Takes a phrase, the from language identifier and the to language identifier (optional).
        To see a number of potential language identifiers, use the langlist command.

        Example Translation:
        $tr Hello there, how are you? en es

        Would translate from English to Spanish resulting in:
        ¿Hola como estás?

        If you do not specify the from language, Google translate will attempt to automatically determine it.
        If you do not specify the to language, it will default to English."""

        usage = "Usage: `{}tr [words] [from code (optional)] [to code (optional)]`".format(ctx.prefix)

        # Find out if we're replying to another message
        reply = None
        if ctx.message.reference:
            # Resolve the replied to reference to a message object
            try:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                reply = message.content
            except:
                pass
        if reply: # Prepend our replied-to text, if any
            translate = reply if not translate else " ".join((reply,translate))
        
        # Check if we ended up with anything
        if translate is None: return await ctx.send(usage)

        word_list = translate.split(" ")
        if len(word_list) < 1: return await ctx.send(usage)

        to_lang = word_list[-1].lower() if word_list[-1].lower() in self.langcodes.values() else None  # check for to_lang
        if to_lang: word_list.pop()  # Remove the last word from the list, i.e. the to_lang
        else: to_lang = "en"  # Default to english

        # there should be at least 2 words left after we remove the to_lang, in case the user specifies a source language
        from_lang = word_list[-1].lower() if len(word_list) >= 2 and word_list[-1].lower() in self.langcodes.values() else None
        if from_lang: word_list.pop()  # remove the last word from the list, i.e. the from_lang (since the to_lang has been removed already)

        # Get the from language name from the passed code
        if from_lang: from_lang_name = self.languages.get(from_lang, None)
        else: from_lang_name = None

        # Get the to language name from the passed code
        if to_lang: to_lang_name = self.languages.get(to_lang, None)
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
            result = await self.bot.loop.run_in_executor(None, functools.partial(self.translator.translate, text=to_translate, src=from_lang, dest=to_lang))
        else:
            # We'll leave Google Translate to figure out the source language if we don't have it
            result = await self.bot.loop.run_in_executor(None, functools.partial(self.translator.translate, text=to_translate, dest=to_lang))

        # Explore the results!
        result.text = self._unpack(result.text)
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

        # We got a translation!
        embed = Message.Embed(
            title="{}, your translation is:".format(DisplayName.name(ctx.author)),
            force_pm=True,
            color=ctx.author,
            description=result.text,
            footer="{} --> {}".format(
                self.languages.get(result.src.lower(), "Unknown").title(),
                self.languages.get(result.dest.lower(), "Unknown").title()
            )
        )

        # If we have a valid pronunciation, add it to the embed!
        result.pronunciation = self._unpack(result.pronunciation)
        if result.pronunciation:
            if isinstance(result.pronunciation,list):
                result.pronunciation = result.pronunciation[0]
            if not any(result.pronunciation == x for x in (result.text,to_translate)):
                embed.add_field(name="Pronunciation", value=result.pronunciation, inline=False)

        await embed.send(ctx)

    @commands.command(name="pronounce", aliases=["pr"])
    async def pronounce(self, ctx, *, text=None):
        """Pronunciation for a sentence in the English language.\n
        $pronounce こんにちは --> returns \"Kon'nichiwa\""""

        if text is None: return await ctx.send("Usage: `{}pronounce [text to identify]`".format(ctx.prefix))

        if text.split()[-1] in self.langcodes.values():
            source_lang = text.split()[-1]
            text = " ".join(text.split()[:-1])  # We are removing the last word from the list, since it's the language code
        else:
            source_lang = None

        if len(text) > 1000:  # We need to keep it under 1024 characters due to field size limits
            return await Message.EmbedText(
                title="Something went wrong...",
                description="Text entered is too long. Please keep it under 1000 characters.",
                color=ctx.author
            ).send(ctx)

        detect_result = await self.bot.loop.run_in_executor(None, functools.partial(self.translator.detect, text))  # We are detecting the language of the text

        if not source_lang:
            if isinstance(detect_result.confidence, list):  # We got multiple results
                source_lang = detect_result.lang[0]
                lang_confidence = detect_result.confidence[0]
            else:
                source_lang = detect_result.lang
                lang_confidence = detect_result.confidence
        else:
            lang_confidence = 1  # When the user specifies a source language, we assume they know what they're doing

        pronunciation_result = await self.bot.loop.run_in_executor(None, functools.partial(self.translator.translate, text=text, src=source_lang, dest=source_lang))
        # We don't need to translate to another language, we just get the pronunciation
        if not pronunciation_result.pronunciation or pronunciation_result.pronunciation == pronunciation_result.src:
            return await Message.EmbedText(
                title="Something went wrong...",
                description="I couldn't find a pronunciation for that text!",
                color=ctx.author
            ).send(ctx) # We don't want a pronunciation that's the same as the text

        english_translation = await self.bot.loop.run_in_executor(None, functools.partial(self.translator.translate, text=text, src=source_lang, dest="en"))
        if not self.languages.get(source_lang):
            return await Message.EmbedText(
                title="Something went wrong...",
                description="I couldn't detect the language of the text!",
                color=ctx.author
            ).send(ctx)

        embed = Message.Embed(title="{}, your pronunciation is:".format(ctx.author.display_name),
                            color=ctx.author.color)
        embed.description = pronunciation_result.pronunciation
        embed.add_field(name="Source Text", value=pronunciation_result.text, inline=False)
        embed.add_field(name="Translated to English", value=english_translation.text, inline=False)
        if int(lang_confidence) != 1:
            embed.footer = {
                "text": "Language: {} (Confidence: {}%)".format(
                    self.languages.get(source_lang).title() if self.languages.get(source_lang) else 'Unknown',
                    round(lang_confidence * 100, 2))
            }
        else:
            embed.footer = {
                "text": "Language: {}".format(self.languages.get(source_lang).title() if self.languages.get(source_lang) else 'Unknown')
            }
        await embed.send(ctx)
