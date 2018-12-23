import discord
from   discord.ext import commands
from   Cogs import DL
from   Cogs import Message

def setup(bot):
	# Add the bot
	bot.add_cog(PciUsb(bot))

class PciUsb:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def pci(self, ctx, ven_dev = None):
		"""Searches pci-ids.ucw.cz for the passed PCI ven:dev id."""
		if not ven_dev:
			await ctx.send("Usage: `{}pci vvvv:iiii` where `vvvv` is the vendor id, and `iiii` is the device id.".format(ctx.prefix))
			return
		try:
			v,i = ven_dev.split(":")
		except:
			await ctx.send("Usage: `{}pci vvvv:iiii` where `vvvv` is the vendor id, and `iiii` is the device id.".format(ctx.prefix))
			return
		if not (len(v)==len(i)==4):
			await ctx.send("Usage: `{}pci vvvv:iiii` where `vvvv` is the vendor id, and `iiii` is the device id.".format(ctx.prefix))
			return
		if not v.isalnum() and not i.isalnum():
			await ctx.send("Ven and dev ids must be alphanumeric.")
			return
		url = "http://pci-ids.ucw.cz/read/PC/{}/{}".format(v,i)
		try:
			html = await DL.async_text(url)
		except:
			await ctx.send("No data returned.")
			return
		out = None
		for line in html.split("\n"):
			if "itemname" in line.lower():
				out = "Name: ".join(line.split("Name: ")[1:]).replace("&amp;","&").replace("&quot;",'"').replace("&apos;","'").replace("&gt;",">").replace("&lt;","<")
				break
		if not out:
			await ctx.send("No name found.")
			return
		# Got data
		await Message.EmbedText(description="`{}` = {}".format(ven_dev,out),title="PCI Device Results",footer="Powered by http://pci-ids.ucw.cz",color=ctx.author).send(ctx)

	@commands.command(pass_context=True)
	async def usb(self, ctx, ven_dev = None):
		"""Searches usb-ids.gowdy.us for the passed USB ven:dev id."""
		if not ven_dev:
			await ctx.send("Usage: `{}usb vvvv:iiii` where `vvvv` is the vendor id, and `iiii` is the device id.".format(ctx.prefix))
			return
		try:
			v,i = ven_dev.split(":")
		except:
			await ctx.send("Usage: `{}usb vvvv:iiii` where `vvvv` is the vendor id, and `iiii` is the device id.".format(ctx.prefix))
			return
		if not (len(v)==len(i)==4):
			await ctx.send("Usage: `{}usb vvvv:iiii` where `vvvv` is the vendor id, and `iiii` is the device id.".format(ctx.prefix))
			return
		if not v.isalnum() and not i.isalnum():
			await ctx.send("Ven and dev ids must be alphanumeric.")
			return
		url = "https://usb-ids.gowdy.us/read/UD/{}/{}".format(v,i)
		try:
			html = await DL.async_text(url)
		except:
			await ctx.send("No data returned.")
			return
		out = None
		for line in html.split("\n"):
			if "itemname" in line.lower():
				out = "Name: ".join(line.split("Name: ")[1:]).replace("&amp;","&").replace("&quot;",'"').replace("&apos;","'").replace("&gt;",">").replace("&lt;","<")
				break
		if not out:
			await ctx.send("No name found.")
			return
		# Got data
		await Message.EmbedText(description="`{}` = {}".format(ven_dev,out),title="USB Device Results",footer="Powered by https://usb-ids.gowdy.us",color=ctx.author).send(ctx)