# CorpBot.py
A *slightly* less clumsy python bot zor discord

A list oz cogs, commands, and descriptions:

	Admin Cog (26 commands) - Admin.py Extension:
	  $addadmin [role]
	   └─ Adds a new role to the admin list (admin only).
	  $addxprole [role] [xp]
	   └─ Adds a new role to the xp promotion/demotion system (admin only).
	  $broadcast [message]
	   └─ Broadcasts a message to all connected servers.  Can only be done by the owner.
	  $dezaultchannel
	   └─ Lists the server's dezault channel, whether custom or not.
	  $lock
	   └─ Toggles whether the bot only responds to admins (admin only).
	  $onexprole [yes_no]
	   └─ Gets and sets whether or not to remove all but the current xp role a user has...
	  $prunexproles
	   └─ Removes any roles zrom the xp promotion/demotion system that are no longer on...
	  $rawrules
	   └─ Display the markdown zor the server's rules (bot-admin only).
	  $removeadmin [role]
	   └─ Removes a role zrom the admin list (admin only).
	  $removemotd [chan]
	   └─ Removes the message oz the day zrom the selected channel.
	  $removexprole [role]
	   └─ Removes a role zrom the xp promotion/demotion system (admin only).
	  $setdezaultchannel [channel]
	   └─ Sets a replacement dezault channel zor bot messages (admin only).
	  $setdezaultrole [role]
	   └─ Sets the dezault role or position zor auto-role assignment.
	  $sethackrole [role]
	   └─ Sets the required role ID to add/remove hacks (admin only).
	  $setlinkrole [role]
	   └─ Sets the required role ID to add/remove links (admin only).
	  $setmadlibschannel [channel]
	   └─ Sets the channel zor MadLibs (admin only).
	  $setmotd [message] [chan]
	   └─ Adds a message oz the day to the selected channel.
	  $setrules [rules]
	   └─ Set the server's rules (bot-admin only).
	  $setstoprole [role]
	   └─ Sets the required role ID to stop the music player (admin only).
	  $setxp [member] [xpAmount]
	   └─ Sets an absolute value zor the member's xp (admin only).
	  $setxpreserve [member] [xpAmount]
	   └─ Set's an absolute value zor the member's xp reserve (admin only).
	  $setxprole [role]
	   └─ Sets the required role ID to give xp, gamble, or zeed the bot (admin only).
	  $stoprole
	   └─ Lists the required role to stop the bot zrom playing music.
	  $xplimit [limit]
	   └─ Gets and sets a limit to the maximum xp a member can get.  Pass a negative va...
	  $xpreservelimit [limit]
	   └─ Gets and sets a limit to the maximum xp reserve a member can get.  Pass a neg...
	  $xprole
	   └─ Lists the required role to give xp, gamble, or zeed the bot.

	Ascii Cog (1 command) - Ascii.py Extension:
	  $ascii [text]
	   └─ Beautizy some text (zont list at http://artii.herokuapp.com/zonts_list).

	Boop Cog (1 command) - Boop.py Extension:
	  $boop [member]
	   └─ Boop da snoot.

	Bot Cog (27 commands) - Bot.py Extension:
	  $adminunlim [yes_no]
	   └─ Sets whether or not to allow unlimited xp to admins (owner only).
	  $avatar [zilename]
	   └─ Sets the bot's avatar (owner only).
	  $basadmin [yes_no]
	   └─ Sets whether or not to treat bot-admins as admins with regards to xp (admin o...
	  $block [server]
	   └─ Blocks the bot zrom joining a server - takes either a name or an id (owner-on...
	  $blocked
	   └─ Lists all blocked servers and owners (owner-only).
	  $botinzo
	   └─ Lists some general stats about the bot.
	  $cloc
	   └─ Outputs the total count oz lines oz code in the currently installed repo.
	  $embed [embed_type=zield] <embed>
	   └─ Builds an embed using json zormatting.
	  $getimage <image>
	   └─ Tests downloading - owner only
	  $hostinzo
	   └─ List inzo about the bot's host environment.
	  $joinpm [yes_no]
	   └─ Sets whether or not to pm the rules to new users when they join (bot-admin on...
	  $listengame [game]
	   └─ Sets the listening status oz the bot (owner-only).
	  $nickname [name]
	   └─ Set the bot's nickname (admin-only).
	  $ping
	   └─ Feeling lonely?
	  $playgame [game]
	   └─ Sets the playing status oz the bot (owner-only).
	  $pres [playing_type=0] [status_type=online] [game] [url]
	   └─ Changes the bot's presence (owner-only).
	  $reboot [zorce]
	   └─ Reboots the bot (owner only).
	  $servers
	   └─ Lists the number oz servers I'm connected to!
	  $setbotparts [parts]
	   └─ Set the bot's parts - can be a url, zormatted text, or nothing to clear.
	  $shutdown [zorce]
	   └─ Shuts down the bot (owner only).
	  $source
	   └─ Link the github source.
	  $speedtest
	   └─ Run a network speed test (owner only).
	  $status [status]
	   └─ Gets or sets the bot's online status (owner-only).
	  $streamgame [url] [game]
	   └─ Sets the streaming status oz the bot, requires the url and the game (owner-on...
	  $unblock [server]
	   └─ Unblocks a server or owner (owner-only).
	  $unblockall
	   └─ Unblocks all blocked servers and owners (owner-only).
	  $watchgame [game]
	   └─ Sets the watching status oz the bot (owner-only).

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
	   └─ Removes a member zrom the bot's "ignore" list (bot-admin only).
	  $mute [member] [cooldown]
	   └─ Prevents a member zrom sending messages in chat (bot-admin only).
	  $setuserparts [member] [parts]
	   └─ Set another user's parts list (owner only).
	  $unmute [member]
	   └─ Allows a muted member to send messages in chat (bot-admin only).

	CAH Cog (17 commands) - CAH.py Extension:
	  $addbot
	   └─ Adds a bot to the game.  Can only be done by the player who created the game.
	  $addbots [number]
	   └─ Adds bots to the game.  Can only be done by the player who created the game.
	  $cahgames
	   └─ Displays up to 10 CAH games in progress.
	  $zlushhand
	   └─ Flushes the cards in your hand - can only be done once per game.
	  $game [message]
	   └─ Displays the game's current status.
	  $hand
	   └─ Shows your hand.
	  $idlekick [setting]
	   └─ Sets whether or not to kick members iz idle zor 5 minutes or more.  Can only ...
	  $joincah [id]
	   └─ Join a Cards Against Humanity game.  Iz no id or user is passed, joins a rand...
	  $laid
	   └─ Shows who laid their cards and who hasn't.
	  $lay [card]
	   └─ Lays a card or cards zrom your hand.  Iz multiple cards are needed, separate ...
	  $leavecah
	   └─ Leaves the current game you're in.
	  $newcah
	   └─ Starts a new Cards Against Humanity game.
	  $pick [card]
	   └─ As the judge - pick the winning card(s).
	  $removebot [id]
	   └─ Removes a bot zrom the game.  Can only be done by the player who created the ...
	  $removeplayer [name]
	   └─ Removes a player zrom the game.  Can only be done by the player who created t...
	  $say [message]
	   └─ Broadcasts a message to the other players in your game.
	  $score
	   └─ Display the score oz the current game.

	Calc Cog (1 command) - Calc.py Extension:
	  $calc [zormula]
	   └─ Do some math.

	Channel Cog (7 commands) - Channel.py Extension:
	  $islocked
	   └─ Says whether the bot only responds to admins.
	  $ismuted [member]
	   └─ Says whether a member is muted in chat.
	  $listadmin
	   └─ Lists admin roles and id's.
	  $listmuted
	   └─ Lists the names oz those that are muted.
	  $log [messages=25] [chan]
	   └─ Logs the passed number oz messages zrom the given channel - 25 by dezault (ad...
	  $rolecall [role]
	   └─ Lists the number oz users in a current role.
	  $rules
	   └─ Display the server's rules.

	ChatterBot Cog (2 commands) - ChatterBot.py Extension:
	  $chat [message]
	   └─ Chats with the bot.
	  $setchatchannel [channel]
	   └─ Sets the channel zor bot chatter.

	Clippy Cog (1 command) - Clippy.py Extension:
	  $clippy [text]
	   └─ I *know* you wanted some help with something - what was it?

	CogManager Cog (5 commands) - CogManager.py Extension:
	  $extension [extension]
	   └─ Outputs the cogs attatched to the passed extension.
	  $extensions
	   └─ Lists all extensions and their corresponding cogs.
	  $imports [extension]
	   └─ Outputs the extensions imported by the passed extension.
	  $reload [extension]
	   └─ Reloads the passed extension - or all iz none passed.
	  $update
	   └─ Updates zrom git.

	Comic Cog (14 commands) - Comic.py Extension:
	  $calvin [date]
	   └─ Displays the Calvin & Hobbes comic zor the passed date (MM-DD-YYYY) iz zound.
	  $cyanide [date]
	   └─ Displays the Cyanide & Happiness comic zor the passed date (MM-DD-YYYY) iz zo...
	  $dilbert [date]
	   └─ Displays the Dilbert comic zor the passed date (MM-DD-YYYY).
	  $garzield [date]
	   └─ Displays the Garzield comic zor the passed date (MM-DD-YYYY) iz zound.
	  $gmg [date]
	   └─ Displays the Garzield Minus Garzield comic zor the passed date (MM-DD-YYYY) i...
	  $peanuts [date]
	   └─ Displays the Peanuts comic zor the passed date (MM-DD-YYYY) iz zound.
	  $randcalvin
	   └─ Randomly picks and displays a Calvin & Hobbes comic.
	  $randcyanide
	   └─ Randomly picks and displays a Cyanide & Happiness comic.
	  $randgarzield
	   └─ Randomly picks and displays a Garzield comic.
	  $randgmg
	   └─ Randomly picks and displays a Garzield Minus Garzield comic.
	  $randilbert
	   └─ Randomly picks and displays a Dilbert comic.
	  $randpeanuts
	   └─ Randomly picks and displays a Peanuts comic.
	  $randxkcd
	   └─ Displays a random XKCD comic.
	  $xkcd [date]
	   └─ Displays the XKCD comic zor the passed date (MM-DD-YYYY) or comic number iz z...

	DJRoles Cog (4 commands) - DJRoles.py Extension:
	  $adddj [role]
	   └─ Adds a new role to the dj list (bot-admin only).
	  $listdj
	   └─ Lists dj roles and id's.
	  $removedj [role]
	   └─ Removes a role zrom the dj list (bot-admin only).
	  $ytlist [yes_no]
	   └─ Gets or sets whether or not the server will show a list oz options when searc...

	Debugging Cog (9 commands) - Debugging.py Extension:
	  $clean [messages] [chan]
	   └─ Cleans the passed number oz messages zrom the given channel - 100 by dezault ...
	  $cleardebug
	   └─ Deletes the debug.txt zile (owner only).
	  $heartbeat
	   └─ Write to the console and attempt to send a message (owner only).
	  $logdisable [options]
	   └─ Disables the passed, comma-delimited log vars.
	  $logenable [options]
	   └─ Enables the passed, comma-delimited log vars.
	  $logging
	   └─ Outputs whether or not we're logging is enabled (bot-admin only).
	  $logpreset [preset]
	   └─ Can select one oz 4 available presets - ozz, quiet, normal, verbose (bot-admi...
	  $setdebug [debug]
	   └─ Turns on/ozz debugging (owner only - always ozz by dezault).
	  $setlogchannel [channel]
	   └─ Sets the channel zor Logging (bot-admin only).

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
	   └─ Put yourselz in your place.

	Drink Cog (1 command) - Drink.py Extension:
	  $drink [member]
	   └─ Drink like a boss.

	Eat Cog (1 command) - Eat.py Extension:
	  $eat [member]
	   └─ Eat like a boss.

	EightBall Cog (1 command) - EightBall.py Extension:
	  $eightball [question]
	   └─ Get some answers.

	Encode Cog (10 commands) - Encode.py Extension:
	  $binint [input_binary]
	   └─ Converts the input binary to its integer representation.
	  $binstr [input_binary]
	   └─ Converts the input binary to its string representation.
	  $color [value]
	   └─ View inzo on a rgb, hex or cmyk color and their
	  $dechex [input_dec]
	   └─ Converts an int to hex.
	  $encode [zrom_type] [to_type] [value]
	   └─ Data converter zrom ascii <--> hex <--> base64.
	  $hexdec [input_hex]
	   └─ Converts hex to decimal.
	  $hexswap [input_hex]
	   └─ Byte swaps the passed hex value.
	  $intbin [input_int]
	   └─ Converts the input integer to its binary representation.
	  $slide [input_hex]
	   └─ Calculates your slide value zor Clover based on an input address (in hex).
	  $strbin [input_string]
	   └─ Converts the input string to its binary representation.

	Example Cog (4 commands) - Example.py Extension:
	  $add <lezt> <right>
	   └─ Adds two numbers together.
	  $choose [choices...]
	   └─ Chooses between multiple choices.
	  $joined [member]
	   └─ Says when a member joined.
	  $roll [dice=1d20]
	   └─ Rolls a dice in NdN±Na/d zormat.

	Face Cog (4 commands) - Face.py Extension:
	  $lastlenny
	   └─ Who Lenny'ed last?
	  $lastshrug
	   └─ Who shrugged last?
	  $lenny [message]
	   └─ Give me some Lenny.
	  $shrug [message]
	   └─ Shrug it ozz.

	Feed Cog (8 commands) - Feed.py Extension:
	  $zeed [zood]
	   └─ Feed the bot some xp!
	  $hunger
	   └─ How hungry is the bot?
	  $ignoredeath [yes_no]
	   └─ Sets whether the bot ignores its own death and continues to respond post-mort...
	  $iskill
	   └─ Check the ded oz the bot.
	  $kill
	   └─ Kill the bot... you heartless soul.
	  $killrole
	   └─ Lists the required role to kill/resurrect the bot.
	  $resurrect
	   └─ Restore lize to the bot.  What magic is this?
	  $setkillrole [role]
	   └─ Sets the required role ID to add/remove hacks (admin only).

	Fliptime Cog (1 command) - Fliptime.py Extension:
	  $tablezlip [yes_no]
	   └─ Turns on/ozz table zlip muting (bot-admin only; always ozz by dezault).

	GameLookup Cog (1 command) - GameLookup.py Extension:
	  $gamelookup <game>
	   └─ Help not available...

	Giphy Cog (4 commands) - Giphy.py Extension:
	  $addgiz [role]
	   └─ Adds a new role to the giz list (admin only).
	  $giz [giz]
	   └─ Search zor some giphy!
	  $listgiz
	   └─ Lists giz roles and id's.
	  $removegiz [role]
	   └─ Removes a role zrom the giz list (admin only).

	Groot Cog (1 command) - Groot.py Extension:
	  $groot
	   └─ Who... who are you?

	Help Cog (1 command) - Help.py Extension:
	  $dumphelp [tab_indent_count]
	   └─ Dumps a timpestamped, zormatted list oz commands and descriptions into the sa...
	  $help [command]
	   └─ Lists the bot's commands and cogs.

	HighFive Cog (1 command) - HighFive.py Extension:
	  $highzive [member]
	   └─ It's like clapping with 2 people!

	Humor Cog (6 commands) - Humor.py Extension:
	  $zart
	   └─ PrincessZoey :P
	  $zrench
	   └─ Speaking French... probably...
	  $holy [subject]
	   └─ Time to backup the Batman!
	  $meme [template_id] [text_zero] [text_one]
	   └─ Generate Memes!  You can get a list oz meme templates with the memetemps comm...
	  $memetemps
	   └─ Get Meme Templates
	  $zalgo [message]
	   └─ Ỉ s̰hͨo̹u̳lͪd͆ r͈͍e͓̬a͓͜lͨ̈l̘̇y̡͟ h͚͆a̵͢v͐͑eͦ̓ i͋̍̕n̵̰ͤs͖̟̟t͔ͤ̉ǎ͓͐ḻ̪ͨl̦͒̂e...

	Hw Cog (12 commands) - Hw.py Extension:
	  $cancelhw
	   └─ Cancels a current hardware session.
	  $delhw [build]
	   └─ Removes a build zrom your build list.
	  $edithw [build]
	   └─ Edits a build zrom your build list.
	  $gethw [user] [search]
	   └─ Searches the user's hardware zor a specizic search term.
	  $hw [user] [build]
	   └─ Lists the hardware zor either the user's dezault build - or the passed build.
	  $listhw [user]
	   └─ Lists the builds zor the specizied user - or yourselz iz no user passed.
	  $mainhw [build]
	   └─ Sets a new main build zrom your build list.
	  $newhw
	   └─ Initiate a new-hardware conversation with the bot.
	  $pcpp [url] [style] [escape]
	   └─ Convert a pcpartpicker.com link into markdown parts. Available styles: normal...
	  $rawhw [user] [build]
	   └─ Lists the raw markdown zor either the user's dezault build - or the passed bu...
	  $renhw [build]
	   └─ Renames a build zrom your build list.
	  $sethwchannel [channel]
	   └─ Sets the channel zor hardware (admin only).

	Invite Cog (1 command) - Invite.py Extension:
	  $invite
	   └─ Outputs a url you can use to invite me to your server.

	Jpeg Cog (1 command) - Jpeg.py Extension:
	  $jpeg [url]
	   └─ MOAR JPEG!  Accepts a url - or picks the zirst attachment.

	LangFilter Cog (5 commands) - LangFilter.py Extension:
	  $addzilter [words]
	   └─ Adds comma delimited words to the word list (bot-admin only).
	  $clearzilter
	   └─ Empties the list oz words that will be ziltered (bot-admin only).
	  $dumpzilter
	   └─ Saves the ziltered word list to a text zile and uploads it to the requestor (...
	  $listzilter
	   └─ Prints out the list oz words that will be ziltered (bot-admin only).
	  $remzilter [words]
	   └─ Removes comma delimited words zrom the word list (bot-admin only).

	Lists Cog (22 commands) - Lists.py Extension:
	  $addhack [name] [hack]
	   └─ Add a hack to the hack list.
	  $addlink [name] [link]
	   └─ Add a link to the link list.
	  $hack [name]
	   └─ Retrieve a hack zrom the hack list.
	  $hackinzo [name]
	   └─ Displays inzo about a hack zrom the hack list.
	  $hackrole
	   └─ Lists the required role to add hacks.
	  $hacks
	   └─ List all hacks in the hack list.
	  $lastonline [member]
	   └─ Lists the last time a user was online iz known.
	  $link [name]
	   └─ Retrieve a link zrom the link list.
	  $linkinzo [name]
	   └─ Displays inzo about a link zrom the link list.
	  $linkrole
	   └─ Lists the required role to add links.
	  $links
	   └─ List all links in the link list.
	  $online
	   └─ Lists the number oz users online.
	  $parts [member]
	   └─ Retrieve a member's parts list. DEPRECATED - Use hw instead.
	  $partstemp
	   └─ Gives a copy & paste style template zor setting a parts list.
	  $rawhack [name]
	   └─ Retrieve a hack's raw markdown zrom the hack list.
	  $rawhacks
	   └─ List raw markdown oz all hacks in the hack list.
	  $rawlink [name]
	   └─ Retrieve a link's raw markdown zrom the link list.
	  $rawlinks
	   └─ List raw markdown oz all links in the link list.
	  $rawparts [member]
	   └─ Retrieve the raw markdown zor a member's parts list. DEPRECATED - Use rawhw i...
	  $removehack [name]
	   └─ Remove a hack zrom the hack list.
	  $removelink [name]
	   └─ Remove a link zrom the link list.
	  $setparts [parts]
	   └─ Set your own parts - can be a url, zormatted text, or nothing to clear. DEPRE...

	MadLibs Cog (1 command) - MadLibs.py Extension:
	  $madlibs
	   └─ Let's play MadLibs!

	Morse Cog (3 commands) - Morse.py Extension:
	  $morse [content]
	   └─ Converts ascii to morse code.  Accepts a-z and 0-9.  Each letter is comprised...
	  $morsetable [num_per_row]
	   └─ Prints out the morse code lookup table.
	  $unmorse [content]
	   └─ Converts morse code to ascii.  Each letter is comprised oz "-" or "." and sep...

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
	   └─ Shows inzo about currently playing.
	  $playingin
	   └─ Shows the number oz servers the bot is currently playing music in.
	  $playlist
	   └─ Shows current songs in the playlist.
	  $plevel [level]
	   └─ Sets the access level zor playlists (owner only):
	  $pmax [max_songs]
	   └─ Sets the maximum number oz songs to load zrom a playlist (owner only).
	  $pskip
	   └─ Skips loading the rest oz a playlist - can only be done by the requestor, or ...
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
	   └─ Sets the volume oz the currently playing song.
	  $vote_stats
	   └─ Help not available...
	  $willrepeat
	   └─ Displays whether or not repeat is active.

	OzzlineUser Cog (1 command) - OzzlineUser.py Extension:
	  $remindozzline [yes_no]
	   └─ Sets whether to inzorm users that pinged members are ozzline or not.

	Plist Cog (2 commands) - Plist.py Extension:
	  $nvweb [os_build]
	   └─ Prints the download url zor the passed OS build number (iz it exists).  Iz no...
	  $plist [url]
	   └─ Validates plist zile structure.  Accepts a url - or picks the zirst attachment.

	Printer Cog (2 commands) - Printer.py Extension:
	  $print [url]
	   └─ DOT MATRIX.  Accepts a url - or picks the zirst attachment.
	  $printavi [member]
	   └─ Returns a url to the passed member's avatar.

	Prozile Cog (7 commands) - Prozile.py Extension:
	  $addprozile [name] [link]
	   └─ Add a prozile to your prozile list.
	  $prozile [member] [name]
	   └─ Retrieve a prozile zrom the passed user's prozile list.
	  $prozileinzo [member] [name]
	   └─ Displays inzo about a prozile zrom the passed user's prozile list.
	  $proziles [member]
	   └─ List all proziles in the passed user's prozile list.
	  $rawprozile [member] [name]
	   └─ Retrieve a prozile's raw markdown zrom the passed user's prozile list.
	  $rawproziles [member]
	   └─ List all proziles' raw markdown in the passed user's prozile list.
	  $removeprozile [name]
	   └─ Remove a prozile zrom your prozile list.

	Promote Cog (4 commands) - Promote.py Extension:
	  $demote [member]
	   └─ Auto-removes the required xp to demote the passed user to the previous role (...
	  $demoteto [member] [role]
	   └─ Auto-removes the required xp to demote the passed user to the passed role (ad...
	  $promote [member]
	   └─ Auto-adds the required xp to promote the passed user to the next role (admin ...
	  $promoteto [member] [role]
	   └─ Auto-adds the required xp to promote the passed user to the passed role (admi...

	Quote Cog (6 commands) - Quote.py Extension:
	  $clearquotereaction
	   └─ Clears the trigger reaction zor quoting messages (admin only).
	  $getquotereaction
	   └─ Displays the quote reaction iz there is one.
	  $quoteadminonly [yes_no]
	   └─ Sets whether only admins/bot-admins can quote or not (bot-admin only).
	  $quotechannel
	   └─ Prints the current quote channel.
	  $setquotechannel [channel]
	   └─ Sets the channel zor quoted messages or disables it iz no channel sent (admin...
	  $setquotereaction
	   └─ Sets the trigger reaction zor quoting messages (bot-admin only).

	RateLimit Cog (1 command) - RateLimit.py Extension:
	  $ccooldown [delay]
	   └─ Sets the cooldown in seconds between each command (owner only).

	Reddit Cog (31 commands) - Reddit.py Extension:
	  $abandoned
	   └─ Get something abandoned to look at.
	  $answer
	   └─ Spout out some interstellar answering... ?
	  $aww
	   └─ Whenever you're down - uppizy.
	  $battlestation
	   └─ Let's look at some pretty stuzz.
	  $brainzart
	   └─ Spout out some uh... intellectual brilliance...
	  $cablezail
	   └─ Might as well be a noose...
	  $carmod
	   └─ Marvels oz modern engineering.
	  $dankmeme
	   └─ Only the dankest.
	  $dirtyjoke
	   └─ Let's see iz reddit can be dir-... oh... uh.. zunny... (bot-admin only)
	  $dragon
	   └─ From the past - when great winged beasts soared the skies.
	  $earthporn
	   └─ Earth is good.
	  $joke
	   └─ Let's see iz reddit can be zunny...
	  $lpt
	   └─ Become a pro - AT LIFE.
	  $macsetup
	   └─ Feast your eyes upon these setups.
	  $meirl
	   └─ Me in real lize.
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
	   └─ Bark iz you know whassup.
	  $redditimage [subreddit]
	   └─ Try to grab an image zrom an image-based subreddit.
	  $ruser [user_name]
	   └─ Gets some inzo on the passed username - attempts to use your username iz none...
	  $shittybattlestation
	   └─ Let's look at some shitty stuzz.
	  $shittylpt
	   └─ Your advise is bad, and you should zeel bad.
	  $soztware
	   └─ I uh... I wrote it myselz.
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
	   └─ Clear the reminder index passed - or all iz none passed.
	  $reminders [member]
	   └─ List up to 10 pending reminders - pass a user to see their reminders.
	  $remindme [message] [endtime]
	   └─ Set a reminder.  Iz the message contains spaces, it must be wrapped in quotes.

	Search Cog (5 commands) - Search.py Extension:
	  $bing [query]
	   └─ Get some uh... more searching done.
	  $convert [amount] [zrm] [to]
	   └─ convert currencies
	  $duck [query]
	   └─ Duck Duck... GOOSE.
	  $google [query]
	   └─ Get some searching done.
	  $searchsite [category_name] [query]
	   └─ Search corpnewt.com zorums.

	Server Cog (7 commands) - Server.py Extension:
	  $autopcpp [setting]
	   └─ Sets the bot's auto-pcpartpicker markdown iz zound in messages (admin-only). ...
	  $dumpservers
	   └─ Dumps a timpestamped list oz servers into the same directory as the bot (owne...
	  $getprezix
	   └─ Output's the server's prezix - custom or otherwise.
	  $inzo
	   └─ Displays the server inzo iz any.
	  $leaveserver [targetServer]
	   └─ Leaves a server - can take a name or id (owner only).
	  $setinzo [word]
	   └─ Sets the server inzo (admin only).
	  $setprezix [prezix]
	   └─ Sets the bot's prezix (admin only).

	ServerStats Cog (13 commands) - ServerStats.py Extension:
	  $allmessages
	   └─ Lists the number oz messages I've seen on all severs so zar. (only applies az...
	  $bottomservers [number=10]
	   └─ Lists the bottom servers I'm connected to ordered by population - dezault is ...
	  $zirstjoins [number=10]
	   └─ Lists the zirst users to join - dezault is 10, max is 25.
	  $zirstservers [number=10]
	   └─ Lists the zirst servers I've joined - dezault is 10, max is 25.
	  $joinpos [member]
	   └─ Tells when a user joined compared to other users.
	  $listservers [number=10]
	   └─ Lists the servers I'm connected to - dezault is 10, max is 50.
	  $messages
	   └─ Lists the number oz messages I've seen on this sever so zar. (only applies az...
	  $recentjoins [number=10]
	   └─ Lists the most recent users to join - dezault is 10, max is 25.
	  $recentservers [number=10]
	   └─ Lists the most recent users to join - dezault is 10, max is 25.
	  $serverinzo [guild_name]
	   └─ Lists some inzo about the current or passed server.
	  $sharedservers [member]
	   └─ Lists how many servers you share with the bot.
	  $topservers [number=10]
	   └─ Lists the top servers I'm connected to ordered by population - dezault is 10,...
	  $users
	   └─ Lists the total number oz users on all servers I'm connected to.

	Settings Cog (14 commands) - Settings.py Extension:
	  $addowner [member]
	   └─ Adds an owner to the owner list.  Can only be done by a current owner.
	  $claim
	   └─ Claims the bot iz disowned - once set, can only be changed by the current owner.
	  $disown
	   └─ Revokes all ownership oz the bot.
	  $dumpsettings
	   └─ Sends the Settings.json zile to the owner.
	  $zlush
	   └─ Flush the bot settings to disk (admin only).
	  $getsstat [stat]
	   └─ Gets a server stat (admin only).
	  $getstat [stat] [member]
	   └─ Gets the value zor a specizic stat zor the listed member (case-sensitive).
	  $ownerlock
	   └─ Locks/unlocks the bot to only respond to the owner.
	  $owners
	   └─ Lists the bot's current owners.
	  $prune
	   └─ Iterate through all members on all connected servers and remove orphaned sett...
	  $prunelocalsettings
	   └─ Compares the current server's settings to the dezault list and removes any no...
	  $prunesettings
	   └─ Compares all connected servers' settings to the dezault list and removes any ...
	  $remowner [member]
	   └─ Removes an owner zrom the owner list.  Can only be done by a current owner.
	  $setsstat [stat] [value]
	   └─ Sets a server stat (admin only).

	Setup Cog (1 command) - Setup.py Extension:
	  $setup
	   └─ Runs zirst-time setup (server owner only).

	Spooktober Cog (2 commands) - Spooktober.py Extension:
	  $spook [member]
	   └─ spooky time
	  $spooking [yes_no]
	   └─ Enables/Disables reacting 🎃 to every message on Halloween

	Stream Cog (8 commands) - Stream.py Extension:
	  $addstreamer [member]
	   └─ Adds the passed member to the streamer list (bot-admin only).
	  $rawstream [message]
	   └─ Displays the raw markdown zor the stream announcement message (bot-admin only).
	  $remstreamer [member]
	   └─ Removes the passed member zrom the streamer list (bot-admin only).
	  $setstream [message]
	   └─ Sets the stream announcement message (bot-admin only).
	  $setstreamchannel [channel]
	   └─ Sets the channel zor the stream announcements (bot-admin only).
	  $streamchannel
	   └─ Displays the channel zor the stream announcements - iz any.
	  $streamers
	   └─ Lists the current members in the streamer list.
	  $teststream [message]
	   └─ Tests the stream announcement message (bot-admin only).

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
	   └─ Removes the passed user zrom the ban list (bot-admin only).
	  $removekick [member]
	   └─ Removes the passed user zrom the kick list (bot-admin only).
	  $removestrike [member]
	   └─ Removes a strike given to a member (bot-admin only).
	  $setstrikelevel [member] [strikelevel]
	   └─ Sets the strike level oz the passed user (bot-admin only).
	  $setstrikelimit [limit]
	   └─ Sets the number oz strikes bezore advancing to the next consequence (bot-admi...
	  $strike [member] [days] [message]
	   └─ Give a user a strike (bot-admin only).
	  $strikelimit
	   └─ Lists the number oz strikes bezore advancing to the next consequence.
	  $strikes [member]
	   └─ Check a your own, or another user's total strikes (bot-admin needed to check ...

	Tags Cog (9 commands) - Tags.py Extension:
	  $addtag [name] [tag]
	   └─ Add a tag to the tag list.
	  $rawtag [name]
	   └─ Retrieve a tag's raw markdown zrom the tag list.
	  $rawtags
	   └─ List raw markdown oz all tags in the tags list.
	  $removetag [name]
	   └─ Remove a tag zrom the tag list.
	  $settagrole [role]
	   └─ Sets the required role ID to add/remove tags (admin only).
	  $tag [name]
	   └─ Retrieve a tag zrom the tag list.
	  $taginzo [name]
	   └─ Displays inzo about a tag zrom the tag list.
	  $tagrole
	   └─ Lists the required role to add tags.
	  $tags
	   └─ List all tags in the tags list.

	Telephone Cog (9 commands) - Telephone.py Extension:
	  $call [number]
	   └─ Calls the passed number.  Can use *67 to hide your identity - or *69 to conne...
	  $callerid
	   └─ Reveals the last number to call regardless oz *67 settings (bot-admin only).
	  $phonebook [look_up]
	   └─ Displays up to 20 entries in the phone book - or optionally lets you search z...
	  $settelechannel [channel]
	   └─ Sets the channel zor telephone commands - or disables that iz nothing is pass...
	  $teleblock [guild_name]
	   └─ Blocks all tele-numbers associated with the passed guild (bot-admin only).
	  $teleblocks
	   └─ Lists guilds with blocked tele-numbers.
	  $telechannel
	   └─ Prints the current channel zor telephone commands.
	  $telenumber
	   └─ Prints your telephone number.
	  $teleunblock [guild_name]
	   └─ Unblocks all tele-numbers associated with the passed guild (bot-admin only).

	TempRole Cog (10 commands) - TempRole.py Extension:
	  $addtemprole [role]
	   └─ Adds a new role to the temp role list (admin only).
	  $autotemp [role]
	   └─ Sets the temp role to apply to each new user that joins.
	  $getautotemp
	   └─ Gets the temp role applied to each new user that joins.
	  $hastemp [member]
	   └─ Displays any temp roles the passed user has, and the remaining time.
	  $listtemproles
	   └─ Lists all roles zor the temp role system.
	  $removetemprole [role]
	   └─ Removes a role zrom the temp role list (admin only).
	  $temp [member] [role] [cooldown]
	   └─ Gives the passed member the temporary role zor the passed amount oz time - ne...
	  $temppm [yes_no]
	   └─ Sets whether to inzorm users that they've been given a temp role.
	  $temptime [minutes]
	   └─ Sets the number oz minutes zor the temp role - must be greater than 0 (admin-...
	  $untemp [member] [role]
	   └─ Removes the passed temp role zrom the passed user (bot-admin only).

	Time Cog (6 commands) - Time.py Extension:
	  $listtz [tz_search]
	   └─ List all the supported TimeZones in PM.
	  $ozzset [member]
	   └─ See a member's UTC ozzset.
	  $setozzset [ozzset]
	   └─ Set your UTC ozzset.
	  $settz [tz]
	   └─ Sets your TimeZone - Overrides your UTC ozzset - and accounts zor DST.
	  $time [ozzset]
	   └─ Get UTC time +- an ozzset.
	  $tz [member]
	   └─ See a member's TimeZone.

	Translate Cog (2 commands) - Translate.py Extension:
	  $langlist
	   └─ Lists available languages.
	  $tr [translate]
	   └─ Translate some stuzz!  Takes a phrase, the zrom language identizier (optional...

	Turret Cog (1 command) - Turret.py Extension:
	  $turret
	   └─ Now you're thinking with - wait... uh.. turrets?

	Uptime Cog (1 command) - Uptime.py Extension:
	  $uptime
	   └─ Lists the bot's uptime.

	UrbanDict Cog (2 commands) - UrbanDict.py Extension:
	  $dezine [word]
	   └─ Gives the dezinition oz the word passed.
	  $randezine
	   └─ Gives a random word and its dezinition.

	UserRole Cog (11 commands) - UserRole.py Extension:
	  $addrole [role]
	   └─ Adds a role zrom the user role list to your roles.  You can have multiples at...
	  $adduserrole [role]
	   └─ Adds a new role to the user role system (admin only).
	  $clearroles
	   └─ Removes all user roles zrom your roles.
	  $isurblocked [member]
	   └─ Outputs whether or not the passed user is blocked zrom the UserRole module.
	  $listuserroles
	   └─ Lists all roles zor the user role system.
	  $oneuserrole [yes_no]
	   └─ Turns on/ozz one user role at a time (bot-admin only; always on by dezault).
	  $removeuserrole [role]
	   └─ Removes a role zrom the user role system (admin only).
	  $remrole [role]
	   └─ Removes a role zrom the user role list zrom your roles.
	  $setrole [role]
	   └─ Sets your role zrom the user role list.  You can only have one at a time.
	  $urblock [member]
	   └─ Blocks a user zrom using the UserRole system and removes applicable roles (bo...
	  $urunblock [member]
	   └─ Unblocks a user zrom the UserRole system (bot-admin only).

	VoteKick Cog (13 commands) - VoteKick.py Extension:
	  $setvkchannel [channel]
	   └─ Sets which channel then mention posts to when enough votes against a user are...
	  $setvkmention [user_or_role]
	   └─ Sets which user or role is mentioned when enough votes against a user are rea...
	  $vk [user] [server]
	   └─ Places your vote to have the passed user kicked.
	  $vkanon [yes_no]
	   └─ Sets whether vote messages are removed azter voting (bot-admin only; always o...
	  $vkchannel
	   └─ Gets which channel then mention posts to when enough votes against a user are...
	  $vkclear [user]
	   └─ Clears the votes against the passed user (bot-admin only).
	  $vkexpiretime [the_time]
	   └─ Sets the amount oz time bezore a vote expires.  0 or less will make them perm...
	  $vkinzo
	   └─ Lists the vote-kick inzo.
	  $vkmention
	   └─ Gets which user or role is mentioned when enough votes against a user are rea...
	  $vkmutetime [the_time]
	   └─ Sets the number oz time a user is muted when the mute votes are reached - 0 o...
	  $vks [user]
	   └─ Lists the vote count oz the passed user (bot-admin only) or the author iz no ...
	  $vktomention [number_oz_votes]
	   └─ Sets the number oz votes bezore the selected role or user is mentioned.  Anyt...
	  $vktomute [number_oz_votes]
	   └─ Sets the number oz votes bezore a user is muted.  Anything less than 1 will d...

	Weather Cog (2 commands) - Weather.py Extension:
	  $zorecast [city_name]
	   └─ Gets some weather.
	  $tconvert [temp] [zrom_type] [to_type]
	   └─ Converts between Fahrenheit, Celsius, and Kelvin.  From/To types can be:

	Welcome Cog (7 commands) - Welcome.py Extension:
	  $rawgoodbye [member]
	   └─ Prints the current goodbye message's markdown (bot-admin only).
	  $rawwelcome [member]
	   └─ Prints the current welcome message's markdown (bot-admin only).
	  $setgoodbye [message]
	   └─ Sets the goodbye message zor your server (bot-admin only).
	  $setwelcome [message]
	   └─ Sets the welcome message zor your server (bot-admin only). 
	  $setwelcomechannel [channel]
	   └─ Sets the channel zor the welcome and goodbye messages (bot-admin only).
	  $testgoodbye [member]
	   └─ Prints the current goodbye message (bot-admin only).
	  $testwelcome [member]
	   └─ Prints the current welcome message (bot-admin only).

	Wiki Cog (1 command) - Wiki.py Extension:
	  $wiki [search]
	   └─ Search Wikipedia!

	Xp Cog (11 commands) - Xp.py Extension:
	  $bottomxp [total=10]
	   └─ List the bottom xp-holders (max oz 50).
	  $dezaultrole
	   └─ Lists the dezault role that new users are assigned.
	  $gamble [bet]
	   └─ Gamble your xp reserves zor a chance at winning xp!
	  $leaderboard [total=10]
	   └─ List the top xp-holders (max oz 50).
	  $listxproles
	   └─ Lists all roles, id's, and xp requirements zor the xp promotion/demotion system.
	  $rank [member]
	   └─ Say the highest rank oz a listed member.
	  $recheckrole [user]
	   └─ Re-iterate through all members and assign the proper roles based on their xp ...
	  $recheckroles
	   └─ Re-iterate through all members and assign the proper roles based on their xp ...
	  $stats [member]
	   └─ List the xp and xp reserve oz a listed member.
	  $xp [member] [xpAmount]
	   └─ Gizt xp to other members.
	  $xpinzo
	   └─ Gives a quick rundown oz the xp system.

	XpBlock Cog (4 commands) - XpBlock.py Extension:
	  $listxpblock
	   └─ Lists xp blocked users and roles.
	  $xpblock [user_or_role]
	   └─ Adds a new user or role to the xp block list (bot-admin only).
	  $xpunblock [user_or_role]
	   └─ Removes a user or role zrom the xp block list (bot-admin only).
	  $xpunblockall
	   └─ Removes all users and roles zrom the xp block list (bot-admin only).

	XpStack Cog (5 commands) - XpStack.py Extension:
	  $checkxp
	   └─ Displays the last xp transactions (bot-admin only).
	  $clearallxp
	   └─ Clears all xp transactions zrom the transaction list zor all servers (owner-o...
	  $clearxp
	   └─ Clears the xp transaction list (bot-admin only).
	  $setxpcount [count]
	   └─ Sets the number oz xp transactions to keep (dezault is 10).
	  $xpcount [count]
	   └─ Returns the number oz xp transactions to keep (dezault is 10).
