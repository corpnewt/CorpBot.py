# CorpBot.py
A *slightly* less clumsy python bot for discord

(Worth noting - youtube-dl on Ubuntu 16.04 at least had a preference for libav over ffmpeg.  That can be installed with `sudo apt-get install libav-tools`)

A sample of his `$help` command:


	A bot that does stuff.... probably

	Admin:
	  addadmin            Adds a new role to the admin list (admin only).
	  addxprole           Adds a new role to the xp promotion/demotion system (ad...
	  broadcast           Broadcasts a message to all connected servers.  Can onl...
	  lock                Toggles whether the bot only responds to admins (admin ...
	  prunexproles        Removes any roles from the xp promotion/demotion system...
	  removeadmin         Removes a role from the admin list (admin only).
	  removemotd          Removes the message of the day from the selected channel.
	  removexprole        Removes a role from the xp promotion/demotion system (a...
	  setdefaultrole      Sets the default role or position for auto-role assignm...
	  sethackrole         Sets the required role ID to add/remove hacks (admin on...
	  setlinkrole         Sets the required role ID to add/remove links (admin on...
	  setmadlibschannel   Sets the channel for MadLibs (admin only).
	  setmotd             Adds a message of the day to the selected channel.
	  setrules            Set the server's rules (admin only).
	  setstoprole         Sets the required role ID to stop the music player (adm...
	  setxp               Sets an absolute value for the member's xp (admin only).
	  setxpreserve        Set's an absolute value for the member's xp reserve (ad...
	  setxprole           Sets the required role ID to give xp, gamble, or feed t...
	  stoprole            Lists the required role to stop the bot from playing mu...
	  xprole              Lists the required role to give xp, gamble, or feed the...
	Ascii:
	  ascii               Beautify some text (font list at http://artii.herokuapp...
	Bot:
	  avatar              Sets the bot's avatar (owner only).
	  hostinfo            List info about the bot's host environment.
	  nickname            Set the bot's nickname (admin-only).
	  ping                Feeling lonely?
	  playgame            Sets the playing status of the bot (owner-only).
	  reboot              Shuts down the bot - allows for reboot if using the sta...
	  servers             Lists the number of servers I'm connected to!
	  setbotparts         Set the bot's parts - can be a url, formatted text, or ...
	  source              Link the github source.
	  speedtest           Run a network speed test (owner only).
	BotAdmin:
	  ban                 Bans the selected member (bot-admin only).
	  ignore              Adds a member to the bot's "ignore" list (bot-admin only).
	  ignored             Lists the users currently being ignored.
	  kick                Kicks the selected member (bot-admin only).
	  listen              Removes a member from the bot's "ignore" list (bot-admi...
	  mute                Prevents a member from sending messages in chat (bot-ad...
	  setuserparts        Set another user's parts list (bot-admin only).
	  unmute              Allows a muted member to send messages in chat (bot-adm...
	Calc:
	  calc                Do some math.
	CardsAgainstHumanity:
	  addbot              Adds a bot to the game.  Can only be done by the player...
	  addbots             Adds bots to the game.  Can only be done by the player ...
	  cahgames            Displays up to 10 CAH games in progress.
	  flushhand           Flushes the cards in your hand - can only be done once ...
	  game                Displays the game's current status.
	  hand                Shows your hand.
	  idlekick            Sets whether or not to kick members if idle for 5 minut...
	  joincah             Join a Cards Against Humanity game.  If no id or user i...
	  laid                Shows who laid their cards and who hasn't.
	  lay                 Lays a card or cards from your hand.  If multiple cards...
	  leavecah            Leaves the current game you're in.
	  newcah              Starts a new Cards Against Humanity game.
	  pick                As the judge - pick the winning card(s).
	  removebot           Removes a bot from the game.  Can only be done by the p...
	  removeplayer        Removes a player from the game.  Can only be done by th...
	  say                 Broadcasts a message to the other players in your game.
	  score               Display the score of the current game.
	Cats:
	  randomcat           Meow.
	Channel:
	  clean               Cleans the passed number of messages from the given cha...
	  islocked            Says whether the bot only responds to admins.
	  ismuted             Says whether a member is muted in chat.
	  listadmin           Lists admin roles and id's.
	  log                 Logs the passed number of messages from the given chann...
	  rolecall            Lists the number of users in a current role.
	  rules               Display the server's rules.
	ChatterBot:
	  chat                Chats with the bot.
	  setchatchannel      Sets the channel for bot chatter.
	Comic:
	  calvin              Displays the Calvin & Hobbes comic for the passed date ...
	  cyanide             Displays the Cyanide & Happiness comic for the passed d...
	  dilbert             Displays the Dilbert comic for the passed date (MM-DD-Y...
	  garfield            Displays the Garfield comic for the passed date (MM-DD-...
	  gmg                 Displays the Garfield Minus Garfield comic for the pass...
	  peanuts             Displays the Peanuts comic for the passed date (MM-DD-Y...
	  randcalvin          Randomly picks and displays a Calvin & Hobbes comic.
	  randcyanide         Randomly picks and displays a Cyanide & Happiness comic.
	  randgarfield        Randomly picks and displays a Garfield comic.
	  randgmg             Randomly picks and displays a Garfield Minus Garfield c...
	  randilbert          Randomly picks and displays a Dilbert comic.
	  randpeanuts         Randomly picks and displays a Peanuts comic.
	  randxkcd            Displays a random XKCD comic.
	  xkcd                Displays the XKCD comic for the passed date (MM-DD-YYYY...
	Debugging:
	  cleardebug          Deletes the debug.txt file (owner only).
	  heartbeat           Write to the console and attempt to send a message (own...
	  logdisable          Disables the passed, comma-delimited log vars.
	  logenable           Enables the passed, comma-delimited log vars.
	  logging             Outputs whether or not we're logging is enabled (bot-ad...
	  logpreset           Can select one of 3 available presets - quiet, normal, ...
	  setdebug            Turns on/off debugging (owner only - always off by defa...
	  setlogchannel       Sets the channel for Logging (bot-admin only).
	DrBeer:
	  drbeer              Put yourself in your place.
	Eat:
	  eat                 Eat like a boss.
	EightBall:
	  eightball           Get some answers.
	Example:
	  add                 Adds two numbers together.
	  choose              Chooses between multiple choices.
	  joined              Says when a member joined.
	  roll                Rolls a dice in NdN format.
	Face:
	  lastlenny           Who Lenny'ed last?
	  lastshrug           Who shrugged last?
	  lenny               Give me some Lenny.
	  shrug               Shrug it off.
	Feed:
	  feed                Feed the bot some xp!
	  hunger              How hungry is the bot?
	  iskill              Check the ded of the bot.
	  kill                Kill the bot... you heartless soul.
	  killrole            Lists the required role to kill/resurrect the bot.
	  resurrect           Restore life to the bot.  What magic is this?
	  setkillrole         Sets the required role ID to add/remove hacks (admin on...
	Humor:
	  fart                PrincessZoey :P
	  meme                Generate Meme
	  memetemps           Get Meme Templates
	Invite:
	  invite              Outputs a url you can use to invite me to your server.
	Lists:
	  addhack             Add a hack to the hack list.
	  addlink             Add a link to the link list.
	  hack                Retrieve a hack from the hack list.
	  hackinfo            Displays info about a hack from the hack list.
	  hackrole            Lists the required role to add hacks.
	  hacks               List all hacks in the hack list.
	  lastonline          Lists the last time a user was online if known.
	  link                Retrieve a link from the link list.
	  linkinfo            Displays info about a link from the link list.
	  linkrole            Lists the required role to add links.
	  links               List all links in the link list.
	  online              Lists the number of users online.
	  parts               Retrieve a member's parts list.
	  partstemp           Gives a copy & paste style template for setting a parts...
	  removehack          Remove a hack from the hack list.
	  removelink          Remove a link from the link list.
	  setparts            Set your own parts - can be a url, formatted text, or n...
	MadLibs:
	  madlibs             Let's play MadLibs!
	Music:
	  join                Joins a voice channel.
	  keep                Vote to keep a song.
	  pause               Pauses the currently played song.
	  play                Plays a song.
	  playing             Shows info about currently playing.
	  playlist            Shows current songs in the playlist.
	  removesong          Removes a song in the playlist by the index.
	  repeat              Checks or sets whether to repeat or not.
	  resume              Resumes the currently played song.
	  skip                Vote to skip a song. The song requester can automatical...
	  stop                Stops playing audio and leaves the voice channel.
	  summon              Summons the bot to join your voice channel.
	  unvote              Remove your song vote.
	  volume              Sets the volume of the currently playing song.
	  vote_stats          
	  willrepeat          Displays whether or not repeat is active.
	Profile:
	  addprofile          Add a profile to your profile list.
	  profile             Retrieve a profile from the passed user's profile list.
	  profileinfo         Displays info about a profile from the passed user's pr...
	  profiles            List all profiles in the passed user's profile list.
	  removeprofile       Remove a profile from your profile list.
	Promote:
	  demote              Auto-removes the required xp to demote the passed user ...
	  demoteto            Auto-removes the required xp to demote the passed user ...
	  promote             Auto-adds the required xp to promote the passed user to...
	  promoteto           Auto-adds the required xp to promote the passed user to...
	RateLimit:
	  ccooldown           Sets the cooldown in seconds between each command (owne...
	Reddit:
	  abandoned           Get something abandoned to look at.
	  answer              Spout out some interstellar answering... ?
	  aww                 Whenever you're down - uppify.
	  battlestation       Let's look at some pretty stuff.
	  brainfart           Spout out some uh... intellectual brilliance...
	  cablefail           Might as well be a noose...
	  carmod              Marvels of modern engineering.
	  dankmeme            Only the dankest.
	  dragon              From the past - when great winged beasts soared the skies.
	  earthporn           Earth is good.
	  lpt                 Become a pro - AT LIFE.
	  macsetup            Feast your eyes upon these setups.
	  meirl               Me in real life.
	  nocontext           Spout out some intersexual brilliance.
	  nosleep             I hope you're not tired...
	  question            Spout out some interstellar questioning... ?
	  randomdog           Bark if you know whassup.
	  redditimage         Try to grab an image from an image-based subreddit.
	  shittybattlestation Let's look at some shitty stuff.
	  shittylpt           Your advise is bad, and you should feel bad.
	  software            I uh... I wrote it myself.
	  starterpack         Starterpacks.
	  techsupport         Tech support irl.
	  thinkdeep           Spout out some intellectual brilliance.
	  wallpaper           Get something pretty to look at.
	  withcontext         Spout out some contextual brilliance.
	Remind:
	  clearmind           Clear the reminder index passed - or all if none passed.
	  reminders           List up to 10 pending reminders.
	  remindme            Set a reminder.
	Search:
	  bing                Get some uh... more searching done.
	  convert             convert currencies
	  duck                Duck Duck... GOOSE.
	  google              Get some searching done.
	  searchsite          Search corpnewt.com forums.
	Server:
	  dumpservers         Dumps a timpestamped list of servers into the same dire...
	  info                Displays the server info if any.
	  leaveserver         Leaves a server - can take a name or id (owner only).
	  prefix              Output's the server's prefix - custom or otherwise.
	  setinfo             Sets the server info (admin only).
	  setprefix           Sets the bot's prefix (admin only).
	ServerStats:
	  bottomservers       Lists the bottom servers I'm connected to ordered by po...
	  firstjoins          Lists the most recent users to join - default is 10, ma...
	  listservers         Lists the servers I'm connected to - default is 10, max...
	  messages            Lists the number of messages I've seen on this sever so...
	  recentjoins         Lists the most recent users to join - default is 10, ma...
	  topservers          Lists the top servers I'm connected to ordered by popul...
	  users               Lists the total number of users on all servers I'm conn...
	Settings:
	  claim               Claims the bot - once set, can only be changed by the c...
	  disown              Revokes ownership of the bot.
	  flush               Flush the bot settings to disk (admin only).
	  getsstat            Gets a server stat (admin only).
	  getstat             Gets the value for a specific stat for the listed membe...
	  owner               Lists the bot's current owner.
	  ownerlock           Locks/unlocks the bot to only respond to the owner.
	  prune               Iterate through all members on all connected servers an...
	  prunelocalsettings  Compares the current server's settings to the default l...
	  prunesettings       Compares all connected servers' settings to the default...
	  setowner            Sets the bot owner - once set, can only be changed by t...
	  setsstat            Sets a server stat (admin only).
	Setup:
	  setup               Runs first-time setup (server owner only).
	Star:
	  randstar            
	Strike:
	  addban              Adds the passed user to the ban list (bot-admin only).
	  addkick             Adds the passed user to the kick list (bot-admin only).
	  isbanned            Lists whether the user is in the ban list.
	  iskicked            Lists whether the user is in the kick list.
	  removeban           Removes the passed user from the ban list (bot-admin on...
	  removekick          Removes the passed user from the kick list (bot-admin o...
	  removestrike        Removes a strike given to a member (bot-admin only).
	  setstrikelevel      Sets the strike level of the passed user (bot-admin only).
	  setstrikelimit      Sets the number of strikes before advancing to the next...
	  strike              Give a user a strike (bot-admin only).
	  strikelimit         Lists the number of strikes before advancing to the nex...
	  strikes             Check a your own, or another user's total strikes (bot-...
	Time:
	  offset              See a member's UTC offset.
	  setoffset           Set your UTC offset.
	  time                Get UTC time +- an offset.
	Uptime:
	  uptime              Lists the bot's uptime.
	UrbanDict:
	  define              Gives the definition of the word passed.
	  randefine           Gives a random word and its definition.
	UserRole:
	  adduserrole         Adds a new role to the user role system (admin only).
	  listuserroles       Lists all roles for the user role system.
	  removeuserrole      Removes a role from the user role system (admin only).
	  setrole             Sets your role from the user role list.  You can only h...
	Welcome:
	  setgoodbye          Sets the goodbye message for your server (bot-admin onl...
	  setwelcome          Sets the welcome message for your server (bot-admin onl...
	  setwelcomechannel   Sets the channel for the welcome and goodbye messages (...
	  testgoodbye         Prints the current goodbye message (bot-admin only).
	  testwelcome         Prints the current welcome message (bot-admin only).
	Xp:
	  bottomxp            List the bottom xp-holders (max of 50).
	  defaultrole         Lists the default role that new users are assigned.
	  gamble              Gamble your xp reserves for a chance at winning xp!
	  leaderboard         List the top xp-holders (max of 50).
	  listxproles         Lists all roles, id's, and xp requirements for the xp p...
	  rank                Say the highest rank of a listed member.
	  recheckrole         Re-iterate through all members and assign the proper ro...
	  recheckroles        Re-iterate through all members and assign the proper ro...
	  stats               List the xp and xp reserve of a listed member.
	  xp                  Gift xp to other members.
	  xpinfo              Gives a quick rundown of the xp system.
	​No Category:
	  help                Shows this message.

	Type $help command for more info on a command.
	You can also type $help category for more info on a category.
