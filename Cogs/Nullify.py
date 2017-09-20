def setup(bot):
	# This module isn't actually a cog
    return

def clean(string):
    # A helper script to strip out @here and @everyone mentions
    zerospace = "​"
    return string.replace("@everyone", "@{}everyone".format(zerospace)).replace("@here", "@{}here".format(zerospace))