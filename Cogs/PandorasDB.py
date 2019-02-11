import json, discord, time, os
from datetime import datetime

def setup(bot):
    # Not a cog
    return

class PandorasDB:
    """The Pandora's Box of DB setup... maybe"""
    # Let's initialize with a file location
    def __init__(self, dbtype = "redis"):
        # Let's gather our stuffs
        self.dbtype = None
        try:
            import redis
            # Connect to the db
            self.db = redis.Redis(host="localhost",port=6379,db=0,decode_responses=True)
            self.dbtype = "redis"
            print("\nConnected to Redis db.\n")
            # let's map functions - needs to support the following:
            # 
            # Set/Get/Get All Global stat
            # Set/Get/Get All GlobalMember stat
            # Set/Get/Get All Server stat
            # Set/Get/Get All Server->Member stat
            self.empty_db   = self.empty_db_redis
            self.save_db    = self.save_db_redis
            # Globals
            self.get_global = self.get_global_stat_redis
            self.get_gmatch = self.get_global_matching_redis
            self.set_global = self.set_global_stat_redis
            self.del_global = self.del_global_stat_redis
            self.all_global = self.get_all_global_keys_redis
            # Global User
            self.get_guser  = self.get_global_user_stat_redis
            self.get_gumatch= self.get_global_user_matching_redis
            self.set_guser  = self.set_global_user_stat_redis
            self.del_guser  = self.del_global_user_stat_redis
            self.del_gusers = self.del_global_users_redis
            self.all_guser  = self.get_all_global_user_keys_redis
            # Server
            self.get_server = self.get_server_stat_redis
            self.get_smatch = self.get_server_matching_redis
            self.set_server = self.set_server_stat_redis
            self.del_server = self.del_server_stat_redis
            self.del_servers= self.del_servers_redis
            self.all_server = self.get_all_server_keys_redis
            # User
            self.get_user   = self.get_user_stat_redis
            self.get_umatch = self.get_user_stat_matching_redis
            self.set_user   = self.set_user_stat_redis
            self.del_user   = self.del_user_stat_redis
            self.del_users  = self.del_users_redis
            self.all_user   = self.get_all_user_keys_redis
        except:
            pass

    ###            ###
    # Helper Methods #
    ###            ###

    def save_db_redis(self):
        self.db.bgsave()

    def get_id(self, value):
        if isinstance(value, (discord.User, discord.Member, discord.Guild)):
            return value.id
        return str(value)

    def load(self, value, type_override = None):
        # Attempts to quickly load a value with the override applied if needed
        if type_override:
            try:
                return type(type_override)(value)
            except:
                pass
        # No explicit type set or it failed, let's try to load semi-intelligently
        if value == "null":
            return None
        elif value == "true":
            return True
        elif value == "false":
            return False
        else:
            try:
                return int(value)
            except:
                return json.loads(value)

    def save(self, value):
        # Attempts to quickly save a value with json serialization
        if value == None:
            return "null"
        elif value == True:
            return "true"
        elif value == False:
            return "false"
        elif isinstance(value, (int,float)):
            return str(value)
        else:
            return json.dumps(value)

    ###                         ###
    # Redis DB Specific Functions #
    ###                         ###

    # Raw getters/setters

    def get_hash_redis(self, name, key, default=None):
        # Retrieves and loads the json data for the passed named hash's key
        if not self.db.exists(name) or not self.db.hexists(name, key):
            return default
        try:
            return self.load(self.db.hget(name, key), int if key=="XP" or key=="XPReserve" else None)
        except:
            # Broken?
            return default

    def set_hash_redis(self, name, key, value):
        # Sets the key in the named hash to the json-serialized value
        return self.db.hset(name, key, self.save(value))
        
    def get_redis(self, key, default=None):
        # Retrieves and loads the json data passed from the redis db
        if not self.db.exists(key):
            return default
        return self.load(self.db.get(key))

    def set_redis(self, key, value):
        # Sets the key to the json-serialized value
        return self.db.set(key, self.save(value))

    def empty_db_redis(self):
        self.db.flushall()

    # Global getters/setters

    def get_global_stat_redis(self, stat, default=None):
        return self.get_redis(stat, default)

    def get_global_matching_redis(self, match):
        return list(self.db.scan_iter(match))

    def set_global_stat_redis(self, stat, value):
        return self.set_redis(stat, value)

    def del_global_stat_redis(self, stat):
        if self.db.exists(stat):
            return self.db.delete(stat)
        return 0

    def get_all_global_keys_redis(self):
        return list(self.db.scan_iter("[^globalmember][^server]*"))

    # Global Member getters/setters

    def get_global_user_stat_redis(self, user, stat, default=None):
        user = self.get_id(user)
        return self.get_hash_redis("globalmember",user,{}).get(stat,default)

    def get_global_user_matching_redis(self, match):
        return list(self.db.hscan_iter("globalmember",match))

    def set_global_user_stat_redis(self, user, stat, value):
        user = self.get_id(user)
        # Get the original user data or an empty dict if it doesn't exist
        mem = self.get_hash_redis("globalmember",user,{})
        mem[stat]=value
        # Save the updated dict back to the hash
        return self.set_hash_redis("globalmember",user,mem)

    def del_global_user_stat_redis(self, user, stat):
        user = self.get_id(user)
        # Get the original user data or an empty dict if it doesn't exist
        mem = self.get_hash_redis("globalmember",user,{})
        # Remove if exist
        d = mem.pop(value,None)
        # Save the result
        self.set_hash_redis("globalmember",user,mem)
        # Return the popped key - just in case
        return d

    def del_global_users_redis(self, users):
        if not isinstance(users, list):
            users = [users]
        for x in users:
            self.db.hdel("globalmember",x)
        return len(users)

    def get_all_global_user_keys_redis(self):
        return self.db.hkeys("globalmember")

    # Server Settings getters/setters

    def get_server_stat_redis(self, server, stat, default=None):
        server = self.get_id(server)
        return self.get_hash_redis("server:{}".format(server),stat,default)

    def get_server_matching_redis(self, server, match):
        return list(self.db.hscan_iter("server:{}".format(server),match))

    def set_server_stat_redis(self, server, stat, value):
        server = self.get_id(server)
        return self.set_hash_redis("server:{}".format(server),stat,value)

    def del_server_stat_redis(self, server, stat):
        server = self.get_id(server)
        return self.db.hdel("server:{}".format(server),stat)

    def del_servers_redis(self, servers):
        if not isinstance(servers, list):
            servers = [servers]
        for server in servers:
            for x in self.db.scan_iter("server:{}*".format(server)):
                self.db.delete(x)
        return len(servers)

    def get_all_server_keys_redis(self):
        return list(self.db.scan_iter("server*"))

    # Server-->User Settings getters/setters

    def get_user_stat_redis(self, user, server, stat, default=None):
        user = self.get_id(user)
        server = self.get_id(server)
        return self.get_hash_redis("server:{}:member".format(server),"{}:{}".format(user,stat),default)

    def get_user_stat_matching_redis(self, match, server):
        return list(self.db.hscan_iter("server:{}:member".format(server),match))

    def set_user_stat_redis(self, user, server, stat, value):
        user = self.get_id(user)
        server = self.get_id(server)
        return self.set_hash_redis("server:{}:member".format(server),"{}:{}".format(user, stat),value)

    def del_user_stat_redis(self, user, server, stat):
        user = self.get_id(user)
        server = self.get_id(server)
        return self.db.hdel("server:{}:member".format(server),"{}:{}".format(user,stat))

    def del_users_redis(self, users, server):
        if not isinstance(users, list):
            users = [users]
        server = self.get_id(server)
        for user in users:
            for x in self.db.hscan_iter("server:{}:member".format(server), "{}:*".format(user)):
                self.db.hdel("server:{}:member".format(server),x[0])
        return len(users)

    def get_all_user_keys_redis(self, server):
        server = self.get_id(server)
        return self.db.hkeys("server:{}:member".format(server))

    # Settings.json migration

    def migrate(self, f):
        # Function to migrate from a flat json file to a db
        # this will clear the db, load the json data, then
        # migrate all settings over.  There will be a logical order
        # to the naming of the keys:
        #
        # Global, top level values:
        #
        # PlistMax
        # PlistLevel
        # OwnerLock
        # Status
        # Type
        # Game
        # Stream
        # BlockedServers
        # ReturnChannel
        # CommandCooldown
        # Owner
        #
        # Global member stats formatting:
        #
        # globalmember hash
        #    0123456789  jsondict of stats
        #
        # HWActive
        # TimeZone
        # UTCOffset
        # Parts
        # Hardware
        #
        # Server-level stats formatting (see defaultServer):
        #
        # server:0123456789 hash
        #     statname
        #
        # Member stats per-server (see default_member):
        #
        # server:0123456789:members hash
        #     0123456789  jsondict of stats
        #
        if not self.dbtype:
            print("No database type set - cannot migrate settings.")
            return
        start = time.time()
        print("")
        print("Located {} - preparing for migration to {}...".format(f, self.dbtype))
        print(" - Loading {}...".format(f))
        try:
            oldset = json.load(open(f))
        except Exception as e:
            print(" --> Failed to open, attempting to rename...")
            print(" ----> {}".format(e))
            try:
                parts = f.split(".")
                if len(parts) == 1:
                    parts.append("json")
                name = ".".join(parts[0:-1]) + "-Error-{:%Y-%m-%d %H.%M.%S}".format(datetime.now()) + "." + parts[-1]
                os.rename(f, name)
                print(" ----> Renamed to {}".format(name))
            except Exception as e:
                print(" ----> Rename failed... wut... Bail.")
                print(" ------> {}".format(e))
                return
        # We should have the loaded json doc now
        # We first need to flush our db so we can import the settings
        print(" - Flushing current db...")
        self.empty_db()
        # Let's go over all the parts and add them to our db
        glob_count = 0
        serv_count = 0
        memb_count = 0
        stat_count = 0
        print(" - Parsing GlobalMembers...")
        glob = oldset.get("GlobalMembers",{})
        glob_count = len(glob)
        # Walk the globs and move them over using the above format
        for g in glob:
            stat_count += len(glob[g])
            for stat in glob[g]:
                if stat == "HWActive":
                    # This doesn't need to persist
                    continue
                self.set_guser(g, stat, glob[g][stat])
        
        # Walk the servers - and members when found in the same fashion
        print(" - Parsing Servers/Members...")
        servs = oldset.get("Servers",{})
        serv_count = len(servs)
        for s in servs:
            # Get the stats
            for t in servs[s]:
                if not t.lower() == "members":
                    stat_count += 1
                    # Not members, we just need to add the stat
                    self.set_server(s,t,servs[s][t])
                else:
                    # Membertime!
                    memb_count += len(servs[s][t])
                    for m in servs[s][t]:
                        # Iterate each member, and their subsequent stats
                        stat_count += len(servs[s][t][m])
                        for stat in servs[s][t][m]:
                            # LOOPS FOR DAYS
                            self.set_user(m,s,stat,servs[s][t][m][stat])
        # Iterate through any settings that aren't Servers or GlobalMembers
        print(" - Parsing remaining Global settings")
        for s in oldset:
            if s in ["GlobalMembers","Servers"]:
                continue
            stat_count += 1
            # Save the global setting!
            self.set_global(s, oldset[s])
        # Now we need to rename the file
        print(" - Renaming {}...".format(f))
        try:
            parts = f.split(".")
            if len(parts) == 1:
                parts.append("json")
            name = ".".join(parts[0:-1]) + "-Migrated-{:%Y-%m-%d %H.%M.%S}".format(datetime.now()) + "." + parts[-1]
            os.rename(f, name)
            print(" --> Renamed to {}".format(name))
        except Exception as e:
            print(" --> Rename failed... wut...")
            print(" ----> {}".format(e))
        print("Migrated {:,} GlobalMembers, {:,} Servers, {:,} Members, and {:,} total stats.".format(
            glob_count,
            serv_count,
            memb_count,
            stat_count
        ))
        print("Migration took {:,} seconds.".format(time.time() - start))
        print("")