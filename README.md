# CorpBot.py
A *slightly* less clumsy python bot for discord

# Installation
Run `git pull https://github.com/corpnewt/CorpBot.py.git` or download as ZIP. CD to the directory.
Then, run the correct file (`Install.bat` for Windows, `sudo bash Install.sh` for MacOS and Linux).
Make sure you scroll through all of the output, as there might be hidden errors.

Linux note: You may need to run `sudo apt install python3 pip3 && sudo pip3 install --upgrade pillow`
to make sure Pillow, Python3, and PIP3 are installed correctly.

# Running the Bot
Create a .txt file and paste your token with no extra lines in it. Save it as token.txt in the same
place where CorpBot's source is.
Run the correct file (`StartBot.bat` for Windows, `bash Start.sh` for MacOS and Linux).

MacOS note: If you get an error about certificate verification failed, you need to update your Python 
key stores, and download from Python.org. In Python 3.6, Apple decided to bundle its own OpenSSL version,
leading to a certificate store that does not have all the root certificates. You can update this by running
`Install Certificates.command`, located in CorpBot's source directory.

# Features
A sample of his `$help` command:

-

	A bot that does stuff.... probably

	Admin:
	  setrules           Set the server's rules (admin-only).
	  stoprole           Lists the required role to stop the bot from playing music.
	  removexprole       Removes a role from the xp promotion/demotion system (ad...
	  mute               Prevents a member from sending messages in chat (admin-o...
	  setuserparts       Set another user's parts list (admin only).
	  setmadlibschannel  Sets the required role ID to stop the music player (admi...
	  lock               Toggles whether the bot only responds to admins (admin-o...
	  setxprole          Sets the required role ID to give xp, gamble, or feed th...
	  setdefaultrole     Sets the default role or position for auto-role assignment.
	  xprole             Lists the required role to give xp, gamble, or feed the ...
	  removemotd         Removes the message of the day from the selected channel.
	  addxprole          Adds a new role to the xp promotion/demotion system (adm...
	  prunexproles       Removes any roles from the xp promotion/demotion system ...
	  unmute             Allows a muted member to send messages in chat (admin-on...
	  broadcast          Broadcasts a message to all connected servers.  Can only...
	  addadmin           Adds a new role to the xp promotion/demotion system (adm...
	  ignore             Adds a member to the bot's "ignore" list (admin-only).
	  setstoprole        Sets the required role ID to stop the music player (admi...
	  setmotd            Adds a message of the day to the selected channel.
	  sethackrole        Sets the required role ID to add/remove hacks (admin only).
	  removeadmin        Removes a role from the admin list (admin only).
	  setlinkrole        Sets the required role ID to add/remove links (admin only).
	  listen             Removes a member from the bot's "ignore" list (admin-only).
	  setxpreserve       Set's an absolute value for the member's xp reserve (adm...
	  ignored            Lists the users currently being ignored.
	Bot:
	  source             Link the github source.
	  avatar             Sets the bot's avatar (owner-only).
	  setbotparts        Set the bot's parts - can be a url, formatted text, or n...
	  nickname           Set the bot's nickname (admin-only).
	  playgame           Sets the playing status of the bot (owner-only).
	  servers            Lists the number of servers I'm connected to!
	Channel:
	  rules              Display the server's rules.
	  clean              Cleans the passed number of messages from the given chan...
	  rolecall           Lists the number of users in a current role.
	  islocked           Says whether the bot only responds to admins.
	  ismuted            Says whether a member is muted in chat.
	  listadmin          Lists admin roles and id's.
	Comic:
	  randilbert         Randomly picks and displays a Dilbert comic.
	  randcyanide        Randomly picks and displays a Cyanide & Happiness comic.
	  gmg                Displays the Garfield Minus Garfield comic for the passe...
	  randxkcd           Displays a random XKCD comic.
	  randpeanuts        Randomly picks and displays a Peanuts comic.
	  randgarfield       Randomly picks and displays a Garfield comic.
	  peanuts            Displays the Peanuts comic for the passed date (MM-DD-YY...
	  xkcd               Displays the XKCD comic for the passed date (MM-DD-YYYY)...
	  calvin             Displays the Calvin & Hobbes comic for the passed date (...
	  randgmg            Randomly picks and displays a Garfield Minus Garfield co...
	  randcalvin         Randomly picks and displays a Calvin & Hobbes comic.
	  cyanide            Displays the Cyanide & Happiness comic for the passed da...
	  garfield           Displays the Garfield comic for the passed date (MM-DD-Y...
	  dilbert            Displays the Dilbert comic for the passed date (MM-DD-YY...
	DrBeer:
	  drbeer             Put yourself in your place.
	Example:
	  joined             Says when a member joined.
	  choose             Chooses between multiple choices.
	  roll               Rolls a dice in NdN format.
	  add                Adds two numbers together.
	Feed:
	  feed               Feed the bot some xp!
	  iskill             Check the ded of the bot.
	  hunger             How hungry is the bot?
	  killrole           Lists the required role to kill/resurrect the bot.
	  kill               Kill the bot... you heartless soul.
	  resurrect          Restore life to the bot.  What magic is this?
	  setkillrole        Sets the required role ID to add/remove hacks (admin only).
	Humor:
	  fart               PrincessZoey :P
	Invite:
	  invite             Outputs a url you can use to invite me to your server.
	Lists:
	  online             Lists the number of users online.
	  addlink            Add a link to the link list.
	  hack               Retrieve a hack from the hack list.
	  hackrole           Lists the required role to add hacks.
	  lastonline         Lists the last time a user was online if known.
	  partstemp          Gives a copy & paste style template for setting a parts ...
	  linkinfo           Displays info about a link from the link list.
	  links              List all links in the link list.
	  hacks              List all hacks in the hack list.
	  hackinfo           Displays info about a hack from the hack list.
	  parts              Retrieve a member's parts list.
	  setparts           Set your own parts - can be a url, formatted text, or no...
	  removehack         Remove a hack from the hack list.
	  addhack            Add a hack to the hack list.
	  linkrole           Lists the required role to add links.
	  removelink         Remove a link from the link list.
	  link               Retrieve a link from the link list.
	MadLibs:
	  madlibs            Let's play MadLibs!  Start with $madlibs, select works w...
	Music:
	  play               Plays a song.
	  pause              Pauses the currently played song.
	  skip               Vote to skip a song. The song requester can automaticall...
	  resume             Resumes the currently played song.
	  stop               Stops playing audio and leaves the voice channel.
	  summon             Summons the bot to join your voice channel.
	  playing            Shows info about currently playing.
	  volume             Sets the volume of the currently playing song.
	  join               Joins a voice channel.
	Reddit:
	  meirl              Me in real life.
	  techsupport        Tech support irl.
	  thinkdeep          Spout out some intellectual brilliance.
	  dankmemes          Only the dankest.
	  brainfart          Spout out some uh... intellectual brilliance...
	  answer             Spout out some interstellar answering... ?
	  earthporn          Earth is good.
	  nocontext          Spout out some intersexual brilliance.
	  software           I uh... I wrote it myself.
	  abandoned          Get something abandoned to look at.
	  starterpack        Starterpacks.
	  wallpaper          Get something pretty to look at.
	  question           Spout out some interstellar questioning... ?
	Server:
	  info               Displays the server info if any.
	  setinfo            Sets the server info (admin only).
	Settings:
	  prune              Iterate through all members on all connected servers and...
	  prunesettings      Compares all connected servers' settings to the default ...
	  owner              Sets the bot owner - once set, can only be changed by th...
	  getstat            Gets the value for a specific stat for the listed member...
	  prunelocalsettings Compares the current server's settings to the default li...
	  setsstat           Sets a server stat (admin only).
	  getsstat           Gets a server stat (admin only).
	  flush              Flush the bot settings to disk (admin only).
	  disown             Revokes ownership of the bot.
	Setup:
	  setup              Runs first-time setup (server owner only).
	Uptime:
	  uptime             Lists the bot's uptime.
	UrbanDict:
	  define             Gives the definition of the word passed.
	  randefine          Gives a random word and its definition.
	Xp:
	  topxp              List the top 10 xp-holders - or all members, if there ar...
	  xp                 Gift xp to other members.
	  setxp              Sets an absolute value for the member's xp (admin only).
	  defaultrole        Lists the default role that new users are assigned.
	  gamble             Gamble your xp reserves for a chance at winning xp!
	  bottomxp           List the bottom 10 xp-holders - or all members, if there...
	  stats              List the xp and xp reserve of a listed member.
	  recheckroles       Re-iterate through all members and assign the proper rol...
	  listxproles        Lists all roles, id's, and xp requirements for the xp pr...
	  rank               Say the highest rank of a listed member.
	  recheckrole        Re-iterate through all members and assign the proper rol...
	  xpinfo             Gives a quick rundown of the xp system.
	​No Category:
	  help               Shows this message.

	Type $help command for more info on a command.
	You can also type $help category for more info on a category.
