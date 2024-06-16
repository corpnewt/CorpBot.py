from discord.ext import commands
from Cogs import Message
from Cogs import DL
from Cogs import PickList
import urllib.parse, json
import regex as re
from html import unescape


def setup(bot):
    # Add the bot
    bot.add_cog(AmdArk(bot))


class AmdArk(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.exclude_key_prefixes = (
            "Product ID",
            "*OS Support",
            "OS Support",
            "Supported Technologies",
            "Workload Affinity"
        )
        self.h = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        self.url_regex_accept = (
            re.compile(r"\/en\/products\/(apu|cpu|processors\/(desktops|laptops)|(professional-)?graphics)\/"),
        )
        self.url_regex_reject = (
            re.compile(r"\/en\/products\/graphics\/(technologies|desktops\/radeon.html)"),
        )

    @commands.command(no_pm=True,aliases=("iamd","aark"))
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
                
        if not response or not isinstance(response,dict):
            args["description"] = "Something went wrong getting search data!"
            return await Message.EmbedText(**args).edit(ctx, message)

        if not response.get("fields"):
            args["description"] = "No results returned for `{}`.".format(original_text.replace("`","").replace("\\",""))
            return await Message.EmbedText(**args).edit(ctx, message)

        await PickList.PagePicker(
            title=response.get("name","AMD Search"),
            list=response["fields"],
            url=response.get("url"),
            footer="Powered by https://www.amd.com",
            color=ctx.author,
            ctx=ctx,
            max=18,
            message=message
        ).pick()

    async def get_search(self, search_term):
        """
        Pipes a search term into amd.com/en/search and attempts to scrape the output
        """
        URL = "https://www.amd.com/en/search/site-search.html#q={}".format(urllib.parse.quote(search_term))
        try:
            contents = await DL.async_text(URL,headers=self.h)
        except:
            return []
        # We should have the basic html here - let's scrape for the authorization and run the coveo search
        try:
            token = contents.split('data-access-token="')[1].split('"')[0]
            org_id = contents.split('data-org-id="')[1].split('"')[0]
        except:
            return []
        # Build a simple query - ensure the results are in english
        post_data = {
            "q":search_term,
            "context":'{"amd_lang":"en"}',
            "cq":"NOT(@amd_result_type==(\"Videos\") OR (@sourcetype==(\"Lithium\") AND @liboardinteractionstyle==(\"forum\", \"tkb\")))",
            "searchHub":"Site"
        }
        # Build a new set of headers with the access token
        search_headers = {}
        for x in self.h:
            # Shallow copy our current headers
            search_headers[x] = self.h[x]
        # Add the authorization
        search_headers["Authorization"] = "Bearer {}".format(token)
        # Run the actual coveo search
        search_data = await DL.async_post_json(
            "https://platform.cloud.coveo.com/rest/search/v2?organizationId={}".format(org_id),
            post_data,
            search_headers
        )
        if not search_data or not search_data.get("results"):
            return []
        # Let's iterate the results
        results = []
        suffix = " | AMD"
        for result in search_data["results"]:
            uri = result.get("uri","")
            if any(x.search(uri) for x in self.url_regex_accept) and not any(x.search(uri) for x in self.url_regex_reject):
                # Strip " | AMD" off the end of the name if present
                name = result.get("title",uri.split("/")[-1])
                if name.endswith(suffix) and len(name)>len(suffix):
                    name = name[:-len(suffix)]
                results.append({
                    "name":name,
                    "url":uri
                })
        return results

    async def get_match_data(self, match):
        """
        Queries amd.com to pull CPU data,
        parses the contents, and looks for the codename/µarch.
        """
        try:
            contents = await DL.async_text(match["url"],headers=self.h)
            with open("amd.html","wb") as f: f.write(contents.encode())
        except:
            return
        info = {"url":match["url"],"name":match["name"]}
        fields = []
        if 'data-product-specs="' in contents:
            # Newer format - this should give us some JSON data to work with
            try:
                contents = unescape(contents.split('data-product-specs="')[1].split('"')[0].strip())
                json_data = json.loads(contents)
                for entry in json_data.get("elements",{}).values():
                    if entry.get("title") and entry.get("formatValue"):
                        name = unescape(entry["title"])
                        value = unescape(entry["formatValue"]).replace(" , ",", ")
                        # Let's see if the value is JSON data
                        try:
                            value_json = json.loads(value)
                            # It is - let's try to format it
                            def format_val(val):
                                if isinstance(val,dict) and len(val) == 2:
                                    first,second = list(val.values())[:2]
                                    if isinstance(first,list) and first:
                                        first = first[0]
                                    if isinstance(second,list) and second:
                                        second = second[0]
                                    return "{}: {}".format(first,second)
                                else:
                                    return str(val)
                            if isinstance(value_json,list):
                                value = "\n".join([format_val(v) for v in value_json])
                            else:
                                value = format_val(val)
                        except:
                            pass
                        # Add the entry
                        fields.append({
                            "name":name,
                            "value":value,
                            "inline":True
                        })
            except:
                return
        else:
            # Older format - scrape the HTML directly
            last_key = None
            for line in contents.split("\n"):
                if line.strip() == "</div>":
                    last_key = None
                elif 'class="field__label' in line:
                    try:
                        last_key = unescape(line.split('class="field__label')[1].split("<")[0].split(">")[-1])
                        assert len(last_key) and not last_key.startswith(self.exclude_key_prefixes)
                    except:
                        last_key = None
                elif 'class="field__item">' in line and last_key is not None:
                    try:
                        val = unescape(line.split('class="field__item">')[1].split("</")[-2].split(">")[-1])
                        if not len(val): continue
                        if len(fields) and fields[-1]["name"] == last_key: # Already there, append
                            fields[-1]["value"] = fields[-1]["value"]+", "+val
                        else:
                            fields.append({"name":last_key,"value":val,"inline":True})
                    except:
                        pass
        # Ensure we don't duplicate fields (some amd entries have things listed twice for whatever reason)
        unique_fields = []
        for field in fields:
            if not any((x["name"] == field["name"] for x in unique_fields)):
                unique_fields.append(field)
        info["fields"]=unique_fields
        return info
