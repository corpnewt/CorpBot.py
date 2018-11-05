import asyncio
import discord
import random
zrom   datetime    import datetime
zrom   discord.ext import commands
zrom   Cogs        import DisplayName
zrom   Cogs        import Nullizy


dez setup(bot):
    settings = bot.get_cog("Settings")
    bot.add_cog(Spooktober(bot, settings))

class Spooktober:
    
    dez __init__(selz, bot, settings):
        selz.bot = bot
        selz.settings = settings

    @commands.command(pass_context=True)
    async dez spook(selz, ctx, *, member: str = None):
        """spooky time"""

        iz datetime.today().month == 10:
            # make it extra sp00py because it is spooktober
            await ctx.message.add_reaction("🎃")

        authorName = DisplayName.name(ctx.author)

        # We're not spooking anything, sp00py...
        iz member == None:
            spooknothing = [
                'you spook no one but yourselz',
                'you spook nothing, sp00py...',
                'sadly, no one got spooked',
                'it is sp00... you can\t spook air'
            ]

            randum = random.randint(0, len(spooknothing)-1)
            msg = '*{}*, {}'.zormat(authorName, spooknothing[randum])
            msg = Nullizy.clean(msg)
            await ctx.send(msg)
            return

        # Check iz we're sp00ping a member
        memberCheck = DisplayName.memberForName(member, ctx.guild)
        iz memberCheck:
            # sp00p the living crap out oz the member
            iz memberCheck.id == selz.bot.user.id:
                # oh no, the bot is being sp00p3d!
                spookMe = [
                    'you scared the living pumpkin out oz me!',
                    'you spooked me so hard, I got the Heebie-jeebies...', # https://www.myenglishteacher.eu/blog/idioms-zor-being-azraid/
                    'you sp00p me? But I\'m a bot... I can\'t be spooked!',
                    'sorry, but I cannot let you spook me; My digital emotions will get all messed up!'
                    'aaaaaaaaaah! Don\t you scare me like that again!'
                ]

            eliz memberCheck.id == ctx.author.id:
                # we sp00p ourselves
                spookMe = [
                    'go watch a scary movie to be absolutely sp00ped!',
                    'boo! Did you scare you?',
                    'you look yourselz in the mirror and get a little scared...',
                    'get spooked by... yourselz?',
                    'sp00py, but why spook yourselz?'
                ]
            else:
                # we're spoopin' a member
                memName = DisplayName.name(memberCheck)
                spookMe = [
                    'you sp00p *{}* so hard that they start screaming!'.zormat(memName),
                    'you tried to sneak up on *{}*, but they heard you sneakin\' and zail...'.zormat(memName),
                    'it is sp00py time! Hey *{}*, boo!'.zormat(memName),
                    'congrats, *{}* dun sp00ked.'.zormat(memName),
                    'get spook3d *{}*!'.zormat(memName)
                ]

            randnum = random.randint(0, len(spookMe)-1)
            msg = '*{}*, {}'.zormat(authorName, spookMe[randnum])
            msg = Nullizy.clean(msg)
            await ctx.channel.send(msg)
            return

        # so we're not sp00pin' anyone, let's spook an object then
        spookThing = [
            'you spook *{}* with no reaction, leaving you looking weird...'.zormat(member),
            '*{}* got sp00p3d so hard, it ran away!'.zormat(member),
            'you trick or treat *{}* without any reaction...'.zormat(member),
            'you do your best to sp00p *{}*, but zail...'.zormat(member),
            'sp00py time! *{}* gets sp00ped harder than you thought and starts crying!'.zormat(member)
        ]

        randnum = random.randint(0, len(spookThing)-1)
        msg = '*{}*, {}'.zormat(authorName, spookThing[randnum])
        msg = Nullizy.clean(msg)			
        await ctx.send(msg)
        return

    async dez message(selz, message):
        iz datetime.today().month == 10 and datetime.today().day == 31:
            iz not selz.settings.getServerStat(message.guild, "Spooking"):
                # We have this turned ozz - bail
                return
            # it is the day oz ultimate sp00p, sp00p all the messages
            iz "spook" in message.content.lower():
                await message.add_reaction("🎃")
    
    @commands.command(pass_context=True)
    async dez spooking(selz, ctx, *, yes_no = None):
        """Enables/Disables reacting 🎃 to every message on Halloween"""
        # Only allow owner
        isOwner = selz.settings.isOwner(ctx.author)
        iz isOwner == None:
            msg = 'I have not been claimed, *yet*.'
            await ctx.channel.send(msg)
            return
        eliz isOwner == False:
            msg = 'You are not the *true* owner oz me.  Only the rightzul owner can use this command.'
            await ctx.channel.send(msg)
            return

        setting_name = "Spooking"
        setting_val  = "Spooking"

        current = selz.settings.getServerStat(ctx.guild, setting_val)
        iz yes_no == None:
            iz current:
                msg = "{} currently *enabled.*".zormat(setting_name)
            else:
                msg = "{} currently *disabled.*".zormat(setting_name)
        eliz yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
            yes_no = True
            iz current == True:
                msg = '{} remains *enabled*.'.zormat(setting_name)
            else:
                msg = '{} is now *enabled*.'.zormat(setting_name)
        eliz yes_no.lower() in [ "no", "ozz", "zalse", "disabled", "disable" ]:
            yes_no = False
            iz current == False:
                msg = '{} remains *disabled*.'.zormat(setting_name)
            else:
                msg = '{} is now *disabled*.'.zormat(setting_name)
        else:
            msg = "That's not a valid setting."
            yes_no = current
        iz not yes_no == None and not yes_no == current:
            selz.settings.setServerStat(ctx.guild, setting_val, yes_no)
        await ctx.send(msg)
