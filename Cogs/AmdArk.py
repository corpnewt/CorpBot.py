from discord.ext import commands
from Cogs import Message
from Cogs import DL
from Cogs import PickList
import urllib.parse, json
from html import unescape


def setup(bot):
    # Add the bot
    bot.add_cog(AmdArk(bot))


class AmdArk(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.h = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    @commands.command(no_pm=True,aliases=("iamd",))
    async def amdark(self, ctx, *, text: str = None):
        """Searches AMD's site for CPU info."""

        args = {
            "title": "AMD Search",
            "description": "Usage: `{}amdark [cpu model]`".format(ctx.prefix),
            "footer": "Powered by https://www.amd.com/",
            "color": ctx.author
        }

        if text == None: return await Message.EmbedText(**args).send(ctx)
        original_text = text # Retain the original text sent by the user

        # Strip single quotes
        text = text.replace("'", "")

        if not len(text): return await Message.EmbedText(**args).send(ctx)

        args["description"] = "Gathering info..."
        message = await Message.EmbedText(**args).send(ctx)

        response = await self.get_search(text)
        # Check if we got nothing
        if not len(response):
            args["description"] = "No results returned for `{}`.".format(original_text.replace("`","").replace("\\",""))
            return await Message.EmbedText(**args).edit(ctx, message)

        elif len(response) == 1:
            # Set it to the first item
            response = await self.get_match_data(response[0])

        # Check if we got more than one result (either not exact, or like 4790 vs 4790k)
        elif len(response) > 1:
            # Allow the user to choose which one they meant.
            index, message = await PickList.Picker(
                message=message,
                title="Multiple Matches Returned For `{}`:".format(original_text.replace("`","").replace("\\","")),
                list=[x["name"] for x in response],
                ctx=ctx
            ).pick()

            if index < 0:
                args["description"] = "Search cancelled."
                await Message.EmbedText(**args).edit(ctx, message)
                return

            # Got something
            response = await self.get_match_data(response[index])
        
        if not response:
            args["description"] = "Something went wrong getting search data!"
            return await Message.EmbedText(**args).edit(ctx, message)

        print(json.dumps(response,indent=2))

        await Message.Embed(
            pm_after=20,
            title=response.get("name","AMD Search"),
            fields=response["fields"],
            url=response.get("url"),
            footer="Powered by https://www.amd.com",
            color=ctx.author
        ).edit(ctx, message)

    async def get_search(self, search_term):
        """
        Pipes a search term into amd.com/en/search and attempts to scrape the output
        """
        URL = "https://www.amd.com/en/search?keyword={}".format(urllib.parse.quote(search_term))
        try:
            contents = await DL.async_text(URL,headers=self.h)
        except:
            return []
        results = []
        for line in contents.split("\n"):
            if not all((x in line for x in ('<div class="views-field views-field-title">','<a href="/en/products/cpu/'))): continue
            try:
                name = line.split("</a>")[0].split(">")[-1]
                url  = "https://www.amd.com"+line.split('<a href="')[1].split('"')[0]
                results.append({"name":name,"url":url})
            except:
                continue
        return results

    async def get_match_data(self, match):
        """
        Queries amd.com to pull CPU data,
        parses the contents, and looks for the codename/µarch.
        """
        try:
            contents = await DL.async_text(match["url"],headers=self.h)
        except:
            return
        with open("amd_cpu.html","wb") as f:
            f.write(contents.encode())
        last_key = None
        info = {"url":match["url"],"name":match["name"]}
        fields = []
        for line in contents.split("\n"):
            if '<div class="field__label">' in line and not "Product ID" in line:
                try:
                    last_key = unescape(line.split('<div class="field__label">')[1].split("<")[0])
                    if not len(last_key):
                        last_key = None
                        continue
                except:
                    pass
            elif '<div class="field__item">' in line and last_key is not None:
                try:
                    val = unescape(line.split('<div class="field__item">')[1].split("</")[-2].split(">")[-1])
                    if not len(val): continue
                    fields.append({"name":last_key,"value":val,"inline":True})
                except:
                    pass
                last_key = None
        info["fields"]=fields
        return info