import asyncio, discord, random
from   discord.ext import commands
from   Cogs import Utils, DisplayName, UserTime, PickList

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Example(bot, settings))

class Example(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    @commands.command()
    async def add(self, ctx, left : int, right : int):
        """Adds two numbers together."""
        await ctx.send(left + right)

    def _roll_string(self, roll):
        # Helper function to give comprehensive breakdown of rolls
        total_rolls = roll["roll_list"]
        vantage     = roll["vantage"]
        add         = roll["add"]
        
        # Format rolls
        dice_string = ""
        final_total = None
        # Format the initial raw rolls
        dice_string += "```\n= Dice Rolls ========================\n"
        dice_rolls = []
        pre_list = []
        total_list = []
        for r in total_rolls:
            dice_rolls.append(", ".join(r['rolls']))
            pre_list.append(r['sum'])
            total_list.append(r['sum']+add)
            
        dice_string += "\n-------------------------------------\n".join(dice_rolls)
        
        # Format modifiers
        if not add == 0:
            sign = "+"
            if add < 0:
                sign = ""
            dice_string += "\n\n= Pre-Total =========================\n{}".format(
                "\n-------------------------------------\n".join([str(x) for x in pre_list])
            )
            dice_string += "\n\n= Modifier ==========================\n{}{}".format(sign, add)
            
        # Format advantage/disadvantage
        if vantage != None:
            if vantage == True:
                # Advantage
                dice_string += "\n\n= Advantage =========================\n"
                total_format = []
                for t in total_list:
                    if t == max(total_list):
                        final_total = t
                        total_format.append("*{}*".format(t))
                    else:
                        total_format.append(str(t))
                dice_string += "\n-------------------------------------\n".join(total_format)
            else:
                # Disadvantage
                dice_string += "\n\n= Disadvantage ======================\n"
                total_format = []
                for t in total_list:
                    if t == min(total_list):
                        final_total = t
                        total_format.append("*{}*".format(t))
                    else:
                        total_format.append(str(t))
                dice_string += "\n-------------------------------------\n".join(total_format)
        
        # Format final total
        if final_total == None:
            final_total = total_list[0]
        dice_string += "\n\n= Final Total =======================\n{}```".format(final_total)
        if len(dice_string) > 2000:
            dice_string = "```\nThe details of this roll are longer than 2,000 characters```"
        return dice_string
    
    def _get_roll_total(self, roll):
        # Helper function to get the final total of a roll
        total_rolls = roll["roll_list"]
        vantage     = roll["vantage"]
        add         = roll["add"]
        total_list = []
        total_crit = []
        total_fail = []
        for r in total_rolls:
            total_list.append(r['sum']+add)
            total_crit.append(r['crit'])
            total_fail.append(r['fail'])

        if vantage != None:
            if vantage == True:
                # Advantage
                highest = max(total_list)
                i = total_list.index(highest)
                return { "total" : highest, "crit" : total_crit[i], "fail" : total_fail[i] }
            else:
                # Disadvantage
                lowest = min(total_list)
                i = total_list.index(lowest)
                return { "total" : lowest, "crit" : total_crit[i], "fail" : total_fail[i] }
        return { "total" : total_list[0], "crit" : total_crit[0], "fail" : total_fail[0] }
        
    @commands.command()
    async def roll(self, ctx, *, dice : str = "1d20"):
        """Rolls a dice in NdN±Na/d format."""
        dice_list = dice.split()
        dice_setup = []
        for dice in dice_list:
            try:
                vantage = None
                d = dice
                if dice.lower().endswith("a"):
                    # Advantage
                    vantage = True
                    dice = dice[:-1]
                elif dice.lower().endswith("d"):
                    # Disadvantage
                    vantage = False
                    dice = dice[:-1]
                parts = dice.split('d')
                rolls = int(parts[0])
                limit = parts[1]
                add   = 0
                if "-" in limit:
                    parts = limit.split('-')
                    limit = int(parts[0])
                    add = int(parts[1])*-1
                elif "+" in limit:
                    parts = limit.split('+')
                    limit = int(parts[0])
                    add = int(parts[1])
                else:
                    limit = int(limit)
                if limit < 1:
                    continue
                dice_setup.append({ "vantage" : vantage, "rolls" : rolls, "limit" : limit, "add" : add, "original" : d })
            except Exception:
                pass
        if not len(dice_setup):
            await ctx.send('Format has to be in NdN±Na/d!')
            return
        if len(dice_setup) > 10:
            await ctx.send("I can only process up to 10 dice rolls at once :(")
            return
        # Got valid dice - let's roll them!
        final_dice = []
        for d in dice_setup:
            vantage = d["vantage"]
            add     = d["add"]
            limit   = d["limit"]
            rolls   = d["rolls"]
            if vantage != None:
                attempts = 2
            else:
                attempts = 1
            total_rolls = []

            # Roll for however many attempts we need
            for i in range(attempts):
                numbers = []
                number_sum = 0
                crit = False
                crit_fail = False
                for r in range(rolls):
                    roll = random.randint(1, limit)
                    if roll == 1:
                        crit_fail = True
                    if roll == limit:
                        crit = True
                    number_sum += roll
                    numbers.append(str(roll))
                total_rolls.append({ "rolls" : numbers, "sum" : number_sum, "crit" : crit, "fail" : crit_fail })
                
            dice_dict = {
                "roll_list" : total_rolls,
                "add" : add,
                "vantage" : vantage,
                "original" : d["original"]
            }
            roll_total = self._get_roll_total(dice_dict)
            dice_dict["total"] = roll_total["total"]
            dice_dict["crit"] = roll_total["crit"]
            dice_dict["fail"] = roll_total["fail"]
            final_dice.append(dice_dict)
            
        # Get a stripped list of items
        dice_list = []
        for d in final_dice:
            d_string = "{} - {}".format(d["original"], d["total"])
            extra = ""
            if d["crit"]:
                extra += "C"
            if d["fail"]:
                extra += "F"
            if len(extra):
                d_string += " (" + extra + ")"
            dice_list.append(d_string)
        # Display the table then wait for a reaction
        message = None
        while True:
            index, message = await PickList.Picker(list=dice_list, title="Pick a roll to show details:", ctx=ctx, timeout=300, message=message).pick()
            if index < 0:
                # Edit message to replace the pick title
                return await message.edit(content=message.content.replace("Pick a roll to show details:", "Roll results:"))
            # Show what we need
            new_mess = "{}. {}:\n{}".format(index+1, dice_list[index], self._roll_string(final_dice[index]))
            await message.edit(content=new_mess)
            # Add the stop reaction - then wait for it or the timeout
            await message.add_reaction("◀")
            # Setup a check function
            def check(reaction, user):
                return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) == "◀"
            # Attempt to wait for a response
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=30, check=check)
            except:
                # Didn't get a reaction
                pass
            # Clear our our reactions
            await message.clear_reactions()
            # Reset back to our totals
            continue

    @commands.command(description='For when you wanna settle the score some other way')
    async def choose(self, ctx, *choices : str):
        """Chooses between multiple choices."""
        await ctx.send(Utils.suppressed(ctx,random.choice(choices)))

    @commands.command(pass_context=True)
    async def joined(self, ctx, *, member : str = None):
        """Says when a member joined."""
        if member is None:
            member = ctx.message.author
            
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                return await Utils.suppressed(ctx,msg)
        # Get localized user time
        local_time = UserTime.getUserTime(ctx.author, self.settings, member.joined_at)
        time_str = "{} {}".format(local_time['time'], local_time['zone'])
        await ctx.send('*{}* joined *{}*'.format(DisplayName.name(member), time_str))