import asyncio
import discord
from geopy.geocoders import Nominatim
import re
from   discord.ext import commands
from   Cogs import Message
from   Cogs import PickList
from   Cogs import Nullify
from   Cogs import DL

def setup(bot):
	# Add the bot
	bot.add_cog(Weather(bot))

# This is the Weather module
class Weather(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.key = "412efff445b9e3ba1f1e80b083b6b3d4"
		self.geo = Nominatim(user_agent="CorpBot")

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
		location = self.geo.geocode(city_name)
		if location == None:
			await ctx.send("I couldn't find that city...")
			return
		r = await DL.async_json("http://api.openweathermap.org/data/2.5/weather?appid={}&lat={}&lon={}".format(
			self.key,
			location.latitude,
			location.longitude
		))
		if r["cod"] == "404":
			await ctx.send("I couldn't find that city...")
			return
		# Gather the city info - and parse the weather info
		main    = r["main"]
		weath   = r["weather"]
		# Make sure we get the temps in both F and C
		tc   = self._k_to_c(main["temp"])
		tf   = self._c_to_f(tc)
		minc = self._k_to_c(main["temp_min"])
		minf = self._c_to_f(minc)
		maxc = self._k_to_c(main["temp_max"])
		maxf = self._c_to_f(maxc)

		title = location.address
		# Gather the formatted conditions
		weath_list = []
		for x,y in enumerate(weath):
			d = y["description"]
			if x == 0:
				d = d.capitalize()
			weath_list.append(self._get_output(d))
		condition = ", ".join(weath_list)
		# Format the description
		desc = "__**Current Forecast:**__\n\n{}, {} °F ({} °C)\n\n__**High/Low:**__\n\n{} °F ({} °C) / {} °F ({} °C)".format(
			condition,
			tf, tc,
			maxf, maxc,
			minf, minc
		)
		# Let's post it!
		await Message.EmbedText(
			title=title,
			description=desc,
			color=ctx.author,
			footer="Powered by OpenWeatherMap"
		).send(ctx)
