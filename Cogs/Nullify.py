import re

def setup(bot):
	# This module isn't actually a cog
    return

def clean(string, deaden_links = False):
    # A helper script to strip out @here and @everyone mentions
    zerospace = "​"
    if deaden_links:
        # Check if we have a url link
        matches = re.finditer(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", string)
        # Isolate to a set
        matches = set([x.group(0) for x in matches])
        # Wrap all links in <>
        for match in matches:
            string = string.replace(match, "<{}>".format(match))
    return string.replace("@everyone", "@{}everyone".format(zerospace)).replace("@here", "@{}here".format(zerospace))