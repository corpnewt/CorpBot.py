import json, os
from   discord.ext import commands
from   Cogs import Settings, DisplayName, Message, Nullify, PickList

def setup(bot):
    # Add the bot and deps
    bot.add_cog(SettingsDict(bot))

class SettingsDict(commands.Cog):

    # Init with the bot reference
    def __init__(self, bot):
        self.bot       = bot
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    def _type(self, val):
        for t,n in ((bool,"bool"),(int,"int"),(float,"float"),(str,"str"),(list,"list"),(tuple,"list"),(dict,"dict")):
            if isinstance(val,t):return n
        return type(val)

    @commands.command()
    async def sdict(self, ctx, command=None, key=None, *, args=None):
        """Allows the bot's owners to interface with the settings_dict.json.

        $sdict [command] ([key] ([type]) [value])

        Commands:
            list - Lists all the current keys
            get  - Gets the passed setting key
            set  - Sets the passed setting key with the passed value
            rem  - Removes the passed setting name if found
            del  - Alias for rem

        Type (optional - will take the first cast match by default):
            int
            float
            bool
            str

        JSON data passed with no type will be serialized and used as-is

        Examples:
            To print the value and type of a key called "some_value":
                $sdict get some_value
            To set "some_value" to an integer value of 10:
                $sdict set some_value int 10
            To remove "some_value":
                $sdict rem some_value"""

        if not await Utils.is_owner_reply(ctx): return
        # We're owner - let's check set our usage
        usage = "Usage: `{}sdict [command] ([key] ([type]) [value])`".format(ctx.prefix)
        if not command: return await ctx.send(usage)
        # Let's see if we got a valid command
        command = command.lower() # Normalize case
        valid_commands = ("list","get","set","rem","del")
        if not command in valid_commands:
            return await ctx.send("Invalid command!\n"+usage)
        if command == "list": # We're just listing the current keys
            try:
                key_list = list(self.bot.settings_dict)
            except:
                key_list = []
            if not key_list:
                desc = "No keys in settings_dict.json!"
            else:
                desc = "\n".join([Utils.truncate_string("{}. {}".format(i,x)) for i,x in enumerate(key_list,start=1)])
            return await PickList.PagePicker(
                title="All Keys ({:,} Total)".format(len(key_list)),
                description=desc,
                ctx=ctx
            ).pick()
        # We have a valid command - let's see if we have a key
        if not key:
            return await ctx.send("Missing key!\n"+usage)
        # Alright - now we should have some stuffs - let's see what we have
        cleaned_key = Nullify.escape_all(key)
        val = self.bot.settings_dict.get(key)
        if command in ("get","rem"): # We're only retrieving keys
            if not val: # The key didn't match anything - throw an error
                return await Message.Embed(
                    title="Missing Key",
                    description="'{}' did not match any keys in settings_dict.".format(cleaned_key),
                    color=ctx.author
                ).send(ctx)
            # We got a value - let's see if we're just returning it - or we're going to remove it
            fields = [
                {"name":"Key","value":cleaned_key},
                {"name":"{}Value | {}".format("" if command=="get" else "Removed ",self._type(val)),"value":Nullify.escape_all(str(val))}
            ]
            await Message.Embed(
                title=("Get" if command=="get" else "Remove")+"Settings Dict Key",
                fields=fields,
                color=ctx.author,
                footer="Settings changes may require Cog or Bot reload to take effect." if command=="rem" else None
            ).send(ctx)
            # Check if we were removing - and remove it
            if command in ("rem","del"):
                self.bot.settings_dict.pop(key,None)
                # Write the new settings dict
                json.dump(self.bot.settings_dict,open("settings_dict.json","w"),indent=4)
        else: # We're setting something!
            if not args: # We're missing arguments
                return await ctx.send("Missing arguments!\n"+usage)
            try: # Try json first
                value = json.loads(args)
            except:
                # Setup some cast functions
                type_func = {"int":int,"float":float,"bool":bool,"str":str}
                # Try to see if the first arg matches any cast functions
                cast_name = args.split(" ")[0].lower()
                cast = type_func.get(cast_name)
                if cast: # Trim the args to remove the leading type
                    args = " ".join(args.split(" ")[1:])
                # Get a list to iterate - if none matched, check them all in order
                check_types = [cast] if cast else list(type_func.values())
                value = None
                for t in check_types:
                    if t == bool:
                        # Special check for true/false
                        value = True if args.lower() == "true" else False if args.lower() == "false" else value
                    else:
                        try:value = t(args)
                        except: pass
                    if value: break # Leave the loop if we got a valid value cast
            if not value:
                # We didn't cast properly - let's whine
                return await Message.Embed(
                    title="Could Not Set Key",
                    description="Unable to cast as {}.".format(
                        cast_name if cast else "int, float, bool, or str"
                    ),
                    color=ctx.author
                ).send(ctx)
            # We got a key, a type, and a value - let's make sure we can serialize
            # it to json data first
            try:
                j = json.dumps({key:value})
            except Exception as e:
                return await Message.Embed(
                    title="Invalid Json Data",
                    description="Error serializing the passed value:\n{}".format(e),
                    color=ctx.author
                ).send(ctx)
            # It serialized properly - let's save it
            fields = [
                {"name":"Key","value":cleaned_key},
                {"name":"New Value | {}".format(self._type(value)),"value":Nullify.escape_all(str(value))}
            ]
            if val: # Show the previous value if we just updated it
                fields.insert(1,{"name":"Prior Value | {}".format(self._type(val)),"value":Nullify.escape_all(str(val))})
            await Message.Embed(
                title="Set Settings Dict Key",
                fields=fields,
                color=ctx.author,
                footer="Settings changes may require Cog or Bot reloads to take effect."
            ).send(ctx)
            # Actually set it - and save it
            self.bot.settings_dict[key] = value
            json.dump(self.bot.settings_dict,open("settings_dict.json","w"),indent=4)
