import asyncio
import discord
import weather
import re
from   discord.ext import commands
from   Cogs import Message
from   Cogs import PickList
from   Cogs import Nullify

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

	def _f_to_c(self, f):
		return int((int(f)-32)/1.8)
	def _c_to_f(self, c):
		return int((int(c)*1.8)+32)
	def _c_to_k(self, c):
		return int(int(c)+273)
	def _k_to_c(self, k):
		return int(int(k)-273)
	def _f_to_k(self, f):
		return self._c_to_k(self._f_to_c(int(f)))
	def _k_to_f(self, k):
		return self._c_to_f(self._k_to_c(int(k)))

	@commands.command(pass_context=True)
	async def tconvert(self, ctx, *, temp = None, from_type = None, to_type = None):
		"""Converts between Fahrenheit, Celsius, and Kelvin.  From/To types can be:
		(F)ahrenheit
		(C)elsius
		(K)elvin"""
		
		types = [ "Fahrenheit", "Celsius", "Kelvin" ]
		usage = "Usage: `{}tconvert [temp] [from_type] [to_type]`".format(ctx.prefix)
		if not temp:
			await ctx.send(usage)
			return
		args = temp.split()
		if not len(args) == 3:
			await ctx.send(usage)
			return
		try:
			f = next((x for x in types if x.lower() == args[1].lower() or x.lower()[:1] == args[1][:1].lower()), None)
			t = next((x for x in types if x.lower() == args[2].lower() or x.lower()[:1] == args[2][:1].lower()), None)
			m = int(args[0])
		except:
			await ctx.send(usage)
			return
		if not(f) or not(t):
			# No valid types
			await ctx.send("Current temp types are: {}".format(", ".join(types)))
			return
		if f == t:
			# Same in as out
			await ctx.send("No change when converting {} ---> {}.".format(f, t))
			return
		output = "I guess I couldn't make that conversion..."
		try:
			out_val = None
			if f == "Fahrenheit":
				if t == "Celsius":
					out_val = self._f_to_c(m)
				else:
					out_val = self._f_to_k(m)
			elif f == "Celsius":
				if t == "Fahrenheit":
					out_val = self._c_to_f(m)
				else:
					out_val = self._c_to_k(m)
			else:
				if t == "Celsius":
					out_val = self._k_to_c(m)
				else:
					out_val = self._k_to_f(m)
			output = "{:,} {} {} is {:,} {} {}".format(m, "degree" if (m==1 or m==-1) else "degrees", f, out_val, "degree" if (out_val==1 or out_val==-1) else "degrees", t)
		except:
			pass
		await ctx.send(output)
	
	@commands.command(pass_context=True)
	async def forecast(self, ctx, *, city_name = None):
		"""Gets some weather."""
		if city_name == None:
			await ctx.send("Usage: `{}forecast [city_name]`".format(ctx.prefix))
			return
		# Strip anything that's non alphanumeric or a space
		city_name = re.sub(r'([^\s\w]|_)+', '', city_name)
		location = self.weather.lookup_by_location(city_name)
		if not location:
			await ctx.send("I couldn't find that city...")
			return
		location_info = location.location
		title = "{}, {} ({})".format(location_info.city, location_info.country, location_info.region[1:])
		
		response_list = ["Current Weather", "10-Day Forecast", "Both"]
		index, message = await PickList.Picker(
			list=response_list, 
			title="Please select an option for `{}`:".format(title.replace('`', '\\`')),
			ctx=ctx
			).pick()

		if index < 0:
			# Aborted!
			await message.edit(content="Forecast cancelled!")
			return
		if index == 0 or index == 2:
			# Build the public response
			current = "__**Current Weather**__:\n\n{}, {} °F ({} °C)".format(self._get_output(location.condition.text), int(self._c_to_f(location.condition.temp)), location.condition.temp)
			await Message.EmbedText(title=title, description=current, color=ctx.author, footer="Powered by Yahoo Weather").edit(ctx, message)
		if index == 1 or index == 2:
			current = "__**Future Forecast:**__"
			fields = []
			for f in location.forecast:
				fields.append({ "name" : f.date, "value" : self._get_output(f.text) + ", {}/{} °F ({}/{} °C)".format(self._c_to_f(f.high), self._c_to_f(f.low), f.high, f.low), "inline" : False })
			mess = await Message.Embed(title=title, description=current, fields=fields, color=ctx.author, pm_after=0, footer="Powered by Yahoo Weather").send(ctx)
			if mess.channel == ctx.author.dm_channel and not index == 2:
				await message.edit(content="Forecast sent to you in dm!")
				return
		await message.edit(content=" ")
