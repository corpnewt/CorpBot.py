# CorpBot.py
A *slightly* less clumsy python bot for discord

A list of cogs, commands, and descriptions:

	Admin Cog (26 commands) - Admin.py Extension:
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

	Ascii Cog (1 command) - Ascii.py Extension:
	  $ascii [text]
	   └─ Beautify some text (font list at http://artii.herokuapp.com/fonts_list).

	Bot Cog (27 commands) - Bot.py Extension:
	  $adminunlim [yes_no]
	   └─ Sets whether or not to allow unlimited xp to admins (owner only).
	  $avatar [filename]
	   └─ Sets the bot's avatar (owner only).
	  $basadmin [yes_no]
	   └─ Sets whether or not to treat bot-admins as admins with regards to xp (admin o...
	  $block [server]
	   └─ Blocks the bot from joining a server - takes either a name or an id (owner-on...
	  $blocked
	   └─ Lists all blocked servers and owners (owner-only).
	  $botinfo
	   └─ Lists some general stats about the bot.
	  $cloc
	   └─ Outputs the total count of lines of code in the currently installed repo.
	  $embed [embed_type=field] <embed>
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
	  $unblock [server]
	   └─ Unblocks a server or owner (owner-only).
	  $unblockall
	   └─ Unblocks all blocked servers and owners (owner-only).
	  $watchgame [game]
	   └─ Sets the watching status of the bot (owner-only).

	BotAdmin Cog (8 commands) - BotAdmin.py Extension:
	  $ban [member]
	   └─ Bans the selected member (bot-admin only).
	  $ignore [member]
	   └─ Adds a member to the bot's "ignore" list (bot-admin only).
	  $ignored
	   └─ Lists the users currently being ignored.
	  $kick [member]
	   └─ Kicks the selected member (bot-admin only).
	  $listen [member]
	   └─ Removes a member from the bot's "ignore" list (bot-admin only).
	  $mute [member] [cooldown]
	   └─ Prevents a member from sending messages in chat (bot-admin only).
	  $setuserparts [member] [parts]
	   └─ Set another user's parts list (owner only).
	  $unmute [member]
	   └─ Allows a muted member to send messages in chat (bot-admin only).

	Calc Cog (1 command) - Calc.py Extension:
	  $calc [formula]
	   └─ Do some math.

	CardsAgainstHumanity Cog (17 commands) - CardsAgainstHumanity.py Extension:
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

	Cats Cog (1 command) - Cats.py Extension:
	  $randomcat
	   └─ Meow.

	Channel Cog (7 commands) - Channel.py Extension:
	  $islocked
	   └─ Says whether the bot only responds to admins.
	  $ismuted [member]
	   └─ Says whether a member is muted in chat.
	  $listadmin
	   └─ Lists admin roles and id's.
	  $listmuted
	   └─ Lists the names of those that are muted.
	  $log [messages=25] [chan]
	   └─ Logs the passed number of messages from the given channel - 25 by default (ad...
	  $rolecall [role]
	   └─ Lists the number of users in a current role.
	  $rules
	   └─ Display the server's rules.

	ChatterBot Cog (2 commands) - ChatterBot.py Extension:
	  $chat [message]
	   └─ Chats with the bot.
	  $setchatchannel [channel]
	   └─ Sets the channel for bot chatter.

	CogManager Cog (5 commands) - CogManager.py Extension:
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

	Comic Cog (14 commands) - Comic.py Extension:
	  $calvin [date]
	   └─ Displays the Calvin & Hobbes comic for the passed date (MM-DD-YYYY) if found.
	  $cyanide [date]
	   └─ Displays the Cyanide & Happiness comic for the passed date (MM-DD-YYYY) if fo...
	  $dilbert [date]
	   └─ Displays the Dilbert comic for the passed date (MM-DD-YYYY).
	  $garfield [date]
	   └─ Displays the Garfield comic for the passed date (MM-DD-YYYY) if found.
	  $gmg [date]
	   └─ Displays the Garfield Minus Garfield comic for the passed date (MM-DD-YYYY) i...
	  $peanuts [date]
	   └─ Displays the Peanuts comic for the passed date (MM-DD-YYYY) if found.
	  $randcalvin
	   └─ Randomly picks and displays a Calvin & Hobbes comic.
	  $randcyanide
	   └─ Randomly picks and displays a Cyanide & Happiness comic.
	  $randgarfield
	   └─ Randomly picks and displays a Garfield comic.
	  $randgmg
	   └─ Randomly picks and displays a Garfield Minus Garfield comic.
	  $randilbert
	   └─ Randomly picks and displays a Dilbert comic.
	  $randpeanuts
	   └─ Randomly picks and displays a Peanuts comic.
	  $randxkcd
	   └─ Displays a random XKCD comic.
	  $xkcd [date]
	   └─ Displays the XKCD comic for the passed date (MM-DD-YYYY) or comic number if f...

	DJRoles Cog (4 commands) - DJRoles.py Extension:
	  $adddj [role]
	   └─ Adds a new role to the dj list (bot-admin only).
	  $listdj
	   └─ Lists dj roles and id's.
	  $removedj [role]
	   └─ Removes a role from the dj list (bot-admin only).
	  $ytlist [yes_no]
	   └─ Gets or sets whether or not the server will show a list of options when searc...

	Debugging Cog (9 commands) - Debugging.py Extension:
	  $clean [messages=100] [chan]
	   └─ Cleans the passed number of messages from the given channel - 100 by default ...
	  $cleardebug
	   └─ Deletes the debug.txt file (owner only).
	  $heartbeat
	   └─ Write to the console and attempt to send a message (owner only).
	  $logdisable [options]
	   └─ Disables the passed, comma-delimited log vars.
	  $logenable [options]
	   └─ Enables the passed, comma-delimited log vars.
	  $logging
	   └─ Outputs whether or not we're logging is enabled (bot-admin only).
	  $logpreset [preset]
	   └─ Can select one of 3 available presets - quiet, normal, verbose (bot-admin only).
	  $setdebug [debug]
	   └─ Turns on/off debugging (owner only - always off by default).
	  $setlogchannel [channel]
	   └─ Sets the channel for Logging (bot-admin only).

	DisableCommand Cog (9 commands) - DisableCommand.py Extension:
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

	DrBeer Cog (1 command) - DrBeer.py Extension:
	  $drbeer
	   └─ Put yourself in your place.

	Eat Cog (1 command) - Eat.py Extension:
	  $eat [member]
	   └─ Eat like a boss.

	EightBall Cog (1 command) - EightBall.py Extension:
	  $eightball [question]
	   └─ Get some answers.

	Encode Cog (7 commands) - Encode.py Extension:
	  $binint [input_binary]
	   └─ Converts the input binary to its integer representation.
	  $binstr [input_binary]
	   └─ Converts the input binary to its string representation.
	  $dechex [input_dec]
	   └─ Converts an int to hex.
	  $encode [value] [from_type] [to_type]
	   └─ Data converter from ascii <--> hex <--> base64.
	  $hexdec [input_hex]
	   └─ Converts hex to decimal.
	  $intbin [input_int]
	   └─ Converts the input integer to its binary representation.
	  $strbin [input_string]
	   └─ Converts the input string to its binary representation.

	Example Cog (4 commands) - Example.py Extension:
	  $add <left> <right>
	   └─ Adds two numbers together.
	  $choose [choices...]
	   └─ Chooses between multiple choices.
	  $joined [member]
	   └─ Says when a member joined.
	  $roll [dice=1d20]
	   └─ Rolls a dice in NdN±Na/d format.

	Face Cog (4 commands) - Face.py Extension:
	  $lastlenny
	   └─ Who Lenny'ed last?
	  $lastshrug
	   └─ Who shrugged last?
	  $lenny [message]
	   └─ Give me some Lenny.
	  $shrug [message]
	   └─ Shrug it off.

	Feed Cog (8 commands) - Feed.py Extension:
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
	   └─ Sets the required role ID to add/remove hacks (admin only).

	Fliptime Cog (1 command) - Fliptime.py Extension:
	  $tableflip [yes_no]
	   └─ Turns on/off table flip muting (bot-admin only; always off by default).

	Giphy Cog (4 commands) - Giphy.py Extension:
	  $addgif [role]
	   └─ Adds a new role to the gif list (admin only).
	  $gif [gif]
	   └─ Search for some giphy!
	  $listgif
	   └─ Lists gif roles and id's.
	  $removegif [role]
	   └─ Removes a role from the gif list (admin only).

	Help Cog (1 command) - Help.py Extension:
	  $dumphelp [tab_indent_count]
	   └─ Dumps a timpestamped, formatted list of commands and descriptions into the sa...
	  $help [command]
	   └─ Lists the bot's commands and cogs.

	HighFive Cog (1 command) - HighFive.py Extension:
	  $highfive [member]
	   └─ It's like clapping with 2 people!

	Humor Cog (6 commands) - Humor.py Extension:
	  $fart
	   └─ PrincessZoey :P
	  $french
	   └─ Speaking French... probably...
	  $holy [subject]
	   └─ Time to backup the Batman!
	  $meme [template_id] [text_zero] [text_one]
	   └─ Generate Meme
	  $memetemps
	   └─ Get Meme Templates
	  $zalgo [message]
	   └─ Ỉ s̰hͨo̹u̳lͪd͆ r͈͍e͓̬a͓͜lͨ̈l̘̇y̡͟ h͚͆a̵͢v͐͑eͦ̓ i͋̍̕n̵̰ͤs͖̟̟t͔ͤ̉ǎ͓͐ḻ̪ͨl̦͒̂e...

	Hw Cog (12 commands) - Hw.py Extension:
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
	   └─ Initiate a new-hardware conversation with the bot.
	  $pcpp [url] [style] [escape]
	   └─ Convert a pcpartpicker.com link into markdown parts. Available styles: normal...
	  $rawhw [user] [build]
	   └─ Lists the raw markdown for either the user's default build - or the passed bu...
	  $renhw [build]
	   └─ Renames a build from your build list.
	  $sethwchannel [channel]
	   └─ Sets the channel for hardware (admin only).

	Invite Cog (1 command) - Invite.py Extension:
	  $invite
	   └─ Outputs a url you can use to invite me to your server.

	Jpeg Cog (1 command) - Jpeg.py Extension:
	  $jpeg [url]
	   └─ MOAR JPEG!  Accepts a url - or picks the first attachment.

	LangFilter Cog (5 commands) - LangFilter.py Extension:
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

	Lists Cog (22 commands) - Lists.py Extension:
	  $addhack [name] [hack]
	   └─ Add a hack to the hack list.
	  $addlink [name] [link]
	   └─ Add a link to the link list.
	  $hack [name]
	   └─ Retrieve a hack from the hack list.
	  $hackinfo [name]
	   └─ Displays info about a hack from the hack list.
	  $hackrole
	   └─ Lists the required role to add hacks.
	  $hacks
	   └─ List all hacks in the hack list.
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
	  $removehack [name]
	   └─ Remove a hack from the hack list.
	  $removelink [name]
	   └─ Remove a link from the link list.
	  $setparts [parts]
	   └─ Set your own parts - can be a url, formatted text, or nothing to clear. DEPRE...

	MadLibs Cog (1 command) - MadLibs.py Extension:
	  $madlibs
	   └─ Let's play MadLibs!

	Morse Cog (3 commands) - Morse.py Extension:
	  $morse [content]
	   └─ Converts ascii to morse code.  Accepts a-z and 0-9.  Each letter is comprised...
	  $morsetable [num_per_row]
	   └─ Prints out the morse code lookup table.
	  $unmorse [content]
	   └─ Converts morse code to ascii.  Each letter is comprised of "-" or "." and sep...

	Music Cog (21 commands) - Example.py Extension:
	  $join [channel]
	   └─ Joins a voice channel.
	  $keep
	   └─ Vote to keep a song.
	  $pause
	   └─ Pauses the currently played song.
	  $pdelay [delay]
	   └─ Sets the delay in seconds between loading songs in playlist (owner only).
	  $play [song]
	   └─ Plays a song.
	  $playing
	   └─ Shows info about currently playing.
	  $playingin
	   └─ Shows the number of servers the bot is currently playing music in.
	  $playlist
	   └─ Shows current songs in the playlist.
	  $plevel [level]
	   └─ Sets the access level for playlists (owner only):
	  $pmax [max_songs]
	   └─ Sets the maximum number of songs to load from a playlist (owner only).
	  $pskip
	   └─ Skips loading the rest of a playlist - can only be done by the requestor, or ...
	  $removesong [idx]
	   └─ Removes a song in the playlist by the index.
	  $repeat [yes_no]
	   └─ Checks or sets whether to repeat or not.
	  $resume
	   └─ Resumes the currently played song.
	  $skip
	   └─ Vote to skip a song. The song requester can automatically skip.
	  $stop
	   └─ Stops playing audio and leaves the voice channel.
	  $summon
	   └─ Summons the bot to join your voice channel.
	  $unvote
	   └─ Remove your song vote.
	  $volume [value]
	   └─ Sets the volume of the currently playing song.
	  $vote_stats
	   └─ Help not available...
	  $willrepeat
	   └─ Displays whether or not repeat is active.

	OfflineUser Cog (1 command) - OfflineUser.py Extension:
	  $remindoffline [yes_no]
	   └─ Sets whether to inform users that pinged members are offline or not.

	Plist Cog (1 command) - Plist.py Extension:
	  $plist [url]
	   └─ Validates plist file structure.  Accepts a url - or picks the first attachment.

	Printer Cog (2 commands) - Printer.py Extension:
	  $print [url]
	   └─ DOT MATRIX.  Accepts a url - or picks the first attachment.
	  $printavi [member]
	   └─ Returns a url to the passed member's avatar.

	Profile Cog (7 commands) - Profile.py Extension:
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

	Promote Cog (4 commands) - Promote.py Extension:
	  $demote [member]
	   └─ Auto-removes the required xp to demote the passed user to the previous role (...
	  $demoteto [member] [role]
	   └─ Auto-removes the required xp to demote the passed user to the passed role (ad...
	  $promote [member]
	   └─ Auto-adds the required xp to promote the passed user to the next role (admin ...
	  $promoteto [member] [role]
	   └─ Auto-adds the required xp to promote the passed user to the passed role (admi...

	RateLimit Cog (1 command) - RateLimit.py Extension:
	  $ccooldown [delay]
	   └─ Sets the cooldown in seconds between each command (owner only).

	Reddit Cog (30 commands) - Reddit.py Extension:
	  $abandoned
	   └─ Get something abandoned to look at.
	  $answer
	   └─ Spout out some interstellar answering... ?
	  $aww
	   └─ Whenever you're down - uppify.
	  $battlestation
	   └─ Let's look at some pretty stuff.
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

	Remind Cog (3 commands) - Remind.py Extension:
	  $clearmind [index]
	   └─ Clear the reminder index passed - or all if none passed.
	  $reminders [member]
	   └─ List up to 10 pending reminders - pass a user to see their reminders.
	  $remindme [message] [endtime]
	   └─ Set a reminder.

	Search Cog (5 commands) - Search.py Extension:
	  $bing [query]
	   └─ Get some uh... more searching done.
	  $convert [amount] [frm] [to]
	   └─ convert currencies
	  $duck [query]
	   └─ Duck Duck... GOOSE.
	  $google [query]
	   └─ Get some searching done.
	  $searchsite [category_name] [query]
	   └─ Search corpnewt.com forums.

	Server Cog (7 commands) - Server.py Extension:
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
	   └─ Sets the server info (admin only).
	  $setprefix [prefix]
	   └─ Sets the bot's prefix (admin only).

	ServerStats Cog (13 commands) - ServerStats.py Extension:
	  $allmessages
	   └─ Lists the number of messages I've seen on all severs so far. (only applies af...
	  $bottomservers [number=10]
	   └─ Lists the bottom servers I'm connected to ordered by population - default is ...
	  $firstjoins [number=10]
	   └─ Lists the first users to join - default is 10, max is 25.
	  $firstservers [number=10]
	   └─ Lists the first servers I've joined - default is 10, max is 25.
	  $joinpos [member]
	   └─ Tells when a user joined compared to other users.
	  $listservers [number=10]
	   └─ Lists the servers I'm connected to - default is 10, max is 50.
	  $messages
	   └─ Lists the number of messages I've seen on this sever so far. (only applies af...
	  $recentjoins [number=10]
	   └─ Lists the most recent users to join - default is 10, max is 25.
	  $recentservers [number=10]
	   └─ Lists the most recent users to join - default is 10, max is 25.
	  $serverinfo [guild_name]
	   └─ Lists some info about the current or passed server.
	  $sharedservers [member]
	   └─ Lists how many servers you share with the bot.
	  $topservers [number=10]
	   └─ Lists the top servers I'm connected to ordered by population - default is 10,...
	  $users
	   └─ Lists the total number of users on all servers I'm connected to.

	Settings Cog (14 commands) - Settings.py Extension:
	  $addowner [member]
	   └─ Adds an owner to the owner list.  Can only be done by a current owner.
	  $claim
	   └─ Claims the bot if disowned - once set, can only be changed by the current owner.
	  $disown
	   └─ Revokes all ownership of the bot.
	  $dumpsettings
	   └─ Sends the Settings.json file to the owner.
	  $flush
	   └─ Flush the bot settings to disk (admin only).
	  $getsstat [stat]
	   └─ Gets a server stat (admin only).
	  $getstat [stat] [member]
	   └─ Gets the value for a specific stat for the listed member (case-sensitive).
	  $ownerlock
	   └─ Locks/unlocks the bot to only respond to the owner.
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

	Setup Cog (1 command) - Setup.py Extension:
	  $setup
	   └─ Runs first-time setup (server owner only).

	Strike Cog (12 commands) - Strike.py Extension:
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

	Tags Cog (9 commands) - Tags.py Extension:
	  $addtag [name] [tag]
	   └─ Add a tag to the tag list.
	  $rawtag [name]
	   └─ Retrieve a tag's raw markdown from the tag list.
	  $rawtags
	   └─ List raw markdown of all tags in the tags list.
	  $removetag [name]
	   └─ Remove a tag from the tag list.
	  $settagrole [role]
	   └─ Sets the required role ID to add/remove tags (admin only).
	  $tag [name]
	   └─ Retrieve a tag from the tag list.
	  $taginfo [name]
	   └─ Displays info about a tag from the tag list.
	  $tagrole
	   └─ Lists the required role to add tags.
	  $tags
	   └─ List all tags in the tags list.

	Telephone Cog (8 commands) - Telephone.py Extension:
	  $call [number]
	   └─ Calls the passed number.  Can use *67 to hide your identity - or *69 to conne...
	  $phonebook [look_up]
	   └─ Displays up to 20 entries in the phone book - or optionally lets you search f...
	  $settelechannel [channel]
	   └─ Sets the channel for telephone commands - or disables that if nothing is pass...
	  $teleblock [guild_name]
	   └─ Blocks all tele-numbers associated with the passed guild (bot-admin only).
	  $teleblocks
	   └─ Lists guilds with blocked tele-numbers.
	  $telechannel
	   └─ Prints the current channel for telephone commands.
	  $telenumber
	   └─ Prints your telephone number.
	  $teleunblock [guild_name]
	   └─ Unblocks all tele-numbers associated with the passed guild (bot-admin only).

	TempRole Cog (9 commands) - TempRole.py Extension:
	  $addtemprole [role]
	   └─ Adds a new role to the temp role list (admin only).
	  $autotemp [role]
	   └─ Sets the temp role to apply to each new user that joins.
	  $getautotemp
	   └─ Gets the temp role applied to each new user that joins.
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

	Time Cog (6 commands) - Time.py Extension:
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

	Translate Cog (2 commands) - Translate.py Extension:
	  $langlist
	   └─ Lists available languages.
	  $tr [translate]
	   └─ Translate some stuff!

	Uptime Cog (1 command) - Uptime.py Extension:
	  $uptime
	   └─ Lists the bot's uptime.

	UrbanDict Cog (2 commands) - UrbanDict.py Extension:
	  $define [word]
	   └─ Gives the definition of the word passed.
	  $randefine
	   └─ Gives a random word and its definition.

	UserRole Cog (7 commands) - UserRole.py Extension:
	  $addrole [role]
	   └─ Adds a role from the user role list to your roles.  You can have multiples at...
	  $adduserrole [role]
	   └─ Adds a new role to the user role system (admin only).
	  $listuserroles
	   └─ Lists all roles for the user role system.
	  $oneuserrole [on_off]
	   └─ Turns on/off one user role at a time (bot-admin only; always on by default).
	  $removeuserrole [role]
	   └─ Removes a role from the user role system (admin only).
	  $remrole [role]
	   └─ Removes a role from the user role list from your roles.
	  $setrole [role]
	   └─ Sets your role from the user role list.  You can only have one at a time.

	VoteKick Cog (13 commands) - VoteKick.py Extension:
	  $setvkchannel [channel]
	   └─ Sets which channel then mention posts to when enough votes against a user are...
	  $setvkmention [user_or_role]
	   └─ Sets which user or role is mentioned when enough votes against a user are rea...
	  $vk [user]
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

	Weather Cog (1 command) - Weather.py Extension:
	  $forecast [city_name]
	   └─ Gets some weather.

	Welcome Cog (7 commands) - Welcome.py Extension:
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

	Wiki Cog (1 command) - Wiki.py Extension:
	  $wiki [search]
	   └─ Search Wikipedia!

	Xp Cog (11 commands) - Xp.py Extension:
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

	XpBlock Cog (4 commands) - XpBlock.py Extension:
	  $listxpblock
	   └─ Lists xp blocked users and roles.
	  $xpblock [user_or_role]
	   └─ Adds a new user or role to the xp block list (bot-admin only).
	  $xpunblock [user_or_role]
	   └─ Removes a user or role from the xp block list (bot-admin only).
	  $xpunblockall
	   └─ Removes all users and roles from the xp block list (bot-admin only).

	XpStack Cog (5 commands) - XpStack.py Extension:
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
