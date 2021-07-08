import random
import asyncio
import discord
import random
from discord.ext import commands
from Cogs import PickList

MAX_ROLLS = "MAX_ROLLS"
MAX_SIDES = "MAX_SIDES"
MAX_DICE = "MAX_DICE"
MAX_CHARS = "MAX_CHARS"
INVALID = "INVALID"


class RollParser:
    '''
    Class to parse individual NdN±N(a|d) roll strings
    '''

    def __init__(self, **kwargs):
        self.roll_string = kwargs.get("roll", "1d20")
        self.index = kwargs.get("index", 0)
        # Stages are 0 = dice, 1 = sides, 2 = modifiers, 3 = (dis)advantage
        self.stage = kwargs.get("stage", 0)
        self.roll = {}

    def reset(self):
        self.index = 0
        self.stage = 0
        self.roll = {}

    def parse(self):
        # Walks the next character, and parses accordingly
        if self.index >= len(self.roll_string):
            # Let's assign any defaults
            if "dice" in self.roll and not "sides" in self.roll:
                # used 2-5d type syntax - assume d20
                self.roll["sides"] = self.roll["dice"]
                self.roll["dice"] = 1
            self.roll["dice"] = int(self.roll.get("dice", 1))
            self.roll["sides"] = int(self.roll.get("sides", 20))
            self.roll["mod_sign"] = self.roll.get("mod_sign", True)
            self.roll["mod"] = int(self.roll.get("mod", 0))
            self.roll["adv_dis"] = self.roll.get("adv_dis", True if self.roll_string.lower(
            ) == "a" else False if self.roll_string.lower() == "d" else None)
            return self.roll
        char = self.roll_string[self.index]
        self.index += 1  # Increment for the next loop
        # Check which stage - and verify values
        if self.stage == 0:  # We're checking only for numbers - "d+-" breaks it
            if char.lower() in "da+-":
                if char.lower() == "a" and len(self.roll_string) > 1:
                    return INVALID  # Can't start with an "a"
                self.stage += 1
                if char.lower() in "+-":
                    self.index -= 1
                return self.parse()
            if not char.isnumeric():
                return INVALID  # Not "d" and not numeric - bail
            # Got what we want, add it to our dice count
            self.roll["dice"] = self.roll.get("dice", "")+char
        elif self.stage == 1:  # We're checking for the number of sides
            if char.lower() in "da":  # We skipped the modifier
                self.index -= 1
                self.stage += 1
                return self.parse()
            if char in "+-":  # We got a modifier break
                # True for +, False for -
                self.roll["mod_sign"] = (char == "+")
                self.stage += 1
                return self.parse()
            if not char.isnumeric():
                return INVALID  # Not "+-" and not numeric - bail
            self.roll["sides"] = self.roll.get("sides", "")+char
        elif self.stage == 2:  # We're checking for the modifier
            if char.lower() in "da":
                self.roll["adv_dis"] = (char.lower() == "a")
                self.stage += 1
                # We got our last char - let's force exit
                return self.parse()
            if not char.isnumeric():
                return INVALID  # Not "da" and not numeric - bail
            self.roll["mod"] = self.roll.get("mod", "")+char
        else:
            return INVALID  # Extra chars - this isn't right
        return self.parse()


class Roller:
    '''
    Class to manage rolling and displaying of dice rolls
    '''

    def __init__(self):
        self.max_sides = 1000  # Max number of sides per die
        self.max_rolls = 10   # Max number of rolls per parse
        self.max_dice = 1000  # Max number of dice per roll
        self.print_pad = 40   # Pad length when printing
        # self.max_chars = 2000 # Max characters per message

    def _roll(self, roll):
        rolls = [random.randint(1, roll["sides"]) for x in range(roll["dice"])]
        roll_dict = {
            "rolls": rolls,
            "pretotal": sum(rolls),
            "total": sum(rolls) + roll["mod"] if roll["mod_sign"] else sum(rolls) - roll["mod"],
            "crit": any(x == roll["sides"] for x in rolls),
            "fail": any(x == 1 for x in rolls)
        }
        roll_dict["crit_string"] = "{}{}".format(
            "C" if roll_dict["crit"] else "", "F" if roll_dict["fail"] else "")
        return roll_dict

    def _string_from_roll(self, roll):
        roll_string = "{}d{}".format(roll["dice"], roll["sides"])
        if roll["mod"]:
            roll_string += ("+" if roll["mod_sign"]
                            else "-") + str(roll["mod"])
        if roll["adv_dis"] != None:
            roll_string += "a" if roll["adv_dis"] else "d"
        return roll_string

    def roll(self, roll_string=None):
        # Default to a single d20 if nothing passed
        roll_string = roll_string if roll_string else "1d20"
        # Let's walk our string - up to 10 valid dice rolls can exist here
        rolls = roll_string.split()
        if len(rolls) > self.max_rolls:
            return MAX_ROLLS
        parsed_rolls = []
        for roll in rolls:
            out = RollParser(roll=roll).parse()
            if out == INVALID:
                return INVALID
            if out["dice"] > self.max_dice:
                return MAX_DICE
            if out["sides"] > self.max_sides:
                return MAX_SIDES
            out["roll_string"] = self._string_from_roll(out)
            # Actually roll the dice
            roll_list = [self._roll(out)]
            if out["adv_dis"] != None:
                # Roll again
                roll_list.append(self._roll(out))
                roll_list = sorted(
                    roll_list, key=lambda x: x["total"], reverse=out["adv_dis"])
            out["rolls"] = roll_list
            parsed_rolls.append(out)
        return parsed_rolls

    def rolls_string(self, roll_list=None):
        if not roll_list:
            return
        return "\n".join(["{}. {}".format(x+1, y) for x, y in enumerate(self.rolls_list(roll_list))])

    def rolls_list(self, roll_list=None):
        if not roll_list:
            return
        return ["{} = {:,}{}".format(x["roll_string"], x["rolls"][0]["total"], " ({})".format(x["rolls"][0]["crit_string"]) if x["rolls"][0]["crit_string"] else "") for x in roll_list]

    def roll_string(self, roll=None):
        # Only get the first roll if a list is passed
        if isinstance(roll, list) and len(roll):
            roll = roll[0]
        # Add our headers - padding them out as needed
        roll_string = "= Dice Roll{} ".format(
            "" if roll["dice"] == 1 else "s").ljust(self.print_pad, "=")+"\n"
        roll_string += "\n{}\n".format("-"*self.print_pad).join(
            [", ".join(["{:,}".format(x) for x in y["rolls"]]) for y in roll["rolls"]])
        if roll["mod"]:  # We have a modifier - give a pre-total, then the modifier
            roll_string += "\n\n" + \
                "= Pre-Total ".ljust(self.print_pad, "=")+"\n"
            roll_string += "\n{}\n".format("-"*self.print_pad).join(
                [str(x["pretotal"]) for x in roll["rolls"]])
            roll_string += "\n\n"+"= Modifier ".ljust(self.print_pad, "=")+"\n"
            roll_string += "{}{:,}".format(
                "+" if roll["mod_sign"] else "-", roll["mod"])
        if roll["adv_dis"] != None:  # We have either advantage or disadvantage - highlight which via *{}*
            roll_string += "\n\n" + \
                "= {}".format("Advantage" if roll["adv_dis"] else "Disadvantage").ljust(
                    self.print_pad, "=")+"\n"
            roll_string += "\n{}\n".format("-"*self.print_pad).join(["*{:,}*".format(
                x["total"]) if i == 0 else "{:,}".format(x["total"]) for i, x in enumerate(roll["rolls"])])
        # Print our final total and return the results
        roll_string += "\n\n"+"= Final Total ".ljust(self.print_pad, "=")+"\n"
        roll_string += "{:,}".format(roll["rolls"][0]["total"])
        return roll_string


def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Dice())


class Dice(commands.Cog):
    '''
    The Dice class exists to roll dice for table top games like Dungeons and Dragons.
    '''
    @commands.command()
    async def roll(self, ctx, *, dice=None):
        """Performs up to 10 space-delimited dice rolls in NdN±Na|d format."""
        # Display the table then wait for a reaction
        d = Roller()
        r = d.roll(dice)
        if r == MAX_ROLLS:
            return await ctx.send("I can only perform {:,} roll{} at a time!".format(d.max_rolls, "" if d.max_rolls == 1 else "s"))
        if r == MAX_DICE:
            return await ctx.send("I can only roll up to {:,} dice per roll!".format(d.max_dice))
        if r == MAX_SIDES:
            return await ctx.send("I can only roll dice with up to {:,} face{} per roll!".format(d.max_sides, "" if d.max_sides == 1 else "s"))
        if r == INVALID:
            return await ctx.send("Dice rolls must be in `NdN±Na|d` format!  Rolling a single d10 with a -5 modifier and disadvantage would look like: `{}roll 1d10-5d`".format(ctx.prefix))
        message = None
        while True:
            index, message = await PickList.Picker(list=d.rolls_list(r), title="Pick a roll to show details:", ctx=ctx, timeout=300, message=message).pick()
            if index < 0:
                # Edit message to replace the pick title
                return await message.edit(content=message.content.replace("Pick a roll to show details:", "Roll results:"))
            # Show what we need
            new_mess = "{}. {}:\n```\n{}\n```".format(
                index+1, r[index]["roll_string"], d.roll_string(r[index]))
            if len(new_mess) > 2000:  # Tooooooo big
                new_mess = "{}. {}:\n```\nThe details of this roll are longer than 2,000 characters :(```".format(
                    index+1, r[index]["roll_string"])
            await message.edit(content=new_mess)
            # Add the return reaction - then wait for it or the timeout
            await message.add_reaction("◀")
            # Setup a check function

            def check(reaction, user):
                return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) == "◀"
            # Attempt to wait for a response
            try:
                reaction, user = await ctx.bot.wait_for('picklist_reaction', timeout=30, check=check)
            except:
                # Didn't get a reaction
                pass
            # Clear our our reactions
            try:
                await message.clear_reactions()
            except:
                pass
            # Reset back to our totals
            continue
