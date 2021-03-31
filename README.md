# CorpBot.py
A *slightly* less clumsy python bot for discord

***

# Basic Settings

The bot's basic settings should be in a file called `settings_dict.json` in the same folder as the `Main.py` file.  Some basic formatting of this file would look like so:

```json
{
    "prefix": "your_custom_prefix_here",
    "token": "your_token_here",
    "weather": "your_weather_api_key_here",
    "currency": "your_currency_api_key_here"
}
```

You'll want to replace the values with your own.  The `prefix` key can be omitted, and the bot will fallback on its default `$` prefix.

***

# Command List

A list of cogs, commands, and descriptions:

[Actions](#actions), [Admin](#admin), [Ascii](#ascii), [Bot](#bot), [BotAdmin](#botadmin), [CAH](#cah), [Calc](#calc), [Channel](#channel), [ChatterBot](#chatterbot), [Claptrap](#claptrap), [Clippy](#clippy), [CogManager](#cogmanager), [Comic](#comic), [DJRoles](#djroles), [Debugging](#debugging), [Dice](#dice), [DisableCommand](#disablecommand), [Discogs](#discogs), [DrBeer](#drbeer), [EightBall](#eightball), [Emoji](#emoji), [Encode](#encode), [Example](#example), [Face](#face), [Feed](#feed), [Fliptime](#fliptime), [GameLookup](#gamelookup), [Giphy](#giphy), [Groot](#groot), [Help](#help), [Humor](#humor), [Hw](#hw), [IntelArk](#intelark), [Invite](#invite), [JazUtils](#jazutils), [Jpeg](#jpeg), [LangFilter](#langfilter), [Lists](#lists), [Lockdown](#lockdown), [MadLibs](#madlibs), [Morse](#morse), [Music](#music), [Mute](#mute), [OfflineUser](#offlineuser), [PciUsb](#pciusb), [Plist](#plist), [Printer](#printer), [Profile](#profile), [Promote](#promote), [Quote](#quote), [RateLimit](#ratelimit), [Reddit](#reddit), [Remind](#remind), [Responses](#responses), [Search](#search), [SecretSanta](#secretsanta), [Server](#server), [ServerStats](#serverstats), [Settings](#settings), [Setup](#setup), [Spooktober](#spooktober), [Stream](#stream), [Strike](#strike), [Telephone](#telephone), [TempRole](#temprole), [Time](#time), [Translate](#translate), [Turret](#turret), [Uptime](#uptime), [UrbanDict](#urbandict), [UserRole](#userrole), [VoteKick](#votekick), [WatchURL](#watchurl), [Weather](#weather), [Welcome](#welcome), [Wiki](#wiki), [Xp](#xp), [XpBlock](#xpblock), [XpStack](#xpstack)

## Actions
####	Actions Cog (6 commands) - Actions.py Extension:
	  $boop [member]
	   └─ Boop da snoot.
	  $drink [member]
	   └─ Drink like a boss.
	  $eat [member]
	   └─ Eat like a boss.
	  $highfive [member]
	   └─ High five like a boss.
	  $pet [member]
	   └─ pet kitties.
	  $spook [member]
	   └─ sp00ktober by camiel.

## Admin
####	Admin Cog (27 commands) - Admin.py Extension:
	  $addadmin [role]
	   └─ Adds a new role to the admin list (admin only).
	  $addxprole [role] [xp]
	   └─ Adds a new role to the xp promotion/demotion system (admin only).
	  $broadcast [message]
	   └─ Broadcasts a message to all connected servers.  Can only be done by the owner.
	  $defaultchannel 
	   └─ Lists the server's default channel, whether custom or not.
	  $lock 
	   └─ Toggles whether the bot only responds to admins (admin only).
	  $onexprole [yes_no]
	   └─ Gets and sets whether or not to remove all but the current xp role a user has...
	  $prunexproles 
	   └─ Removes any roles from the xp promotion/demotion system that are no longer on...
	  $rawrules 
	   └─ Display the markdown for the server's rules (bot-admin only).
	  $removeadmin [role]
	   └─ Removes a role from the admin list (admin only).
	  $removemotd [chan]
	   └─ Removes the message of the day from the selected channel.
	  $removexprole [role]
	   └─ Removes a role from the xp promotion/demotion system (admin only).
	  $setdefaultchannel [channel]
	   └─ Sets a replacement default channel for bot messages (admin only).
	  $setdefaultrole [role]
	   └─ Sets the default role or position for auto-role assignment.
	  $sethackrole [role]
	   └─ Sets the required role ID to add/remove hacks (admin only).
	  $setlinkrole [role]
	   └─ Sets the required role ID to add/remove links (admin only).
	  $setmadlibschannel [channel]
	   └─ Sets the channel for MadLibs (admin only).
	  $setmotd [message] [chan]
	   └─ Adds a message of the day to the selected channel.
	  $setrules [rules]
	   └─ Set the server's rules (bot-admin only).
	  $setstoprole [role]
	   └─ Sets the required role ID to stop the music player (admin only).
	  $settagrole [role]
	   └─ Sets the required role ID to add/remove tags (admin only).
	  $setxp [member] [xpAmount]
	   └─ Sets an absolute value for the member's xp (admin only).
	  $setxpreserve [member] [xpAmount]
	   └─ Set's an absolute value for the member's xp reserve (admin only).
	  $setxprole [role]
	   └─ Sets the required role ID to give xp, gamble, or feed the bot (admin only).
	  $stoprole 
	   └─ Lists the required role to stop the bot from playing music.
	  $xplimit [limit]
	   └─ Gets and sets a limit to the maximum xp a member can get.  Pass a negative va...
	  $xpreservelimit [limit]
	   └─ Gets and sets a limit to the maximum xp reserve a member can get.  Pass a neg...
	  $xprole 
	   └─ Lists the required role to give xp, gamble, or feed the bot.

## Ascii
####	Ascii Cog (1 command) - Ascii.py Extension:
	  $ascii [text]
	   └─ Beautify some text (font list at http://artii.herokuapp.com/fonts_list).

## Bot
####	Bot Cog (23 commands) - Bot.py Extension:
	  $adminunlim [yes_no]
	   └─ Sets whether or not to allow unlimited xp to admins (bot-admin only).
	  $avatar [filename]
	   └─ Sets the bot's avatar (owner only).
	  $basadmin [yes_no]
	   └─ Sets whether or not to treat bot-admins as admins with regards to xp (admin o...
	  $botinfo 
	   └─ Lists some general stats about the bot.
	  $cloc 
	   └─ Outputs the total count of lines of code in the currently installed repo.
	  $embed [embed]
	   └─ Builds an embed using json formatting.
	  $getimage <image>
	   └─ Tests downloading - owner only
	  $hostinfo 
	   └─ List info about the bot's host environment.
	  $joinpm [yes_no]
	   └─ Sets whether or not to pm the rules to new users when they join (bot-admin on...
	  $listengame [game]
	   └─ Sets the listening status of the bot (owner-only).
	  $nickname [name]
	   └─ Set the bot's nickname (admin-only).
	  $ping 
	   └─ Feeling lonely?
	  $playgame [game]
	   └─ Sets the playing status of the bot (owner-only).
	  $pres [playing_type=0] [status_type=online] [game] [url]
	   └─ Changes the bot's presence (owner-only).
	  $reboot [force]
	   └─ Reboots the bot (owner only).
	  $servers 
	   └─ Lists the number of servers I'm connected to!
	  $setbotparts [parts]
	   └─ Set the bot's parts - can be a url, formatted text, or nothing to clear.
	  $shutdown [force]
	   └─ Shuts down the bot (owner only).
	  $source 
	   └─ Link the github source.
	  $speedtest 
	   └─ Run a network speed test (owner only).
	  $status [status]
	   └─ Gets or sets the bot's online status (owner-only).
	  $streamgame [url] [game]
	   └─ Sets the streaming status of the bot, requires the url and the game (owner-on...
	  $watchgame [game]
	   └─ Sets the watching status of the bot (owner-only).

## BotAdmin
####	BotAdmin Cog (7 commands) - BotAdmin.py Extension:
	  $ban [members] [reason]
	   └─ Bans the passed members for the specified reason.
	  $ignore [member]
	   └─ Adds a member to the bot's "ignore" list (bot-admin only).
	  $ignored 
	   └─ Lists the users currently being ignored.
	  $kick [members] [reason]
	   └─ Kicks the passed members for the specified reason.
	  $listen [member]
	   └─ Removes a member from the bot's "ignore" list (bot-admin only).
	  $removeinvitelinks [yes_no]
	   └─ Enables/Disables auto-deleting discord invite links in chat (bot-admin only).
	  $setuserparts [member] [parts]
	   └─ Set another user's parts list (owner only).

## CAH
####	CAH Cog (17 commands) - CAH.py Extension:
	  $addbot 
	   └─ Adds a bot to the game.  Can only be done by the player who created the game.
	  $addbots [number]
	   └─ Adds bots to the game.  Can only be done by the player who created the game.
	  $cahgames 
	   └─ Displays up to 10 CAH games in progress.
	  $flushhand 
	   └─ Flushes the cards in your hand - can only be done once per game.
	  $game [message]
	   └─ Displays the game's current status.
	  $hand 
	   └─ Shows your hand.
	  $idlekick [setting]
	   └─ Sets whether or not to kick members if idle for 5 minutes or more.  Can only ...
	  $joincah [id]
	   └─ Join a Cards Against Humanity game.  If no id or user is passed, joins a rand...
	  $laid 
	   └─ Shows who laid their cards and who hasn't.
	  $lay [card]
	   └─ Lays a card or cards from your hand.  If multiple cards are needed, separate ...
	  $leavecah 
	   └─ Leaves the current game you're in.
	  $newcah 
	   └─ Starts a new Cards Against Humanity game.
	  $pick [card]
	   └─ As the judge - pick the winning card(s).
	  $removebot [id]
	   └─ Removes a bot from the game.  Can only be done by the player who created the ...
	  $removeplayer [name]
	   └─ Removes a player from the game.  Can only be done by the player who created t...
	  $say [message]
	   └─ Broadcasts a message to the other players in your game.
	  $score 
	   └─ Display the score of the current game.

## Calc
####	Calc Cog (1 command) - Calc.py Extension:
	  $calc [formula]
	   └─ Do some math.

## Channel
####	Channel Cog (5 commands) - Channel.py Extension:
	  $islocked 
	   └─ Says whether the bot only responds to admins.
	  $listadmin 
	   └─ Lists admin roles and id's.
	  $listmuted 
	   └─ Lists the names of those that are muted.
	  $log [messages=25] [chan]
	   └─ Logs the passed number of messages from the given channel - 25 by default (ad...
	  $rules 
	   └─ Display the server's rules.

## ChatterBot
####	ChatterBot Cog (2 commands) - ChatterBot.py Extension:
	  $chat [message]
	   └─ Chats with the bot.
	  $setchatchannel [channel]
	   └─ Sets the channel for bot chatter.

## Claptrap
####	Claptrap Cog (1 command) - Claptrap.py Extension:
	  $claptrap 
	   └─ Can I shoot something now? Or climb some stairs? SOMETHING exciting?

## Clippy
####	Clippy Cog (1 command) - Clippy.py Extension:
	  $clippy [text]
	   └─ I *know* you wanted some help with something - what was it?

## CogManager
####	CogManager Cog (5 commands) - CogManager.py Extension:
	  $extension [extension]
	   └─ Outputs the cogs attatched to the passed extension.
	  $extensions 
	   └─ Lists all extensions and their corresponding cogs.
	  $imports [extension]
	   └─ Outputs the extensions imported by the passed extension.
	  $reload [extension]
	   └─ Reloads the passed extension - or all if none passed.
	  $update 
	   └─ Updates from git.

## Comic
####	Comic Cog (12 commands) - Comic.py Extension:
	  $cyanide [date]
	   └─ Displays the Cyanide & Happiness comic for the passed date (MM-DD-YYYY) from ...
	  $dilbert [date]
	   └─ Displays the Dilbert comic for the passed date (MM-DD-YYYY) from 04-16-1989 t...
	  $garfield [date]
	   └─ Displays the Garfield comic for the passed date (MM-DD-YYYY) from 06-19-1978 ...
	  $gmg [date]
	   └─ Displays the Garfield Minus Garfield comic for the passed date (MM-DD-YYYY) f...
	  $peanuts [date]
	   └─ Displays the Peanuts comic for the passed date (MM-DD-YYYY) from 10-02-1950 t...
	  $randcyanide 
	   └─ Displays a random Cyanide & Happiness comic from 01-26-2005 to today.
	  $randgarfield 
	   └─ Displays a random Garfield comic from 06-19-1978 to today.
	  $randgmg 
	   └─ Displays a random Garfield Minus Garfield comic from 02-13-2008 to today.
	  $randilbert [date]
	   └─ Displays a random Dilbert comic from 04-16-1989 to today.
	  $randpeanuts 
	   └─ Displays a random Peanuts comic from 10-02-1950 to today.
	  $randxkcd 
	   └─ Displays a random XKCD comic from 01-01-2006 to today.
	  $xkcd [date]
	   └─ Displays the XKCD comic for the passed date (MM-DD-YYYY) from 01-01-2006 to t...

## DJRoles
####	DJRoles Cog (3 commands) - DJRoles.py Extension:
	  $adddj [role]
	   └─ Adds a new role to the dj list (bot-admin only).
	  $listdj 
	   └─ Lists dj roles and id's.
	  $removedj [role]
	   └─ Removes a role from the dj list (bot-admin only).

## Debugging
####	Debugging Cog (9 commands) - Debugging.py Extension:
	  $clean [messages] [chan]
	   └─ Cleans the passed number of messages from the given channel (admin only).
	  $cleardebug 
	   └─ Deletes the debug.txt file (owner only).
	  $heartbeat 
	   └─ Write to the console and attempt to send a message (owner only).
	  $logdisable [options]
	   └─ Disables the passed, comma-delimited log vars.  If run with no arguments, dis...
	  $logenable [options]
	   └─ Enables the passed, comma-delimited log vars (bot-admin only).
	  $logging 
	   └─ Outputs whether or not we're logging is enabled (bot-admin only).
	  $logpreset [preset]
	   └─ Can select one of 4 available presets - off, quiet, normal, verbose (bot-admi...
	  $setdebug [debug]
	   └─ Turns on/off debugging (owner only - always off by default).
	  $setlogchannel [channel]
	   └─ Sets the channel for Logging (bot-admin only).

## Dice
####	Dice Cog (1 command) - Dice.py Extension:
	  $roll [dice]
	   └─ Performs up to 10 space-delimited dice rolls in NdN±Na|d format.

## DisableCommand
####	DisableCommand Cog (9 commands) - DisableCommand.py Extension:
	  $adminallow [yes_no]
	   └─ Sets whether admins can access disabled commands (admin-only).
	  $badminallow [yes_no]
	   └─ Sets whether bot-admins can access disabled commands (admin-only).
	  $disable [command_or_cog_name]
	   └─ Disables the passed command or all commands in the passed cog (admin-only).  ...
	  $disableall 
	   └─ Disables all enabled commands outside this module (admin-only).
	  $disabledreact [yes_no]
	   └─ Sets whether the bot reacts to disabled commands when attempted (admin-only).
	  $enable [command_or_cog_name]
	   └─ Enables the passed command or all commands in the passed cog (admin-only).  C...
	  $enableall 
	   └─ Enables all disabled commands (admin-only).
	  $isdisabled [command_or_cog_name]
	   └─ Outputs whether the passed command - or all commands in a passed cog are disa...
	  $listdisabled 
	   └─ Lists all disabled commands (admin-only).

## Discogs
####	Discogs Cog (1 command) - Discogs.py Extension:
	  $discogs [search]
	   └─ Perform a general discogs.com search. Could return albums, artits, etc.

## DrBeer
####	DrBeer Cog (1 command) - DrBeer.py Extension:
	  $drbeer 
	   └─ Put yourself in your place.

## EightBall
####	EightBall Cog (1 command) - EightBall.py Extension:
	  $eightball [question]
	   └─ Get some answers.

## Emoji
####	Emoji Cog (2 commands) - Emoji.py Extension:
	  $addemoji [emoji] [name]
	   └─ Adds the passed emoji, url, or attachment as a custom emoji with the passed n...
	  $emoji [emoji]
	   └─ Outputs the passed emoji... but bigger!

## Encode
####	Encode Cog (10 commands) - Encode.py Extension:
	  $binint [input_binary]
	   └─ Converts the input binary to its integer representation.
	  $binstr [input_binary]
	   └─ Converts the input binary to its string representation.
	  $color [value]
	   └─ View info on a rgb, hex or cmyk color and their
	  $dechex [input_dec]
	   └─ Converts an int to hex.
	  $encode [from_type] [to_type] [value]
	   └─ Data converter from ascii <--> hex <--> base64.
	  $hexdec [input_hex]
	   └─ Converts hex to decimal.
	  $hexswap [input_hex]
	   └─ Byte swaps the passed hex value.
	  $intbin [input_int]
	   └─ Converts the input integer to its binary representation.
	  $slide [input_hex]
	   └─ Calculates your slide value for Clover based on an input address (in hex).
	  $strbin [input_string]
	   └─ Converts the input string to its binary representation.

## Example
####	Example Cog (3 commands) - Example.py Extension:
	  $add <left> <right>
	   └─ Adds two numbers together.
	  $choose [choices...]
	   └─ Chooses between multiple choices.
	  $joined [member]
	   └─ Says when a member joined.

## Face
####	Face Cog (4 commands) - Face.py Extension:
	  $lastlenny 
	   └─ Who Lenny'ed last?
	  $lastshrug 
	   └─ Who shrugged last?
	  $lenny [message]
	   └─ Give me some Lenny.
	  $shrug [message]
	   └─ Shrug it off.

## Feed
####	Feed Cog (8 commands) - Feed.py Extension:
	  $feed [food]
	   └─ Feed the bot some xp!
	  $hunger 
	   └─ How hungry is the bot?
	  $ignoredeath [yes_no]
	   └─ Sets whether the bot ignores its own death and continues to respond post-mort...
	  $iskill 
	   └─ Check the ded of the bot.
	  $kill 
	   └─ Kill the bot... you heartless soul.
	  $killrole 
	   └─ Lists the required role to kill/resurrect the bot.
	  $resurrect 
	   └─ Restore life to the bot.  What magic is this?
	  $setkillrole [role]
	   └─ Sets the required role to kill/resurrect the bot (admin only).

## Fliptime
####	Fliptime Cog (1 command) - Fliptime.py Extension:
	  $tableflip [yes_no]
	   └─ Turns on/off table flip muting (bot-admin only; always off by default).

## GameLookup
####	GameLookup Cog (1 command) - GameLookup.py Extension:
	  $gamelookup <game>
	   └─ Help not available...

## Giphy
####	Giphy Cog (4 commands) - Giphy.py Extension:
	  $addgif [role]
	   └─ Adds a new role to the gif list (admin only).
	  $gif [gif]
	   └─ Search for some giphy!
	  $listgif 
	   └─ Lists gif roles and id's.
	  $removegif [role]
	   └─ Removes a role from the gif list (admin only).

## Groot
####	Groot Cog (1 command) - Groot.py Extension:
	  $groot 
	   └─ Who... who are you?

## Help
####	Help Cog (3 commands) - Help.py Extension:
	  $dumphelp [tab_indent_count]
	   └─ Dumps a timestamped, formatted list of commands and descriptions into the sam...
	  $dumpmarkdown 
	   └─ Dumps a timestamped, markdown-formatted list of commands and descriptions int...
	  $help [command]
	   └─ Lists the bot's commands and cogs.

## Humor
####	Humor Cog (9 commands) - Humor.py Extension:
	  $fart 
	   └─ PrincessZoey :P
	  $french 
	   └─ Speaking French... probably...
	  $german 
	   └─ Speaking German... probably...
	  $holy [subject]
	   └─ Time to backup the Batman!
	  $meme [template_id] [text_zero] [text_one]
	   └─ Generate Memes!  You can get a list of meme templates with the memetemps comm...
	  $memetemps 
	   └─ Get Meme Templates
	  $poke [url]
	   └─ Pokes the passed url/user/uploaded image.
	  $stardew [user]
	   └─ Test your luck with another user.
	  $zalgo [message]
	   └─ Ỉ s̰hͨo̹u̳lͪd͆ r͈͍e͓̬a͓͜lͨ̈l̘̇y̡͟ h͚͆a̵͢v͐͑eͦ̓ i͋̍̕n̵̰ͤs͖̟̟t͔ͤ̉ǎ͓͐ḻ̪ͨl̦͒̂e...

## Hw
####	Hw Cog (12 commands) - Hw.py Extension:
	  $cancelhw 
	   └─ Cancels a current hardware session.
	  $delhw [build]
	   └─ Removes a build from your build list.
	  $edithw [build]
	   └─ Edits a build from your build list.
	  $gethw [user] [search]
	   └─ Searches the user's hardware for a specific search term.
	  $hw [user] [build]
	   └─ Lists the hardware for either the user's default build - or the passed build.
	  $listhw [user]
	   └─ Lists the builds for the specified user - or yourself if no user passed.
	  $mainhw [build]
	   └─ Sets a new main build from your build list.
	  $newhw 
	   └─ Initiate a new-hardware conversation with the bot.  The hardware added will a...
	  $pcpp [url] [style] [escape]
	   └─ Convert a pcpartpicker.com link into markdown parts. Available styles: normal...
	  $rawhw [user] [build]
	   └─ Lists the raw markdown for either the user's default build - or the passed bu...
	  $renhw [build]
	   └─ Renames a build from your build list.
	  $sethwchannel [channel]
	   └─ Sets the channel for hardware (admin only).

## IntelArk
####	IntelArk Cog (1 command) - IntelArk.py Extension:
	  $iark [text]
	   └─ Search Ark for Intel CPU info.

## Invite
####	Invite Cog (9 commands) - Invite.py Extension:
	  $approvejoin [server_id]
	   └─ Temporarily allows the bot to join the passed server id or join url (owner-on...
	  $block [server]
	   └─ Blocks the bot from joining a server - takes either a name or an id (owner-on...
	  $blocked 
	   └─ Lists all blocked servers and owners (owner-only).
	  $canjoin [yes_no]
	   └─ Sets whether the bot is allowed to join new servers (owner-only and enabled b...
	  $invite [invite_url]
	   └─ Outputs a url you can use to invite me to your server.
	  $requestjoin [invite_url]
	   └─ Forwards the invite url to the bot's owners for review.
	  $revokejoin [server_id]
	   └─ Revokes a previously approved temporary join (owner-only).
	  $unblock [server]
	   └─ Unblocks a server or owner (owner-only).
	  $unblockall 
	   └─ Unblocks all blocked servers and owners (owner-only).

## JazUtils
####	JazUtils Cog (7 commands) - JazUtils.py Extension:
	  $emptyroles 
	   └─ Shows a list of roles that have zero members.
	  $fullsnowflake [sid]
	   └─ show all available data about a snowflake ID
	  $rolecall <rolename>
	   └─ Counts the number of members with a specific role.
	  $rolecount 
	   └─ Simply counts the number of roles on the server. (excluding @everyone)
	  $roles [sort_order=name]
	   └─ Shows roles and their member counts. Takes one argument,
	  $snowflake [sid]
	   └─ show the date a snowflake ID was created
	  $whohas <rolename>
	   └─ Lists the people who have the specified role alongside their online status.

## Jpeg
####	Jpeg Cog (1 command) - Jpeg.py Extension:
	  $jpeg [url]
	   └─ MOAR JPEG!  Accepts a url - or picks the first attachment.

## LangFilter
####	LangFilter Cog (5 commands) - LangFilter.py Extension:
	  $addfilter [words]
	   └─ Adds comma delimited words to the word list (bot-admin only).
	  $clearfilter 
	   └─ Empties the list of words that will be filtered (bot-admin only).
	  $dumpfilter 
	   └─ Saves the filtered word list to a text file and uploads it to the requestor (...
	  $listfilter 
	   └─ Prints out the list of words that will be filtered (bot-admin only).
	  $remfilter [words]
	   └─ Removes comma delimited words from the word list (bot-admin only).

## Lists
####	Lists Cog (30 commands) - Lists.py Extension:
	  $addhack [name] [hack]
	   └─ Add a hack to the hack list.
	  $addlink [name] [link]
	   └─ Add a link to the link list.
	  $addtag [name] [tag]
	   └─ Add a tag to the tag list.
	  $hack [name]
	   └─ Retrieve a hack from the hack list.
	  $hackinfo [name]
	   └─ Displays info about a hack from the hack list.
	  $hackrole 
	   └─ Lists the required role to add hacks.
	  $hacks 
	   └─ List all hack in the hack list.
	  $lastonline [member]
	   └─ Lists the last time a user was online if known.
	  $link [name]
	   └─ Retrieve a link from the link list.
	  $linkinfo [name]
	   └─ Displays info about a link from the link list.
	  $linkrole 
	   └─ Lists the required role to add links.
	  $links 
	   └─ List all links in the link list.
	  $online 
	   └─ Lists the number of users online.
	  $parts [member]
	   └─ Retrieve a member's parts list. DEPRECATED - Use hw instead.
	  $partstemp 
	   └─ Gives a copy & paste style template for setting a parts list.
	  $rawhack [name]
	   └─ Retrieve a hack's raw markdown from the hack list.
	  $rawhacks 
	   └─ List raw markdown of all hacks in the hack list.
	  $rawlink [name]
	   └─ Retrieve a link's raw markdown from the link list.
	  $rawlinks 
	   └─ List raw markdown of all links in the link list.
	  $rawparts [member]
	   └─ Retrieve the raw markdown for a member's parts list. DEPRECATED - Use rawhw i...
	  $rawtag [name]
	   └─ Retrieve a tag's raw markdown from the tag list.
	  $rawtags 
	   └─ List raw markdown of all tags in the tag list.
	  $removehack [name]
	   └─ Remove a hack from the hack list.
	  $removelink [name]
	   └─ Remove a link from the link list.
	  $removetag [name]
	   └─ Remove a tag from the tag list.
	  $setparts [parts]
	   └─ Set your own parts - can be a url, formatted text, or nothing to clear. DEPRE...
	  $tag [name]
	   └─ Retrieve a tag from the tag list.
	  $taginfo [name]
	   └─ Displays info about a tag from the tag list.
	  $tagrole 
	   └─ Lists the required role to add tags.
	  $tags 
	   └─ List all tag in the tag list.

## Lockdown
####	Lockdown Cog (10 commands) - Lockdown.py Extension:
	  $addlock [channel_list]
	   └─ Adds the passed space-delimited list of channels and categories to the lockdo...
	  $addlockall 
	   └─ Adds all channels and categories to the lockdown list (bot-admin only).
	  $antiraid [on_off] [join_number] [join_seconds] [kick_ban_mute] [cooldown_minutes]
	   └─ Sets up the anti-raid module (bot-admin only).
	  $antiraidping [user_or_role] [channel]
	   └─ Sets up what user or role to ping and in what channel when anti-raid is activ...
	  $listlock 
	   └─ Lists the channels and categories configured for lockdown (bot-admin only).
	  $listlockall 
	   └─ Lists all channels and categories and their lockdown/sync status (bot-admin o...
	  $lockdown [target_channel]
	   └─ Iterate through the channels in the lockdown list and revoke the send_message...
	  $remlock [channel_list]
	   └─ Removes the passed space-delimited list of channels and categories from the l...
	  $remlockall 
	   └─ Removes all channels and categories from the lockdown list (bot-admin only).
	  $unlockdown [target_channel]
	   └─ Iterate through the channels in the lockdown list and clear the send_message,...

## MadLibs
####	MadLibs Cog (2 commands) - MadLibs.py Extension:
	  $madlibs 
	   └─ Let's play MadLibs!
	  $ml [word]
	   └─ Used to choose your words when in the middle of a madlibs.

## Morse
####	Morse Cog (3 commands) - Morse.py Extension:
	  $morse [content]
	   └─ Converts ascii to morse code.  Accepts a-z and 0-9.  Each letter is comprised...
	  $morsetable [num_per_row]
	   └─ Prints out the morse code lookup table.
	  $unmorse [content]
	   └─ Converts morse code to ascii.  Each letter is comprised of "-" or "." and sep...

## Music
####	Music Cog (31 commands) - Music.py Extension:
	  $autodeleteafter [seconds]
	   └─ Lists or sets the current delay before auto-deleting music related messages (...
	  $disableplay [yes_no]
	   └─ Enables/Disables the music commands.  Helpful in case Youtube is rate limitin...
	  $eqpreset [preset]
	   └─ Sets the current eq to one of the following presets:  Boost, Flat, Metal
	  $geteq 
	   └─ Prints the current equalizer settings.
	  $join [channel]
	   └─ Joins a voice channel.
	  $leave 
	   └─ Stops and disconnects the bot from voice.
	  $loadpl [url]
	   └─ Loads the passed playlist json data.  Accepts a url - or picks the first atta...
	  $pause 
	   └─ Pauses the currently playing song.
	  $paused [moons]
	   └─ Lists whether or not the player is paused.  Synonym of the playing command.
	  $play [url]
	   └─ Plays from a url (almost anything youtube_dl supports) or resumes a currently...
	  $playing [moons]
	   └─ Lists the currently playing song if any.
	  $playingin 
	   └─ Shows the number of servers the bot is currently playing music in.
	  $playlist 
	   └─ Lists the queued songs in the playlist.
	  $repeat [yes_no]
	   └─ Checks or sets whether to repeat the current playlist.
	  $reseteq 
	   └─ Resets the current eq to the flat preset.
	  $resume 
	   └─ Resumes the song if paused.
	  $savepl [options]
	   └─ Saves the current playlist to a json file that can be loaded later.
	  $searchlist [yes_no]
	   └─ Gets or sets whether or not the server will show a list of options when searc...
	  $seek [position]
	   └─ Seeks to the passed position in the song if possible.  Position should be in ...
	  $setband [band_number] [value]
	   └─ Sets the value of the passed eq band (1-15) to the passed value from -5 (sile...
	  $seteq [bands]
	   └─ Sets the equalizer to the passed 15 space-delimited values from -5 (silent) t...
	  $shuffle [url]
	   └─ Shuffles the current queue. If you pass a playlist url or search term, it fir...
	  $shufflepl [url]
	   └─ Loads and shuffles the passed playlist json data.  Accepts a url - or picks t...
	  $skip 
	   └─ Adds your vote to skip the current song.  50% or more of the non-bot users ne...
	  $stop 
	   └─ Stops and empties the current playlist.
	  $stopall 
	   └─ Stops and disconnects the bot from all voice channels in all servers (owner-o...
	  $summon [channel]
	   └─ Joins the summoner's voice channel.
	  $unplay [song_number]
	   └─ Removes the passed song number from the queue.  You must be the requestor, or...
	  $unqueue 
	   └─ Removes all songs you've added from the queue (does not include the currently...
	  $unskip 
	   └─ Removes your vote to skip the current song.
	  $volume [volume]
	   └─ Changes the player's volume (0-150%).

## Mute
####	Mute Cog (8 commands) - Mute.py Extension:
	  $createmuterole [role_name]
	   └─ Sets the target role to apply when muting (bot-admin only).
	  $desyncmuterole 
	   └─ Removes send_messages, add_reactions, and speak overrides from the mute role ...
	  $ismuted [member]
	   └─ Says whether a member is muted in chat.
	  $mute [member] [cooldown]
	   └─ Prevents a member from sending messages in chat or speaking in voice (bot-adm...
	  $muterole 
	   └─ Lists the target role to apply when muting (bot-admin only).
	  $setmuterole [role]
	   └─ Sets the target role to apply when muting.  Passing nothing will disable the ...
	  $syncmuterole 
	   └─ Ensures that the mute role has the send_messages, add_reactions, and speak ov...
	  $unmute [member]
	   └─ Allows a muted member to send messages in chat (bot-admin only).

## OfflineUser
####	OfflineUser Cog (1 command) - OfflineUser.py Extension:
	  $remindoffline [yes_no]
	   └─ Sets whether to inform users that pinged members are offline or not.

## PciUsb
####	PciUsb Cog (2 commands) - PciUsb.py Extension:
	  $pci [ven_dev]
	   └─ Searches pci-ids.ucw.cz for the passed PCI ven:dev id.
	  $usb [ven_dev]
	   └─ Searches usb-ids.gowdy.us for the passed USB ven:dev id.

## Plist
####	Plist Cog (2 commands) - Plist.py Extension:
	  $nvweb [os_build]
	   └─ Prints the download url for the passed OS build number (if it exists).  If no...
	  $plist [url]
	   └─ Validates plist file structure.  Accepts a url - or picks the first attachment.

## Printer
####	Printer Cog (2 commands) - Printer.py Extension:
	  $print [url]
	   └─ DOT MATRIX.  Accepts a url - or picks the first attachment.
	  $printavi [member]
	   └─ Returns a url to the passed member's avatar.

## Profile
####	Profile Cog (7 commands) - Profile.py Extension:
	  $addprofile [name] [link]
	   └─ Add a profile to your profile list.
	  $profile [member] [name]
	   └─ Retrieve a profile from the passed user's profile list.
	  $profileinfo [member] [name]
	   └─ Displays info about a profile from the passed user's profile list.
	  $profiles [member]
	   └─ List all profiles in the passed user's profile list.
	  $rawprofile [member] [name]
	   └─ Retrieve a profile's raw markdown from the passed user's profile list.
	  $rawprofiles [member]
	   └─ List all profiles' raw markdown in the passed user's profile list.
	  $removeprofile [name]
	   └─ Remove a profile from your profile list.

## Promote
####	Promote Cog (4 commands) - Promote.py Extension:
	  $demote [member]
	   └─ Auto-removes the required xp to demote the passed user to the previous role (...
	  $demoteto [member] [role]
	   └─ Auto-removes the required xp to demote the passed user to the passed role (ad...
	  $promote [member]
	   └─ Auto-adds the required xp to promote the passed user to the next role (admin ...
	  $promoteto [member] [role]
	   └─ Auto-adds the required xp to promote the passed user to the passed role (admi...

## Quote
####	Quote Cog (6 commands) - Quote.py Extension:
	  $clearquotereaction 
	   └─ Clears the trigger reaction for quoting messages (admin only).
	  $getquotereaction 
	   └─ Displays the quote reaction if there is one.
	  $quoteadminonly [yes_no]
	   └─ Sets whether only admins/bot-admins can quote or not (bot-admin only).
	  $quotechannel 
	   └─ Prints the current quote channel.
	  $setquotechannel [channel]
	   └─ Sets the channel for quoted messages or disables it if no channel sent (admin...
	  $setquotereaction 
	   └─ Sets the trigger reaction for quoting messages (bot-admin only).

## RateLimit
####	RateLimit Cog (1 command) - RateLimit.py Extension:
	  $ccooldown [delay]
	   └─ Sets the cooldown in seconds between each command (owner only).

## Reddit
####	Reddit Cog (32 commands) - Reddit.py Extension:
	  $abandoned 
	   └─ Get something abandoned to look at.
	  $answer 
	   └─ Spout out some interstellar answering... ?
	  $aww 
	   └─ Whenever you're down - uppify.
	  $battlestation 
	   └─ Let's look at some pretty stuff.
	  $beeple 
	   └─ A new image every day... for years.
	  $brainfart 
	   └─ Spout out some uh... intellectual brilliance...
	  $cablefail 
	   └─ Might as well be a noose...
	  $carmod 
	   └─ Marvels of modern engineering.
	  $dankmeme 
	   └─ Only the dankest.
	  $dirtyjoke 
	   └─ Let's see if reddit can be dir-... oh... uh.. funny... (bot-admin only)
	  $dragon 
	   └─ From the past - when great winged beasts soared the skies.
	  $earthporn 
	   └─ Earth is good.
	  $joke 
	   └─ Let's see if reddit can be funny...
	  $lpt 
	   └─ Become a pro - AT LIFE.
	  $macsetup 
	   └─ Feast your eyes upon these setups.
	  $meirl 
	   └─ Me in real life.
	  $nocontext 
	   └─ Spout out some intersexual brilliance.
	  $nosleep 
	   └─ I hope you're not tired...
	  $pun 
	   └─ I don't know, don't ask...
	  $question 
	   └─ Spout out some interstellar questioning... ?
	  $randomcat 
	   └─ Meow.
	  $randomdog 
	   └─ Bark if you know whassup.
	  $redditimage [subreddit]
	   └─ Try to grab an image from an image-based subreddit.
	  $ruser [user_name]
	   └─ Gets some info on the passed username - attempts to use your username if none...
	  $shittybattlestation 
	   └─ Let's look at some shitty stuff.
	  $shittylpt 
	   └─ Your advise is bad, and you should feel bad.
	  $software 
	   └─ I uh... I wrote it myself.
	  $starterpack 
	   └─ Starterpacks.
	  $techsupport 
	   └─ Tech support irl.
	  $thinkdeep 
	   └─ Spout out some intellectual brilliance.
	  $wallpaper 
	   └─ Get something pretty to look at.
	  $withcontext 
	   └─ Spout out some contextual brilliance.

## Remind
####	Remind Cog (3 commands) - Remind.py Extension:
	  $clearmind [index]
	   └─ Clear the reminder index passed - or all if none passed.
	  $reminders [member]
	   └─ List up to 10 pending reminders - pass a user to see their reminders.
	  $remindme [message] [endtime]
	   └─ Set a reminder.  If the message contains spaces, it must be wrapped in quotes.

## Responses
####	Responses Cog (4 commands) - Responses.py Extension:
	  $addresponse [regex_trigger] [response]
	   └─ Adds a new response for the regex trigger.  If the trigger has spaces, it mus...
	  $clearresponses 
	   └─ Removes all response triggers (bot-admin only).
	  $remresponse [regex_trigger_number]
	   └─ Removes the passed response trigger (bot-admin only).
	  $responses 
	   └─ Lists the response triggers and their responses (bot-admin only).

## Search
####	Search Cog (8 commands) - Search.py Extension:
	  $aol [query]
	   └─ The OG search engine.
	  $ask [query]
	   └─ Jeeves, please answer these questions.
	  $bing [query]
	   └─ Get some uh... more searching done.
	  $convert [amount] [frm] [to]
	   └─ Convert currencies.  If run with no values, the script will print a list of a...
	  $duck [query]
	   └─ Duck Duck... GOOSE.
	  $google [query]
	   └─ Get some searching done.
	  $searchsite [category_name] [query]
	   └─ Search corpnewt.com forums.
	  $yahoo [query]
	   └─ Let Yahoo! answer your questions.

## SecretSanta
####	SecretSanta Cog (11 commands) - SecretSanta.py Extension:
	  $allowss [yes_no]
	   └─ Sets whether the Secret Santa module is enabled (owner only; always off by de...
	  $getssrole 
	   └─ Lists the current Secret Santa role.
	  $rawssmessage 
	   └─ Prints the raw markdown for the Secret Santa channel create message (bot-admi...
	  $setssmessage [message]
	   └─ Sets the Secret Santa channel create message (bot-admin only). 
	  $setssrole [role]
	   └─ Sets the Secret Santa role, or clears it if no role passed (bot-admin only).
	  $ssapplyreport [url]
	   └─ Applies the passed ss.json file's settings and gives the Secret Santa channel...
	  $sscreatechannels [category]
	   └─ Creates the private channels for all users with the Secret Santa role under t...
	  $ssgenreport [category]
	   └─ Randomly pairs users for Secret Santa and uploads a ss.json report (bot-admin...
	  $ssremovechannels [category]
	   └─ Removes all Secret Santa channels under a given category whose names correspo...
	  $ssrevert [category]
	   └─ Returns ownership of the Secret Santa channels to their original owners if fo...
	  $testssmessage 
	   └─ Prints the current Secret Santa channel create message (bot-admin only).

## Server
####	Server Cog (7 commands) - Server.py Extension:
	  $autopcpp [setting]
	   └─ Sets the bot's auto-pcpartpicker markdown if found in messages (admin-only). ...
	  $dumpservers 
	   └─ Dumps a timpestamped list of servers into the same directory as the bot (owne...
	  $getprefix 
	   └─ Output's the server's prefix - custom or otherwise.
	  $info 
	   └─ Displays the server info if any.
	  $leaveserver [targetServer]
	   └─ Leaves a server - can take a name or id (owner only).
	  $setinfo [word]
	   └─ Sets the server info (bot-admin only).
	  $setprefix [prefix]
	   └─ Sets the bot's prefix (bot-admin only).

## ServerStats
####	ServerStats Cog (15 commands) - ServerStats.py Extension:
	  $allmessages 
	   └─ Lists the number of messages I've seen on all severs so far. (only applies af...
	  $bottomservers 
	   └─ Lists the bottom servers I'm connected to ordered by population.
	  $firstjoins 
	   └─ Lists the first users to join.
	  $firstservers 
	   └─ Lists the first servers I've joined.
	  $joinedatpos <position>
	   └─ Lists the user that joined at the passed position.
	  $joinpos [member]
	   └─ Tells when a user joined compared to other users.
	  $listbots [guild_name]
	   └─ Lists up to the first 20 bots of the current or passed server.
	  $listservers 
	   └─ Lists the servers I'm connected to.
	  $messages 
	   └─ Lists the number of messages I've seen on this sever so far. (only applies af...
	  $recentjoins 
	   └─ Lists the most recent users to join.
	  $recentservers 
	   └─ Lists the most recent users to join - default is 10, max is 25.
	  $serverinfo [guild_name]
	   └─ Lists some info about the current or passed server.
	  $sharedservers [member]
	   └─ Lists how many servers you share with the bot.
	  $topservers 
	   └─ Lists the top servers I'm connected to ordered by population.
	  $users 
	   └─ Lists the total number of users on all servers I'm connected to.

## Settings
####	Settings Cog (13 commands) - Settings.py Extension:
	  $addowner [member]
	   └─ Adds an owner to the owner list.  Can only be done by a current owner.
	  $claim 
	   └─ Claims the bot if disowned - once set, can only be changed by the current owner.
	  $disown 
	   └─ Revokes all ownership of the bot.
	  $flush 
	   └─ Flush the bot settings to disk (admin only).
	  $getsstat [stat]
	   └─ Gets a server stat (admin only).
	  $getstat [stat] [member]
	   └─ Gets the value for a specific stat for the listed member (case-sensitive).
	  $ownerlock 
	   └─ Locks/unlocks the bot to only respond to the owner (owner-only... ofc).
	  $owners 
	   └─ Lists the bot's current owners.
	  $prune 
	   └─ Iterate through all members on all connected servers and remove orphaned sett...
	  $prunelocalsettings 
	   └─ Compares the current server's settings to the default list and removes any no...
	  $prunesettings 
	   └─ Compares all connected servers' settings to the default list and removes any ...
	  $remowner [member]
	   └─ Removes an owner from the owner list.  Can only be done by a current owner.
	  $setsstat [stat] [value]
	   └─ Sets a server stat (admin only).

## Setup
####	Setup Cog (1 command) - Setup.py Extension:
	  $setup 
	   └─ Runs first-time setup (server owner only).

## Spooktober
####	Spooktober Cog (1 command) - Spooktober.py Extension:
	  $spooking [yes_no]
	   └─ Enables/Disables reacting 🎃 to every sp00py message on Halloween (owner only).

## Stream
####	Stream Cog (8 commands) - Stream.py Extension:
	  $addstreamer [member]
	   └─ Adds the passed member to the streamer list (bot-admin only).
	  $rawstream [message]
	   └─ Displays the raw markdown for the stream announcement message (bot-admin only).
	  $remstreamer [member]
	   └─ Removes the passed member from the streamer list (bot-admin only).
	  $setstream [message]
	   └─ Sets the stream announcement message (bot-admin only).
	  $setstreamchannel [channel]
	   └─ Sets the channel for the stream announcements (bot-admin only).
	  $streamchannel 
	   └─ Displays the channel for the stream announcements - if any.
	  $streamers 
	   └─ Lists the current members in the streamer list.
	  $teststream [message]
	   └─ Tests the stream announcement message (bot-admin only).

## Strike
####	Strike Cog (12 commands) - Strike.py Extension:
	  $addban [member]
	   └─ Adds the passed user to the ban list (bot-admin only).
	  $addkick [member]
	   └─ Adds the passed user to the kick list (bot-admin only).
	  $isbanned [member]
	   └─ Lists whether the user is in the ban list.
	  $iskicked [member]
	   └─ Lists whether the user is in the kick list.
	  $removeban [member]
	   └─ Removes the passed user from the ban list (bot-admin only).
	  $removekick [member]
	   └─ Removes the passed user from the kick list (bot-admin only).
	  $removestrike [member]
	   └─ Removes a strike given to a member (bot-admin only).
	  $setstrikelevel [member] [strikelevel]
	   └─ Sets the strike level of the passed user (bot-admin only).
	  $setstrikelimit [limit]
	   └─ Sets the number of strikes before advancing to the next consequence (bot-admi...
	  $strike [member] [days] [message]
	   └─ Give a user a strike (bot-admin only).
	  $strikelimit 
	   └─ Lists the number of strikes before advancing to the next consequence.
	  $strikes [member]
	   └─ Check a your own, or another user's total strikes (bot-admin needed to check ...

## Telephone
####	Telephone Cog (10 commands) - Telephone.py Extension:
	  $call [number]
	   └─ Calls the passed number.  Can use *67 to hide your identity - or *69 to conne...
	  $callerid 
	   └─ Reveals the last number to call regardless of *67 settings (bot-admin only).
	  $phonebook [look_up]
	   └─ Lets you page through the phonebook - or optionally lets you search for a ser...
	  $settelechannel [channel]
	   └─ Sets the channel for telephone commands - or disables that if nothing is pass...
	  $teleblock [guild_name]
	   └─ Blocks all tele-numbers associated with the passed guild (bot-admin only).
	  $teleblocklinks [yes_no]
	   └─ Enables/Disables removing links sent over telephone calls (bot-admin only).
	  $teleblocks 
	   └─ Lists guilds with blocked tele-numbers.
	  $telechannel 
	   └─ Prints the current channel for telephone commands.
	  $telenumber 
	   └─ Prints your telephone number.
	  $teleunblock [guild_name]
	   └─ Unblocks all tele-numbers associated with the passed guild (bot-admin only).

## TempRole
####	TempRole Cog (10 commands) - TempRole.py Extension:
	  $addtemprole [role]
	   └─ Adds a new role to the temp role list (admin only).
	  $autotemp [role]
	   └─ Sets the temp role to apply to each new user that joins.
	  $getautotemp 
	   └─ Gets the temp role applied to each new user that joins.
	  $hastemp [member]
	   └─ Displays any temp roles the passed user has, and the remaining time.
	  $listtemproles 
	   └─ Lists all roles for the temp role system.
	  $removetemprole [role]
	   └─ Removes a role from the temp role list (admin only).
	  $temp [member] [role] [cooldown]
	   └─ Gives the passed member the temporary role for the passed amount of time - ne...
	  $temppm [yes_no]
	   └─ Sets whether to inform users that they've been given a temp role.
	  $temptime [minutes]
	   └─ Sets the number of minutes for the temp role - must be greater than 0 (admin-...
	  $untemp [member] [role]
	   └─ Removes the passed temp role from the passed user (bot-admin only).

## Time
####	Time Cog (6 commands) - Time.py Extension:
	  $listtz [tz_search]
	   └─ List all the supported TimeZones in PM.
	  $offset [member]
	   └─ See a member's UTC offset.
	  $setoffset [offset]
	   └─ Set your UTC offset.
	  $settz [tz]
	   └─ Sets your TimeZone - Overrides your UTC offset - and accounts for DST.
	  $time [offset]
	   └─ Get UTC time +- an offset.
	  $tz [member]
	   └─ See a member's TimeZone.

## Translate
####	Translate Cog (3 commands) - Translate.py Extension:
	  $detectlang <text>
	   └─ Reports the detected language and certainty of the passed text.
	  $langlist 
	   └─ Lists available languages.
	  $tr [translate]
	   └─ Translate some stuff!  Takes a phrase, the from language identifier (optional...

## Turret
####	Turret Cog (1 command) - Turret.py Extension:
	  $turret 
	   └─ Now you're thinking with - wait... uh.. turrets?

## Uptime
####	Uptime Cog (1 command) - Uptime.py Extension:
	  $uptime 
	   └─ Lists the bot's uptime.

## UrbanDict
####	UrbanDict Cog (2 commands) - UrbanDict.py Extension:
	  $define [word]
	   └─ Gives the definition of the word passed.
	  $randefine 
	   └─ Gives a random word and its definition.

## UserRole
####	UserRole Cog (17 commands) - UserRole.py Extension:
	  $addrole [role]
	   └─ Adds a role from the user role list to your roles.  You can have multiples at...
	  $adduserrole [role]
	   └─ Adds a new role to the user role system (admin only).
	  $clearroles 
	   └─ Removes all user roles from your roles.
	  $isurblocked [member]
	   └─ Outputs whether or not the passed user is blocked from the UserRole module.
	  $listuserroles 
	   └─ Lists all roles for the user role system.
	  $oneuserrole [yes_no]
	   └─ Turns on/off one user role at a time (bot-admin only; always on by default).
	  $removeuserrole [role]
	   └─ Removes a role from the user role system (admin only).
	  $remrole [role]
	   └─ Removes a role from the user role list from your roles.
	  $rradd [role_name_or_id]
	   └─ Adds a new role to the reaction roles list.
	  $rrclear 
	   └─ Removes the message to watch for user reaction roles, as well as all roles an...
	  $rrdel [role_name_or_id]
	   └─ Removes the passed role from the reaction roles list (bot-admin only).
	  $rrlist 
	   └─ Lists the current reaction roles and their corresponding reactions (bot-admin...
	  $rrmessage [message_url]
	   └─ Gets or sets the message to watch for user reaction roles (bot-admin only).
	  $rrtoggle [yes_no]
	   └─ Sets whether or not reaction messages will toggle roles - or only add them (b...
	  $setrole [role]
	   └─ Sets your role from the user role list.  You can only have one at a time.
	  $urblock [member]
	   └─ Blocks a user from using the UserRole system and removes applicable roles (bo...
	  $urunblock [member]
	   └─ Unblocks a user from the UserRole system (bot-admin only).

## VoteKick
####	VoteKick Cog (13 commands) - VoteKick.py Extension:
	  $setvkchannel [channel]
	   └─ Sets which channel then mention posts to when enough votes against a user are...
	  $setvkmention [user_or_role]
	   └─ Sets which user or role is mentioned when enough votes against a user are rea...
	  $vk [user] [server]
	   └─ Places your vote to have the passed user kicked.
	  $vkanon [yes_no]
	   └─ Sets whether vote messages are removed after voting (bot-admin only; always o...
	  $vkchannel 
	   └─ Gets which channel then mention posts to when enough votes against a user are...
	  $vkclear [user]
	   └─ Clears the votes against the passed user (bot-admin only).
	  $vkexpiretime [the_time]
	   └─ Sets the amount of time before a vote expires.  0 or less will make them perm...
	  $vkinfo 
	   └─ Lists the vote-kick info.
	  $vkmention 
	   └─ Gets which user or role is mentioned when enough votes against a user are rea...
	  $vkmutetime [the_time]
	   └─ Sets the number of time a user is muted when the mute votes are reached - 0 o...
	  $vks [user]
	   └─ Lists the vote count of the passed user (bot-admin only) or the author if no ...
	  $vktomention [number_of_votes]
	   └─ Sets the number of votes before the selected role or user is mentioned.  Anyt...
	  $vktomute [number_of_votes]
	   └─ Sets the number of votes before a user is muted.  Anything less than 1 will d...

## WatchURL
####	WatchURL Cog (7 commands) - WatchURL.py Extension:
	  $addwatchurl [url]
	   └─ Adds a new URL to watch for (bot-admin only).
	  $clearwatchedurls 
	   └─ Clears all URLs to watch for (bot-admin only).
	  $clearwatchurlmatches 
	   └─ Clears all URL watch list matches (bot-admin only).
	  $delwatchurl [url]
	   └─ Removes a URL from the watch list (bot-admin only).
	  $lasturls 
	   └─ Shows up to the last 200 URLs sent that matched the URL watch lists in order ...
	  $listwatchurls 
	   └─ Lists the URLs to watch for in passed messages.
	  $watchboturls [yes_no]
	   └─ Sets whether we watch for URLs from other bots (bot-admin only - disabled by ...

## Weather
####	Weather Cog (3 commands) - Weather.py Extension:
	  $forecast [city_name]
	   └─ Gets some weather, for 5 days or whatever.
	  $tconvert [temp] [from_type] [to_type]
	   └─ Converts between Fahrenheit, Celsius, and Kelvin.  From/To types can be:
	  $weather [city_name]
	   └─ Gets some weather.

## Welcome
####	Welcome Cog (7 commands) - Welcome.py Extension:
	  $rawgoodbye [member]
	   └─ Prints the current goodbye message's markdown (bot-admin only).
	  $rawwelcome [member]
	   └─ Prints the current welcome message's markdown (bot-admin only).
	  $setgoodbye [message]
	   └─ Sets the goodbye message for your server (bot-admin only).
	  $setwelcome [message]
	   └─ Sets the welcome message for your server (bot-admin only). 
	  $setwelcomechannel [channel]
	   └─ Sets the channel for the welcome and goodbye messages (bot-admin only).
	  $testgoodbye [member]
	   └─ Prints the current goodbye message (bot-admin only).
	  $testwelcome [member]
	   └─ Prints the current welcome message (bot-admin only).

## Wiki
####	Wiki Cog (1 command) - Wiki.py Extension:
	  $wiki [search]
	   └─ Search Wikipedia!

## Xp
####	Xp Cog (11 commands) - Xp.py Extension:
	  $bottomxp [total=10]
	   └─ List the bottom xp-holders (max of 50).
	  $defaultrole 
	   └─ Lists the default role that new users are assigned.
	  $gamble [bet]
	   └─ Gamble your xp reserves for a chance at winning xp!
	  $leaderboard [total=10]
	   └─ List the top xp-holders (max of 50).
	  $listxproles 
	   └─ Lists all roles, id's, and xp requirements for the xp promotion/demotion system.
	  $rank [member]
	   └─ Say the highest rank of a listed member.
	  $recheckrole [user]
	   └─ Re-iterate through all members and assign the proper roles based on their xp ...
	  $recheckroles 
	   └─ Re-iterate through all members and assign the proper roles based on their xp ...
	  $stats [member]
	   └─ List the xp and xp reserve of a listed member.
	  $xp [member] [xpAmount]
	   └─ Gift xp to other members.
	  $xpinfo 
	   └─ Gives a quick rundown of the xp system.

## XpBlock
####	XpBlock Cog (4 commands) - XpBlock.py Extension:
	  $listxpblock 
	   └─ Lists xp blocked users and roles.
	  $xpblock [user_or_role]
	   └─ Adds a new user or role to the xp block list (bot-admin only).
	  $xpunblock [user_or_role]
	   └─ Removes a user or role from the xp block list (bot-admin only).
	  $xpunblockall 
	   └─ Removes all users and roles from the xp block list (bot-admin only).

## XpStack
####	XpStack Cog (5 commands) - XpStack.py Extension:
	  $checkxp 
	   └─ Displays the last xp transactions (bot-admin only).
	  $clearallxp 
	   └─ Clears all xp transactions from the transaction list for all servers (owner-o...
	  $clearxp 
	   └─ Clears the xp transaction list (bot-admin only).
	  $setxpcount [count]
	   └─ Sets the number of xp transactions to keep (default is 10).
	  $xpcount [count]
	   └─ Returns the number of xp transactions to keep (default is 10).
