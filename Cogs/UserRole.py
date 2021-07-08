import asyncio
import discord
from discord.ext import commands
from Cogs import Settings, DisplayName, Nullify, Utils, PickList


def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(UserRole(bot, settings))


class UserRole(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.loop_list = []
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    def _is_submodule(self, parent, child):
        return parent == child or child.startswith(parent + ".")

    @commands.Cog.listener()
    async def on_unloaded_extension(self, ext):
        # Called to shut things down
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        for task in self.loop_list:
            task.cancel()

    @commands.Cog.listener()
    async def on_loaded_extension(self, ext):
        # See if we were loaded
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        # Add a loop to remove expired user blocks in the UserRoleBlock list
        self.loop_list.append(
            self.bot.loop.create_task(self.block_check_list()))

    async def block_check_list(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # Iterate through the ids in the UserRoleBlock list and
            # remove any for members who aren't here
            for guild in self.bot.guilds:
                block_list = self.settings.getServerStat(
                    guild, "UserRoleBlock")
                rem_list = [x for x in block_list if not guild.get_member(x)]
                if len(rem_list):
                    block_list = [x for x in block_list if x not in rem_list]
                    self.settings.setServerStat(
                        guild, "UserRoleBlock", block_list)
            # Check once per hour
            await asyncio.sleep(3600)

    def _get_emoji_mention(self, emoji):
        if not emoji["emoji_id"]:
            return emoji["emoji_name"]  # Unicode
        return "<{}:{}:{}>".format("a" if emoji["emoji_a"] else "", emoji["emoji_name"], emoji["emoji_id"])

    def _get_channel_message(self, ctx):
        if not ctx.guild:
            return None
        channel = message = None
        chan_message = self.settings.getServerStat(
            ctx.guild, "ReactionMessageId", None)
        if chan_message:
            channel, message = [int(x) for x in chan_message.split()]
        if not (message and channel):
            return None
        return (channel, message)

    async def _get_message_url(self, ctx):
        m = await self._get_message(ctx)
        if not m:
            return None
        # Let's build the url
        return "https://discord.com/channels/{}/{}/{}".format(m.guild.id, m.channel.id, m.id)

    async def _get_message(self, ctx):
        if not ctx.guild:
            return None
        chan_message = self._get_channel_message(ctx)
        if not chan_message:
            return None
        # Let's actually get the channel+message and ensure it exists
        c = ctx.guild.get_channel(chan_message[0])
        try:
            return await c.fetch_message(chan_message[1])
        except Exception as e:
            print(e)  # pass
        return None

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return
        await self._check_react(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not payload.guild_id:
            return
        await self._check_react(payload)

    async def _check_react(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return
        block_list = self.settings.getServerStat(
            member.guild, "UserRoleBlock", [])
        if member.id in block_list:
            return  # User is blocked
        m = await self._get_message(member)
        if not m:
            return
        # Gather the reaction role info - and apply roles if necessary
        chan_message = self._get_channel_message(m)
        # Check if it's the right channel and message id
        if not chan_message or not (payload.channel_id == chan_message[0] and payload.message_id == chan_message[1]):
            return
        # Got the right setup - let's see if it's a valid reaction
        ur_list = self.settings.getServerStat(m.guild, "UserRoles", [])
        ur_id_list = [x["ID"] for x in ur_list]
        rr_list = self.settings.getServerStat(
            m.guild, "ReactionMessageList", [])
        entry = next((x for x in rr_list if x["emoji_name"] ==
                     payload.emoji.name and x["emoji_id"] == payload.emoji.id), None)
        if not entry:  # Doesn't match, try to remove
            try:
                await m.clear_reaction(payload.emoji)
            except:
                pass  # Might not have perms
            return
        role = guild.get_role(entry["role_id"])
        if not role or not role.id in ur_id_list:
            return  # Doesn't exist
        toggle = self.settings.getServerStat(
            m.guild, "ReactionMessageToggle", True)
        only_one = self.settings.getServerStat(
            m.guild, "OnlyOneUserRole", True)
        rem_roles = []
        add_roles = []
        # Find out if we need to add/remove roles
        if role in member.roles:
            if toggle:
                rem_roles.append(role)
        else:
            add_roles.append(role)
        if only_one:
            for r_dict in ur_list:
                if r_dict["ID"] == role.id:
                    continue  # Don't remove the one we just found
                r_test = m.guild.get_role(r_dict["ID"])
                if not r_test:
                    continue
                # Add it to the remove list
                rem_roles.append(r_test)
        if len(rem_roles) or len(add_roles):
            self.settings.role.change_roles(
                member, add_roles=add_roles, rem_roles=rem_roles)

    @commands.command()
    async def rrmessage(self, ctx, *, message_url=None):
        """Gets or sets the message to watch for user reaction roles (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx):
            return
        # We want to know what message the bot is watching, if any
        if not message_url:
            return await ctx.invoke(self.rrlist)
        # We are setting a message - let's split the url and get the last 2 integers - then save them.
        parts = [x for x in message_url.replace("/", " ").split() if len(x)]
        try:
            channel, message = [int(x) for x in parts[-2:]]
        except:
            return await ctx.send("Improperly formatted message url!")
        # Let's actually get the channel+message and ensure it exists
        c = ctx.guild.get_channel(channel)
        if not c:
            return await ctx.send("I couldn't find the channel connected to that id.")
        try:
            await c.fetch_message(message)
        except:
            return await ctx.send("I couldn't find the message connected to that id.")
        # Here we have what we need - save it and print the final url
        self.settings.setServerStat(
            ctx.guild, "ReactionMessageId", "{} {}".format(channel, message))
        return await ctx.send("I will watch the following message for reactions:\nhttps://discord.com/channels/{}/{}/{}".format(
            ctx.guild.id, channel, message
        ))

    @commands.command()
    async def rrclear(self, ctx):
        """Removes the message to watch for user reaction roles, as well as all roles and reactions (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx):
            return
        self.settings.setServerStat(ctx.guild, "ReactionMessageId", None)
        self.settings.setServerStat(ctx.guild, "ReactionMessageList", [])
        return await ctx.send("Reaction message info cleared!")

    @commands.command()
    async def rrtoggle(self, ctx, yes_no=None):
        """Sets whether or not reaction messages will toggle roles - or only add them (bot-admin only)."""
        if not await Utils.is_admin_reply(ctx):
            return
        await ctx.send(Utils.yes_no_setting(ctx, "Reaction role add/remove toggle", "ReactionMessageToggle", yes_no, True))

    @commands.command()
    async def rradd(self, ctx, *, role_name_or_id=None):
        """Adds a new role to the reaction roles list.
        The added role must be in the user role list, and rrmessage must be setup (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx):
            return
        m = await self._get_message(ctx)
        if not m:
            return await ctx.send("Reaction role message is not currently set.  Please set that up first with `{}rrmessage [message_url]`.".format(ctx.prefix))
        # We should meet prerequisites - let's resolve the role.
        if not role_name_or_id:
            return await ctx.send("No role passed.")
        role = DisplayName.roleForName(role_name_or_id, ctx.guild)
        if not role:
            return await ctx.send("I couldn't find that role.")
        # We have the role - make sure it's in the user roles list
        ur_list = self.settings.getServerStat(ctx.guild, "UserRoles", [])
        # Make sure it's in the user role list
        if not next((x for x in ur_list if int(x["ID"]) == role.id), None):
            return await ctx.send("That role is not in the user role list.  Please add it first with `{}adduserrole [role]`.".format(ctx.prefix))
        message = await ctx.send("Please react to this message with the desired emoji.")
        # Now we would wait...
        def check(
            reaction, user): return reaction.message.id == message.id and user == ctx.author
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
        except:
            # Didn't get a reaction
            return await message.edit(content="Looks like we ran out of time - run `{}rradd [role_name_or_id]` to try again.".format(ctx.prefix))
        # Let's walk through the reaction list and verify what we have
        rr_list = self.settings.getServerStat(
            ctx.guild, "ReactionMessageList", [])
        emoji_a, emoji_id, emoji_name = (False, None, str(reaction.emoji)) if isinstance(
            reaction.emoji, str) else (reaction.emoji.animated, reaction.emoji.id, reaction.emoji.name)
        # Check if we are already using that reaction for a different role
        using_that_emoji = [x for x in rr_list if x["emoji_a"] == emoji_a and x["emoji_id"]
                            == emoji_id and x["emoji_name"] == emoji_name and x["role_id"] != role.id]
        using_that_role = [x for x in rr_list if x["role_id"] == role.id]
        if using_that_emoji:
            # Evaluate the role id - and ensure it exists
            using_role = DisplayName.roleForName(
                using_that_emoji[0]["role_id"], ctx.guild)
            if using_role:
                return await message.edit(content="That reaction is already being used for \"{}\".".format(Nullify.escape_all(using_role.name)))
            # If we got here - it doesn't exist - pop it from that list
            rr_list.remove(using_that_emoji[0])
        if using_that_role:
            # Pop the role from the list so we can re-add it with the new emoji
            rr_list.remove(using_that_role[0])
        # Add the emoji name/id and role id to the list
        rr_list.append({"emoji_a": emoji_a, "emoji_id": emoji_id,
                       "emoji_name": emoji_name, "role_id": role.id})
        self.settings.setServerStat(ctx.guild, "ReactionMessageList", rr_list)
        await message.edit(content="Reaction for \"{}\" set to {}".format(
            Nullify.escape_all(role.name),
            str(reaction.emoji)
        ))

    @commands.command()
    async def rrdel(self, ctx, *, role_name_or_id=None):
        """Removes the passed role from the reaction roles list (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx):
            return
        m = await self._get_message(ctx)
        if not m:
            return await ctx.send("Reaction role message is not currently set.  Please set that up first with `{}rrmessage [message_url]`.".format(ctx.prefix))
        # We should meet prerequisites - let's resolve the role.
        if not role_name_or_id:
            return await ctx.send("No role passed.")
        role = DisplayName.roleForName(role_name_or_id, ctx.guild)
        if not role:
            return await ctx.send("I couldn't find that role.")
        rr_list = self.settings.getServerStat(
            ctx.guild, "ReactionMessageList", [])
        to_remove = next((x for x in rr_list if x["role_id"] == role.id), None)
        if not to_remove:
            return await ctx.send("That role is not in the reaction roles list.")
        rr_list.remove(to_remove)
        self.settings.setServerStat(ctx.guild, "ReactionMessageList", rr_list)
        return await ctx.send("\"{}\" has been removed from the reaction roles list.".format(Nullify.escape_all(role.name)))

    @commands.command()
    async def rrlist(self, ctx):
        """Lists the current reaction roles and their corresponding reactions (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx):
            return
        url = await self._get_message_url(ctx)
        if not url:
            return await ctx.send("Reaction role message is not currently set.")
        toggle = self.settings.getServerStat(
            ctx.guild, "ReactionMessageToggle", True)
        only_one = self.settings.getServerStat(
            ctx.guild, "OnlyOneUserRole", True)
        desc = "Currently watching [this message]({}) for reactions.\nReacting will **{}** the target role.\nUsers can select {}".format(
            url,
            "add or remove" if toggle else "only add",
            "**only one** role at a time." if only_one else "**multiple** roles at a time."
        )
        # Gather the roles/reactions
        rr_list = self.settings.getServerStat(
            ctx.guild, "ReactionMessageList", [])
        if not rr_list:
            return await ctx.send("There are no reaction roles setup currently.")
        role_list = []
        for x in rr_list:
            role = ctx.guild.get_role(x["role_id"])
            if not role:
                continue  # Doesn't exist, ignore it
            name = "{} ({})".format(role.name, role.id)
            # Check if it's a custom emoji - and give the name, id, and a ping
            if x["emoji_id"]:
                emoji = self.bot.get_emoji(x["emoji_id"])
                if emoji:
                    value = "{} - `{}`".format(self._get_emoji_mention(x),
                                               self._get_emoji_mention(x))
                else:
                    value = "`{}` - Not from a shared server".format(
                        self._get_emoji_mention(x))
            else:
                value = x["emoji_name"]
            role_list.append({"name": name, "value": value})
        return await PickList.PagePicker(title="Current Reaction Roles", list=role_list, description=desc, ctx=ctx).pick()

    @commands.command(pass_context=True)
    async def urblock(self, ctx, *, member=None):
        """Blocks a user from using the UserRole system and removes applicable roles (bot-admin only)."""
        isAdmin = ctx.author.permissions_in(ctx.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
            for role in ctx.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True
                        break
        # Only allow bot-admins to change server stats
        if not isAdmin:
            await ctx.send('You do not have sufficient privileges to access this command.')
            return
        # Get the target user
        mem = DisplayName.memberForName(member, ctx.guild)
        if not mem:
            await ctx.send("I couldn't find {}.".format(Nullify.escape_all(member)))
            return
        # Check if we're trying to block a bot-admin
        isAdmin = mem.permissions_in(ctx.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
            for role in mem.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True
                        break
        # Only allow bot-admins to change server stats
        if isAdmin:
            await ctx.send("You can't block other admins or bot-admins from the UserRole module.")
            return
        # At this point - we have someone to block - see if they're already blocked
        block_list = self.settings.getServerStat(ctx.guild, "UserRoleBlock")
        m = ""
        if mem.id in block_list:
            m += "{} is already blocked from the UserRole module.".format(
                DisplayName.name(mem))
        else:
            block_list.append(mem.id)
            self.settings.setServerStat(ctx.guild, "UserRoleBlock", block_list)
            m += "{} now blocked from the UserRole module.".format(
                DisplayName.name(mem))
        # Remove any roles
        # Get the array
        try:
            promoArray = self.settings.getServerStat(ctx.guild, "UserRoles")
        except Exception:
            promoArray = []
        if promoArray == None:
            promoArray = []
        # Populate the roles that need to be removed
        remRole = []
        for arole in promoArray:
            roleTest = DisplayName.roleForID(arole['ID'], ctx.guild)
            if not roleTest:
                # Not a real role - skip
                continue
            if roleTest in mem.roles:
                # We have it
                remRole.append(roleTest)
        if len(remRole):
            # Only remove if we have roles to remove
            self.settings.role.rem_roles(mem, remRole)
        m += "\n\n*{} {}* removed.".format(len(remRole),
                                           "role" if len(remRole) == 1 else "roles")
        await ctx.send(m)

    @commands.command(pass_context=True)
    async def urunblock(self, ctx, *, member=None):
        """Unblocks a user from the UserRole system (bot-admin only)."""
        isAdmin = ctx.author.permissions_in(ctx.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
            for role in ctx.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True
                        break
        # Only allow bot-admins to change server stats
        if not isAdmin:
            await ctx.send('You do not have sufficient privileges to access this command.')
            return
        # Get the target user
        mem = DisplayName.memberForName(member, ctx.guild)
        if not mem:
            await ctx.send("I couldn't find {}.".format(Nullify.escape_all(member)))
            return
        # At this point - we have someone to unblock - see if they're blocked
        block_list = self.settings.getServerStat(ctx.guild, "UserRoleBlock")
        if not mem.id in block_list:
            await ctx.send("{} is not blocked from the UserRole module.".format(DisplayName.name(mem)))
            return
        block_list.remove(mem.id)
        self.settings.setServerStat(ctx.guild, "UserRoleBlock", block_list)
        await ctx.send("{} has been unblocked from the UserRole module.".format(DisplayName.name(mem)))

    @commands.command(pass_context=True)
    async def isurblocked(self, ctx, *, member=None):
        """Outputs whether or not the passed user is blocked from the UserRole module."""
        if member == None:
            member = "{}".format(ctx.author.mention)
        # Get the target user
        mem = DisplayName.memberForName(member, ctx.guild)
        if not mem:
            await ctx.send("I couldn't find {}.".format(Nullify.escape_all(member)))
            return
        block_list = self.settings.getServerStat(ctx.guild, "UserRoleBlock")
        name = "You are" if mem.id == ctx.author.id else DisplayName.name(
            mem) + " is"
        if mem.id in block_list:
            await ctx.send(name + " blocked from the UserRole module.")
        else:
            await ctx.send(name + " not blocked from the UserRole module.")

    @commands.command(pass_context=True)
    async def adduserrole(self, ctx, *, role=None):
        """Adds a new role to the user role system (admin only)."""

        author = ctx.message.author
        server = ctx.message.guild
        channel = ctx.message.channel

        usage = 'Usage: `{}adduserrole [role]`'.format(ctx.prefix)

        isAdmin = author.permissions_in(channel).administrator
        # Only allow admins to change server stats
        if not isAdmin:
            await channel.send('You do not have sufficient privileges to access this command.')
            return

        if role == None:
            await ctx.send(usage)
            return

        if type(role) is str:
            if role == "everyone":
                role = "@everyone"
            # It' a string - the hope continues
            roleCheck = DisplayName.roleForName(role, server)
            if not roleCheck:
                msg = "I couldn't find **{}**...".format(
                    Nullify.escape_all(role))
                await ctx.send(msg)
                return
            role = roleCheck

        # Now we see if we already have that role in our list
        try:
            promoArray = self.settings.getServerStat(server, "UserRoles")
        except Exception:
            promoArray = []
        if promoArray == None:
            promoArray = []

        for aRole in promoArray:
            # Get the role that corresponds to the id
            if str(aRole['ID']) == str(role.id):
                # We found it - throw an error message and return
                msg = '**{}** is already in the list.'.format(
                    Nullify.escape_all(role.name))
                await channel.send(msg)
                return

        # If we made it this far - then we can add it
        promoArray.append({'ID': role.id, 'Name': role.name})
        self.settings.setServerStat(server, "UserRoles", promoArray)

        msg = '**{}** added to list.'.format(Nullify.escape_all(role.name))
        await channel.send(msg)
        return

    @adduserrole.error
    async def adduserrole_error(self, ctx, error):
        # do stuff
        msg = 'adduserrole Error: {}'.format(ctx)
        await error.channel.send(msg)

    @commands.command(pass_context=True)
    async def removeuserrole(self, ctx, *, role=None):
        """Removes a role from the user role system (admin only)."""

        author = ctx.message.author
        server = ctx.message.guild
        channel = ctx.message.channel

        usage = 'Usage: `{}removeuserrole [role]`'.format(ctx.prefix)

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        isAdmin = author.permissions_in(channel).administrator
        # Only allow admins to change server stats
        if not isAdmin:
            await channel.send('You do not have sufficient privileges to access this command.')
            return

        if role == None:
            await channel.send(usage)
            return

        rr_list = self.settings.getServerStat(
            ctx.guild, "ReactionMessageList", [])

        if type(role) is str:
            if role == "everyone":
                role = "@everyone"
            # It' a string - the hope continues
            # Let's clear out by name first - then by role id
            try:
                promoArray = self.settings.getServerStat(server, "UserRoles")
            except Exception:
                promoArray = []
            if promoArray == None:
                promoArray = []

            for aRole in promoArray:
                # Get the role that corresponds to the name
                if aRole['Name'].lower() == role.lower():
                    # We found it - let's remove it
                    promoArray.remove(aRole)
                    # Also remove it from the rr_list
                    rr_list = [x for x in rr_list if x["role_id"]
                               != int(aRole["ID"])]
                    self.settings.setServerStat(
                        server, "ReactionMessageList", rr_list)
                    self.settings.setServerStat(
                        server, "UserRoles", promoArray)
                    msg = '**{}** removed successfully.'.format(
                        Nullify.escape_all(aRole['Name']))
                    await channel.send(msg)
                    return
            # At this point - no name
            # Let's see if it's a role that's had a name change

            roleCheck = DisplayName.roleForName(role, server)
            if roleCheck:
                # We got a role
                # If we're here - then the role is an actual role
                try:
                    promoArray = self.settings.getServerStat(
                        server, "UserRoles")
                except Exception:
                    promoArray = []
                if promoArray == None:
                    promoArray = []

                for aRole in promoArray:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(roleCheck.id):
                        # We found it - let's remove it
                        promoArray.remove(aRole)
                        # Also remove it from the rr_list
                        rr_list = [
                            x for x in rr_list if x["role_id"] != roleCheck.id]
                        self.settings.setServerStat(
                            server, "ReactionMessageList", rr_list)
                        self.settings.setServerStat(
                            server, "UserRoles", promoArray)
                        msg = '**{}** removed successfully.'.format(
                            Nullify.escape_all(aRole['Name']))
                        await channel.send(msg)
                        return

            # If we made it this far - then we didn't find it
            msg = '*{}* not found in list.'.format(
                Nullify.escape_all(roleCheck.name))
            await channel.send(msg)
            return

        # If we're here - then the role is an actual role - I think?
        try:
            promoArray = self.settings.getServerStat(server, "UserRoles")
        except Exception:
            promoArray = []
        if promoArray == None:
            promoArray = []

        for aRole in promoArray:
            # Get the role that corresponds to the id
            if str(arole['ID']) == str(role.id):
                # We found it - let's remove it
                promoArray.remove(aRole)
                # Also remove it from the rr_list
                rr_list = [x for x in rr_list if x["role_id"] != role.id]
                self.settings.setServerStat(
                    server, "ReactionMessageList", rr_list)
                self.settings.setServerStat(server, "UserRoles", promoArray)
                msg = '**{}** removed successfully.'.format(
                    Nullify.escape_all(aRole['Name']))
                await channel.send(msg)
                return

        # If we made it this far - then we didn't find it
        msg = '*{}* not found in list.'.format(Nullify.escape_all(role.name))
        await channel.send(msg)

    '''@removeuserrole.error
	async def removeuserrole_error(self, ctx, error):
		# do stuff
		msg = 'removeuserrole Error: {}'.format(ctx)
		await error.channel.send(msg)'''

    @commands.command(pass_context=True)
    async def listuserroles(self, ctx):
        """Lists all roles for the user role system."""

        server = ctx.message.guild
        channel = ctx.message.channel

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        # Get the array
        try:
            promoArray = self.settings.getServerStat(server, "UserRoles")
        except Exception:
            promoArray = []
        if promoArray == None:
            promoArray = []

        if not len(promoArray):
            msg = "There aren't any roles in the user role list yet.  Add some with the `{}adduserrole` command!".format(
                ctx.prefix)
            await ctx.channel.send(msg)
            return

        # Sort by XP first, then by name
        # promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
        promoSorted = sorted(promoArray, key=lambda x: x['Name'])

        roleText = "**__Current Roles:__**\n\n"
        for arole in promoSorted:
            # Get current role name based on id
            foundRole = False
            for role in server.roles:
                if str(role.id) == str(arole['ID']):
                    # We found it
                    foundRole = True
                    roleText = '{}**{}**\n'.format(roleText,
                                                   Nullify.escape_all(role.name))
            if not foundRole:
                roleText = '{}**{}** (removed from server)\n'.format(
                    roleText, Nullify.escape_all(arole['Name']))

        await channel.send(roleText)

    @commands.command(pass_context=True)
    async def oneuserrole(self, ctx, *, yes_no=None):
        """Turns on/off one user role at a time (bot-admin only; always on by default)."""
        if not await Utils.is_admin_reply(ctx):
            return
        await ctx.send(Utils.yes_no_setting(ctx, "One user role at a time", "OnlyOneUserRole", yes_no, True))

    @commands.command(pass_context=True)
    async def clearroles(self, ctx):
        """Removes all user roles from your roles."""
        block_list = self.settings.getServerStat(ctx.guild, "UserRoleBlock")
        if ctx.author.id in block_list:
            await ctx.send("You are currently blocked from using this command.")
            return
        # Get the array
        try:
            promoArray = self.settings.getServerStat(ctx.guild, "UserRoles")
        except Exception:
            promoArray = []
        if promoArray == None:
            promoArray = []

        remRole = []
        for arole in promoArray:
            roleTest = DisplayName.roleForID(arole['ID'], ctx.guild)
            if not roleTest:
                # Not a real role - skip
                continue
            if roleTest in ctx.author.roles:
                # We have it
                remRole.append(roleTest)

        if not len(remRole):
            await ctx.send("You have no roles from the user role list.")
            return
        self.settings.role.rem_roles(ctx.author, remRole)
        if len(remRole) == 1:
            await ctx.send("1 user role removed from your roles.")
        else:
            await ctx.send("{} user roles removed from your roles.".format(len(remRole)))

    @commands.command(pass_context=True)
    async def remrole(self, ctx, *, role=None):
        """Removes a role from the user role list from your roles."""
        block_list = self.settings.getServerStat(ctx.guild, "UserRoleBlock")
        if ctx.author.id in block_list:
            await ctx.send("You are currently blocked from using this command.")
            return

        if role == None:
            await ctx.send("Usage: `{}remrole [role name]`".format(ctx.prefix))
            return

        server = ctx.message.guild
        channel = ctx.message.channel

        if self.settings.getServerStat(server, "OnlyOneUserRole"):
            await ctx.invoke(self.setrole, role=None)
            return

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        # Get the array
        try:
            promoArray = self.settings.getServerStat(server, "UserRoles")
        except Exception:
            promoArray = []
        if promoArray == None:
            promoArray = []

        # Check if role is real
        roleCheck = DisplayName.roleForName(role, server)
        if not roleCheck:
            # No luck...
            msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(
                Nullify.escape_all(role), ctx.prefix)
            await channel.send(msg)
            return

        # Got a role - set it
        role = roleCheck

        remRole = []
        for arole in promoArray:
            roleTest = DisplayName.roleForID(arole['ID'], server)
            if not roleTest:
                # Not a real role - skip
                continue
            if str(arole['ID']) == str(role.id):
                # We found it!
                if roleTest in ctx.author.roles:
                    # We have it
                    remRole.append(roleTest)
                else:
                    # We don't have it...
                    await ctx.send("You don't currently have that role.")
                    return
                break

        if not len(remRole):
            # We didn't find that role
            msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(
                Nullify.escape_all(role.name), ctx.prefix)
            await channel.send(msg)
            return

        if len(remRole):
            self.settings.role.rem_roles(ctx.author, remRole)

        msg = '*{}* has been removed from **{}!**'.format(
            DisplayName.name(ctx.message.author), Nullify.escape_all(role.name))
        await channel.send(msg)

    @commands.command(pass_context=True)
    async def addrole(self, ctx, *, role=None):
        """Adds a role from the user role list to your roles.  You can have multiples at a time."""
        block_list = self.settings.getServerStat(ctx.guild, "UserRoleBlock")
        if ctx.author.id in block_list:
            await ctx.send("You are currently blocked from using this command.")
            return

        if role == None:
            await ctx.send("Usage: `{}addrole [role name]`".format(ctx.prefix))
            return

        server = ctx.message.guild
        channel = ctx.message.channel

        if self.settings.getServerStat(server, "OnlyOneUserRole"):
            await ctx.invoke(self.setrole, role=role)
            return

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        # Get the array
        try:
            promoArray = self.settings.getServerStat(server, "UserRoles")
        except Exception:
            promoArray = []
        if promoArray == None:
            promoArray = []

        # Check if role is real
        roleCheck = DisplayName.roleForName(role, server)
        if not roleCheck:
            # No luck...
            msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(
                Nullify.escape_all(role), ctx.prefix)
            await channel.send(msg)
            return

        # Got a role - set it
        role = roleCheck

        addRole = []
        for arole in promoArray:
            roleTest = DisplayName.roleForID(arole['ID'], server)
            if not roleTest:
                # Not a real role - skip
                continue
            if str(arole['ID']) == str(role.id):
                # We found it!
                if roleTest in ctx.author.roles:
                    # We already have it
                    await ctx.send("You already have that role.")
                    return
                addRole.append(roleTest)
                break

        if not len(addRole):
            # We didn't find that role
            msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(
                Nullify.escape_all(role.name), ctx.prefix)
            await channel.send(msg)
            return

        if len(addRole):
            self.settings.role.add_roles(ctx.author, addRole)

        msg = '*{}* has acquired **{}!**'.format(DisplayName.name(
            ctx.message.author), Nullify.escape_all(role.name))
        await channel.send(msg)

    @commands.command(pass_context=True)
    async def setrole(self, ctx, *, role=None):
        """Sets your role from the user role list.  You can only have one at a time."""
        block_list = self.settings.getServerStat(ctx.guild, "UserRoleBlock")
        if ctx.author.id in block_list:
            await ctx.send("You are currently blocked from using this command.")
            return

        server = ctx.message.guild
        channel = ctx.message.channel

        if not self.settings.getServerStat(server, "OnlyOneUserRole"):
            await ctx.invoke(self.addrole, role=role)
            return

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        # Get the array
        try:
            promoArray = self.settings.getServerStat(server, "UserRoles")
        except Exception:
            promoArray = []
        if promoArray == None:
            promoArray = []

        if role == None:
            # Remove us from all roles
            remRole = []
            for arole in promoArray:
                roleTest = DisplayName.roleForID(arole['ID'], server)
                if not roleTest:
                    # Not a real role - skip
                    continue
                if roleTest in ctx.message.author.roles:
                    # We have this in our roles - remove it
                    remRole.append(roleTest)
            if len(remRole):
                self.settings.role.rem_roles(ctx.author, remRole)
            # Give a quick status
            msg = '*{}* has been moved out of all roles in the list!'.format(
                DisplayName.name(ctx.message.author))
            await channel.send(msg)
            return

        # Check if role is real
        roleCheck = DisplayName.roleForName(role, server)
        if not roleCheck:
            # No luck...
            msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(
                Nullify.escape_all(role), ctx.prefix)
            await channel.send(msg)
            return

        # Got a role - set it
        role = roleCheck

        addRole = []
        remRole = []
        for arole in promoArray:
            roleTest = DisplayName.roleForID(arole['ID'], server)
            if not roleTest:
                # Not a real role - skip
                continue
            if str(arole['ID']) == str(role.id):
                # We found it!
                addRole.append(roleTest)
            elif roleTest in ctx.message.author.roles:
                # Not our intended role and we have this in our roles - remove it
                remRole.append(roleTest)

        if not len(addRole):
            # We didn't find that role
            msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(
                Nullify.escape_all(role.name), ctx.prefix)
            await channel.send(msg)
            return

        if len(remRole) or len(addRole):
            self.settings.role.change_roles(
                ctx.author, add_roles=addRole, rem_roles=remRole)

        msg = '*{}* has been moved to **{}!**'.format(
            DisplayName.name(ctx.message.author), Nullify.escape_all(role.name))
        await channel.send(msg)
