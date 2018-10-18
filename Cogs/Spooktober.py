import asyncio
import discord
import random
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
            await ctx.message.add_reaction("🎃")

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
                    'go watch a scary movie to be absolutely sp00ped!',
                    'boo! Did you scare you?',
                    'you look yourself in the mirror and get a little scared...',
                    'get spooked by... yourself?',
                    'sp00py, but why spook yourself?'
                ]
            else:
                # we're spoopin' a member
                memName = DisplayName.name(memberCheck)
                spookMe = [
                    'you sp00p *{}* so hard that they start screaming!'.format(memName),
                    'you tried to sneak up on *{}*, but they heard you sneakin\' and fail...'.format(memName),
                    'it is sp00py time! Hey *{}*, boo!'.format(memName),
                    'congrats, *{}* dun sp00ked.'.format(memName),
                    'get spook3d *{}*!'.format(memName)
                ]

            randnum = random.randint(0, len(spookMe)-1)
            msg = '*{}*, {}'.format(authorName, spookMe[randnum])
            msg = Nullify.clean(msg)
            await ctx.channel.send(msg)
            return

        # so we're not sp00pin' anyone, let's spook an object then
        spookThing = [
            'you spook *{}* with no reaction, leaving you looking weird...'.format(memName),
            '*{}* got sp00p3d so hard, it ran away!'.format(memName),
            'you trick or treat *{}* without any reaction...'.format(memName),
            'you do your best to sp00p *{}*, but fail...'.format(memName),
            'sp00py time! *{}* gets sp00ped harder than you thought and starts crying!'.format(memName)
        ]

        randnum = random.randint(0, len(spookThing)-1)
        msg = '*{}*, {}'.format(authorName, spookThing[randnum])
        msg = Nullify.clean(msg)			
        await ctx.send(msg)
        return

    async def message(self, message):
        if datetime.today().month == 10 and datetime.today().day == 31:
            if not self.settings.getServerStat(message.guild, "Spooking"):
                # We have this turned off - bail
                return
            # it is the day of ultimate sp00p, sp00p all the messages
            if "spook" in message.content.lower():
                await message.add_reaction("🎃")
    
    @commands.command(pass_context=True)
    async def spooking(self, ctx, *, yes_no = None):
        """Enables/Disables reacting 🎃 to every message on Halloween"""
        # Only allow owner
        isOwner = self.settings.isOwner(ctx.author)
        if isOwner == None:
            msg = 'I have not been claimed, *yet*.'
            await ctx.channel.send(msg)
            return
        elif isOwner == False:
            msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
            await ctx.channel.send(msg)
            return

        setting_name = "Spooking"
        setting_val  = "Spooking"

        current = self.settings.getServerStat(ctx.guild, setting_val)
        if yes_no == None:
            if current:
                msg = "{} currently *enabled.*".format(setting_name)
            else:
                msg = "{} currently *disabled.*".format(setting_name)
        elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
            yes_no = True
            if current == True:
                msg = '{} remains *enabled*.'.format(setting_name)
            else:
                msg = '{} is now *enabled*.'.format(setting_name)
        elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
            yes_no = False
            if current == False:
                msg = '{} remains *disabled*.'.format(setting_name)
            else:
                msg = '{} is now *disabled*.'.format(setting_name)
        else:
            msg = "That's not a valid setting."
            yes_no = current
        if not yes_no == None and not yes_no == current:
            self.settings.setServerStat(ctx.guild, setting_val, yes_no)
        await ctx.send(msg)
