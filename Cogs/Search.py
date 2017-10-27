import asyncio
import discord
import json
import os
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import TinyURL
from   Cogs import DL
from   pyquery import PyQuery as pq

def setup(bot):
	# Add the bot and deps
	auth = "corpSiteAuth.txt"
	bot.add_cog(Search(bot, auth))

class Search:

	# Init with the bot reference
	def __init__(self, bot, auth_file: str = None):
		self.bot = bot
		self.site_auth = None
		if os.path.isfile(auth_file):
		        with open(auth_file, 'r') as f:
		                self.site_auth = f.read()

	@commands.command(pass_context=True)
	async def google(self, ctx, *, query = None):
		"""Get some searching done."""

		if query == None:
			msg = 'You need a topic for me to Google.'
			await ctx.channel.send(msg)
			return

		lmgtfy = "http://lmgtfy.com/?q={}".format(quote(query))
		lmgtfyT = TinyURL.tiny_url(lmgtfy)
		msg = '*{}*, you can find your answers here:\n\n<{}>'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		# Say message
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def bing(self, ctx, *, query = None):
		"""Get some uh... more searching done."""

		if query == None:
			msg = 'You need a topic for me to Bing.'
			await ctx.channel.send(msg)
			return

		lmgtfy = "http://letmebingthatforyou.com/?q={}".format(quote(query))
		lmgtfyT = TinyURL.tiny_url(lmgtfy)
		msg = '*{}*, you can find your answers here:\n\n<{}>'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		# Say message
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def duck(self, ctx, *, query = None):
		"""Duck Duck... GOOSE."""

		if query == None:
			msg = 'You need a topic for me to DuckDuckGo.'
			await ctx.channel.send(msg)
			return

		lmgtfy = "https://lmddgtfy.net/?q={}".format(quote(query))
		lmgtfyT = TinyURL.tiny_url(lmgtfy)
		msg = '*{}*, you can find your answers here:\n\n<{}>'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		# Say message
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def searchsite(self, ctx, category_name = None, *, query = None):
		"""Search corpnewt.com forums."""

		auth = self.site_auth

		if auth == None:
			await ctx.channel.send("Sorry this feature is not supported!")
			return

		if query == None or category_name == None:
			msg = "Usage: `{}searchsite [category] [search term]`\n\n Categories can be found at:\n\nhttps://corpnewt.com/".format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		categories_url = "https://corpnewt.com/api/categories"
		categories_json = await DL.async_json(categories_url, headers={'Authorization': auth})
		categories = categories_json["categories"]

		category = await self.find_category(categories, category_name)

		if category == None:
			await ctx.channel.send("Usage: `{}searchsite [category] [search term]`\n\n Categories can be found at:\n\nhttps://corpnewt.com/".format(ctx.prefix))
			return

		search_url = "https://corpnewt.com/api/search?term={}&in=titlesposts&categories[]={}&searchChildren=true&showAs=posts".format(query, category["cid"])
		search_json = await DL.async_json(search_url, headers={'Authorization': auth})
		posts = search_json["posts"]
		resultString = 'Results'
		if len(posts) == 1 :
			resultString = 'Result'
		result_string = '**Found {} {} for:** ***{}***\n\n'.format(len(posts), resultString, query)
		limit = 5
		ctr = 0
		for post in posts:
			if ctr < limit:
				ctr = ctr + 1
				result_string += '__{}__\n<https://corpnewt.com/topic/{}>\n\n'.format(post["topic"]["title"], post["topic"]["slug"])
			
		await ctx.channel.send(result_string)


	@commands.command(pass_context=True)
	async def convert(self, ctx, amount = None , frm = None, *, to = None):
		"""convert currencies"""

		hasError = False

		try:
			amount = float(amount)
		except:
			hasError = True

		if frm == None or to == None or amount <= 0:
			hasError = True
		
		if hasError == True:
			errorMsg = 'Usage: `$convert <amount> <fromCurrency> <toCurrency>`\n *Here are the list of currencies* ```Markdown\n<AED = United Arab Emirates Dirham (AED)>\n<AFN = Afghan Afghani (AFN)>\n<ALL = Albanian Lek (ALL)>\n<AMD = Armenian Dram (AMD)>\n<ANG = Netherlands Antillean Guilder (ANG)>\n<AOA = Angolan Kwanza (AOA)>\n<ARS = Argentine Peso (ARS)>\n<AUD = Australian Dollar (A$)>\n<AWG = Aruban Florin (AWG)>\n<AZN = Azerbaijani Manat (AZN)>\n<BAM = Bosnia-Herzegovina Convertible Mark (BAM)>\n<BBD = Barbadian Dollar (BBD)>\n<BDT = Bangladeshi Taka (BDT)>\n<BGN = Bulgarian Lev (BGN)>\n<BHD = Bahraini Dinar (BHD)>\n<BIF = Burundian Franc (BIF)>\n<BMD = Bermudan Dollar (BMD)>\n<BND = Brunei Dollar (BND)>\n<BOB = Bolivian Boliviano (BOB)>\n<BRL = Brazilian Real (R$)>\n<BSD = Bahamian Dollar (BSD)>\n<BTC = Bitcoin (฿)>\n<BTN = Bhutanese Ngultrum (BTN)>\n<BWP = Botswanan Pula (BWP)>\n<BYN = Belarusian Ruble (BYN)>\n<BYR = Belarusian Ruble (2000-2016) (BYR)>\n<BZD = Belize Dollar (BZD)>\n<CAD = Canadian Dollar (CA$)>\n<CDF = Congolese Franc (CDF)>\n<CHF = Swiss Franc (CHF)>\n<CLF = Chilean Unit of Account (UF) (CLF)>\n<CLP = Chilean Peso (CLP)>\n```';
			await ctx.message.author.send(errorMsg)
			errorMsg = '```Markdown\n<CNH = CNH (CNH)>\n<CNY = Chinese Yuan (CN¥)>\n<COP = Colombian Peso (COP)>\n<CRC = Costa Rican Colón (CRC)>\n<CUP = Cuban Peso (CUP)>\n<CVE = Cape Verdean Escudo (CVE)>\n<CZK = Czech Republic Koruna (CZK)>\n<DEM = German Mark (DEM)>\n<DJF = Djiboutian Franc (DJF)>\n<DKK = Danish Krone (DKK)>\n<DOP = Dominican Peso (DOP)>\n<DZD = Algerian Dinar (DZD)>\n<EGP = Egyptian Pound (EGP)>\n<ERN = Eritrean Nakfa (ERN)>\n<ETB = Ethiopian Birr (ETB)>\n<EUR = Euro (€)>\n<FIM = Finnish Markka (FIM)>\n<FJD = Fijian Dollar (FJD)>\n<FKP = Falkland Islands Pound (FKP)>\n<FRF = French Franc (FRF)>\n<GBP = British Pound (£)>\n<GEL = Georgian Lari (GEL)>\n<GHS = Ghanaian Cedi (GHS)>\n<GIP = Gibraltar Pound (GIP)>\n<GMD = Gambian Dalasi (GMD)>\n<GNF = Guinean Franc (GNF)>\n<GTQ = Guatemalan Quetzal (GTQ)>\n<GYD = Guyanaese Dollar (GYD)>\n<HKD = Hong Kong Dollar (HK$)>\n<HNL = Honduran Lempira (HNL)>\n<HRK = Croatian Kuna (HRK)>\n<HTG = Haitian Gourde (HTG)>\n<HUF = Hungarian Forint (HUF)>\n<IDR = Indonesian Rupiah (IDR)>\n<IEP = Irish Pound (IEP)>\n<ILS = Israeli New Sheqel (₪)>\n<INR = Indian Rupee (₹)>\n<IQD = Iraqi Dinar (IQD)>\n<IRR = Iranian Rial (IRR)>\n<ISK = Icelandic Króna (ISK)>\n<ITL = Italian Lira (ITL)>\n<JMD = Jamaican Dollar (JMD)>\n<JOD = Jordanian Dinar (JOD)>\n<JPY = Japanese Yen (¥)>\n<KES = Kenyan Shilling (KES)>\n<KGS = Kyrgystani Som (KGS)>\n<KHR = Cambodian Riel (KHR)>\n<KMF = Comorian Franc (KMF)>\n```';
			await ctx.message.author.send(errorMsg)
			errorMsg = '```Markdown\n<KPW = North Korean Won (KPW)>\n<KRW = South Korean Won (₩)>\n<KWD = Kuwaiti Dinar (KWD)>\n<KYD = Cayman Islands Dollar (KYD)>\n<KZT = Kazakhstani Tenge (KZT)>\n<LAK = Laotian Kip (LAK)>\n<LBP = Lebanese Pound (LBP)>\n<LKR = Sri Lankan Rupee (LKR)>\n<LRD = Liberian Dollar (LRD)>\n<LSL = Lesotho Loti (LSL)>\n<LTL = Lithuanian Litas (LTL)>\n<LVL = Latvian Lats (LVL)>\n<LYD = Libyan Dinar (LYD)>\n<MAD = Moroccan Dirham (MAD)>\n<MDL = Moldovan Leu (MDL)>\n<MGA = Malagasy Ariary (MGA)>\n<MKD = Macedonian Denar (MKD)>\n<MMK = Myanmar Kyat (MMK)>\n<MNT = Mongolian Tugrik (MNT)>\n<MOP = Macanese Pataca (MOP)>\n<MRO = Mauritanian Ouguiya (MRO)>\n<MUR = Mauritian Rupee (MUR)>\n<MVR = Maldivian Rufiyaa (MVR)>\n<MWK = Malawian Kwacha (MWK)>\n<MXN = Mexican Peso (MX$)>\n<MYR = Malaysian Ringgit (MYR)>\n<MZN = Mozambican Metical (MZN)>\n<NAD = Namibian Dollar (NAD)>\n<NGN = Nigerian Naira (NGN)>\n<NIO = Nicaraguan Córdoba (NIO)>\n<NOK = Norwegian Krone (NOK)>\n<NPR = Nepalese Rupee (NPR)>\n<NZD = New Zealand Dollar (NZ$)>\n<OMR = Omani Rial (OMR)>\n<PAB = Panamanian Balboa (PAB)>\n<PEN = Peruvian Nuevo Sol (PEN)>\n<PGK = Papua New Guinean Kina (PGK)>\n```';
			await ctx.message.author.send(errorMsg)
			errorMsg = '```Markdown\n<PHP = Philippine Peso (PHP)>\n<PKG = PKG (PKG)>\n<PKR = Pakistani Rupee (PKR)>\n<PLN = Polish Zloty (PLN)>\n<PYG = Paraguayan Guarani (PYG)>\n<QAR = Qatari Rial (QAR)>\n<RON = Romanian Leu (RON)>\n<RSD = Serbian Dinar (RSD)>\n<RUB = Russian Ruble (RUB)>\n<RWF = Rwandan Franc (RWF)>\n<SAR = Saudi Riyal (SAR)>\n<SBD = Solomon Islands Dollar (SBD)>\n<SCR = Seychellois Rupee (SCR)>\n<SDG = Sudanese Pound (SDG)>\n<SEK = Swedish Krona (SEK)>\n<SGD = Singapore Dollar (SGD)>\n<SHP = St. Helena Pound (SHP)>\n<SKK = Slovak Koruna (SKK)>\n<SLL = Sierra Leonean Leone (SLL)>\n<SOS = Somali Shilling (SOS)>\n<SRD = Surinamese Dollar (SRD)>\n<STD = São Tomé & Príncipe Dobra (STD)>\n<SVC = Salvadoran Colón (SVC)>\n<SYP = Syrian Pound (SYP)>\n<SZL = Swazi Lilangeni (SZL)>\n<THB = Thai Baht (THB)>\n<TJS = Tajikistani Somoni (TJS)>\n<TMT = Turkmenistani Manat (TMT)>\n<TND = Tunisian Dinar (TND)>\n<TOP = Tongan Paʻanga (TOP)>\n<TRY = Turkish Lira (TRY)>\n<TTD = Trinidad & Tobago Dollar (TTD)>\n<TWD = New Taiwan Dollar (NT$)>\n<TZS = Tanzanian Shilling (TZS)>\n<UAH = Ukrainian Hryvnia (UAH)>\n<UGX = Ugandan Shilling (UGX)>\n<USD = US Dollar ($)>\n<UYU = Uruguayan Peso (UYU)>\n<UZS = Uzbekistani Som (UZS)>\n<VEF = Venezuelan Bolívar (VEF)>\n<VND = Vietnamese Dong (₫)>\n<VUV = Vanuatu Vatu (VUV)>\n<WST = Samoan Tala (WST)>\n<XAF = Central African CFA Franc (FCFA)>\n<XCD = East Caribbean Dollar (EC$)>\n<XDR = Special Drawing Rights (XDR)>\n<XOF = West African CFA Franc (CFA)>\n<XPF = CFP Franc (CFPF)>\n<YER = Yemeni Rial (YER)>\n<ZAR = South African Rand (ZAR)>\n<ZMK = Zambian Kwacha (1968–2012) (ZMK)>\n<ZMW = Zambian Kwacha (ZMW)>\n<ZWL = Zimbabwean Dollar (2009) (ZWL)>\n```';
			await ctx.message.author.send(errorMsg)
			return;

		if"to" in to:
			to = to.replace("to","")
			to = to.strip()

		convert_url = "https://finance.google.com/finance/converter?a={}&from={}&to={}".format(amount,frm,to)
		r = await DL.async_text(convert_url)
		doc = pq(r)
		result = str(doc('#currency_converter_result span').text())
		results = result.split(" ")
		
		if len(results):
			amount = "{:,}".format(int(amount)) if int(amount) == float(amount) else "{:,f}".format(amount).rstrip("0")
			results[0] = float(results[0])
			results[0] = "{:,}".format(int(results[0])) if int(results[0]) == float(results[0]) else "{:,f}".format(results[0]).rstrip("0")
			await ctx.channel.send("{} {} is {} {}".format(amount,str(frm).upper(),results[0], results[1]))
		else:
			await ctx.channel.send("Whoops!  I couldn't make that conversion.")

	async def find_category(self, categories, category_to_search):
		"""recurse through the categories and sub categories to find the correct category"""
		result_category = None
		
		for category in categories:
			if str(category["name"].lower()).strip() == str(category_to_search.lower()).strip():
					return category

			if len(category["children"]) > 0:
					result_category = await self.find_category(category["children"], category_to_search)
					if result_category != None:
							return result_category
		
		return result_category

