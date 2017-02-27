This is the standard set of AIML files.


They require a bot that is AIML 1.0 complient.

Starting with Program D release 4.1.2, the "startup.aiml" file has been eliminated, 
along with the std-bot.aiml file.

Program D now uses the file "startup.xml" to set all bot specific values, and then
loads all AIML file which are in the specified bot AIML directory.

1. std-*.aiml
  The basic standard set, should be guaranteed as compliant with
  a given level of AIML.  They are becoming a "generic" reference, with as
  many personality and gender specific categories removed as possible.
 
2. dev-*.aiml
  Experimental set, should vary from bot to bot.
  They contain proprietary/experimental/work-in-progress AIML.
 
3. per-*.aiml
  Equivalent to std-*.aiml but with a customization of the bot
  personality; this is a work of a specific botmaster.


If you find errors, please bring them to my attention on the ALICEBOT General list.

Links to it can be found at http://www.alicebot.org/

Thomas Ringate

