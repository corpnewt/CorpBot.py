import discord
from discord.ext import commands
from Cogs import Message

def setup(bot):
	# Add the bot
	bot.add_cog(Beer(bot))

class Beer(commands.Cog):

	# Init with the bot reference
	def __init__(self, bot):
		self.bot = bot
		self.ounces = {
			"ounce":1,
			"gallon":128,
			"liter":33.814023,
		}
		self.ounces["milliliter"] = self.ounces["liter"]/1000
		self.ounces["bbl"] = self.ounces["gallon"]*31

	def _check_float(self, f, round_to=4):
		if f == int(f): return int(f)
		if round_to<=0: return f
		temp = f*10**round_to
		if temp-int(temp) >= 0.5: temp += 1
		return self._check_float(int(temp)/10**round_to,round_to=0)

	@commands.command()
	async def vconvert(self, ctx, *, volume = None, from_type = None, to_type = None):
		"""Converts between Ounces, Gallons, Liters, Milliliters, and Beer Barrels.  From/To types can be:
		(O)unces
		(G)allons
		(L)iters
		(M)illiliters
		(B)eer Barrels"""
		usage = "Usage: `{}vconvert [volume] [from_type] [to_type]`".format(ctx.prefix)
		if not volume: return await ctx.send(usage)
		args = volume.split()
		if not len(args) == 3: return await ctx.send(usage)
		try:
			f = next((x for x in self.ounces if x[0].lower().startswith(args[1][0].lower())),None)
			t = next((x for x in self.ounces if x[0].lower().startswith(args[2][0].lower())),None)
			m = self._check_float(float(args[0]))
		except:
			return await ctx.send(usage)
		if not f or not t:
			# No valid types
			return await ctx.send("Current volume types are: {}".format(", ".join(types)))
		if f == t:
			# Same in as out
			return await ctx.send("No change when converting {} ---> {}.".format(f, t))
		output = "I guess I couldn't make that conversion..."
		try:
			out_val = self._check_float(m*self.ounces[f]/self.ounces[t])
			output = "{:,} {} == {:,} {}".format(
				m,
				f+("" if abs(m)==1 else "s"),
				out_val,
				t+("" if abs(out_val)==1 else "s")
			)
		except:
			pass
		await ctx.send(output)

	def _sg_from_plato(self, plato):
		return 259/(259-float(plato))

	def _plato_from_sg(self, sg):
		return 259-(259/float(sg))

	@commands.command()
	async def abv(self, ctx, original_gravity = None, final_gravity = None):
		"""Calculates the alcohol by volume for the passed original and final gravity.
		Accepts (P)lato or (S)tandard Gravity values."""
		usage = "Usage: `{}abv [original_gravity] [final_gravity]`\neg: `{}abv 1.055s 1.015s` or `{}abv 12p 2.5p`".replace("{}",ctx.prefix)
		if not original_gravity or not final_gravity: return await ctx.send(usage)
		# Let's check for gravity values and get our suffixes
		o_grav = "".join([x for x in original_gravity if x in ",.0123456789"])
		o_suffix = next((x for x in original_gravity if x.isalpha()),"").lower()
		f_grav = "".join([x for x in final_gravity if x in ",.0123456789"])
		f_suffix = next((x for x in final_gravity if x.isalpha()),"").lower()
		# Make sure the numbers are numbers
		try:
			o_grav = float(o_grav)
			f_grav = float(f_grav)
		except:
			return await ctx.send(usage)
		# Try to get proper suffixes - fall back on auto-detection based on values if needed
		o_suffix = o_suffix if o_suffix in ("p","s") else "p" if o_grav > 1.2 else "s"
		f_suffix = f_suffix if f_suffix in ("p","s") else "p" if f_grav > 1.2 else "s"
		# Ensure we're using SG for our calculations
		o_sg = o_grav if o_suffix == "s" else self._sg_from_plato(o_grav)
		o_p  = o_grav if o_suffix == "p" else self._plato_from_sg(o_grav)
		f_sg = f_grav if f_suffix == "s" else self._sg_from_plato(f_grav)
		f_p  = f_grav if f_suffix == "p" else self._plato_from_sg(f_grav) 
		# Make sure the larger number is the original gravity
		if f_sg > o_sg:
			# Reverse them
			f_sg,f_p,o_sg,o_p = o_sg,o_p,f_sg,f_p
		# Let's process what we have and show the user their values
		# Check if we need to show "~" for rounding with SG
		o_sg_round = self._check_float(o_sg)
		f_sg_round = self._check_float(f_sg)
		abv = self._check_float((o_sg-f_sg)*131.25,round_to=2)
		fields = [
			{"inline":False,"name":"Final ABV: {:,}%".format(abv),"value":"({}{:,} - {}{:,}) * 131.25 = {:,}".format(
				"" if o_sg==o_sg_round else "~",
				o_sg_round,
				"" if f_sg==f_sg_round else "~",
				f_sg_round,
				abv
			)},
			{"inline":False,"name":"Original Gravity","value":"{:,} SG - {:,} Plato".format(
				self._check_float(o_sg),
				self._check_float(o_p,round_to=2)
			)},
			{"inline":False,"name":"Final Gravity","value":"{:,} SG - {:,} Plato".format(
				self._check_float(f_sg),
				self._check_float(f_p,round_to=2)
			)}
		]
		await Message.Embed(
			title="ABV: (OG - FG) * 131.25",
			fields=fields,
			color=ctx.author
		).send(ctx)