# CorpBot.py
A *slightly* less clumsy python bot for discord

A sample of his `$help` command:

-

      A bot that does stuff.... probably

      Admin:
        setxprole          Sets the required role ID to give xp, gamble, or feed th...
        addadmin           Adds a new role to the xp promotion/demotion system (adm...
        setmotd            Adds a message of the day to the selected channel.
        unmute             Allows a muted member to send messages in chat (admin-on...
        broadcast          Broadcasts a message to all connected servers.  Can only...
        stoprole           Lists the required role to stop the bot from playing music.
        removeadmin        Removes a role from the admin list (admin only).
        setdefaultrole     Sets the default role or position for auto-role assignment.
        lock               Toggles whether the bot only responds to admins (admin-o...
        xprole             Lists the required role to give xp, gamble, or feed the ...
        setlinkrole        Sets the required role ID to add/remove links (admin only).
        removemotd         Removes the message of the day from the selected channel.
        ignored            Lists the users currently being ignored.
        mute               Toggles whether a member can send messages in chat (admi...
        setxpreserve       Set's an absolute value for the member's xp reserve (adm...
        setuserparts       Set another user's parts list (admin only).
        setstoprole        Sets the required role ID to stop the music player (admi...
        listen             Removes a member from the bot's "ignore" list (admin-only).
        setrules           Set the server's rules (admin-only).
        setmadlibschannel  Sets the required role ID to stop the music player (admi...
        removexprole       Removes a role from the xp promotion/demotion system (ad...
       sethackrole        Sets the required role ID to add/remove hacks (admin only).
        ignore             Adds a member to the bot's "ignore" list (admin-only).
        addxprole          Adds a new role to the xp promotion/demotion system (adm...
      Bot:
    nickname           Set the bot's nickname (admin-only).
    playgame           Sets the playing status of the bot (owner-only).
    avatar             Sets the bot's avatar (owner-only).
    servers            Lists the number of servers I'm connected to!
    setbotparts        Set the bot's parts - can be a url, formatted text, or n...
      Channel:
        ismuted            Says whether a member is muted in chat.
        rules              Display the server's rules.
        islocked           Says whether the bot only responds to admins.
        listadmin          Lists admin roles and id's.
      Comic:
        calvin             Displays the Calvin & Hobbes comic for the passed date (...
        garfield           Displays the Garfield comic for the passed date (MM-DD-Y...
        randilbert         Randomly picks and displays a Dilbert comic.
        gmg                Displays the Garfield Minus Garfield comic for the passe...
        dilbert            Displays the Dilbert comic for the passed date (MM-DD-YY...
        randgarfield       Randomly picks and displays a Garfield comic.
        randpeanuts        Randomly picks and displays a Peanuts comic.
        peanuts            Displays the Peanuts comic for the passed date (MM-DD-YY...
        randgmg            Randomly picks and displays a Garfield Minus Garfield co...
        randcyanide        Randomly picks and displays a Cyanide & Happiness comic.
        randxkcd           Displays a random XKCD comic.
        cyanide            Displays the Cyanide & Happiness comic for the passed da...
        randcalvin         Randomly picks and displays a Calvin & Hobbes comic.
        xkcd               Displays the XKCD comic for the passed date (MM-DD-YYYY)...
      DrBeer:
        drbeer             Put yourself in your place.
      Example:
        add                Adds two numbers together.
        joined             Says when a member joined.
        choose             Chooses between multiple choices.
        roll               Rolls a dice in NdN format.
      Feed:
        setkillrole        Sets the required role ID to add/remove hacks (admin only).
        feed               Feed the bot some xp!
        resurrect          Restore life to the bot.  What magic is this?
        iskill             Check the ded of the bot.
        kill               Kill the bot... you heartless soul.
        hunger             How hungry is the bot?
        killrole           Lists the required role to kill/resurrect the bot.
      Humor:
        fart               PrincessZoey :P
      Lists:
        addhack            Add a hack to the hack list.
        hackrole           Lists the required role to add hacks.
        hacks              List all hacks in the hack list.
        removehack         Remove a hack from the hack list.
        partstemp          Gives a copy & paste style template for setting a parts ...
        hack               Retrieve a hack from the hack list.
        linkrole           Lists the required role to add links.
        link               Retrieve a link from the link list.
        removelink         Remove a link from the link list.
        parts              Retrieve a member's parts list.
        online             Lists the number of users online.
        linkinfo           Displays info about a link from the link list.
        setparts           Set your own parts - can be a url, formatted text, or no...
        hackinfo           Displays info about a hack from the hack list.
        addlink            Add a link to the link list.
        links              List all links in the link list.
      MadLibs:
        madlibs            Let's play MadLibs!  Start with $madlibs, select works w...
      Music:
        resume             Resumes the currently played song.
        skip               Vote to skip a song. The song requester can automaticall...
        stop               Stops playing audio and leaves the voice channel.
        playing            Shows info about currently playing.
        summon             Summons the bot to join your voice channel.
        join               Joins a voice channel.
        volume             Sets the volume of the currently playing song.
        pause              Pauses the currently played song.
        play               Plays a song.
      Reddit:
        thinkdeep          Spout out some intellectual brilliance.
        earthporn          Earth is good.
        dankmemes          Only the dankest.
        nocontext          Spout out some intersexual brilliance.
        answer             Spout out some interstellar answering... ?
        software           I uh... I wrote it myself.
        techsupport        Tech support irl.
        meirl              Me in real life.
        abandoned          Get something abandoned to look at.
        brainfart          Spout out some uh... intellectual brilliance...
        starterpack        Starterpacks.
        question           Spout out some interstellar questioning... ?
        wallpaper          Get something pretty to look at.
      Settings:
        prune              Iterate through all members on all connected servers and...
        setsstat           Sets a server stat (admin only).
        flush              Flush the bot settings to disk (admin only).
        owner              Sets the bot owner - once set, can only be changed by th...
        prunelocalsettings Compares the current server's settings to the default li...
        getsstat           Gets a server stat (admin only).
        prunesettings      Compares all connected servers' settings to the default ...
        disown             Revokes ownership of the bot.
        getstat            Gets the value for a specific stat for the listed member...
      Uptime:
        uptime             Lists the bot's uptime.
      Xp:
        bottomxp           List the bottom 10 xp-holders - or all members, if there...
        xp                 Gift xp to other members.
        stats              List the xp and xp reserve of a listed member.
        gamble             Gamble your xp reserves for a chance at winning xp!
        setxp              Sets an absolute value for the member's xp (admin only).
        defaultrole        Lists the default role that new users are assigned.
        rank               Say the highest rank of a listed member.
        topxp              List the top 10 xp-holders - or all members, if there ar...
        listxproles        Lists all roles, id's, and xp requirements for the xp pr...
      No Category:
        help               Shows this message.

      Type $help command for more info on a command.
      You can also type $help category for more info on a category.
