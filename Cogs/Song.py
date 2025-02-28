import asyncio, discord, aiohttp, re, html
from   discord.ext import commands
from   Cogs import Utils, Message, DisplayName, PickList, DL
from   urllib.parse import quote

def setup(bot):
    settings = bot.get_cog("Settings")
    if not bot.settings_dict.get("song"):
        if not bot.settings_dict.get("suppress_disabled_warnings"):     
            print("\n!! Song Cog has been disabled !!")
            print("* Genius API key is missing ('song' in settings_dict.json)")
            print("* You can get a free Genius API key by signing up at:")
            print("   https://genius.com/api-clients")
            return
    bot.add_cog(Song(bot, settings))

class Song(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.ua = "CorpNewt DeepThoughtBot"
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    async def _getSong(self, query : str):
        headers = {"Authorization" : "Bearer {}".format(self.bot.settings_dict.get("song")), "User-agent" : self.ua}
        song = None
        try:
            response = await DL.async_json("https://api.genius.com/search?q={}".format(quote(query)), headers=headers)
            songs = response["response"]["hits"]
            song = next((x.get("result") for x in songs if x.get("type") == "song"),None)
        except Exception as e:
            print(e)
            return False
        return song

    async def _songInfo(self, songid : int):
        headers = {"Authorization" : "Bearer {}".format(self.bot.settings_dict.get("song")), "User-agent" : self.ua}
        try:
            response = await DL.async_json("https://api.genius.com/songs/{}".format(songid), headers=headers)
            return response["response"]
        except Exception as e:
            print(e)
            return False

    @commands.command(aliases=["songinfo", "music", "musicinfo"])
    async def song(self, ctx, *, query : str = None):
        """Get data for a specific song."""

        if query is None:
            return await ctx.send("Usage: `{}song [query]`".format(ctx.prefix))
        message = await ctx.send("Searching for song...")
        song = await self._getSong(query)
        if song:
            title = song["title"]
            artist = song["primary_artist"]["name"]
            url = song["url"]
            art = song["song_art_image_thumbnail_url"]
            if art is None:
                art = song["header_image_thumbnail_url"]
            link = "Unable to obtain link"
            await message.edit(content="Gathering song info...")
            try:
                detailedsongdata = await self._songInfo(song["id"])
                detailedsongdata = detailedsongdata["song"]["media"]
                link = "\n".join([
                    "[{}]({})".format(x["provider"],x["url"]) \
                    for x in detailedsongdata if "url" in x \
                    and "provider" in x
                ])
            except:
                pass
            await Message.Embed(
                title = "**{}** by **{}**".format(title, artist),
                color = ctx.author,
                description = link,
                url = url,
                thumbnail = art,
                footer="Powered by Genius"
            ).send(ctx,message)
        elif song == False:
            await message.edit(content="Error retrieving song data")
        else:
            await message.edit(content="No results found for that query.")

    @commands.command(aliases=["lyric"])
    async def lyrics(self, ctx, *, query : str = None):
        """Get lyrics for a song."""

        if query is None:
            return await ctx.send("Usage: `{}song [query]`".format(ctx.prefix))
        message = await ctx.send("Searching for lyrics...")
        song = await self._getSong(query)
        if song:
            response = await DL.async_text(song["url"], headers={"User-agent" : self.ua})
            # Get Lyrics part
            lyrics_parts = re.findall('<div data-lyrics-container="true" class="Lyrics.+?">(.+?)</div><div class="RightSidebar', response)
            lyrics = "\n".join(lyrics_parts) # Join all the lyrics parts together with a newline after each part
            lyrics = lyrics.replace("<br/>", "\n")
            lyrics = html.unescape(lyrics) # Remove HTML escapes and replaces them with proper characters
            lyrics = re.sub(r"<[^>]+>", "", lyrics, flags=re.DOTALL) # Remove all HTML tags but keep the text inside
            if "You might also likeEmbed" in lyrics: # Remove "You might also likeEmbed" if it exists (this may be useful, I don't know if new code has this)
                lyrics = lyrics.split("You might also likeEmbed")[0].strip() 
            title = song["title"]
            artist = song["primary_artist"]["name"]
            url = song["url"]
            art = song["song_art_image_thumbnail_url"]
            if art is None:
                art = song["header_image_thumbnail_url"]
            return await PickList.PagePicker(
                title="**{}** by **{}**".format(title, artist),
                ctx=ctx,
                description=lyrics,
                timeout=180,
                url=url,
                footer="Powered by Genius",
                message=message,
                thumbnail=art
            ).pick()
        elif song == False:
            await message.edit(content="Error retrieving lyrics data")
        else:
            await message.edit(content="No results found for that query.")
