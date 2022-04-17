from   discord.ext import commands
from   Cogs import Utils, DisplayName, PickList, FuzzySearch, Message
import pyfiglet

def setup(bot):
	# Add the bot
	bot.add_cog(Ascii(bot))
	
class Ascii(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		self.font_list = pyfiglet.FigletFont.getFonts()

	@commands.command(aliases=["font","fonts","fontlist"])
	async def asciifonts(self, ctx, search_term = None):
		"""Lists the available ascii fonts."""
		if search_term is None:
			return await PickList.PagePicker(
				title="Available ASCII Fonts ({:,} total)".format(len(self.font_list)),
				description="\n".join(["{}. {}".format(str(i).rjust(3),x) for i,x in enumerate(self.font_list,start=1)]),
				d_header="```\n",
				d_footer="\n```",
				ctx=ctx
			).pick()
		# Let's see if it's a full match
		if search_term.lower() in self.font_list:
			return await Message.Embed(
				title="Font Exists",
				description="`{}` is in the font list.".format(search_term.lower()),
				color=ctx.author
			).send(ctx)
		# Let's get 3 close matches
		font_match = FuzzySearch.search(search_term.lower(), self.font_list)
		font_mess = "\n".join(["`└─ {}`".format(x["Item"]) for x in font_match])
		await Message.Embed(
			title="Font \"{}\" Not Fount".format(search_term),
			fields=[{"name":"Close Font Matches:","value":font_mess}],
			color=ctx.author
		).send(ctx)

	@commands.command(pass_context=True, no_pm=True)
	async def ascii(self, ctx, *, text : str = None):
		"""Beautify some text."""

		if text is None: return await ctx.channel.send('Usage: `{}ascii [font (optional)] [text]`'.format(ctx.prefix))

		font = None
		# Split text by space - and see if the first word is a font
		parts = text.split()
		if len(parts) > 1 and parts[0].lower() in self.font_list:
			# We got a font!
			font = parts[0]
			text = " ".join(parts[1:])
		output = pyfiglet.figlet_format(text,font=font if font else pyfiglet.DEFAULT_FONT)
		if not output: return await ctx.send("I couldn't beautify that text :(")
		await ctx.send("```\n{}```".format(output))
