import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

def setup(bot):
    bot.add_cog(Clippy(bot))

class Clippy:

    def __init__(self, bot):
        self.bot = bot

    def text_wrap(self, text, font, max_width):
        lines = []
        # If the width of the text is smaller than image width
        # we don't need to split it, just add it to the lines array
        # and return
        if font.getsize(text)[0] <= max_width:
            lines.append(text)
        else:
            # split the line by spaces to get words
            words = text.split(' ')
            i = 0
            # append every word to a line while its width is shorter than image width
            while i < len(words):
                line = ''
                while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                    line = line + words[i] + " "
                    i += 1
                if not line:
                    line = words[i]
                    i += 1
                # when the line gets longer than the max width do not append the word,
                # add the line to the lines array
                lines.append(line)
        return lines
    
    @commands.command()
    async def clippy(self, ctx, *,text: str):
        """I *know* you wanted some help with something - what was it?"""
        image = Image.open('images/clippy.png')
        image_size = image.size
        image_height = image.size[1]
        image_width = image.size[0]
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype('fonts/comic.ttf', size=20)
        #340 is the width we want to set the image width to
        lines = self.text_wrap(text, font, 340)
        line_height = font.getsize('hg')[1]
        (x, y) = (25, 20)
        color = 'rgb(0, 0, 0)' # black color
        text_size = draw.textsize(text, font=font)
        image_x = (image_width / 2) - (text_size[0] / 2)

        for line in lines:
            draw.text((x, y), line, fill=color, font=font)
            y = y + line_height

        image.save('images/clippynow.png')
        await ctx.send(file=discord.File(fp='images/clippynow.png'))
