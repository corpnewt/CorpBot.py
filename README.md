# CorpBot.py
A *slightly* less clumsy python bot for discord

A sample of his `$help` command:

-

	A bot that does stuff.... probably
	Admin:
	  removemotd         Removes the message of the day from the selected channel.
	  setxpreserve       Set's an absolute value for the member's xp reserve (adm...
	  stoprole           Lists the required role to stop the bot from playing music.
	  setmadlibschannel  Sets the required role ID to stop the music player (admi...
	  setxp              Sets an absolute value for the member's xp (admin only).
	  prunexproles       Removes any roles from the xp promotion/demotion system ...
	  lock               Toggles whether the bot only responds to admins (admin o...
	  setrules           Set the server's rules (admin only).
	  removexprole       Removes a role from the xp promotion/demotion system (ad...
	  setstoprole        Sets the required role ID to stop the music player (admi...
	  setxprole          Sets the required role ID to give xp, gamble, or feed th...
	  addxprole          Adds a new role to the xp promotion/demotion system (adm...
	  sethackrole        Sets the required role ID to add/remove hacks (admin only).
	  broadcast          Broadcasts a message to all connected servers.  Can only...
	  setmotd            Adds a message of the day to the selected channel.
	  xprole             Lists the required role to give xp, gamble, or feed the ...
	  removeadmin        Removes a role from the admin list (admin only).
	  addadmin           Adds a new role to the xp promotion/demotion system (adm...
	  setlinkrole        Sets the required role ID to add/remove links (admin only).
	  setdefaultrole     Sets the default role or position for auto-role assignment.
	Ascii:
	  ascii              Beautify some text (font list at http://artii.herokuapp....
	Bot:
	  servers            Lists the number of servers I'm connected to!
	  source             Link the github source.
	  hostinfo           List info about the bot's host environment.
	  nickname           Set the bot's nickname (admin-only).
	  avatar             Sets the bot's avatar (owner only).
	  ping               Feeling lonely?
	  setbotparts        Set the bot's parts - can be a url, formatted text, or n...
	  playgame           Sets the playing status of the bot (owner-only).
	BotAdmin:
	  ban                Bans the selected member (bot-admin only).
	  unmute             Allows a muted member to send messages in chat (bot-admi...
	  ignored            Lists the users currently being ignored.
	  ignore             Adds a member to the bot's "ignore" list (bot-admin only).
	  mute               Prevents a member from sending messages in chat (bot-adm...
	  setuserparts       Set another user's parts list (bot-admin only).
	  kick               Kicks the selected member (bot-admin only).
	  listen             Removes a member from the bot's "ignore" list (bot-admin...
	Calc:
	  calc               Do some math.
	Cats:
	  randomcat          Meow.
	Channel:
	  rules              Display the server's rules.
	  ismuted            Says whether a member is muted in chat.
	  listadmin          Lists admin roles and id's.
	  clean              Cleans the passed number of messages from the given chan...
	  rolecall           Lists the number of users in a current role.
	  islocked           Says whether the bot only responds to admins.
	Comic:
	  randpeanuts        Randomly picks and displays a Peanuts comic.
	  garfield           Displays the Garfield comic for the passed date (MM-DD-Y...
	  randcalvin         Randomly picks and displays a Calvin & Hobbes comic.
	  peanuts            Displays the Peanuts comic for the passed date (MM-DD-YY...
	  randilbert         Randomly picks and displays a Dilbert comic.
	  dilbert            Displays the Dilbert comic for the passed date (MM-DD-YY...
	  randgmg            Randomly picks and displays a Garfield Minus Garfield co...
	  cyanide            Displays the Cyanide & Happiness comic for the passed da...
	  randxkcd           Displays a random XKCD comic.
	  calvin             Displays the Calvin & Hobbes comic for the passed date (...
	  randcyanide        Randomly picks and displays a Cyanide & Happiness comic.
	  gmg                Displays the Garfield Minus Garfield comic for the passe...
	  xkcd               Displays the XKCD comic for the passed date (MM-DD-YYYY)...
	  randgarfield       Randomly picks and displays a Garfield comic.
	DrBeer:
	  drbeer             Put yourself in your place.
	Eat:
	  eat                Eat like a boss.
	EightBall:
	  eightball          Get some answers.
	Example:
	  add                Adds two numbers together.
	  joined             Says when a member joined.
	  roll               Rolls a dice in NdN format.
	  choose             Chooses between multiple choices.
	Face:
	  lastlenny          Who Lenny'ed last?
	  lenny              Give me some Lenny.
	  shrug              Shrug it off.
	  lastshrug          Who shrugged last?
	Feed:
	  killrole           Lists the required role to kill/resurrect the bot.
	  resurrect          Restore life to the bot.  What magic is this?
	  iskill             Check the ded of the bot.
	  hunger             How hungry is the bot?
	  kill               Kill the bot... you heartless soul.
	  setkillrole        Sets the required role ID to add/remove hacks (admin only).
	  feed               Feed the bot some xp!
	Humor:
	  fart               PrincessZoey :P
	Invite:
	  invite             Outputs a url you can use to invite me to your server.
	Lists:
	  hack               Retrieve a hack from the hack list.
	  linkinfo           Displays info about a link from the link list.
	  partstemp          Gives a copy & paste style template for setting a parts ...
	  parts              Retrieve a member's parts list.
	  hackrole           Lists the required role to add hacks.
	  hacks              List all hacks in the hack list.
	  setparts           Set your own parts - can be a url, formatted text, or no...
	  link               Retrieve a link from the link list.
	  linkrole           Lists the required role to add links.
	  removehack         Remove a hack from the hack list.
	  addhack            Add a hack to the hack list.
	  removelink         Remove a link from the link list.
	  lastonline         Lists the last time a user was online if known.
	  online             Lists the number of users online.
	  addlink            Add a link to the link list.
	  hackinfo           Displays info about a hack from the hack list.
	  links              List all links in the link list.
	MadLibs:
	  madlibs            Let's play MadLibs!
	Music:
	  play               Plays a song.
	  stop               Stops playing audio and leaves the voice channel.
	  summon             Summons the bot to join your voice channel.
	  vote_stats         
	  removesong         Removes a song in the playlist by the index.
	  join               Joins a voice channel.
	  playlist           Shows current songs in the playlist.
	  skip               Vote to skip a song. The song requester can automaticall...
	  keep               Vote to keep a song.
	  pause              Pauses the currently played song.
	  volume             Sets the volume of the currently playing song.
	  playing            Shows info about currently playing.
	  unvote             Remove your song vote.
	  resume             Resumes the currently played song.
	Profile:
	  profileinfo        Displays info about a profile from the passed user's pro...
	  addprofile         Add a profile to your profile list.
	  profile            Retrieve a profile from the passed user's profile list.
	  removeprofile      Remove a profile from your profile list.
	  profiles           List all profiles in the passed user's profile list.
	Reddit:
	  techsupport        Tech support irl.
	  answer             Spout out some interstellar answering... ?
	  software           I uh... I wrote it myself.
	  earthporn          Earth is good.
	  brainfart          Spout out some uh... intellectual brilliance...
	  dragon             From the past - when great winged beasts soared the skies.
	  meirl              Me in real life.
	  aww                Whenever you're down - uppify.
	  starterpack        Starterpacks.
	  dankmemes          Only the dankest.
	  randomdog          Bark if you know whassup.
	  cablefail          Might as well be a noose...
	  abandoned          Get something abandoned to look at.
	  thinkdeep          Spout out some intellectual brilliance.
	  nocontext          Spout out some intersexual brilliance.
	  question           Spout out some interstellar questioning... ?
	  wallpaper          Get something pretty to look at.
	Remind:
	  clearmind          Clear all reminders.
	  reminders          List up to 10 pending reminders.
	  remindme           Set a reminder.
	Search:
	  searchsite         Search corpnewt.com forums.
	  google             Get some searching done.
	  bing               Get some uh... more searching done.
	  duck               Duck Duck... GOOSE.
	Server:
	  info               Displays the server info if any.
	  setinfo            Sets the server info (admin only).
	Settings:
	  getsstat           Gets a server stat (admin only).
	  ownerlock          Locks/unlocks the bot to only respond to the owner.
	  prune              Iterate through all members on all connected servers and...
	  prunesettings      Compares all connected servers' settings to the default ...
	  disown             Revokes ownership of the bot.
	  prunelocalsettings Compares the current server's settings to the default li...
	  owner              Lists the bot's current owner.
	  setsstat           Sets a server stat (admin only).
	  claim              Claims the bot - once set, can only be changed by the cu...
	  setowner           Sets the bot owner - once set, can only be changed by th...
	  getstat            Gets the value for a specific stat for the listed member...
	  flush              Flush the bot settings to disk (admin only).
	Setup:
	  setup              Runs first-time setup (server owner only).
	Time:
	  setoffset          Set your UTC offset.
	  time               Get UTC time +- an offset.
	  offset             See a member's UTC offset.
	Uptime:
	  uptime             Lists the bot's uptime.
	UrbanDict:
	  define             Gives the definition of the word passed.
	  randefine          Gives a random word and its definition.
	Xp:
	  gamble             Gamble your xp reserves for a chance at winning xp!
	  xp                 Gift xp to other members.
	  listxproles        Lists all roles, id's, and xp requirements for the xp pr...
	  leaderboard        List the top xp-holders (max of 50).
	  xpinfo             Gives a quick rundown of the xp system.
	  recheckroles       Re-iterate through all members and assign the proper rol...
	  recheckrole        Re-iterate through all members and assign the proper rol...
	  stats              List the xp and xp reserve of a listed member.
	  bottomxp           List the bottom xp-holders (max of 50).
	  defaultrole        Lists the default role that new users are assigned.
	  rank               Say the highest rank of a listed member.
	​No Category:
	  help               Shows this message.

	Type $help command for more info on a command.
	You can also type $help category for more info on a category.
	You can also type $help category for more info on a category.
