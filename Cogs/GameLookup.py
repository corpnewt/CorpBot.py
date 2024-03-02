import discord, time
from   discord.ext import commands
from   Cogs import Settings, Message, UserTime, DL, FuzzySearch

def setup(bot):
    # Do some simple setup
    if not bot.settings_dict.get("igdbclientid") or not bot.settings_dict.get("igdbsecret"):
        if not bot.settings_dict.get("suppress_requirement_warnings"):
            print("\n!! IGDB API key is missing ('igdbclientid' & 'igdbsecret' in settings_dict.json)")
            print(" - You can find instructions for getting them at:")
            print("   https://api-docs.igdb.com/#getting-started\n")
        return
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(GameLookup(bot, settings, bot.settings_dict["igdbclientid"], bot.settings_dict["igdbsecret"]))

class GameLookup(commands.Cog):
    def __init__(self, bot, settings, clientid, secret):
        self.bot = bot
        self.settings = settings
        self.clientid = clientid
        self.secret = secret
        self.access_token = None
        self.expire_time = 0

    async def _update_token(self):
        # First reset our values
        self.access_token = None
        self.expire_time  = 0
        # Attempt to update the access token
        if not self.clientid or not self.secret:
            return False # Missing info - bail
        # Build our URL
        access_url = "https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials".format(self.clientid,self.secret)
        try: output = await DL.async_post_json(access_url)
        except: output = None
        if not output:
            return False # Something went wrong - bail
        # Get the token and expiration - set them and return success
        self.access_token = output.get("access_token")
        self.expire_time  = int(output.get("expires_in",0) + time.time())
        return True

    @commands.command(aliases=["glu","glup","gamel","gamelu","glookup"])
    async def gamelookup(self, ctx, *, game_name = None):
        """Leverage IGDB's API to search for game information."""

        if not game_name: return await ctx.send("Usage: `{}gamelookup [game_name]`".format(ctx.prefix))
        if not self.access_token or time.time() >= self.expire_time:
            if not await self._update_token():
                return await ctx.send("I couldn't update my access token :(  Make sure the `igdbclientid` and `igdbsecret` are correct in my settings_dict.json!")
        # Let's build our search query
        search_url = "https://api.igdb.com/v4/games"
        data = 'search "{}"; fields name,url,summary,first_release_date,platforms.*,cover.*; limit 10;'.format(game_name.replace('"',"").replace("\\",""))
        headers = {"Client-ID":self.clientid,"Authorization":"Bearer {}".format(self.access_token)}
        try:
            search_data = await DL.async_post_json(search_url,data=data,headers=headers)
        except:
            return await Message.Embed(
                title="Something went wrong searching for that game :(",
                color=ctx.author
            ).send(ctx)
        if not search_data:
            # Nothing was returned - bail.
            return await Message.Embed(
                title="Nothing was returned for that search!",
                color=ctx.author
            ).send(ctx)
        if len(search_data)==1 and all((x in search_data[0] for x in ("title","status","cause"))):
            # Got an error - print it and bail
            return await Message.Embed(
                title="Something went wrong searching :(",
                description="{}: {}".format(search_data[0]["title"],search_data[0]["cause"]),
                color=ctx.author
            ).send(ctx)
        # Organize the search data by the closest match
        game = FuzzySearch.search(game_name,search_data,"name",1)[0]["Item"]
        # Print the results!
        await Message.Embed(
            title=game["name"],
            thumbnail="http:{}".format(game["cover"]["url"].replace("/t_thumb/","/t_cover_big/")),
            url=game["url"],
            color=ctx.author,
            description=game["summary"],
            fields=[
                {"name":"Release Date", "value": "<t:{}:D>".format(game["first_release_date"])},
                {"name":"Platforms", "value":"\n".join(sorted([x["name"] for x in game["platforms"]]))}
            ]
        ).send(ctx)
