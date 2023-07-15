import discord, os, random, textwrap
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from Cogs import Nullify

def setup(bot):
    bot.add_cog(Clippy(bot))

class Clippy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.max_font = 30
        self.min_font = 2
        # Pre-load font sizes to make later calcs faster
        self.font_dicts = {}
        for s in range(self.max_font,self.min_font-1,-1):
            self.font_dicts[s] = self.get_size_dict(ImageFont.truetype("fonts/comic.ttf",size=s))

        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    def get_size_dict(self,font):
        # Returns the size of all ascii chars in the passed font
        draw = ImageDraw.Draw(Image.open('images/clippy.png'))
        size_dict = {}
        max_w = max_h = avg_w = 0
        for x in range(128):
            char = chr(x)
            l,t,r,b = draw.textbbox((0,0),char,font=font)
            w,h = r-l,b-t
            if char != "\n":
                # Use the textlength instead - but skip newlines
                w = draw.textlength(char,font=font)
            size_dict[char] = (w,h)
            if w > max_w: max_w = w
            if h > max_h: max_h = h
            avg_w += w
        size_dict["max_w"] = max_w
        size_dict["max_h"] = max_h
        size_dict["avg_w"] = avg_w/128
        # Get some kerning info
        text = "the quick brown fox jumps over the lazy dog"
        for k,x in (("kern_upper",text.upper()),("kern_lower",text)):
            l,t,r,b = draw.textbbox((0,0),x,font=font)
            w,h = r-l,b-t
            size_dict[k] = w/len(x) # Get the average width with kerning
        return size_dict

    def get_text_size(self,text,size_dict):
        w = h = 0
        for x in text:
            width,height = size_dict.get(x,(0,0))
            w += width
            if height > h: h = height
        return w,h
    
    @commands.command()
    async def clippy(self, ctx, *,text: str = ""):
        """I *know* you wanted some help with something - what was it?"""

        text = Nullify.resolve_mentions(text,ctx=ctx,escape=False,channel_mentions=True)
        # Remove any non-ascii chars
        text = ''.join([i for i in text if ord(i) < 128])

        clippy_errors = [
            "I guess I couldn't print that... whatever it was.",
            "It looks like you're trying to break things!  Maybe I can help.",
            "Whoops, I guess I wasn't coded to understand that.",
            "After filtering your input, I've come up with... well... nothing.",
            "Nope.",
            "y u du dis to clippy :("
        ]

        if not len(text):
            text = random.choice(clippy_errors)

        # Let's try to find a sane size
        s = self.max_font
        char_limit = None
        while True:
            font_dict = self.font_dicts[s]
            # Let's get our textwrap list based on the avg char width
            # Multiply by an adjustment ratio for better formatting
            if char_limit is None:
                char_limit = int(343/font_dict["avg_w"])
                lines = textwrap.wrap(text,char_limit)
                if all((" " in l for l in lines)):
                    # All lines contain spaces - apply some formatting adjustments
                    # based on the text size
                    char_limit *= 1.15 if s < 10 else 1.1 if s < 18 else 1
                    lines = textwrap.wrap(text,char_limit)
            else:
                lines = textwrap.wrap(text,char_limit)
            max_h = font_dict.get("max_h",0) # Max char height
            line_r = max_h/20 # Ratio for space between each line
            line_h = max_h + line_r # Fixed line height
            lines_h = len(lines)*line_h # Total height of all lines
            # Max y is 175, y start is 20 - max line height is 155
            if s > self.min_font and lines_h > 155:
                s -= 1
                char_limit = None
                continue
            image = Image.open('images/clippy.png')
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype('fonts/comic.ttf',size=s)
            color = 'rgb(0, 0, 0)' # black color
            # y = 9
            y = 16 + (155-lines_h)/2
            rewrap = False
            for line in lines:
                # Get the actual text size per line
                l,t,r,b = draw.textbbox((0,0),line,font=font)
                w,h = r-l,b-t # Resolve to width and height
                if w > 343:
                    # Rework the character limit based on the width
                    char_limit = int(char_limit*343/w)
                    rewrap = True
                    break
                x = (image.size[0]-w)/2
                draw.text((int(x),int(y)),line,fill=color,font=font)
                y += line_h # Increment by a fixed amount
            if rewrap:
                continue
            image.save('images/clippynow.png')
            await ctx.send(file=discord.File(fp='images/clippynow.png'))
            # Remove the png
            os.remove("images/clippynow.png")
            break
