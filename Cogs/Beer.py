import discord, math
from discord.ext import commands
from Cogs import Message

def setup(bot):
    # Add the bot
    bot.add_cog(Beer(bot))

class Beer(commands.Cog):

    # Init with the bot reference
    def __init__(self, bot):
        self.bot = bot
        self.volume_oz = {
            "ounce":1,
            "gallon":128,
            "liter":33.814023,
        }
        self.volume_oz["milliliter"] = self.volume_oz["liter"]/1000
        self.volume_oz["hectoliter"] = self.volume_oz["liter"]*100
        self.volume_oz["bbl"] = self.volume_oz["gallon"]*31
        self.volume_oz["oz"] = self.volume_oz["ounce"]
        self.weight_oz = {
            "ounce":1,
            "gram":0.035274,
            "lb":16
        }
        self.weight_oz["pound"] = self.weight_oz["lb"]
        self.weight_oz["kilogram"] = self.weight_oz["gram"]*1000
        self.weight_oz["oz"] = self.weight_oz["ounce"]

    def _check_float(self, f, round_to=4):
        if f == int(f): return int(f)
        if round_to<=0: return f
        temp = f*10**round_to
        if temp-int(temp) >= 0.5: temp += 1
        return self._check_float(int(temp)/10**round_to,round_to=0)

    def _parse_value(self, value, valid, default=None):
        # Let's walk the value getting any 0-9, or . chars first
        # then look for a suffix
        num = suf = ""
        value = "".join(value.split()) # Remove any whitespace
        nums = True
        for i,x in enumerate(value.replace(",","")):
            if nums and x in "0123456789.": # got a number
                num += x
            else: # non-number
                nums = False
                suf += x
        # Try to cast our number properly
        try: num = float(num)
        except: return # Just bail
        suf = suf or default
        if not suf: return (num,None) # No suffix, and no default - return as-is
        # Let's check for pluralization of the suffix - and strip the trailing "s"
        if len(suf) > 1 and suf[-1].lower() == "s":
            suf = suf[:-1]
        # Try to get the suffix in the valid values
        suf = next((x for x in valid if x.lower().startswith(suf.lower())),None)
        if suf is None: return # Wasn't found
        # We got a valid value - return it
        return (num,suf)

    def _tanh(self, value):
        return (math.exp(value) - math.exp(-value)) / (math.exp(value) + math.exp(-value))

    @commands.command(aliases=["hop","hops4ibu","hopsforibu","hibu"])
    async def hops(self, ctx, *, batch_size = None, original_gravity = None, target_ibu = None, alpha_acid_percent = None, boil_time_minutes = None, output_unit = None):
        """Calculates the amount of hops required to reach the target IBU.

        Required Arguments:
            batch_size - accepts Ounces, Gallons, Liters, Hectoliters, Milliliters, or Bbl (default is Bbl)
                eg. 19.75bbl
            original_gravity - accepts Plato or Standard (default is Plato if > 1.2 otherwise Standard)
                eg. 11.0p
            target_ibu - accepts an IBU value in either Rager or Tinseth
                eg. 38.68r or 30.45t
            alpha_acid_percent - accepts a percent range from 0-100
                eg. 11.5%
            boil_time_minutes - accepts a > 0 minute value for boil time
                eg. 60
        Optional Arguments:
            output_unit - accepts Ounces, Pounds, Grams, or Kilograms (default is lb)
            leaf - change the hop amount from pellets to whole leaf
        """
        usage = "Usage: `{}hops [batch_size] [original_gravity] [target_ibu] [alpha_acid_percent] [boil_time_minutes]`".format(ctx.prefix)
        if not batch_size: return await ctx.send(usage)
        args = batch_size.split()
        use_whole_leaf = next((x for x in args if x.lower() in ("whole","wholeleaf","leaf","whole_leaf")),None)
        if use_whole_leaf: # Strip the arg
            args = [x for x in args if not x == use_whole_leaf]
        if len(args) == 6: # Last arg should be the output
            try:
                _,output_unit = self._parse_value("1"+args.pop(),self.weight_oz,default="lb")
            except:
                return await ctx.send("Incorrect value for `output_unit`\n{}".format(usage))
        else:
            output_unit = "lb" # Default is pounds
        if not len(args) == 5: return await ctx.send(usage)
        # Should have enough args - let's start sanitizing them
        batch_size,original_gravity,target_ibu,alpha_acid_percent,boil_time_minutes = args
        try:
            b_val,b_suf = self._parse_value(batch_size,self.volume_oz,default="bbl")
            assert b_val > 0
            b_oz = self.volume_oz[b_suf]*b_val
            b_l  = b_oz/self.volume_oz["liter"] # Get batch size in liters
        except:
            return await ctx.send("Incorrect value for `batch_size`\n{}".format(usage))
        try:
            g_val,g_suf = self._parse_value(original_gravity,("standard","sg","plato"))
            assert g_val > 0
            g_suf = g_suf or "plato" if g_val > 1.2 else "standard"
            g_sg  = self._sg_from_plato(g_val) if g_suf == "plato" else g_val
        except:
            return await ctx.send("Incorrect value for `original_gravity`\n{}".format(usage))
        try:
            i_val,i_suf = self._parse_value(target_ibu,("rager","tinseth"),default="tinseth")
            assert i_val > 0
        except:
            return await ctx.send("Incorrect value for `target_ibu`\n{}".format(usage))
        try:
            aa = float(alpha_acid_percent.replace(",","").replace("%",""))
            assert 0 < aa <= 100
        except:
            return await ctx.send("Incorrect value for `alpha_acid_percent`\n{}".format(usage))
        try:
            bt = float(boil_time_minutes)
            assert bt > 0
        except:
            return await ctx.send("Incorrect value for `boil_time_minutes`\n{}".format(usage))
        # We should have proper values here - let's gooooooooo
        hop_val = 1 if use_whole_leaf else 1.15
        # Do some hefty rearranged math
        if i_suf.lower() == "tinseth":
            h = (2**(6*g_sg-5) * 5**(3*g_sg-2) * b_l * i_val * math.e**(bt/25)) / (39759 * aa * hop_val * (math.e**(bt/25)-1))
        else:
            u = 18.11 + 13.86 * self._tanh((bt - 31.32) / 18.27)
            d = max((g_sg - 1.050)/0.2, 0)
            h = ((d+1) * b_l * i_val) / (100 * aa * u * hop_val)
        # Let's convert our h value to the proper units - it's in KG currently
        h_final = self.weight_oz["kilogram"] * h / self.weight_oz[output_unit]
        # Let's build the embed with our output
        fields = [
            {"inline":False,"name":"Batch Size","value":"{:,} {}{}".format(
                self._check_float(b_val),b_suf,"" if b_val=="oz" or b_val==1 else "s"
            )},
            {"inline":False,"name":"Original Target Gravity","value":"{:,} {}".format(
                self._check_float(g_val),"SG" if g_suf=="standard" else g_suf.capitalize()
            )},
            {"inline":False,"name":"Target IBU","value":"{:,} ({})".format(
                self._check_float(i_val),i_suf.capitalize()
            )},
            {"inline":False,"name":"Alpha Acid Percent","value":"{:,}%".format(
                self._check_float(aa,round_to=2)
            )},
            {"inline":False,"name":"Boil Time","value":"{:,} minute{}".format(
                self._check_float(bt),"" if bt==1 else "s"
            )},
            {"inline":False,"name":"Hop Amount Needed ({})".format("Whole Leaf" if use_whole_leaf else "Pellets"),"value":"{:,} {}{}".format(
                self._check_float(h_final,round_to=2),output_unit,"" if output_unit=="oz" or h==1 else "s"
            )}
        ]
        await Message.Embed(
            title="Required Hops for Target IBU",
            fields=fields,
            color=ctx.author
        ).send(ctx)

    @commands.command(aliases=["bitternes","bitter"])
    async def ibu(self, ctx, *, batch_size = None, original_gravity = None, hops_amount = None, alpha_acid_percent = None, boil_time_minutes = None):
        """Calculates the IBU (International Bitterness Units) for the given values.  The output is listed in both Rager and Tinseth.

        Required Arguments:
            batch_size - accepts Ounces, Gallons, Liters, Hectoliters, Milliliters, or Bbl (default is Bbl)
                eg. 19.75bbl
            original_gravity - accepts Plato or Standard (default is Plato if > 1.2 otherwise Standard)
                eg. 11.0p
            hops_amount - accepts Ounces, Pounds, Grams, or Kilograms (default is lb, assumes hop pellets)
                eg. 5.5lb
            alpha_acid_percent - accepts a percent range from 0-100
                eg. 11.5%
            boil_time_minutes - accepts a > 0 minute value for boil time
                eg. 60
        Optional Arguments:
            leaf - change the hop amount from pellets to whole leaf

        Replying to a previous ibu command's output message will append the IBU values in a running total.
        """
        usage = "Usage: `{}ibu [batch_size] [original_gravity] [hops_amount] [alpha_acid_percent] [boil_time_minutes]`".format(ctx.prefix)
        if not batch_size: return await ctx.send(usage)
        args = batch_size.split()
        use_whole_leaf = next((x for x in args if x.lower() in ("whole","wholeleaf","leaf","whole_leaf")),None)
        if use_whole_leaf: # Strip the arg
            args = [x for x in args if not x == use_whole_leaf]
        if not len(args) == 5: return await ctx.send(usage)
        # Let's see if we're responding to a prior message
        prev_r = prev_t = prev_e = None
        try:
            if ctx.message.reference: # Resolve the replied to reference to a message object
                reply = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                if reply.embeds: # Get the first embed - if any
                    prev_e = reply.embeds[0]
        except: pass
        # If we have an embed in the reply - check for IBU Total (Rager) and IBU Total (Tinseth)
        # or IBU (Rager) and IBU (Tinseth)
        if prev_e:
            embed_dict = prev_e.to_dict()
            def get_vals_from_embed(ibu_vals):
                r,t = ibu_vals.split("\n")
                return (float(r.split()[0]),float(t.split()[0]))
            for field in embed_dict.get("fields",[]):
                if field.get("name") == "IBU Results (Total)" or (field.get("name") == "IBU Results" and prev_r is None and prev_t is None):
                    try: prev_r,prev_t = get_vals_from_embed(field.get("value"))
                    except: pass
        # Should have enough args - let's start sanitizing them
        batch_size,original_gravity,hops_amount,alpha_acid_percent,boil_time_minutes = args
        try:
            b_val,b_suf = self._parse_value(batch_size,self.volume_oz,default="bbl")
            assert b_val > 0
            b_oz = self.volume_oz[b_suf]*b_val
            b_l  = b_oz/self.volume_oz["liter"] # Get batch size in liters
        except:
            return await ctx.send("Incorrect value for `batch_size`\n{}".format(usage))
        try:
            g_val,g_suf = self._parse_value(original_gravity,("standard","sg","plato"))
            assert g_val > 0
            g_suf = g_suf or "plato" if g_val > 1.2 else "standard"
            g_sg  = self._sg_from_plato(g_val) if g_suf == "plato" else g_val
        except:
            return await ctx.send("Incorrect value for `original_gravity`\n{}".format(usage))
        try:
            h_val,h_suf = self._parse_value(hops_amount,self.weight_oz,default="lb")
            assert h_val > 0
            h_oz = self.weight_oz[h_suf]*h_val
            h_kg = h_oz/self.weight_oz["kilogram"] # Get in kg
        except:
            return await ctx.send("Incorrect value for `hops_amount`\n{}".format(usage))
        try:
            aa = float(alpha_acid_percent.replace(",","").replace("%",""))
            assert 0 < aa <= 100
        except:
            return await ctx.send("Incorrect value for `alpha_acid_percent`\n{}".format(usage))
        try:
            bt = float(boil_time_minutes)
            assert bt > 0
        except:
            return await ctx.send("Incorrect value for `boil_time_minutes`\n{}".format(usage))
        # We should have proper values here - let's gooooooooo
        hop_val = 1 if use_whole_leaf else 1.15
        # Do some hefty math
        t = (3975.9 * 0.000125 ** (g_sg-1) * aa * h_kg * hop_val * (1-math.e**(-0.04 * bt))) / b_l
        u = 18.11 + 13.86 * self._tanh((bt - 31.32) / 18.27)
        d = max((g_sg - 1.050)/0.2, 0)
        r = h_kg * 100 * u * hop_val * aa / (b_l * (1 + d))
        # Let's build the embed with our output
        fields = [
            {"inline":False,"name":"Batch Size","value":"{:,} {}{}".format(
                self._check_float(b_val),b_suf,"" if b_val=="oz" or b_val==1 else "s"
            )},
            {"inline":False,"name":"Original Target Gravity","value":"{:,} {}".format(
                self._check_float(g_val),"SG" if g_suf=="standard" else g_suf.capitalize()
            )},
            {"inline":False,"name":"Hops Amount ({})".format("Whole Leaf" if use_whole_leaf else "Pellets"),"value":"{:,} {}{}".format(
                self._check_float(h_val),h_suf,"" if h_suf=="oz" or h_val==1 else "s"
            )},
            {"inline":False,"name":"Alpha Acid Percent","value":"{:,}%".format(
                self._check_float(aa,round_to=2)
            )},
            {"inline":False,"name":"Boil Time","value":"{:,} minute{}".format(
                self._check_float(bt),"" if bt==1 else "s"
            )},
            {"inline":False,"name":"IBU Results","value":"{:,} (Rager)\n{:,} (Tinseth)".format(
                self._check_float(r,round_to=2),
                self._check_float(t,round_to=2)
            )}
        ]
        if prev_r is not None and prev_t is not None:
            # Insert the previous values
            fields.insert(-1,{"inline":False,"name":"IBU Results (Previous)","value":"{:,} (Rager)\n{:,} (Tinseth)".format(
                self._check_float(prev_r,round_to=2),
                self._check_float(prev_t,round_to=2)
            )})
            # Add the totals to the end
            fields.append({"inline":False,"name":"IBU Results (Total)","value":"{:,} (Rager)\n{:,} (Tinseth)".format(
                self._check_float(prev_r+r,round_to=2),
                self._check_float(prev_t+t,round_to=2)
            )})
        await Message.Embed(
            title="Bitterness Calculation (IBU)",
            fields=fields,
            color=ctx.author
        ).send(ctx)

    @commands.command()
    async def vconvert(self, ctx, *, volume = None, from_type = None, to_type = None):
        """Converts between Ounces, Gallons, Liters, Milliliters, and Beer Barrels.  From/To types can be:
        (O)unces
        (G)allons
        (L)iters
        (H)ectoliters
        (M)illiliters
        (B)eer Barrels"""
        usage = "Usage: `{}vconvert [volume] [from_type] [to_type]`".format(ctx.prefix)
        if not volume: return await ctx.send(usage)
        args = volume.split()
        if not len(args) == 3: return await ctx.send(usage)
        try:
            f = next((x for x in self.volume_oz if x[0].lower().startswith(args[1][0].lower())),None)
            t = next((x for x in self.volume_oz if x[0].lower().startswith(args[2][0].lower())),None)
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
            out_val = self._check_float(m*self.volume_oz[f]/self.volume_oz[t])
            output = "{:,} {} is {:,} {}".format(
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
