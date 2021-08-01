import ast
import datetime

import aiohttp
import discord
from discord.ext import commands

from assets import time_calc


class Covid(commands.Cog, description="Get Covid-19 stats worldwide, or for a selected country\n"
                                               "Powered by __[disease.sh](https://disease.sh/)__"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="coronastats", aliases=["covidstats"])
    async def corona_stats(self, ctx, country: str = None):
        """Status of the Corona virus worldwide"""
        if country is None:
            track_url = "https://disease.sh/v3/covid-19/all"
        else:
            track_url = f"https://disease.sh/v3/covid-19/countries/{country}?strict=true"
        async with aiohttp.ClientSession() as session:
            async with session.get(track_url) as response:
                response_dict = (await response.content.read()).decode('utf-8')
        response_dict = ast.literal_eval(response_dict)

        if response_dict.get("message") == "Country not found or doesn't have any cases":
            return await ctx.send("Country not found or doesn't have any cases.")

        time_unix = response_dict.get("updated") / 1000
        time_utcformat = datetime.datetime.utcfromtimestamp(time_unix)

        updated_date, updated_time = time_calc.parse_utc(str(time_utcformat))
        total_cases = response_dict.get("cases")
        today_cases = response_dict.get("todayCases")
        total_deaths = response_dict.get("deaths")
        today_deaths = response_dict.get("todayDeaths")
        total_recovered = response_dict.get("recovered")
        today_recovered = response_dict.get("todayRecovered")
        active_cases = response_dict.get("active")
        critical_cases = response_dict.get("critical")
        cases_per_million = response_dict.get("casesPerOneMillion")
        deaths_per_million = response_dict.get("deathsPerOneMillion")
        total_tests = response_dict.get("tests")
        population = response_dict.get("population")
        active_per_million = response_dict.get("activePerOneMillion")
        recovered_per_million = response_dict.get("recoveredPerOneMillion")
        critical_per_million = response_dict.get("criticalPerOneMillion")

        virus_image_url = "https://upload.wikimedia.org/wikipedia/commons/8/82/SARS-CoV-2_without_background.png"
        country_name = response_dict.get("country")  # not used in worldwide stats
        try:
            country_flag_url = response_dict.get("countryInfo").get("flag")
        except AttributeError:
            country_flag_url = virus_image_url
            pass

        if country is None:
            embed = discord.Embed(title="Covid-19 Stats Worldwide",
                                  description=f"Updated **{updated_date}** at **{updated_time} UTC+0**",
                                  color=discord.Color.dark_red())
            embed.set_thumbnail(url=virus_image_url)
        else:
            embed = discord.Embed(title=f"Covid-19 Stats in {country_name}",
                                  description=f"Updated **{updated_date}** at **{updated_time} UTC+0**",
                                  color=discord.Color.dark_red())
            embed.set_thumbnail(url=country_flag_url)
        embed.add_field(name="Total cases", value=total_cases, inline=True)
        embed.add_field(name="New Cases Today", value=today_cases, inline=True)
        embed.add_field(name="Cases per Million", value=cases_per_million, inline=True)

        embed.add_field(name="Total Deaths", value=total_deaths, inline=True)
        embed.add_field(name="Deaths Today", value=today_deaths, inline=True)
        embed.add_field(name="Deaths per Million", value=deaths_per_million, inline=True)

        embed.add_field(name="Active cases", value=active_cases, inline=True)
        embed.add_field(name="Active per Million", value=active_per_million, inline=True)

        embed.add_field(name="Critical Cases", value=critical_cases, inline=True)
        embed.add_field(name="Critical per Million", value=critical_per_million, inline=True)

        embed.add_field(name="Recovered", value=total_recovered, inline=True)
        embed.add_field(name="Recovered Today", value=today_recovered, inline=True)
        embed.add_field(name="Recovered per Million", value=recovered_per_million, inline=True)

        embed.add_field(name="Total Tests", value=total_tests, inline=False)

        if country is None:
            embed.add_field(name="World Population", value=population, inline=True)
        else:
            embed.add_field(name=f"Population of {country_name}", value=population, inline=True)

        embed.set_footer(text=f"Powered by disease.sh")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Covid(bot))
