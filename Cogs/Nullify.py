import re, discord

def setup(bot):
	# This module isn't actually a cog
    return

def clean(string, deaden_links = False, ctx = None):
    # A helper function to strip out user and role mentions
    if deaden_links:
        # Check if we have a url link
        matches = re.finditer(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", string)
        i_adjust = 0
        for m in matches:
            match = m.group(0)
            # Ensure it starts and ends with <>
            if not match.startswith("<"): match = "<"+match
            if not match.endswith(">"): match += ">"
            # Replace the indices and update the adjusted index
            string = string[0:m.start()+i_adjust] + match + string[i_adjust+m.end():]
            i_adjust += len(match)-len(m.group(0))
    return resolve_mentions(string,ctx=ctx)

def escape_all(string, mentions = True, markdown = True):
    if mentions: string = discord.utils.escape_mentions(string)
    if markdown: string = discord.utils.escape_markdown(string)
    return string

def resolve_mentions(string, ctx = None, escape = True, show_mentions = True):
    guild = ctx if isinstance(ctx,discord.Guild) else ctx.guild if hasattr(ctx,"guild") else None
    if guild:
        # We have a guild - let's try to resolve!
        matches = re.finditer(r"\<\@[!&]?\d+\>", string)
        # Iterate the mention matches, and resolve them to their names
        d = re.compile("\\d+")
        i_adjust = 0
        for m in matches:
            try: id_match = int(d.search(m.group(0)).group(0))
            except: continue
            check_func = guild.get_role if "@&" in m.group(0) else guild.get_member
            check_entry = check_func(id_match)
            if not check_entry: continue
            # Let's replace the indices in the original string - but then also update our adjusted index
            name = check_entry.display_name if hasattr(check_entry,"display_name") else check_entry.name
            if escape: name = escape_all(name)
            # Add the @ prefix if we're showing mentions
            if show_mentions: name = "@"+name
            string = string[0:m.start()+i_adjust] + name + string[i_adjust+m.end():]
            i_adjust += len(name)-len(m.group(0))
    return escape_all(string,markdown=False) if escape else string # Catch any missing mentions as needed