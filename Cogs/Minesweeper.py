from discord.ext import commands
import random

def setup(bot):
    bot.add_cog(Minesweeper(bot))

class Minesweeper(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["ms","minesweep","msweep","msweeper"])
    async def minesweeper(self, ctx, grid_size = 5):
        """Generate and post a new minesweeper game - grid size can range from 3x3 to 9x9"""

        try: grid_size = int(grid_size)
        except: grid_size = 10
        grid_size = max(min(grid_size,10),3)

        # Percent chance each entry could be a mine
        mine_perc = 20

        # Use 0 -> 8 for the neighbors, and X for bombs
        while True:
            rows = []
            # Populate the bombs
            for x in range(grid_size):
                row = []
                for y in range(grid_size):
                    row.append("X" if random.randint(1,100) <= mine_perc else "0")
                rows.append(row)
            if any(("X" in r for r in rows)): break # We got at least 1
        # Walk the rows and count neighboring bombs
        for x in range(len(rows)):
            for y in range(len(rows[x])):
                if rows[x][y] == "X": continue # Already a bomb, no need to count
                noisy_neighbors = 0
                valid_x = [x]
                valid_y = [y]
                if x-1 >= 0: valid_x.append(x-1)
                if x+1 < len(rows): valid_x.append(x+1)
                if y-1 >= 0: valid_y.append(y-1)
                if y+1 < len(rows[x]): valid_y.append(y+1)
                # Walk the values around our target and count the bombs
                for a in valid_x:
                    for b in valid_y:
                        if rows[a][b] == "X": noisy_neighbors += 1
                # Change the value to reflect the neighbors
                rows[x][y] = str(noisy_neighbors)
        # Walk our list once more replacing the values as needed
        pretty_dict = {
            "0":"||0️⃣||",
            "1":"||1️⃣||",
            "2":"||2️⃣||",
            "3":"||3️⃣||",
            "4":"||4️⃣||",
            "5":"||5️⃣||",
            "6":"||6️⃣||",
            "7":"||7️⃣||",
            "8":"||8️⃣||",
            "X":"||💥||"
        }
        messages = []
        pretty_rows = []
        max_emojis = 99 # Weird limit from discord
        for x in rows:
            if (len(pretty_rows)+1)*len(x) > max_emojis: # Over the limit
                messages.append(pretty_rows)
                pretty_rows = [] # Reset
            row = ""
            for y in x:
                row += pretty_dict.get(y,"")
            pretty_rows.append(row)
        # Catch any leftovers
        if pretty_rows: messages.append(pretty_rows)

        for i,m in enumerate(messages):
            msg = "{}{}".format(
                "" if i!=0 else "__**Minesweeper {}x{}**:__\n".format(
                    grid_size,grid_size,
                ),
                "\n".join(m)
            )
            await ctx.send(msg)