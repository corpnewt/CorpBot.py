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
	  setmotd            Adds a message of the day to the selected channel.
	  prunexproles       Removes any roles from the xp promotion/demotion system ...
	  removemotd         Removes the message of the day from the selected channel.
	  setxpreserve       Set's an absolute value for the member's xp reserve (adm...
	  setlinkrole        Sets the required role ID to add/remove links (admin only).
	  setrules           Set the server's rules (admin only).
	  addxprole          Adds a new role to the xp promotion/demotion system (adm...
	  sethackrole        Sets the required role ID to add/remove hacks (admin only).
	  setmadlibschannel  Sets the required role ID to stop the music player (admi...
	  setxp              Sets an absolute value for the member's xp (admin only).
	  xprole             Lists the required role to give xp, gamble, or feed the ...
	  broadcast          Broadcasts a message to all connected servers.  Can only...
	  removexprole       Removes a role from the xp promotion/demotion system (ad...
	  setxprole          Sets the required role ID to give xp, gamble, or feed th...
	  stoprole           Lists the required role to stop the bot from playing music.
	  setstoprole        Sets the required role ID to stop the music player (admi...
	  lock               Toggles whether the bot only responds to admins (admin o...
	  addadmin           Adds a new role to the xp promotion/demotion system (adm...
	  setdefaultrole     Sets the default role or position for auto-role assignment.
	  removeadmin        Removes a role from the admin list (admin only).
	Ascii:
	  ascii              Beautify some text (font list at http://artii.herokuapp....
	Bot:
	  nickname           Set the bot's nickname (admin-only).
	  hostinfo           List info about the bot's host environment.
	  avatar             Sets the bot's avatar (owner only).
	  ping               Feeling lonely?
	  playgame           Sets the playing status of the bot (owner-only).
	  source             Link the github source.
	  setbotparts        Set the bot's parts - can be a url, formatted text, or n...
	  servers            Lists the number of servers I'm connected to!
	BotAdmin:
	  listen             Removes a member from the bot's "ignore" list (bot-admin...
	  unmute             Allows a muted member to send messages in chat (bot-admi...
	  ignored            Lists the users currently being ignored.
	  ignore             Adds a member to the bot's "ignore" list (bot-admin only).
	  ban                Bans the selected member (bot-admin only).
	  kick               Kicks the selected member (bot-admin only).
	  setuserparts       Set another user's parts list (bot-admin only).
	  mute               Prevents a member from sending messages in chat (bot-adm...
	Calc:
	  calc               Do some math.
	Cats:
	  randomcat          Meow.
	Channel:
	  islocked           Says whether the bot only responds to admins.
	  rules              Display the server's rules.
	  clean              Cleans the passed number of messages from the given chan...
	  rolecall           Lists the number of users in a current role.
	  listadmin          Lists admin roles and id's.
	  ismuted            Says whether a member is muted in chat.
	Comic:
	  randxkcd           Displays a random XKCD comic.
	  randcalvin         Randomly picks and displays a Calvin & Hobbes comic.
	  randgarfield       Randomly picks and displays a Garfield comic.
	  peanuts            Displays the Peanuts comic for the passed date (MM-DD-YY...
	  randpeanuts        Randomly picks and displays a Peanuts comic.
	  cyanide            Displays the Cyanide & Happiness comic for the passed da...
	  calvin             Displays the Calvin & Hobbes comic for the passed date (...
	  randgmg            Randomly picks and displays a Garfield Minus Garfield co...
	  gmg                Displays the Garfield Minus Garfield comic for the passe...
	  randcyanide        Randomly picks and displays a Cyanide & Happiness comic.
	  randilbert         Randomly picks and displays a Dilbert comic.
	  dilbert            Displays the Dilbert comic for the passed date (MM-DD-YY...
	  garfield           Displays the Garfield comic for the passed date (MM-DD-Y...
	  xkcd               Displays the XKCD comic for the passed date (MM-DD-YYYY)...
	DrBeer:
	  drbeer             Put yourself in your place.
	Eat:
	  eat                Eat like a boss.
	EightBall:
	  eightball          Get some answers.
	Example:
	  choose             Chooses between multiple choices.
	  add                Adds two numbers together.
	  roll               Rolls a dice in NdN format.
	  joined             Says when a member joined.
	Face:
	  shrug              Shrug it off.
	  lenny              Give me some Lenny.
	  lastlenny          Who Lenny'ed last?
	  lastshrug          Who shrugged last?
	Feed:
	  killrole           Lists the required role to kill/resurrect the bot.
	  setkillrole        Sets the required role ID to add/remove hacks (admin only).
	  feed               Feed the bot some xp!
	  resurrect          Restore life to the bot.  What magic is this?
	  iskill             Check the ded of the bot.
	  hunger             How hungry is the bot?
	  kill               Kill the bot... you heartless soul.
	Humor:
	  fart               PrincessZoey :P
	Invite:
	  invite             Outputs a url you can use to invite me to your server.
	Lists:
	  removelink         Remove a link from the link list.
	  removehack         Remove a hack from the hack list.
	  linkrole           Lists the required role to add links.
	  hack               Retrieve a hack from the hack list.
	  lastonline         Lists the last time a user was online if known.
	  online             Lists the number of users online.
	  setparts           Set your own parts - can be a url, formatted text, or no...
	  addhack            Add a hack to the hack list.
	  hacks              List all hacks in the hack list.
	  addlink            Add a link to the link list.
	  hackrole           Lists the required role to add hacks.
	  links              List all links in the link list.
	  parts              Retrieve a member's parts list.
	  link               Retrieve a link from the link list.
	  linkinfo           Displays info about a link from the link list.
	  hackinfo           Displays info about a hack from the hack list.
	  partstemp          Gives a copy & paste style template for setting a parts ...
	MadLibs:
	  madlibs            Let's play MadLibs!
	Music:
	  playlist           Shows current songs in the playlist.
	  playing            Shows info about currently playing.
	  vote_stats         
	  removesong         Removes a song in the playlist by the index.
	  play               Plays a song.
	  join               Joins a voice channel.
	  keep               Vote to keep a song.
	  volume             Sets the volume of the currently playing song.
	  resume             Resumes the currently played song.
	  skip               Vote to skip a song. The song requester can automaticall...
	  unvote             Remove your song vote.
	  pause              Pauses the currently played song.
	  stop               Stops playing audio and leaves the voice channel.
	  summon             Summons the bot to join your voice channel.
	Profile:
	  profileinfo        Displays info about a profile from the passed user's pro...
	  profile            Retrieve a profile from the passed user's profile list.
	  addprofile         Add a profile to your profile list.
	  removeprofile      Remove a profile from your profile list.
	  profiles           List all profiles in the passed user's profile list.
	Reddit:
	  earthporn          Earth is good.
	  meirl              Me in real life.
	  question           Spout out some interstellar questioning... ?
	  randomdog          Bark if you know whassup.
	  thinkdeep          Spout out some intellectual brilliance.
	  starterpack        Starterpacks.
	  software           I uh... I wrote it myself.
	  wallpaper          Get something pretty to look at.
	  cablefail          Might as well be a noose...
	  brainfart          Spout out some uh... intellectual brilliance...
	  dragon             From the past - when great winged beasts soared the skies.
	  aww                Whenever you're down - uppify.
	  answer             Spout out some interstellar answering... ?
	  nocontext          Spout out some intersexual brilliance.
	  techsupport        Tech support irl.
	  dankmemes          Only the dankest.
	  abandoned          Get something abandoned to look at.
	Remind:
	  reminders          List up to 10 pending reminders.
	  clearmind          Clear all reminders.
	  remindme           Set a reminder.
	Search:
	  duck               Duck Duck... GOOSE.
	  google             Get some searching done.
	  bing               Get some uh... more searching done.
	  searchsite         Search corpnewt.com forums.
	Server:
	  info               Displays the server info if any.
	  setinfo            Sets the server info (admin only).
	Settings:
	  getstat            Gets the value for a specific stat for the listed member...
	  getsstat           Gets a server stat (admin only).
	  flush              Flush the bot settings to disk (admin only).
	  setsstat           Sets a server stat (admin only).
	  prune              Iterate through all members on all connected servers and...
	  prunesettings      Compares all connected servers' settings to the default ...
	  disown             Revokes ownership of the bot.
	  setowner           Sets the bot owner - once set, can only be changed by th...
	  owner              Lists the bot's current owner.
		  claim              Claims the bot - once set, can only be changed by the cu...
	  ownerlock          Locks/unlocks the bot to only respond to the owner.
	  prunelocalsettings Compares the current server's settings to the default li...
	Setup:
	  setup              Runs first-time setup (server owner only).
	Time:
	  time               Get UTC time +- an offset.
	  offset             See a member's UTC offset.
	  setoffset          Set your UTC offset.
	Uptime:
	  uptime             Lists the bot's uptime.
	UrbanDict:
	  define             Gives the definition of the word passed.
	  randefine          Gives a random word and its definition.
	Xp:
	  defaultrole        Lists the default role that new users are assigned.
	  stats              List the xp and xp reserve of a listed member.
	  listxproles        Lists all roles, id's, and xp requirements for the xp pr...
	  xpinfo             Gives a quick rundown of the xp system.
	  leaderboard        List the top xp-holders (max of 50).
	  rank               Say the highest rank of a listed member.
	  bottomxp           List the bottom xp-holders (max of 50).
	  recheckroles       Re-iterate through all members and assign the proper rol...
	  recheckrole        Re-iterate through all members and assign the proper rol...
	  xp                 Gift xp to other members.
	  gamble             Gamble your xp reserves for a chance at winning xp!
	​No Category:
	  help               Shows this message.

	Type $help command for more info on a command.
	You can also type $help category for more info on a category.
