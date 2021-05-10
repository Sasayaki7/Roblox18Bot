import discord
from discord.utils import get
from discord.ext import commands, tasks
from discord.utils import find
import json
import datetime
import math
import re
from util.pageMenu import PageList
from util.DataHandler import ROBLOXProfileHandler
import aiohttp
import asyncio

changeEmoji = '⚔️'
removeEmoji = '🛡️'
cancelEmoji = '❌'
goodEmoji = '✅'




class ROBLOXAPIAccess():



    typeDict = {1: 'Image', 2: 'T-Shirt', 8:'Hat',
        11: 'Shirt', 12:'Pants', 17: 'Head', 18: 'Face', 19: 'Gear', 24: 'Animation',
        27: 'Torso', 28: 'RightArm', 29: 'Left Arm', 30: 'Left Leg', 31: 'Right Leg', 32: 'Package',
        41: 'Hair', 42: 'Accessory', 43: 'Accessory', 44: 'Accessory', 45:'Accessory', 46: 'Accessory', 47:'Accessory',
        48:'Animation', 49:'Animation', 50:'Animation', 51:'Animation', 52:'Animation', 53:'Animation', 54:'Animation', 55:'Animation',
        56:'Animation', 61:'Animation'}



    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.item_cache={}


    async def loadCache(self):
        with open('cache.json') as f:
            self.item_cache=json.load(f)




    def saveCache(self):
        with open('cache.json', "w") as f:
            json.dump(self.item_cache,f)





    #Gets the asset type of roblox given the AssetTypeId of the item.
    def getAssetType(self, type):
        if type in self.typeDict:
            return self.typeDict[type]
        else:
            return None



    #function that takes the username and returns the corresponding userid. is a coroutine.
    async def fetch_roblox_id_from_username(self, username):
        async with self.session.get(f'https://api.roblox.com/users/get-by-username', params={'username': username}) as resp:

            #We make sure that the response we get back is valid
            if resp.status == 200:
                json = await resp.json()
                return json["Id"]
            #0 is not a valid id, so if this is returned we know something is wrong.
            else:
                return 0




    #function that obtains the roblox id of the player described in the command. returns id (int)
    #Input can be the username, the roblox profile link itself, or the roblox id.
    async def get_robloxid_from_text(self, text):
        #First case is if they linked the roblox link itself. We can extract this from numbers.
        if re.search('http', text):
            id = re.search('\d+', text).group(0)
            if id:
                return int(id)
            else:
                return 0

        #If the user input is a number, we can assume it is their userID. Otherwise we interpret it as text.
        elif text.isdigit():
            return int(text)
        else:
            return await self.fetch_roblox_id_from_username(text)



    #API Call that retrieves the username from the roblox ID
    async def fetch_username_from_roblox_id(self, userid):
        async with self.session.get(f'https://users.roblox.com/v1/users/{userid}') as resp:
            if resp.status == 200:
                jsonData= await resp.json()
                return jsonData["name"]
            else:
                return 0




    #API Call that retrieves the avatar of a roblox user given their ROBLOX ID.
    async def fetch_avatar_image(self, userId):
        async with self.session.get(f'https://thumbnails.roblox.com/v1/users/avatar?userIds={userId}&size=720x720&format=Png&isCircular=false') as resp:
            if resp.status==200:
                jsonData = await resp.json()
                return jsonData["data"][0]["imageUrl"]
            else:
                return 0


    #coroutine that fetchs information from roblox catalog with given id.
    #returns a dictionary of relevant info.
    #If response is bad, return None
    async def fetch_item_info(self, productAssetId):
        if productAssetId in self.item_cache:
            print('pulled from cache! amazing!')

            return self.item_cache[productAssetId]
        else:
            async with self.session.get(f'https://api.roblox.com/marketplace/productinfo?assetId={productAssetId}') as resp:
                if resp.status == 200:
                    respJson = await resp.json()
                    jsonContracts = {'Name': respJson["Name"], 'AssetTypeId': respJson['AssetTypeId'], 'IsLimited': respJson['IsLimited'], 'IsLimitedUnique': respJson['IsLimitedUnique'], 'MinimumMembershipLevel': respJson['MinimumMembershipLevel']}

                    self.item_cache[productAssetId] = jsonContracts
                    return respJson
                else:
                    print(resp.status)
                    return None







    #coroutine that returns what roblox items the player is wearing at the moment.
    #takes in robloxid as the input, returns a list of links that the user is wearing.
    async def fetch_avatar_clothes(self, userId):
        listOfItems = []
        async with self.session.get(f'https://avatar.roblox.com/v1/users/{userId}/currently-wearing') as resp:
            if resp.status==200:
                jsonList = await resp.json()
        #we want to reuse the session so we do this second part outside the session. Loops through the json and gets the name and link of the item
        for index, item in enumerate(jsonList["assetIds"]):
            for i in range(3):
                response = await self.fetch_item_info(item)
                await asyncio.sleep(0.5)
                if response:
                    assetDescription = self.getAssetType(response["AssetTypeId"])
                    if not (assetDescription == 'Animation' or assetDescription == None):
                        listOfItems.append(f'{assetDescription}: [{response["Name"]}](http://www.roblox.com/catalog/{item})')
                    break
        return listOfItems





    async def fetch_item_rap(self, productAssetId):
        async with self.session.get(f'https://economy.roblox.com/v1/assets/{productAssetId}/resale-data') as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 400:
                return 'notlimited'
            else:
                return None



    #coroutine that returns total rap that the player is wearing at the moment.
    #takes in robloxid as the input, returns a list of links that the user is wearing.
    async def fetch_avatar_rap(self, userId):
        listOfLimiteds = []
        total_rap = 0
        obtained = False
        async with self.session.get(f'https://avatar.roblox.com/v1/users/{userId}/currently-wearing') as resp:
            if resp.status==200:
                jsonList = await resp.json()
        #we want to reuse the session so we do this second part outside the session. Loops through the json and gets the name and link of the item
        for index, item in enumerate(jsonList["assetIds"]):
            obtained=False
            for i in range(3):
                response = await self.fetch_item_rap(item)
                await asyncio.sleep(0.3)
                if response == 'notlimited':
                    break
                elif response:
                    obtained = True
                    total_rap += response["recentAveragePrice"]
                    for j in range(3):
                        resp2 = await self.fetch_item_info(item)
                        await asyncio.sleep(0.3)
                        if resp2:
                            listOfLimiteds.append(f'[{resp2["Name"]}](http://www.roblox.com/catalog/{item}): R${response["recentAveragePrice"]}')
                            break
                    if obtained:
                        break
        return listOfLimiteds, total_rap




    async def fetch_rap_from_player(self, userId, cursor=None, prevRap=0):
        if cursor == None:
            url = f'https://inventory.roblox.com/v1/users/{userId}/assets/collectibles?sortOrder=Asc&limit=100'
        else:
            url= f'https://inventory.roblox.com/v1/users/{userId}/assets/collectibles?sortOrder=Asc&limit=100&cursor={cursor}'
        async with self.session.get(url) as resp:
            rap = prevRap
            if resp.status == 200:
                jsonData = await resp.json()
                for items in jsonData["data"]:
                    rap=rap+items["recentAveragePrice"]
                if jsonData["nextPageCursor"]:
                    return await self.fetch_rap_from_player(userId, cursor=jsonData["nextPageCursor"], prevRap=rap)
                else:
                    return rap
            elif resp.status == 403:
                return -1
            elif resp.status == 400:
                return -2





class User(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.data_handler = ROBLOXProfileHandler()
        self.rbxapi = ROBLOXAPIAccess()
        self.bot.loop.create_task(self.rbxapi.loadCache())
        self.saveCache.start()



    def cog_unload(self):
        self.saveCache.cancel()
        self.rbxapi.saveCache()




    @tasks.loop(seconds=20.0)
    async def saveCache(self):
        self.rbxapi.saveCache()




    async def update_user(self, id, profile):  #updates the user for set discord account
        await self.data_handler.update_entry(id, profile)



    async def ruser_exists(self, id): #checks if link database already contains the given message. returns a boolean
        return await self.data_handler.entry_exists(userId=id)



    async def get_ruser(self, id):
        if (await self.ruser_exists(id)):
            record= await self.data_handler.get_entry(id)
            return record['profileid']
        else:
            return None





    def get_roblox_embed(self, id):
        return f'https://www.roblox.com/users/{id}/profile'


    def getOneLineEmbed(self, embedTitle, embedText):
        embed=discord.Embed(title=embedTitle, description=embedText, color=0xff0000)
        return embed

    async def set_ruser(self, userid, ruser):
        await self.data_handler.add_entry(userid, ruser)


    async def remove_ruser(self, userid):
        await self.data_handler.remove_entry(userid)

    def match_member_tag(self, guild, tag):
        for member in guild.members:
            if f'{member.name}#{member.discriminator}' == tag:
                return member
            elif member.name.lower() == tag.lower():
                return member
            elif member.nick and member.nick.lower() == tag.lower():
                return member
        return None


    async def embedify(self, robloxid, outfit):
        embed = discord.Embed(title=f"{await self.rbxapi.fetch_username_from_roblox_id(robloxid)}'s ROBLOX outfit")
        embed.set_thumbnail(url=await self.rbxapi.fetch_avatar_image(robloxid))
        embed.description = '\n'.join(outfit)
        return embed


    async def rapembedify(self, robloxid, outfit, total):
        embed = discord.Embed(title=f"{await self.rbxapi.fetch_username_from_roblox_id(robloxid)}'s avatar limiteds")
        embed.set_thumbnail(url=await self.rbxapi.fetch_avatar_image(robloxid))
        embed.description = '\n'.join(outfit)
        embed.add_field(name="Total", value=f'R${total}')
        return embed


    def identifyUser(self, ctx, tag):
        if tag.isdigit() and ctx.guild.get_member(int(tag)):
            return ctx.guild.get_member(int(tag))
        elif len(ctx.message.mentions)> 0:
            return ctx.message.mentions[0]
        else:
            return self.match_member_tag(ctx.guild, tag)



    async def getAndRegisterUser(self, ctx):
        confirm = False
        while not (confirm):
            newmsg=await ctx.send("Type your ROBLOX account below (name, link or userId works) or say 'cancel' to quit")
            def checkm(m):
                return m.author == ctx.author
            rAcc =  await ctx.bot.wait_for('message', check=checkm)
            if rAcc.content == 'cancel':
                await rAcc.delete()
                await newmsg.delete()
                break
            profileid = await self.get_robloxid_from_text(rAcc.content)
            await newmsg.delete()
            if profileid:
                reply_msg=await ctx.send(f'{ctx.author.mention}, is {self.get_roblox_embed(profileid)} your ROBLOX profile?  React {goodEmoji} if yes, {cancelEmoji} if no.')
                await reply_msg.add_reaction(goodEmoji)
                await reply_msg.add_reaction(cancelEmoji)
                def checkr2(r, u):
                    return r.message.id == reply_msg.id and u == ctx.author and (str(r.emoji)==goodEmoji or str(r.emoji) == cancelEmoji)
                try:
                    reaction2, user = await ctx.bot.wait_for('reaction_add', check=checkr2, timeout = 15)
                except asyncio.TimeoutError:
                    await reply_msg.delete()
                if str(reaction2.emoji) == goodEmoji:
                    if await self.ruser_exists(ctx.author.id):
                        await self.update_user(ctx.author.id, profileid)
                        await reply_msg.delete()
                        await ctx.send('ROBLOX profile successfully updated!', delete_after=10)
                    else:
                        await self.set_ruser(ctx.author.id, profileid)
                        await reply_msg.delete()
                        await ctx.send('ROBLOX profile successfully registered to your account.', delete_after=10)
                    confirm = True
                elif str(reaction2.emoji) == cancelEmoji:
                    await reply_msg.delete()
            else:
                await ctx.send("Invalid ROBLOX account. Please try again", delete_after=10)







    #coroutine that checks that the arguments of the command.
    async def check_valid_inputs(self, ctx, *args):
        if not args[0]:
            if await self.ruser_exists(ctx.author.id):
                robloxid=await self.get_ruser(ctx.author.id)
                return robloxid, ctx.author.id
            else:
                await ctx.send(f"You have not registered your roblox account yet. register using the {ctx.prefix}register command")
                return None, None
        else:
            if args[0][len(args[0])-1] == '-r':
                robloxid = await self.rbxapi.fetch_roblox_id_from_username(' '.join(args[0])[:-2])
                return int(robloxid), None
            if self.identifyUser(ctx, ' '.join(args[0])):
                discid = self.identifyUser(ctx, ' '.join(args[0])).id
                if await self.ruser_exists(discid):
                    robloxid = await self.get_ruser(discid)
                    return robloxid, discid
                else:
                    await ctx.send(f"``{ctx.guild.get_member(discid).name}`` has not yet registered a ROBLOX account. Have them by typing ``{ctx.prefix}register``")
                    return None, None
            else:
                await ctx.send(f"Couldn't identify ``{' '.join(args[0])}``. Try mentioning them or use their Name#Discriminator (i.e. Sasa#7557). If this is their ROBLOX username add ``-r`` at the end (i.e. builderman -r)")
                return None, None





    @commands.command(help="""[JP]:outfit [Discordユーザー] でROBLOXユーザーの衣装を引っ張ってきます。!
        [EN]:outfit <discorduser> obtains the items that the ROBLOX user is currently wearing.
        """)
    async def outfit(self, ctx, *args):
        robloxid, discid = await self.check_valid_inputs(ctx, args)
        if not robloxid:
            return
        async with ctx.typing():
            outfit=await self.rbxapi.fetch_avatar_clothes(robloxid)
            if outfit == None:
                counter = 0
                while counter < 5 and (outfit == None):
                    outfit=await self.rbxapi.fetch_avatar_clothes(robloxid)
            if outfit == 0 or outfit == None:
                await ctx.send("Something went wrong... Maybe ROBLOX is down or user is invalid")
            else:
                await ctx.send(embed=await self.embedify(robloxid, outfit))



    @commands.command(help="""[JP]:networth [Discordユーザー] でROBLOXユーザーの衣装の総額を引っ張ってきます。!
        [EN]:networth <discorduser> obtains the total rap of items that the ROBLOX user is currently wearing.
        """,aliases=["flex"] )
    async def networth(self, ctx, *args):
        robloxid, discid = await self.check_valid_inputs(ctx, args)
        if not robloxid:
            return
        async with ctx.typing():
            outfit, total_rap=await self.rbxapi.fetch_avatar_rap(robloxid)
            if outfit == None:
                counter = 0
                while counter < 5 and (outfit == None):
                    outfit, total_rap=await self.rbxapi.fetch_avatar_rap(robloxid)
            if outfit == 0 or outfit == None:
                await ctx.send("Something went wrong... Maybe ROBLOX is down or user is invalid")
            else:
                await ctx.send(embed=await self.rapembedify(robloxid, outfit, total_rap))



    @commands.command(help="""[JP]:user [Discordユーザー] でDiscordユーザーのROBLOXユーザーを引っ張ってきます。!
        [EN]:user <discorduser> obtains the ROBLOX user for that discord user.
        """)
    async def user(self, ctx, *args):
        robloxid, discid = await self.check_valid_inputs(ctx, args)
        if not robloxid:
            return
        if discid == None:
            await ctx.send(f"{self.get_roblox_embed(robloxid)}")
        else:
            await ctx.send(f"{ctx.guild.get_member(discid).name}'s roblox profile: {self.get_roblox_embed(robloxid)}")





    @commands.command(help="[JP]:rap ユーザーのRAPを取得します。 [EN]: rap <discorduser> Gets RAP of ROBLOX account associated with said discord user")
    async def rap(self, ctx, *args):
        robloxid, discid = await self.check_valid_inputs(ctx, args)
        if not robloxid:
            return
        rap = await self.rbxapi.fetch_rap_from_player(robloxid)
        if rap == -1:
            rap = "Unknown (User hid inventory)"
        elif rap == -2:
            rap = "Unknown (Error fetching data. Perhaps server is down or TimeoutError, or invalid user)"
        if discid == None:
            await ctx.send(f"{await self.rbxapi.fetch_username_from_roblox_id(robloxid)}'s total RAP: {rap}")
        else:
            await ctx.send(f"{ctx.guild.get_member(discid).name}'s total RAP: {rap}")






    @commands.command(help="[JP]:avatar ユーザーのアバターを取得します。 [EN]: avatar <discorduser> Gets avatar image of ROBLOX account associated with said discord user", aliases=["drip"])
    async def avatar(self, ctx, *args):
        robloxid, discid = await self.check_valid_inputs(ctx, args)
        if not robloxid:
            return
        avatarImage=await self.rbxapi.fetch_avatar_image(robloxid)
        if avatarImage == None or avatarImage == "None":
            counter = 0
            while counter < 5 and (avatarImage == "None" or avatarImage == None):
                avatarImage=await self.rbxapi.fetch_avatar_image(robloxid)
        if avatarImage == 0 or avatarImage == None or avatarImage == "None":
            await ctx.send("Something went wrong... Maybe ROBLOX is down or user is invalid")
        else:
            await ctx.send(f"{avatarImage}")




    @commands.command(help="[JP]:register ROBLOX垢を登録します。[EN]:register. Use this to register your ROBLOX account.")
    async def register(self, ctx):
        lang = self.bot.get_language(ctx)
        userid = ctx.author.id

        if await self.ruser_exists(userid):
            msg = ""
            if lang == "JP":
                msg=await ctx.send(f"あなたのROBLOX垢は既に登録されています。")
            elif lang == "EN":
                msg=await ctx.send(f"Your account is already registered. Please react with what you would like to do:\nChange: {changeEmoji}\n Remove: {removeEmoji}\n Cancel: {cancelEmoji}")
            else:
                print(lang)
            await msg.add_reaction(changeEmoji)
            await msg.add_reaction(removeEmoji)
            await msg.add_reaction(cancelEmoji)
            reaction = ""
            def check(r, u):
                return r.message.id == msg.id and u == ctx.author and (str(r.emoji)==changeEmoji or str(r.emoji)==removeEmoji or str(r.emoji) == cancelEmoji)
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', check=check, timeout = 15)
            except asyncio.TimeoutError:
                await msg.delete()
                return
            else:
                if str(reaction.emoji) == changeEmoji:
                    await msg.delete()
                    await self.getAndRegisterUser(ctx)

                elif str(reaction.emoji)==removeEmoji:
                    await msg.delete()
                    response_msg = await ctx.send(f"Are you sure you want to disassociate ANY roblox account from this discord account? React to this message.")
                    await response_msg.add_reaction(goodEmoji)
                    await response_msg.add_reaction(cancelEmoji)
                    def checkr2(r, u):
                        return r.message.id == response_msg.id and u == ctx.author and (str(r.emoji)==goodEmoji or str(r.emoji) == cancelEmoji)
                    try:
                        reaction2, user = await ctx.bot.wait_for('reaction_add', check=checkr2, timeout = 15)
                    except asyncio.TimeoutError:
                        await response_msg.delete()
                    if str(reaction2.emoji) == goodEmoji:
                        await self.remove_ruser(ctx.author.id)
                        await response_msg.delete()
                        await ctx.send('ROBLOX profile successfully disassociated from your account.', delete_after=10)
                    elif str(reaction2.emoji) == cancelEmoji:
                        await response_msg.delete()
                        await ctx.send('Command cancelled', delete_after=5)
                else:
                    await msg.delete()
                await msg.clear_reactions()
        else:
            await self.getAndRegisterUser(ctx)


def setup(bot):
    bot.add_cog(User(bot))
