from plusminus import ArithmeticParser
import regex as re
import math
from discord.ext import commands

def setup(bot):
    # Add the bot
    bot.add_cog(Calc(bot))

class CustomArithmeticParser(ArithmeticParser):
    
    def customize(self):
        # Ensure the ArithmeticParser class customizes first
        super().customize()
        # Add our customizations
        self.add_operator("&",2,ArithmeticParser.LEFT,lambda a,b:a&b)
        self.add_operator("|",2,ArithmeticParser.LEFT,lambda a,b:a|b)
        self.add_operator("^",2,ArithmeticParser.LEFT,lambda a,b:a^b)
        self.add_operator("~",1,ArithmeticParser.RIGHT,lambda a:~a)
        self.add_operator("<<",2,ArithmeticParser.LEFT,lambda a,b:a<<b)
        self.add_operator(">>",2,ArithmeticParser.LEFT,lambda a,b:a>>b)
        self.add_function("sqrt",1,lambda a:math.sqrt(a))

class Calc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.hex_re = re.compile(r"(?i)(0x|#)[0-9a-f]+")

    @commands.command(aliases=["calculate","math"])
    async def calc(self, ctx, *, formula = None):
        """Do some math."""

        if formula is None:
            return await ctx.send('Usage: `{}calc [formula]`'.format(ctx.prefix))
        parser_lines = [x.strip() for x in formula.replace(";","\n").replace(",","\n").split("\n") if x.strip()]
        if not parser_lines:
            return await ctx.send('Usage: `{}calc [formula]`'.format(ctx.prefix))
        clean_lines = "\n".join(x.replace("`","").replace("\\","") for x in parser_lines)
        parser = CustomArithmeticParser()
        try:
            for line in parser_lines:
                offset = 0
                # Let's regex our way through 0x and # integers
                for m in re.finditer(self.hex_re,line):
                    try:
                        start,end = m.span()
                        hex_int = str(int(m.group(0).replace("#","0x"),16))
                        current_len = len(line)
                        # Specifically replace this *one* instance
                        line = line[0:start+offset]+str(hex_int)+line[end+offset:]
                        # Get the offset - i.e. how much our line length
                        # changed after applying - so we know to adjust
                        offset += len(line)-current_len
                    except:
                        pass
                result = parser.evaluate(line)
        except Exception as e:
            msg  = 'I couldn\'t parse that formula :(\n'
            msg += "```\n{}\n```\n".format(str(e).replace("`","back tick"))
            msg += 'Please see [this page](<https://github.com/pyparsing/plusminus/blob/master/doc/arithmetic_parser.md>) for parsing info.\n\n'
            msg += '__Additional syntax supported:__\n'
            msg += '* Newlines, `;`, or `,` characters separate lines passed to the parser\n'
            msg += '* `0x` or `#` prefixes denote hexadecimal values\n'
            msg += '* `&` for bitwise AND\n'
            msg += '* `|` for bitwise OR\n'
            msg += '* `^` for bitwise XOR\n'
            msg += '* `~` for bitwise NOT\n'
            msg += '* `<<` bit shift left\n'
            msg += '* `>>` bit shift right\n'
            msg += '* `sqrt()` square root'
            return await ctx.send(msg)
        # Send the results
        over_amount = (len(clean_lines)+len(str(result))+17)-2000
        if over_amount > 0:
            clean_lines = "..."+clean_lines[over_amount+3:]
        await ctx.send("```\n{}\n```=```\n{}\n```".format(clean_lines,result))
