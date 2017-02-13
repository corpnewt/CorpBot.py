# CorpBot.py
A *slightly* less clumsy python bot for discord

A sample of his `$help` command:

-

	A bot that does stuff.... probably

	Admin:
	  removeadmin        Removes a role from the admin list (admin only).
	  addxprole          Adds a new role to the xp promotion/demotion system (adm...
	  setmotd            Adds a message of the day to the selected channel.
	  broadcast          Broadcasts a message to all connected servers.  Can only...
	  stoprole           Lists the required role to stop the bot from playing music.
	  setstoprole        Sets the required role ID to stop the music player (admi...
	  removemotd         Removes the message of the day from the selected channel.
	  lock               Toggles whether the bot only responds to admins (admin o...
	  setxprole          Sets the required role ID to give xp, gamble, or feed th...
	  setxp              Sets an absolute value for the member's xp (admin only).
	  setdefaultrole     Sets the default role or position for auto-role assignment.
	  removexprole       Removes a role from the xp promotion/demotion system (ad...
	  xprole             Lists the required role to give xp, gamble, or feed the ...
	  setlinkrole        Sets the required role ID to add/remove links (admin only).
	  addadmin           Adds a new role to the xp promotion/demotion system (adm...
	  setxpreserve       Set's an absolute value for the member's xp reserve (adm...
	  prunexproles       Removes any roles from the xp promotion/demotion system ...
	  sethackrole        Sets the required role ID to add/remove hacks (admin only).
	  setrules           Set the server's rules (admin only).
	  setmadlibschannel  Sets the channel for MadLibs (admin only).
	Ascii:
	  ascii              Beautify some text (font list at http://artii.herokuapp....
	Bot:
	  setbotparts        Set the bot's parts - can be a url, formatted text, or n...
	  avatar             Sets the bot's avatar (owner only).
	  nickname           Set the bot's nickname (admin-only).
	  ping               Feeling lonely?
	  source             Link the github source.
	  servers            Lists the number of servers I'm connected to!
	  playgame           Sets the playing status of the bot (owner-only).
	  hostinfo           List info about the bot's host environment.
	  reboot             Shuts down the bot - allows for reboot if using the star...
	BotAdmin:
	  ignored            Lists the users currently being ignored.
	  unmute             Allows a muted member to send messages in chat (bot-admi...
	  listen             Removes a member from the bot's "ignore" list (bot-admin...
	  ban                Bans the selected member (bot-admin only).
	  mute               Prevents a member from sending messages in chat (bot-adm...
	  kick               Kicks the selected member (bot-admin only).
	  ignore             Adds a member to the bot's "ignore" list (bot-admin only).
	  setuserparts       Set another user's parts list (bot-admin only).
	Calc:
	  calc               Do some math.
	CardsAgainstHumanity:
	  addbot             Adds a bot to the game.  Can only be done by the player ...
	  cahgames           Displays up to 10 CAH games in progress.
	  newcah             Starts a new Cards Against Humanity game.
	  flushhand          Flushes the cards in your hand - can only be done once p...
	  removebot          Removes a bot from the game.  Can only be done by the pl...
	  addbots            Adds bots to the game.  Can only be done by the player w...
	  lay                Lays a card or cards from your hand.  If multiple cards ...
	  pick               As the judge - pick the winning card(s).
	  say                Broadcasts a message to the other players in your game.
	  score              Display the score of the current game.
	  joincah            Join a Cards Against Humanity game.  If no id or user is...
	  game               Displays the game's current status.
	  leavecah           Leaves the current game you're in.
	  hand               Shows your hand.
	  removeplayer       Removes a player from the game.  Can only be done by the...
	Cats:
	  randomcat          Meow.
	Channel:
	  clean              Cleans the passed number of messages from the given chan...
	  listadmin          Lists admin roles and id's.
	  rolecall           Lists the number of users in a current role.
	  rules              Display the server's rules.
	  ismuted            Says whether a member is muted in chat.
	  islocked           Says whether the bot only responds to admins.
	Comic:
	  randxkcd           Displays a random XKCD comic.
	  randgarfield       Randomly picks and displays a Garfield comic.
	  randgmg            Randomly picks and displays a Garfield Minus Garfield co...
	  randilbert         Randomly picks and displays a Dilbert comic.
	  cyanide            Displays the Cyanide & Happiness comic for the passed da...
	  randpeanuts        Randomly picks and displays a Peanuts comic.
	  garfield           Displays the Garfield comic for the passed date (MM-DD-Y...
	  peanuts            Displays the Peanuts comic for the passed date (MM-DD-YY...
	  randcalvin         Randomly picks and displays a Calvin & Hobbes comic.
	  xkcd               Displays the XKCD comic for the passed date (MM-DD-YYYY)...
	  calvin             Displays the Calvin & Hobbes comic for the passed date (...
	  dilbert            Displays the Dilbert comic for the passed date (MM-DD-YY...
	  gmg                Displays the Garfield Minus Garfield comic for the passe...
	  randcyanide        Randomly picks and displays a Cyanide & Happiness comic.
	Debugging:
	  cleardebug         Deletes the debug.txt file (owner only).
	  setdebug           Turns on/off debugging (owner only - always off by defau...
	DrBeer:
	  drbeer             Put yourself in your place.
	Eat:
	  eat                Eat like a boss.
	EightBall:
	  eightball          Get some answers.
	Example:
	  choose             Chooses between multiple choices.
	  roll               Rolls a dice in NdN format.
	  add                Adds two numbers together.
	  joined             Says when a member joined.
	Face:
	  shrug              Shrug it off.
	  lastlenny          Who Lenny'ed last?
	  lenny              Give me some Lenny.
	  lastshrug          Who shrugged last?
	Feed:
	  setkillrole        Sets the required role ID to add/remove hacks (admin only).
	  iskill             Check the ded of the bot.
	  resurrect          Restore life to the bot.  What magic is this?
	  feed               Feed the bot some xp!
	  kill               Kill the bot... you heartless soul.
	  hunger             How hungry is the bot?
	  killrole           Lists the required role to kill/resurrect the bot.
	Humor:
	  fart               PrincessZoey :P
	  meme               Generate Meme
	  memetemps          Get Meme Templates
	Invite:
	  invite             Outputs a url you can use to invite me to your server.
	Lists:
	  lastonline         Lists the last time a user was online if known.
	  linkrole           Lists the required role to add links.
	  setparts           Set your own parts - can be a url, formatted text, or no...
	  links              List all links in the link list.
	  addhack            Add a hack to the hack list.
	  hack               Retrieve a hack from the hack list.
	  hacks              List all hacks in the hack list.
	  linkinfo           Displays info about a link from the link list.
	  addlink            Add a link to the link list.
	  removehack         Remove a hack from the hack list.
	  parts              Retrieve a member's parts list.
	  online             Lists the number of users online.
	  hackinfo           Displays info about a hack from the hack list.
	  hackrole           Lists the required role to add hacks.
	  link               Retrieve a link from the link list.
	  partstemp          Gives a copy & paste style template for setting a parts ...
	  removelink         Remove a link from the link list.
	MadLibs:
	  madlibs            Let's play MadLibs!
	Music:
	  removesong         Removes a song in the playlist by the index.
	  volume             Sets the volume of the currently playing song.
	  keep               Vote to keep a song.
	  play               Plays a song.
	  stop               Stops playing audio and leaves the voice channel.
	  vote_stats         
	  unvote             Remove your song vote.
	  summon             Summons the bot to join your voice channel.
	  willrepeat         Displays whether or not repeat is active.
	  skip               Vote to skip a song. The song requester can automaticall...
	  playlist           Shows current songs in the playlist.
	  repeat             Checks or sets whether to repeat or not.
	  join               Joins a voice channel.
	  resume             Resumes the currently played song.
	  pause              Pauses the currently played song.
	  playing            Shows info about currently playing.
	Profile:
	  profiles           List all profiles in the passed user's profile list.
	  addprofile         Add a profile to your profile list.
	  profile            Retrieve a profile from the passed user's profile list.
	  profileinfo        Displays info about a profile from the passed user's pro...
	  removeprofile      Remove a profile from your profile list.
	Promote:
	  demoteto           Auto-removes the required xp to demote the passed user t...
	  promote            Auto-adds the required xp to promote the passed user to ...
	  demote             Auto-removes the required xp to demote the passed user t...
	  promoteto          Auto-adds the required xp to promote the passed user to ...
	Reddit:
	  question           Spout out some interstellar questioning... ?
	  randomdog          Bark if you know whassup.
	  dragon             From the past - when great winged beasts soared the skies.
	  thinkdeep          Spout out some intellectual brilliance.
	  dankmemes          Only the dankest.
	  abandoned          Get something abandoned to look at.
	  brainfart          Spout out some uh... intellectual brilliance...
	  nocontext          Spout out some intersexual brilliance.
	  wallpaper          Get something pretty to look at.
	  starterpack        Starterpacks.
	  software           I uh... I wrote it myself.
	  aww                Whenever you're down - uppify.
	  cablefail          Might as well be a noose...
	  earthporn          Earth is good.
	  answer             Spout out some interstellar answering... ?
	  meirl              Me in real life.
	  techsupport        Tech support irl.
	Remind:
	  clearmind          Clear all reminders.
	  reminders          List up to 10 pending reminders.
	  remindme           Set a reminder.
	Search:
	  convert            convert currencies
	  searchsite         Search corpnewt.com forums.
	  bing               Get some uh... more searching done.
	  duck               Duck Duck... GOOSE.
	  google             Get some searching done.
	Server:
	  setinfo            Sets the server info (admin only).
	  info               Displays the server info if any.
	ServerStats:
	  messages           Lists the number of messages I've seen on this sever so ...
	  topservers         Lists the top servers I'm connected to ordered by popula...
	  bottomservers      Lists the bottom servers I'm connected to ordered by pop...
	  users              Lists the total number of users on all servers I'm conne...
	  recentjoins        Lists the most recent users to join - default is 10, max...
	  firstjoins         Lists the most recent users to join - default is 10, max...
	  listservers        Lists the servers I'm connected to - default is 10, max ...
	Settings:
	  setowner           Sets the bot owner - once set, can only be changed by th...
	  prunesettings      Compares all connected servers' settings to the default ...
	  prunelocalsettings Compares the current server's settings to the default li...
	  disown             Revokes ownership of the bot.
	  getstat            Gets the value for a specific stat for the listed member...
	  flush              Flush the bot settings to disk (admin only).
	  claim              Claims the bot - once set, can only be changed by the cu...
	  prune              Iterate through all members on all connected servers and...
	  setsstat           Sets a server stat (admin only).
	  ownerlock          Locks/unlocks the bot to only respond to the owner.
	  getsstat           Gets a server stat (admin only).
	  owner              Lists the bot's current owner.
	Setup:
	  setup              Runs first-time setup (server owner only).
	Strike:
	  removestrike       Removes a strike given to a member (bot-admin only).
	  strike             Give a user a strike (bot-admin only).
	  removekick         Removes the passed user from the kick list (bot-admin on...
	  isbanned           Lists whether the user is in the ban list.
	  strikes            Check a your own, or another user's total strikes (bot-a...
	  addban             Adds the passed user to the ban list (bot-admin only).
	  strikelimit        Lists the number of strikes before advancing to the next...
	  setstrikelevel     Sets the strike level of the passed user (bot-admin only).
	  iskicked           Lists whether the user is in the kick list.
	  addkick            Adds the passed user to the kick list (bot-admin only).
	  removeban          Removes the passed user from the ban list (bot-admin only).
	  setstrikelimit     Sets the number of strikes before advancing to the next ...
	Time:
	  setoffset          Set your UTC offset.
	  offset             See a member's UTC offset.
	  time               Get UTC time +- an offset.
	Uptime:
	  uptime             Lists the bot's uptime.
	UrbanDict:
	  define             Gives the definition of the word passed.
	  randefine          Gives a random word and its definition.
	Welcome:
	  setwelcomechannel  Sets the channel for the welcome and goodbye messages (b...
	  testwelcome        Prints the current welcome message (bot-admin only).
	  testgoodbye        Prints the current goodbye message (bot-admin only).
	  setwelcome         Sets the welcome message for your server (bot-admin only...
	  setgoodbye         Sets the goodbye message for your server (bot-admin only...
	Xp:
	  listxproles        Lists all roles, id's, and xp requirements for the xp pr...
	  bottomxp           List the bottom xp-holders (max of 50).
	  xpinfo             Gives a quick rundown of the xp system.
	  gamble             Gamble your xp reserves for a chance at winning xp!
	  xp                 Gift xp to other members.
	  leaderboard        List the top xp-holders (max of 50).
	  recheckroles       Re-iterate through all members and assign the proper rol...
	  stats              List the xp and xp reserve of a listed member.
	  defaultrole        Lists the default role that new users are assigned.
	  rank               Say the highest rank of a listed member.
	  recheckrole        Re-iterate through all members and assign the proper rol...
	​No Category:
	  help               Shows this message.

	Type $help command for more info on a command.
	You can also type $help category for more info on a category.
