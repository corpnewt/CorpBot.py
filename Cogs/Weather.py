import asyncio
import discord
import datetime
import re
from geopy.geocoders import Nominatim
from discord.ext import commands
from Cogs import Message, PickList, DL


def setup(bot):
    # Add the bot
    bot.add_cog(Weather(bot))

# This is the Weather module


class Weather(commands.Cog):

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot):
        self.bot = bot
        self.key = bot.settings_dict.get("weather", "")
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
        if any(x in w_text.lower() for x in ["partly cloudy", "scattered clouds", "few clouds", "broken clouds"]):
            return "🌤️ "+w_text
        if any(x in w_text.lower() for x in ["cloudy", "clouds"]):
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
    async def tconvert(self, ctx, *, temp=None, from_type=None, to_type=None):
        """Converts between Fahrenheit, Celsius, and Kelvin.  From/To types can be:
        (F)ahrenheit
        (C)elsius
        (K)elvin"""

        types = ["Fahrenheit", "Celsius", "Kelvin"]
        usage = "Usage: `{}tconvert [temp] [from_type] [to_type]`".format(
            ctx.prefix)
        if not temp:
            await ctx.send(usage)
            return
        args = temp.split()
        if not len(args) == 3:
            await ctx.send(usage)
            return
        try:
            f = next((x for x in types if x.lower() == args[1].lower(
            ) or x.lower()[:1] == args[1][:1].lower()), None)
            t = next((x for x in types if x.lower() == args[2].lower(
            ) or x.lower()[:1] == args[2][:1].lower()), None)
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
            output = "{:,} {} {} is {:,} {} {}".format(m, "degree" if (
                m == 1 or m == -1) else "degrees", f, out_val, "degree" if (out_val == 1 or out_val == -1) else "degrees", t)
        except:
            pass
        await ctx.send(output)

    def get_weather_text(self, r={}, show_current=True):
        # Returns a string representing the weather passed
        main = r["main"]
        weath = r["weather"]
        # Make sure we get the temps in both F and C
        tc = self._k_to_c(main["temp"])
        tf = self._c_to_f(tc)
        minc = self._k_to_c(main["temp_min"])
        minf = self._c_to_f(minc)
        maxc = self._k_to_c(main["temp_max"])
        maxf = self._c_to_f(maxc)
        # Gather the formatted conditions
        weath_list = []
        for x, y in enumerate(weath):
            d = y["description"]
            if x == 0:
                d = d.capitalize()
            weath_list.append(self._get_output(d))
        condition = ", ".join(weath_list)
        # Format the description
        if show_current:
            desc = "{} °F ({} °C),\n\n".format(tf, tc)
        else:
            desc = ""
        desc += "{}\n\nHigh of {} °F ({} °C) - Low of {} °F ({} °C)\n\n".format(
                condition,
                maxf, maxc,
                minf, minc
        )
        return desc

    @commands.command(pass_context=True)
    async def weather(self, ctx, *, city_name=None):
        """Gets some weather."""
        if city_name == None:
            await ctx.send("Usage: `{}weather [city_name]`".format(ctx.prefix))
            return
        # Strip anything that's non alphanumeric or a space
        city_name = re.sub(r'([^\s\w]|_)+', '', city_name)
        location = self.geo.geocode(city_name)
        if location == None:
            await ctx.send("I couldn't find that city...")
            return
        title = location.address
        # Just want the current weather
        r = await DL.async_json("http://api.openweathermap.org/data/2.5/weather?appid={}&lat={}&lon={}".format(
            self.key,
            location.latitude,
            location.longitude
        ))
        desc = self.get_weather_text(r)
        # Let's post it!
        await Message.EmbedText(
            title=title,
            description=desc,
            color=ctx.author,
            footer="Powered by OpenWeatherMap"
        ).send(ctx)

    @commands.command(pass_context=True)
    async def forecast(self, ctx, *, city_name=None):
        """Gets some weather, for 5 days or whatever."""
        if city_name == None:
            await ctx.send("Usage: `{}forecast [city_name]`".format(ctx.prefix))
            return
        # Strip anything that's non alphanumeric or a space
        city_name = re.sub(r'([^\s\w]|_)+', '', city_name)
        location = self.geo.geocode(city_name)
        if location == None:
            await ctx.send("I couldn't find that city...")
            return
        title = location.address
        # We want the 5-day forecast at this point
        r = await DL.async_json("http://api.openweathermap.org/data/2.5/forecast?appid={}&lat={}&lon={}".format(
            self.key,
            location.latitude,
            location.longitude
        ))
        days = {}
        for x in r["list"]:
            # Check if the day exists - if not, we set up a pre-day
            day = x["dt_txt"].split(" ")[0]
            is_noon = "12:00:00" in x["dt_txt"]
            if not day in days:
                days[day] = {
                    "main": x["main"],
                    "weather": x["weather"],
                    "day_count": 1
                }
                continue
            # Day is in the list - let's check values
            if x["main"]["temp_min"] < days[day]["main"]["temp_min"]:
                days[day]["main"]["temp_min"] = x["main"]["temp_min"]
            if x["main"]["temp_max"] > days[day]["main"]["temp_max"]:
                days[day]["main"]["temp_max"] = x["main"]["temp_max"]
            # Add the temp
            days[day]["main"]["temp"] += x["main"]["temp"]
            days[day]["day_count"] += 1
            # Set the weather data if is noon
            if is_noon:
                days[day]["weather"] = x["weather"]
        fields = []
        for day in sorted(days):
            # Average the temp, strip weather duplicates
            days[day]["main"]["temp"] /= days[day]["day_count"]
            fields.append({
                "name": datetime.datetime.strptime(day, "%Y-%m-%d").strftime("%A, %b %d, %Y")+":",
                "value": self.get_weather_text(days[day], False),
                "inline": False
            })
        # Now we send our embed!
        await Message.Embed(
            title=title,
            fields=fields,
            color=ctx.author,
            footer="Powered by OpenWeatherMap"
        ).send(ctx)
