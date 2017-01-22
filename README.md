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
	  addadmin           Adds a new role to the xp promotion/demotion system (adm...
	  addxprole          Adds a new role to the xp promotion/demotion system (adm...
	  broadcast          Broadcasts a message to all connected servers.  Can only...
	  lock               Toggles whether the bot only responds to admins (admin o...
	  prunexproles       Removes any roles from the xp promotion/demotion system ...
	  removeadmin        Removes a role from the admin list (admin only).
	  removemotd         Removes the message of the day from the selected channel.
	  removexprole       Removes a role from the xp promotion/demotion system (ad...
	  setdefaultrole     Sets the default role or position for auto-role assignment.
	  sethackrole        Sets the required role ID to add/remove hacks (admin only).
	  setlinkrole        Sets the required role ID to add/remove links (admin only).
	  setmadlibschannel  Sets the required role ID to stop the music player (admi...
	  setmotd            Adds a message of the day to the selected channel.
	  setrules           Set the server's rules (admin only).
	  setstoprole        Sets the required role ID to stop the music player (admi...
	  setxp              Sets an absolute value for the member's xp (admin only).
	  setxpreserve       Set's an absolute value for the member's xp reserve (adm...
	  setxprole          Sets the required role ID to give xp, gamble, or feed th...
	  stoprole           Lists the required role to stop the bot from playing music.
	  xprole             Lists the required role to give xp, gamble, or feed the ...
	Ascii:
	  ascii              Beautify some text (font list at http://artii.herokuapp....
	Bot:
	  avatar             Sets the bot's avatar (owner only).
	  hostinfo           List info about the bot's host environment.
	  nickname           Set the bot's nickname (admin-only).
	  ping               Feeling lonely?
	  playgame           Sets the playing status of the bot (owner-only).
	  servers            Lists the number of servers I'm connected to!
	  setbotparts        Set the bot's parts - can be a url, formatted text, or n...
	  source             Link the github source.
	BotAdmin:
	  ban                Bans the selected member (bot-admin only).
	  ignore             Adds a member to the bot's "ignore" list (bot-admin only).
	  ignored            Lists the users currently being ignored.
	  kick               Kicks the selected member (bot-admin only).
	  listen             Removes a member from the bot's "ignore" list (bot-admin...
	  mute               Prevents a member from sending messages in chat (bot-adm...
	  setuserparts       Set another user's parts list (bot-admin only).
	  unmute             Allows a muted member to send messages in chat (bot-admi...
	Calc:
	  calc               Do some math.
	Cats:
	  randomcat          Meow.
	Channel:
	  clean              Cleans the passed number of messages from the given chan...
	  islocked           Says whether the bot only responds to admins.
	  ismuted            Says whether a member is muted in chat.
	  listadmin          Lists admin roles and id's.
	  rolecall           Lists the number of users in a current role.
	  rules              Display the server's rules.
	Comic:
	  calvin             Displays the Calvin & Hobbes comic for the passed date (...
	  cyanide            Displays the Cyanide & Happiness comic for the passed da...
	  dilbert            Displays the Dilbert comic for the passed date (MM-DD-YY...
	  garfield           Displays the Garfield comic for the passed date (MM-DD-Y...
	  gmg                Displays the Garfield Minus Garfield comic for the passe...
	  peanuts            Displays the Peanuts comic for the passed date (MM-DD-YY...
	  randcalvin         Randomly picks and displays a Calvin & Hobbes comic.
	  randcyanide        Randomly picks and displays a Cyanide & Happiness comic.
	  randgarfield       Randomly picks and displays a Garfield comic.
	  randgmg            Randomly picks and displays a Garfield Minus Garfield co...
	  randilbert         Randomly picks and displays a Dilbert comic.
	  randpeanuts        Randomly picks and displays a Peanuts comic.
	  randxkcd           Displays a random XKCD comic.
	  xkcd               Displays the XKCD comic for the passed date (MM-DD-YYYY)...
	DrBeer:
	  drbeer             Put yourself in your place.
	Eat:
	  eat                Eat like a boss.
	EightBall:
	  eightball          Get some answers.
	Example:
	  add                Adds two numbers together.
	  choose             Chooses between multiple choices.
	  joined             Says when a member joined.
	  roll               Rolls a dice in NdN format.
	Face:
	  lastlenny          Who Lenny'ed last?
	  lastshrug          Who shrugged last?
	  lenny              Give me some Lenny.
	  shrug              Shrug it off.
	Feed:
	  feed               Feed the bot some xp!
	  hunger             How hungry is the bot?
	  iskill             Check the ded of the bot.
	  kill               Kill the bot... you heartless soul.
	  killrole           Lists the required role to kill/resurrect the bot.
	  resurrect          Restore life to the bot.  What magic is this?
	  setkillrole        Sets the required role ID to add/remove hacks (admin only).
	Humor:
	  fart               PrincessZoey :P
	Invite:
	  invite             Outputs a url you can use to invite me to your server.
	Lists:
	  addhack            Add a hack to the hack list.
	  addlink            Add a link to the link list.
	  hack               Retrieve a hack from the hack list.
	  hackinfo           Displays info about a hack from the hack list.
	  hackrole           Lists the required role to add hacks.
	  hacks              List all hacks in the hack list.
	  lastonline         Lists the last time a user was online if known.
	  link               Retrieve a link from the link list.
	  linkinfo           Displays info about a link from the link list.
	  linkrole           Lists the required role to add links.
  links              List all links in the link list.
  online             Lists the number of users online.
  parts              Retrieve a member's parts list.
  partstemp          Gives a copy & paste style template for setting a parts ...
  removehack         Remove a hack from the hack list.
  removelink         Remove a link from the link list.
  setparts           Set your own parts - can be a url, formatted text, or no...
MadLibs:
  madlibs            Let's play MadLibs!
Music:
  join               Joins a voice channel.
  keep               Vote to keep a song.
  pause              Pauses the currently played song.
  play               Plays a song.
  playing            Shows info about currently playing.
  playlist           Shows current songs in the playlist.
  removesong         Removes a song in the playlist by the index.
  repeat             Toggles whether or not to repeat the playlist.
  resume             Resumes the currently played song.
  skip               Vote to skip a song. The song requester can automaticall...
  stop               Stops playing audio and leaves the voice channel.
  summon             Summons the bot to join your voice channel.
  unvote             Remove your song vote.
  volume             Sets the volume of the currently playing song.
  vote_stats         
  willrepeat         Displays whether or not repeat is active.
Profile:
  addprofile         Add a profile to your profile list.
  profile            Retrieve a profile from the passed user's profile list.
  profileinfo        Displays info about a profile from the passed user's pro...
  profiles           List all profiles in the passed user's profile list.
  removeprofile      Remove a profile from your profile list.
Promote:
  demote             Auto-removes the required xp to demote the passed user t...
  demoteto           Auto-removes the required xp to demote the passed user t...
  promote            Auto-adds the required xp to promote the passed user to ...
  promoteto          Auto-adds the required xp to promote the passed user to ...
Reddit:
  abandoned          Get something abandoned to look at.
  answer             Spout out some interstellar answering... ?
  aww                Whenever you're down - uppify.
  brainfart          Spout out some uh... intellectual brilliance...
  cablefail          Might as well be a noose...
  dankmemes          Only the dankest.
  dragon             From the past - when great winged beasts soared the skies.
  earthporn          Earth is good.
  meirl              Me in real life.
  nocontext          Spout out some intersexual brilliance.
  question           Spout out some interstellar questioning... ?
  randomdog          Bark if you know whassup.
  software           I uh... I wrote it myself.
  starterpack        Starterpacks.
  techsupport        Tech support irl.
  thinkdeep          Spout out some intellectual brilliance.
  wallpaper          Get something pretty to look at.
Remind:
  clearmind          Clear all reminders.
  reminders          List up to 10 pending reminders.
  remindme           Set a reminder.
Search:
  bing               Get some uh... more searching done.
  duck               Duck Duck... GOOSE.
  google             Get some searching done.
  searchsite         Search corpnewt.com forums.
Server:
  info               Displays the server info if any.
  setinfo            Sets the server info (admin only).
Settings:
  claim              Claims the bot - once set, can only be changed by the cu...
  disown             Revokes ownership of the bot.
  flush              Flush the bot settings to disk (admin only).
  getsstat           Gets a server stat (admin only).
  getstat            Gets the value for a specific stat for the listed member...
  owner              Lists the bot's current owner.
  ownerlock          Locks/unlocks the bot to only respond to the owner.
  prune              Iterate through all members on all connected servers and...
  prunelocalsettings Compares the current server's settings to the default li...
  prunesettings      Compares all connected servers' settings to the default ...
  setowner           Sets the bot owner - once set, can only be changed by th...
  setsstat           Sets a server stat (admin only).
Setup:
  setup              Runs first-time setup (server owner only).
Time:
  offset             See a member's UTC offset.
  setoffset          Set your UTC offset.
  time               Get UTC time +- an offset.
Uptime:
  uptime             Lists the bot's uptime.
UrbanDict:
  define             Gives the definition of the word passed.
  randefine          Gives a random word and its definition.
Xp:
  bottomxp           List the bottom xp-holders (max of 50).
  defaultrole        Lists the default role that new users are assigned.
  gamble             Gamble your xp reserves for a chance at winning xp!
  leaderboard        List the top xp-holders (max of 50).
  listxproles        Lists all roles, id's, and xp requirements for the xp pr...
  rank               Say the highest rank of a listed member.
  recheckrole        Re-iterate through all members and assign the proper rol...
  recheckroles       Re-iterate through all members and assign the proper rol...
  stats              List the xp and xp reserve of a listed member.
  xp                 Gift xp to other members.
  xpinfo             Gives a quick rundown of the xp system.
​No Category:
  help               Shows this message.

Type $help command for more info on a command.
You can also type $help category for more info on a category.
