from urllib.request import urlopen

# Looks like there's more I didn't plan super well
# Global vars to the rescue again!
bot = None

def setup(bot_start):
    # This module isn't actually a cog - but it is a place
    # where small fires can grow - let's give it some kindling...
    global bot
    bot = bot_start
    return

async def tiny_url(url):
    apiurl = "http://tinyurl.com/api-create.php?url="
    tinyurl = await bot.loop.run_in_executor(None, lambda: urlopen(apiurl + url).read().decode("utf-8"))
    # tinyurl = urlopen(apiurl + url).read().decode("utf-8")
    return tinyurl