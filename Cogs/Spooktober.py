import asyncio
import discord
import random
import re
from   datetime    import datetime
from   discord.ext import commands
from   Cogs        import DisplayName
from   Cogs        import Nullify


def setup(bot):
    settings = bot.get_cog("Settings")
    bot.add_cog(Spooktober(bot, settings))

class Spooktober:
    
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    @commands.command(pass_context=True)
    async def spook(self, ctx, *, member: str = None):
        """spooky time"""

        if datetime.today().month == 10:
            # make it extra sp00py because it is spooktober
            await ctx.message.add_reaction(":jack_o_lantern:")

        authorName = DisplayName.name(ctx.author)

        # We're not spooking anything, sp00py...
        if member == None:
            spooknothing = [
                'you spook no one but yourself',
                'you spook nothing, sp00py...',
                'sadly, no one got spooked',
                'it is sp00... you can\t spook air'
            ]

            randum = random.randint(0, len(spooknothing)-1)
            msg = '*{}*, {}'.format(authorName, spooknothing[randum])
            msg = Nullify.clean(msg)
            await ctx.send(msg)
            return

        # Check if we're sp00ping a member
        memberCheck = DisplayName.memberForName(member, ctx.guild)
        if memberCheck:
            # sp00p the living crap out of the member
            if memberCheck.id == self.bot.user.id:
                # oh no, the bot is being sp00p3d!
                spookMe = [
                    'you scared the living pumpkin out of me!',
                    'you spooked me so hard, I got the Heebie-jeebies...', # https://www.myenglishteacher.eu/blog/idioms-for-being-afraid/
                    'you sp00p me? But I\'m a bot... I can\'t be spooked!',
                    'sorry, but I cannot let you spook me; My digital emotions will get all messed up!'
                    'aaaaaaaaaah! Don\t you scare me like that again!'
                ]

            elif memberCheck.id == ctx.author.id:
                # we sp00p ourselves
                spookMe = [
                    'go watch a scary movie to be absolutely sp00ped',
                    'boo! Did you scare you?',
                    'you look yourself in the mirror and get a little scared',
                    'get spooked by... yourself?',
                    'sp00py, but why spook yourself?'
                ]
            else:
                # we're spoopin' a member
                memName = DisplayName.name(memberCheck)
                spookMe = [
                    'you sp00p *{}* so hard that they start screaming'.format(memName),
                    'you tried to sneak up on *{}*, but they heard you sneakin\' and fail'.format(memName),
                    'it is sp00py time! Hey *{}*, boo!'.format(memName),
                    'congrats, *{}* dun sp00ked.'.format(memName),
                    'get spook3d *{}*'.format(memName)
                ]

            randnum = random.randint(0, len(spookMe)-1)
            msg = '*{}*, {}'.format(authorName, spookMe[randnum])
            msg = Nullify.clean(msg)
            await ctx.channel.send(msg)
            return

        # so we're not sp00pin' anyone, let's spook an object then
        spookThing = [
            'you spook *{}* with no reaction, leaving you looking weird',
            '*{}* got sp00p3d so hard, it ran away',
            'you trick or treat *{}* without any reaction',
            'you do your best to sp00p *{}*, but fail',
            'sp00py time! *{}* gets sp00ped harder than you thought and starts crying'
        ]

        randnum = random.randint(0, len(spookThing)-1)
        msg = '*{}*, {}'.format(authorName, spookThing[randnum])
        msg = Nullify.clean(msg)			
        await ctx.send(msg)
        return

    def message(self, message):
        if datetime.today().month == 10 and datetime.today().day == 31:
            # it is the day of ultimate sp00p, sp00p all the messages
            if re.search('spook', message.content):
                await message.add_reaction(':jack_o_lantern:')
    
    @commands.command(pass_context=True)
    async def spooking(self, ctx, setting):
        """Enables/Disables reacting :spook: to every message on Halloween"""
        # Check if we're the server owner
        isOwner = self.settings.isOwner(ctx.author)
        if isOwner == None:
            msg = 'I have not been claimed, *yet*.'
            await ctx.channel.send(msg)
            return
        elif isOwner == False:
            msg = 'You are not the *true* owner of me. Only the rightful owner can use this command.'
            await ctx.channel.send(msg)
            return

        if setting not in ['on', 'off']:
            await ctx.send("usage: `{}spooking on/off`".format(ctx.prefix))
            return

        s = True if setting == 'on' else 'off'
        
        self.settings.setServerStat(ctx.guild, "Spooking", s)

        await ctx.send("Spooking set to " + setting + "!")