import asyncio, discord, aiohttp, re, html
from   discord.ext import commands
from   Cogs import Utils, Message, DisplayName, PickList, DL
#from   lyricsgenius import Genius # TODO: Remove this line, and import in Install.py
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
        self.ua = 'CorpNewt DeepThoughtBot'
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    async def _getSong(self, query : str):
        print("Gathering song data for: " + query)
        headers = {"Authorization" : "Bearer " + self.bot.settings_dict.get("song"), "User-agent" : self.ua}
        song = None
        try:
            response = await DL.async_json('https://api.genius.com/search?q=' + quote(query), headers=headers)
            songs = response['response']['hits']
            for hit in songs:
                if hit['type'] == "song":
                    song = hit['result']
                    break

        except Exception as e:
            print("Error retrieving song data")
            print(e)
            return False
        
        return song

    async def _songInfo(self, songid : int):
        print("Gathering detailed song data for: " + str(songid))
        headers = {"Authorization" : "Bearer " + self.bot.settings_dict.get("song"), "User-agent" : self.ua}
        try:
            response = await DL.async_json('https://api.genius.com/songs/' + str(songid), headers=headers)
            song = response['response']
            return song
        except Exception as e:
            print("Error retrieving detailed song data")
            print(e)
            return False


    @commands.command(aliases=['songinfo', 'music', 'musicinfo'])
    async def song(self, ctx, *, query : str):
        """Get data for a specific song."""

        message = await ctx.send("Searching for song...")
        song = await self._getSong(query)
        
        if song == False:
            await message.edit(content=f"Error retrieving song data")
        elif song != None:
            title = song['title']
            artist = song['primary_artist']['name']
            url = song['url']
            art = song['song_art_image_thumbnail_url']
            if art == None:
                art = song['header_image_thumbnail_url']
            link = "Unable to obtain link"
            detailedsongdata = await self._songInfo(song['id'])
            detailedsongdata = detailedsongdata['song']
            if detailedsongdata != False and detailedsongdata != None:
                if "media" in detailedsongdata:
                    link = ""
                    for media in detailedsongdata['media']:
                        if "url" in media: # This check should be unnecessary, but it is done just in case
                            link += f"[{media['provider']}](<{media['url']}>)\n"
            embed = discord.Embed(
                title = "**{}** by **{}**".format(title, artist),
                color = ctx.author.color,
                description = link,
                url = url
            )

            embed.set_thumbnail(url=art)
            embed.set_footer(text="Powered by Genius")
            await message.edit(content=None, embed=embed)
            print("Success: "+title+" by "+artist)
        else:
            message.edit(content="No results found for that query.")

    @commands.command(aliases=['lyric'])
    async def lyrics(self, ctx, *, query : str):
        """Get lyrics for a song."""
        message = await ctx.send("Searching for lyrics...")
        song = await self._getSong(query)
        if song == False:
            await message.edit(content=f"Error retrieving lyrics data")
        elif song != None:
            print("Gathering Lyrics data")
            response = await DL.async_text(song['url'], headers={"User-agent" : self.ua})
            # Get Lyrics part
            lyrics_parts = re.findall('<div data-lyrics-container="true" class="Lyrics.+?">(.+?)</div><div class="RightSidebar', response)
            lyrics = '\n'.join(lyrics_parts) # Join all the lyrics parts together with a newline after each part
            lyrics = lyrics.replace("<br/>", "\n")
            lyrics = html.unescape(lyrics) # Remove HTML escapes and replaces them with proper characters
            #lyrics = re.sub(r'<a.*?>|</a>', '', lyrics, flags=re.DOTALL) # Remove 'a' tags but keep the text inside
            #lyrics = re.sub(r'<span.*?>|</span>', '', lyrics, flags=re.DOTALL) # Remove 'span' tags but keep the text inside
            lyrics = re.sub(r'<[^>]+>', '', lyrics, flags=re.DOTALL) # Remove all HTML tags but keep the text inside
            if "You might also likeEmbed" in lyrics: # Remove "You might also likeEmbed" if it exists (this may be useful, I don't know if new code has this)
                lyrics = lyrics.split("You might also likeEmbed")[0].strip() 
            title = song['title']
            artist = song['primary_artist']['name']
            url = song['url']
            art = song['song_art_image_thumbnail_url']
            if art == None:
                art = song['header_image_thumbnail_url']
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
        else:
            message.edit(content="No results found for that query.")