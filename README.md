# CorpBot.py
A *slightly* less clumsy python bot for discord

A sample of his `$help` command:

-

        A bot that does stuff.... probably 
    Admin: 
        stoprole           Lists the required role to stop the bot from playing music. 
        setxprole          Sets the required role ID to give xp, gamble, or feed th... 
        setstoprole        Sets the required role ID to stop the music player (admi... 
        mute               Prevents a member from sending messages in chat (admin-o... 
        setxpreserve       Set's an absolute value for the member's xp reserve (adm... 
        removexprole       Removes a role from the xp promotion/demotion system (ad... 
        xprole             Lists the required role to give xp, gamble, or feed the ... 
        setmotd            Adds a message of the day to the selected channel. 
        removeadmin        Removes a role from the admin list (admin only). 
        unmute             Allows a muted member to send messages in chat (admin-on... 
        setmadlibschannel  Sets the required role ID to stop the music player (admi... 
        sethackrole        Sets the required role ID to add/remove hacks (admin only). 
        addxprole          Adds a new role to the xp promotion/demotion system (adm... 
        broadcast          Broadcasts a message to all connected servers.  Can only... 
        ignored            Lists the users currently being ignored. 
        addadmin           Adds a new role to the xp promotion/demotion system (adm... 
        lock               Toggles whether the bot only responds to admins (admin-o... 
        setrules           Set the server's rules (admin-only). 
        listen             Removes a member from the bot's "ignore" list (admin-only). 
        setlinkrole        Sets the required role ID to add/remove links (admin only). 
        setdefaultrole     Sets the default role or position for auto-role assignment. 
        removemotd         Removes the message of the day from the selected channel. 
        ignore             Adds a member to the bot's "ignore" list (admin-only). 
        setuserparts       Set another user's parts list (admin only). 
        Bot: 
        avatar             Sets the bot's avatar (owner-only). 
        nickname           Set the bot's nickname (admin-only). 
        setbotparts        Set the bot's parts - can be a url, formatted text, or n... 
        playgame           Sets the playing status of the bot (owner-only). 
        servers            Lists the number of servers I'm connected to 
        Channel: 
        islocked           Says whether the bot only responds to admins. 
        listadmin          Lists admin roles and id's. 
        rules              Display the server's rules. 
        ismuted            Says whether a member is muted in chat. 
    Comic: 
        randcalvin         Randomly picks and displays a Calvin & Hobbes comic. 
        peanuts            Displays the Peanuts comic for the passed date (MM-DD-YY... 
        xkcd               Displays the XKCD comic for the passed date (MM-DD-YYYY)... 
        gmg                Displays the Garfield Minus Garfield comic for the passe... 
        randcyanide        Randomly picks and displays a Cyanide & Happiness comic. 
        randgmg            Randomly picks and displays a Garfield Minus Garfield co... 
        randgarfield       Randomly picks and displays a Garfield comic. 
        randxkcd           Displays a random XKCD comic. 
        calvin             Displays the Calvin & Hobbes comic for the passed date (... 
        cyanide            Displays the Cyanide & Happiness comic for the passed da... 
        garfield           Displays the Garfield comic for the passed date (MM-DD-Y... 
        randpeanuts        Randomly picks and displays a Peanuts comic. 
        randilbert         Randomly picks and displays a Dilbert comic. 
        dilbert            Displays the Dilbert comic for the passed date (MM-DD-YY... 
        DrBeer: 
        drbeer             Put yourself in your place. 
        Example: 
        joined             Says when a member joined. 
        choose             Chooses between multiple choices. 
        add                Adds two numbers together. 
        roll               Rolls a dice in NdN format. 
    Feed: 
        setkillrole        Sets the required role ID to add/remove hacks (admin only). 
        feed               Feed the bot some xp 
        iskill             Check the ded of the bot. 
        killrole           Lists the required role to kill/resurrect the bot. 
        resurrect          Restore life to the bot.  What magic is this? 
        hunger             How hungry is the bot? 
        kill               Kill the bot... you heartless soul. 
        Humor: 
        fart               PrincessZoey :P 
        Lists: 
        setparts           Set your own parts - can be a url, formatted text, or no... 
        linkinfo           Displays info about a link from the link list. 
        hacks              List all hacks in the hack list. 
        hack               Retrieve a hack from the hack list. 
        removehack         Remove a hack from the hack list. 
        online             Lists the number of users online. 
        addlink            Add a link to the link list. 
        parts              Retrieve a member's parts list. 
        hackinfo           Displays info about a hack from the hack list. 
        hackrole           Lists the required role to add hacks. 
        link               Retrieve a link from the link list. 
        addhack            Add a hack to the hack list. 
        removelink         Remove a link from the link list. 
        partstemp          Gives a copy & paste style template for setting a parts ... 
        links              List all links in the link list. 
        linkrole           Lists the required role to add links. 
    MadLibs: 
        madlibs            Let's play MadLibs  Start with $madlibs, select works w... 
    Music: 
        volume             Sets the volume of the currently playing song. 
        summon             Summons the bot to join your voice channel. 
        play               Plays a song. 
        resume             Resumes the currently played song. 
        join               Joins a voice channel. 
        playing            Shows info about currently playing. 
        skip               Vote to skip a song. The song requester can automaticall... 
        pause              Pauses the currently played song. 
        stop               Stops playing audio and leaves the voice channel. 
    Reddit: 
        starterpack        Starterpacks. 
        earthporn          Earth is good. 
        meirl              Me in real life. 
        wallpaper          Get something pretty to look at. 
        techsupport        Tech support irl. 
        brainfart          Spout out some uh... intellectual brilliance... 
        software           I uh... I wrote it myself. 
        nocontext          Spout out some intersexual brilliance. 
        thinkdeep          Spout out some intellectual brilliance. 
        answer             Spout out some interstellar answering... ? 
        dankmemes          Only the dankest. 
        abandoned          Get something abandoned to look at. 
        question           Spout out some interstellar questioning... ? 
    Settings: 
        setsstat           Sets a server stat (admin only). 
        getstat            Gets the value for a specific stat for the listed member... 
        getsstat           Gets a server stat (admin only). 
        prunesettings      Compares all connected servers' settings to the default ... 
        owner              Sets the bot owner - once set, can only be changed by th... 
        flush              Flush the bot settings to disk (admin only). 
        prunelocalsettings Compares the current server's settings to the default li... 
        disown             Revokes ownership of the bot. 
        prune              Iterate through all members on all connected servers and... 
    Uptime: 
        uptime             Lists the bot's uptime. 
    Xp: 
        listxproles        Lists all roles, id's, and xp requirements for the xp pr... 
        stats              List the xp and xp reserve of a listed member. 
        gamble             Gamble your xp reserves for a chance at winning xp 
        topxp              List the top 10 xp-holders - or all members, if there ar... 
        rank               Say the highest rank of a listed member. 
        setxp              Sets an absolute value for the member's xp (admin only). 
        xp                 Gift xp to other members. 
        bottomxp           List the bottom 10 xp-holders - or all members, if there... 
        defaultrole        Lists the default role that new users are assigned. 
    ​No Category: 
        help               Shows this message. 
    Type $help command for more info on a command. 
    You can also type $help category for more info on a category. 
