import asyncio
import discord
import weather
from   discord.ext import commands
from   Cogs import Message

def setup(bot):
	# Add the bot
	bot.add_cog(Weather(bot))

# This is the Weather module
class Weather:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.weather = weather.Weather()

	def _get_output(self, w_text):
		if "tornado" in w_text.lower():
			return "🌪️ "+w_text
		if any(x in w_text.lower() for x in ["hurricane", "tropical"]):
			return "🌀 "+w_text
		if any(x in w_text.lower() for x in ["snow", "flurries", "hail"]):
			return "🌨️ "+w_text
		if "thunder" in w_text.lower():
			return "⛈️ "+w_text
		if any(x in w_text.lower() for x in ["rain", "drizzle", "showers", "sleet"]):
			return "🌧️ "+w_text
		if "cold" in w_text.lower():
			return "❄️ "+w_text
		if any(x in w_text.lower() for x in ["windy", "blustery", "breezy"]):
			return "🌬️ "+w_text
		if "mostly cloudy" in w_text.lower():
			return "⛅ "+w_text
		if "partly cloudy" in w_text.lower():
			return "🌤️ "+w_text
		if "cloudy" in w_text.lower():
			return "☁️ "+w_text
		if "fair" in w_text.lower():
			return "🌄 "+w_text
		if any(x in w_text.lower() for x in ["hot", "sunny", "clear"]):
			return "☀️ "+w_text
		if any(x in w_text.lower() for x in ["dust", "foggy", "haze", "smoky"]):
			return "️🌫️ "+w_text
		return w_text

	@commands.command(pass_context=True)
	async def forecast(self, ctx, *, location = None):
		"""Gets some weather."""
		if location == None:
			await ctx.send("Usage: `{}forecast [city name]`".format(ctx.prefix))
			return
		location = self.weather.lookup_by_location(location)
		if not location:
			await ctx.send("I couldn't find that city...")
			return
		location_info = location.location()
		title = "{}, {} ({})".format(location_info['city'], location_info['country'], location_info['region'][1:])
		current = "__**Current Weather**__:\n\n{}, {} °F\n\n__**Future Forecast:**__\n\n".format(self._get_output(location.condition().text()), location.condition().temp())
		fields = []
		for f in location.forecast():
			fields.append({ "name" : f.date(), "value" : self._get_output(f.text()) + ", {}/{} °F".format(f.high(), f.low()), "inline" : False })
		await Message.Embed(title=title, description=current, fields=fields, color=ctx.author).send(ctx)