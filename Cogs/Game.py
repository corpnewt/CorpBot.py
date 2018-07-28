import asyncio
import discord
import time
import parsedatetime
from igdb_api_python.igdb import igdb
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import CheckRoles

Platform_Lookup ={3:'Linux',
        4:'Nintendo 64',
        5:'Wii',
        6:'PC (Microsoft Windows)',
        7:'PlayStation',
        8:'PlayStation 2',
        9:'PlayStation 3',
        11:'Xbox',
        12:'Xbox 360',
        13:'PC DOS',
        14:'Mac',
        15:'Commodore C64/128',
        16:'Amiga',
        18:'Nintendo Entertainment System (NES)',
        19:'Super Nintendo (SNES)',
        20:'Nintendo DS',
        21:'Nintendo GameCube',
        22:'Game Boy Color',
        23:'Dreamcast',
        24:'Game Boy Advance',
        25:'Amstrad CPC',
        26:'ZX Spectrum',
        27:'MSX',
        29:'Sega Mega Drive/Genesis',
        30:'Sega 32X',
        32:'Sega Saturn',
        33:'Game Boy',
        34:'Android',
        35:'Sega Game Gear',
        36:'Xbox Live Arcade',
        37:'Nintendo 3DS',
        38:'PlayStation Portable',
        39:'iOS',
        41:'Wii U',
        42:'N-Gage',
        44:'Tapwave Zodiac',
        45:'PlayStation Network',
        46:'PlayStation Vita',
        47:'Virtual Console (Nintendo)',
        48:'PlayStation 4',
        49:'Xbox One',
        50:'3DO Interactive Multiplayer',
        51:'Family Computer Disk System',
        52:'Arcade',
        53:'MSX2',
        55:'Mobile',
        56:'WiiWare',
        57:'WonderSwan',
        58:'Super Famicom',
        59:'Atari 2600',
        60:'Atari 7800',
        61:'Atari Lynx',
        62:'Atari Jaguar',
        63:'Atari ST/STE',
        64:'Sega Master System',
        65:'Atari 8-bit',
        66:'Atari 5200',
        67:'Intellivision',
        68:'ColecoVision',
        68:'ColecoVision',
        70:'Vectrex',
        71:'Commodore VIC-20',
        72:'Ouya',
        73:'BlaclkBerry OS',
        74:'Windows Phone',
        75:'Apple II',
        77:'Sharp X1',
        78:'Sega CD',
        79:'Neo Geo MVS',
        80:'Neo Geo AES',
        82:'Web browser',
        84:'SG-1000',
        85:'Donner Model 30',
        86:'TurboGrafx-16/PC Engine',
        87:'Virtual Boy',
        88:'Odyssey',
        89:'Microvision',
        90:'Commodore PET',
        91:'Bally Astrocade',
        92:'SteamOS',
        93:'Commodore 16',
        94:'Commodore Plus/4',
        95:'PDP-1',
        96:'PDP-10',
        97:'PDP-8',
        98:'DEC GT40',
        99:'Family Computer (FAMICOM)',
        100:'Analogue electronics',
        101:'Ferranti Nimrod Computer',
        102:'EDSAC',
        103:'PDP-7',
        104:'HP 2100',
        105:'HP 3000',
        106:'SDS Sigma 7',
        107:'Call-A-Computer time-shared mainframe computer system',
        108:'PDP-11',
        109:'CDC Cyber 70',
        110:'PLATO',
        111:'Imlac PDS-1',
        112:'Microcomputer',
        113:'OnLive Game System',
        114:'Amiga CD32',
        115:'Apple IIGS',
        116:'Acorn Archimedes',
        117:'Philips CD-i',
        118:'FM Towns',
        119:'Neo Geo Pocket',
        120:'Neo Geo Pocket Color',
        121:'Sharp X68000',
        122:'Nuon',
        123:'WonderSwan Color',
        124:'SwanCrystal',
        125:'PC-8801',
        126:'TRS-80',
        127:'Fairchild Channel F',
        128:'PC Engine SuperGrafx',
        129:'Texas Instruments TI-99',
        130:'Nintendo Switch',
        131:'Nintendo PlayStation',
        132:'Amazon Fire TV',
        133:'Philips Videopac G7000',
        134:'Acorn Electron',
        135:'Hyper Neo Geo 64',
        136:'Neo Geo CD',
        137:'New Nintendo 3DS',
        138:'VC 4000',
        139:'1292 Advanced Programmable Video System',
        140:'AY-3-8500',
        141:'AY-3-8610',
        142:'PC-50X Family',
        143:'AY-3-8760',
        144:'AY-3-8710',
        145:'AY-3-8603',
        146:'AY-3-8605',
        147:'AY-3-8606',
        148:'AY-3-8607',
        149:'PC-98',
        150:'Turbografx-16/PC Engine CD',
        151:'TRS-80 Color Computer',
        152:'FM-7',
        153:'Dragon 32/64',
        154:'Amstrad PCW',
        155:'Tatung Einstein',
        156:'Thomson MO5',
        157:'NEC PC-6000 Series',
        158:'Commodore CDTV',
        159:'Nintendo DSi',
        160:'Nintendo eShop',
        161:'Windows Mixed Reality',
        162:'Oculus VR',
        163:'SteamVR',
        164:'Daydream',
        164:'Daydream',
        165:'PlayStation VR'}

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Lookup(bot, settings))

class Lookup:
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    def suppressed(self, guild, msg):
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(guild, "SuppressMentions"):
            return Nullify.clean(msg)
        else:
            return msg

    @commands.command()
    async def gamelookup(self, ctx, *,game: str):
        igdb1 = igdb("YourKeyHere")
        result = igdb1.games({
            'search': "{}".format(game),
            'fields': ['name','game',
                'first_release_date','summary',
                'cover','platforms','url']
            })
        result = result.body
        GameInfo=result[0]
        cover = GameInfo['cover']
        platformconvert = GameInfo['platforms']
        gameurl = GameInfo['url']
        platformconvert.sort()
        plat = ''
        for i in platformconvert:
            plat += Platform_Lookup[i] + '\n'
        date = time.strftime("%a, %b %d %Y", time.localtime(GameInfo['first_release_date']/1000.))
        summary = GameInfo['summary'] if len(GameInfo['summary']) <= 1024 else GameInfo['summary'][:1021]+'...'
        embed=discord.Embed(title=GameInfo['name'], url=gameurl, color=0xed)
        embed.add_field(name="Summary", value=summary, inline=False)
        embed.add_field(name="Release Date", value=date, inline=True)
        embed.add_field(name="Platforms", value=plat, inline=True)
        embed.set_thumbnail(url="http:{}".format(cover['url']))
        await ctx.send(embed=embed)

