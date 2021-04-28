import discord
from discord.utils import get
from discord.ext import commands
from discord.utils import find
import json
from Cogs.Starboard.StarboardEntry import StarboardEntry
from util.DataHandler import StarboardParameterHandler, StarboardHandler, LeaderboardHandler
from util.pageMenu import PageMenu
import math
import datetime

class Starboard(commands.Cog):
    
    
    #The Starboard Cog.
    
    def __init__(self, bot):
        self.bot = bot
        self.starboard_handler = StarboardHandler()
        self.leaderboard_handler = LeaderboardHandler()
        self.parameter_manager = StarboardParameterHandler()

		
    async def update_Starboard(self, entry):  #updates starboardJson and returns the number of reactions that changed
        await self.starboard_handler.update_entry(entry.guild_id, entry)
        
    
    async def remove_from_Starboard(self, entry): #removes message from starboardJson and returns the number of reactions that changed
        await self.starboard_handler.remove_entry(entry.guild_id, entry)

    

    async def starboard_entry_exists(self, entry): #checks if the starboardJson already contains the given message. returns a boolean
        return await self.starboard_handler.entry_exists(entry.guild_id, entry)


    async def get_parameter(self, guild_id, parameter_name):
        record= await self.parameter_manager.get_entry(guild_id)
        return record[parameter_name]


    #A quick function that checks if a file extension is an image
    def _isImage(self, filename):
        if not isinstance(filename, str):
            return False
        formats = ["jpg", "png", "jpeg", "bmp", "tiff", "tif"]
        tuples = filename.lower().rsplit(".")
        if tuples[-1] in formats:
            return True
        else:
            return False
  

    #Takes a starboard_entry and removes it from the database. Sets the starboard_count for that message to 0.
    #Does not return anything
    async def wipe_from_starboard(self, starboard_entry, original_message, starboard_message):
        increment = starboard_entry.update_count(0)
        await self.leaderboard_handler.increment_entry(starboard_entry.guild_id, original_message.author.id, increment) #We then update the leaderboard.
        await self.starboard_handler.remove_entry(starboard_entry.guild_id, starboard_entry)
        if starboard_message:
            await starboard_message.delete()
        
        
    
    async def get_starboard_message(self, channel, starboard_item):
        """ Takes a starboard entry and returns the actual message associated with the starboard entry"""
        
        message = await channel.fetch_message(starboard_item.get_starboard_message())
        return message
        
        
        
    def createStarboardEmbed(self, message, reaction, lang):
        title = lang == "JP" and "スターボード" or "Starboard"
        embed=discord.Embed(title= title, color=0x00ff00)
        if len(message.attachments) > 0:
            if self._isImage(message.attachments[0].filename):
                embed.set_image(url=message.attachments[0].url)
        elif len(message.embeds) > 0:
            for emb in message.embeds:
                if (not (emb.image is discord.Embed.Empty)) and not ((emb.image.url is discord.Embed.Empty) and  (emb.image.proxy_url is discord.Embed.Empty)):
                
                    if emb.image.proxy_url is discord.Embed.Empty:
                        embed.set_image(url=emb.image.url)
                    else:
                        embed.set_image(url=emb.image.proxy_url)
                    break
                elif (not (emb.thumbnail is discord.Embed.Empty)) and not ((emb.thumbnail.url is discord.Embed.Empty) and  (emb.thumbnail.proxy_url is discord.Embed.Empty)):
                    if emb.thumbnail.proxy_url is discord.Embed.Empty:
                        embed.set_image(url=emb.thumbnail.url)
                    else:
                        embed.set_image(url=emb.thumbnail.proxy_url)
                    break
            
        
        embed.add_field(name= lang == "JP" and "内容" or "Content", value=message.content or len(message.attachments) > 0 and message.attachments[0].url or (lang == "JP" and "添付内容をご自分で確認ください!" or "See message for details"), inline=False)
        embed.add_field(name= lang=="JP" and "発言者" or "Author", value=message.author.mention, inline=True)
        embed.add_field(name= lang=="JP" and "チャンネル" or "Channel", value=message.channel.mention, inline=True)
        embed.add_field(name= lang=="JP" and "元のメッセージ" or "Original Message", value=f"[Original]({message.jump_url})", inline=False)
        embed.timestamp = datetime.datetime.now()
        if reaction.custom_emoji:
            embed.set_footer(icon_url=reaction.emoji.url, text=f"{reaction.count} {reaction.emoji.name}")
        else:
            embed.set_footer(text=f"{reaction.emoji}  {reaction.count} {str(reaction.emoji)}")
        return embed


    async def createLeaderboardEmbed(self, keyArray, ctx):
        lang = await self.bot.get_language(ctx)
        list_A = [f"{i+1}. <@!{keyArray[i][0]}>" for i in range(len(keyArray))]
        list_B = [keyArray[i][1] for i in range(len(keyArray))]
        emoji = await self.get_parameter(ctx.guild.id, 'starboard_emoji')
        if lang == "JP":
            pages = PageMenu(ctx, title=f"{emoji} =====リーダーボード===== {emoji}", lists=[list_A, list_B], subheaders = ["名前", "票数"], lang=lang, color=0xfed8b1, entry_per_page=10)
            await pages.activate()
        elif lang == "EN":
            pages = PageMenu(ctx, title=f"{emoji} =====Leaderboard===== {emoji}", lists=[list_A, list_B], subheaders = ["Name", "Count"], lang=lang, color=0xfed8b1, entry_per_page=10)
            await pages.activate()



    async def get_starboard_entry(self, guildid, messageid):
        record = await self.starboard_handler.get_entry(guildId, messageid)
        entry = Starboard(guild_id=guildid, id=messageid, starboard_message=record["starboard_message"], channel_id=record["channel_id"], count=record["count"],
            author_id = record["author_id"])
        return entry
        
        
    async def _fetch_parameter(self, guild_id,  parameter):
        record = await self.parameter_manager.get_entry(guild_id)
        return record.get(parameter)
    
    def _getOneLineEmbed(self,embedTitle, embedText):
        embed=discord.Embed(title=embedTitle, description=embedText, color=0x15ee00)
        return embed   



    def _insufficientPermEmbed(self):
        embed = discord.Embed(title="権限が足りません！", description="このコマンドを使う権限を持っていません！", color=0xff0000)
        return embed



    async def botError(self,ctx, type):
        await ctx.send(embed=self._getOneLineEmbed("Error", f"{ctx.command.name} {self.bot.errorList[type]}"))   




    @commands.Cog.listener()
    async def on_guild_join(self, guild):  #When the bot joins a server, we initalize certain parameters to avoid KeyError later on.
        await self.starboard_handler.create_table(guild.id)  #If the Server id is not registered in the JSON, we initailize it.
        await self.leaderboard_handler.create_table(guild.id) 
        if not await self.parameter_manager.entry_exists(guild.id):
            starboard = find(lambda x: x.name == 'starboard',  guild.text_channels)  #We try to define the #general channel to be the default channels.
            if starboard and starboard.permissions_for(guild.me).send_messages:  #Making sure we can send messages at all.... If so, we go ahead and set the channels.
                await self.parameter_manager.add_entry(guild.id, starboard.id)
            else:  #Otherwise, we just set up the potatoes to be the first channel that we can identify.
                quick_setup = find(lambda x: x.permissions_for(guild.me).send_messages, guild.text_channels)
                await self.parameter_manager.add_entry(guild.id, quick_setup.id)

       
    @commands.command(help="[JP]:setstarboardchannel [チャンネル名]　で私がスターボードに相応しいメッセージを[チャンネル名]に貼ります！[EN]:setstarboardchannel <channel> changes the starboard channel to <channel>", brief="スターボード発言を投稿するチャンネルを変えます。")
    async def setstarboardchannel(self, ctx, args):
        lang = await self.bot.get_language(ctx)
        guildId=ctx.guild.id
        if not args:
            await self.botError(ctx, "noargs")
        elif not self.bot.has_permissions(ctx):
            await ctx.send(embed=self._insufficientPermEmbed())
        elif len(ctx.message.channel_mentions)==0:
            await self.botError(ctx, "specifyChannel")
        else:
            await self.parameter_manager.update_entry(guildId, "starboard_channel",  ctx.message.channel_mentions[0].id)
            if lang=="JP":
                await ctx.send(embed=self._getOneLineEmbed("スターボードチャンネル変えました！", f"これからは　{ctx.message.channel_mentions[0].mention}　にスターボードメッセージを貼ります！"))    
            elif lang == "EN":
                await ctx.send(embed=self._getOneLineEmbed("Starboard channel changed！", f"From now on all starboard messages will be sent to {ctx.message.channel_mentions[0].mention}"))    
            else:
                print('error')            
            
            
    @commands.command(help="[JP]:threshold: スターボード登録されるまでに必要なリアクション数を教えてあげる！　\nthreshold [整数]: で私がスターボードに貼るまでに必要なリアクション数を [数字] に変えちゃいます！ [EN]:reaction: Tells you the number of reactions to reach starboard\nreaction <number>: Changes the number of reactions to qualify for starboard to <number>", brief="スターボード登録の為に必要なリアクション数の提示/変更")
    async def threshold(self, ctx, *, args):
        lang = await self.bot.get_language(ctx)
        if not args:
            threshold = await self._fetch_parameter(ctx.guild.id, "starboard_threshold")
            await ctx.send(threshold)
        elif not self.bot.has_permissions(ctx):
            await ctx.send(embed=self._insufficientPermEmbed())
        else:
            threshNum = int(args)
            if threshNum and threshNum > 0:
                guildId=ctx.guild.id
                await self.parameter_manager.update_entry(guildId, "starboard_threshold", threshNum)
                if lang == "JP":
                    await ctx.send(embed=self._getOneLineEmbed("設定変更完了！", f"これからはリアクション数　{threshNum} でメッセージをスターボードに貼り付けます！"))
                elif lang == "EN":
                    await ctx.send(embed=self._getOneLineEmbed("Settings successfully changed！", f"The number of reacts required for starboard is now:　{threshNum}"))
                else:
                    print('error')
            elif threshNum <= 0:
                await self.botError(ctx, "lessThan0")
            else:
                await botError(ctx, "intError")

    async def modifyleaderboard(self, guildId, user, count):
        if leaderboard_handler.entry_exists(guildId, user.id):
            await leaderboard_handler.update_entry(guildId, user.id, count)
        else:
            await leaderboard_handler.add_entry(guildId, user.id, count)




    @commands.command(help="[JP]:reaction: 気に入ったメッセージをスターボードに貼りたいときに使うリアクションを教えちゃおう！ \nreaction [絵文字]: でやるべきリアクションを [絵文字] に変えちゃうよ～[EN]:reaction: Shows the reaction needed to qualify for starboard.\nreaction <emoji> changes the reaction to qualify for starboard to <emoji>", brief="スターボード登録に必要なリアクションを変更/提示", aliases=["react"])
    async def reaction(self, ctx, *, args):
        lang = await self.bot.get_language(ctx)
        if not args:
            reaction = await self._fetch_parameter(ctx.guild.id, "starboard_emoji")
            await ctx.send(reaction)
            return
        elif not self.bot.has_permissions(ctx):
            await ctx.send(embed=self._insufficientPermEmbed())
        else:
            guildId=ctx.guild.id
            await self.parameter_manager.update_entry(guildId,"starboard_emoji", str(args))
            if lang == "JP":
                await ctx.send(embed=self._getOneLineEmbed("設定変更完了！", f"これからお気に入りのメッセージには　{args}でリアクションしてね！"))
            elif lang == "EN":
                await ctx.send(embed=self._getOneLineEmbed("Settings successfully changed!", f"Please react with {args} on messages you want on starboard"))            
            else:
                print('error')
    
    @commands.command(help="[JP]:今まで一番人気のコメントした人達をランキングで表しちゃう！10位以降の人達見たかったら下のリアクトで操作してね![EN]:Shows the top ranking users on the starboard. To see ranks below 10th, use the reacts at the bottom.", brief="スターボードのトップランキングを提示します。")
    async def leaderboard(self, ctx, *args):
        lang = await self.bot.get_language(ctx)
        temparray = await self.leaderboard_handler.get_all_data(ctx.guild.id)
        if len(temparray) == 0: #If the guild doesn't have anybody on the starboard, we return a message informing the user.
            if lang == "JP":
                embed=discord.Embed(description="このサーバーのスターボードは空っぽです。好きなメッセージにリアクションを付けてスターボードを活用させちゃおう！", color=0xff0000)
                await ctx.send(embed=embed)
            elif lang == "EN":
                embed=discord.Embed(description="There are nothing on the starboard. Go react to your favorite messages!", color=0xff0000)
                await ctx.send(embed=embed)
            else:
                print(lang)    
        else:
            keyArray = sorted(temparray, key = lambda x: x["count"], reverse = True)  #Quick code that sorts the leaderboard entries from highest to lowest
            leaderboardEmbed = await self.createLeaderboardEmbed(keyArray, ctx)
            
            
    async def starboard_condition_check(self, payload, message, reaction, check):
        reactor = self.bot.get_user(payload.user_id)
        if message.author.bot:
            return False
        if message.author.id == payload.user_id:
            await message.remove_reaction(payload.emoji, reactor)
            return False
        if str(reaction) !=str(check):
            return False
        return True
            
            
            
    def _get_reaction(self, message, reaction):
        for emoji in message.reactions:
            if str(emoji) == str(reaction):
                return emoji        
    
    async def unpack_payload(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = self._get_reaction(message, payload.emoji)
        dict = {"guild": guild, "channel": channel, "message": message, "reaction": reaction, "reactor": self.bot.get_user(payload.user_id)}
        return dict
                
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):  #updates the starboard when the threshold of reactions is met 
        object_list = await self.unpack_payload(payload)
        check_emoji = await self._fetch_parameter(payload.guild_id, "starboard_emoji")
        guild = object_list["guild"]
        channelToPost = guild.get_channel(await self._fetch_parameter(payload.guild_id, "starboard_channel"))
        message =object_list["message"]
        lang = await self.bot.get_language(guild)
        if await self.starboard_condition_check(payload, message, payload.emoji, check_emoji):
            count =object_list["reaction"].count
            
            if count >= await self._fetch_parameter(guild.id, "starboard_threshold"):  #If there are more reactions than required, we add it to the leaderboard
                starboard_entry = None
                if await self.starboard_handler.entry_exists(guild.id, id=message.id):       
                    record = await self.starboard_handler.get_entry(guild.id,message.id)
                    starboard_entry = StarboardEntry(id=record["id"], guild_id = guild.id, starboard_channel = record["starboard_channel"], message=message.content, count=record["count"], author_id=record["author_id"],
                        starboard_message=record["starboard_message"])
                else: 
                    starboard_entry=StarboardEntry(id=message.id, guild_id = guild.id, message=message.content, starboard_channel = channelToPost.id, count=0, author_id=message.author.id)
                embed = self.createStarboardEmbed(message, object_list["reaction"], lang) #We need to create a new embed  
                
                if starboard_entry.starboard_message == None:  #If the starboardJson currently does not contain the message, we create a new message to send to starboard_channel
                    starboard_message = await channelToPost.send(embed=embed)  #We need to get the message id of the bot's message so that we can link the original message with the starboard message.
                    starboard_entry.update_starboard_message(starboard_message.id) 
                else:  #If the message already exists, we need to edit the message rather than start from scratch.
                    if not getattr(starboard_entry, "starboard_channel", None):  #For old data.
                        try:
                            starboard_message = await get_starboard_message(channelToPost, starboard_entry).fetch_message(starboard_entry.starboard_message) #Using the id we fetched, we can get the actual message that the bot sent          
                        except discord.errors.NotFound:
                            starboard_message = await channelToPost.send(embed=embed)
                            starboard_entry.update_starboard_message(starboard_message.id)                        
                        else:
                            await starboard_message.edit(embed=embed) #We edit the message with the new embed containing the latest info.
                            
                    elif getattr(starboard_entry, "starboard_channel") != channelToPost.id:
                        if guild.get_channel(getattr(starboard_entry, "starboard_channel")):
                            try:
                                messageToDelete = await guild.get_channel(getattr(starboard_entry, "starboard_channel")).fetch_message(getattr(starboard_entry, "starboard_message"))
                            except discord.errors.NotFound:
                                pass                 
                            else:
                                await messageToDelete.delete()
                                
                        starboard_message = await channelToPost.send(embed=embed)
                        starboard_entry.update_starboard_message(starboard_message.id)
                    else:
                        try:
                            starboard_message = await channelToPost.fetch_message(starboard_entry.starboard_message) #Using the id we fetched, we can get the actual message that the bot sent          
                        except discord.errors.NotFound:
                            starboard_message = await channelToPost.send(embed=embed)
                            starboard_entry.update_starboard_message(starboard_message.id)                            
                        else: #If messageToEdit exists.....
                            await starboard_message.edit(embed=embed) #We edit the message with the new embed containing the latest info.
                        
                    
                increment = starboard_entry.update_count(count) #Updates starboardJson with the message and corresponding starboard info, along with the number of reactions.
                if await self.leaderboard_handler.entry_exists(guild.id, message.author.id):
                    await self.leaderboard_handler.increment_entry(guild.id, message.author.id, increment) #We then update the leaderboard.
                else:
                    await self.leaderboard_handler.add_entry(guild.id, message.author.id, count)
                await self.starboard_handler.update_entry(guild.id, starboard_entry)

                
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):  #updates the starboard when the threshold of reactions is met 
        object_list = await self.unpack_payload(payload)
        check_emoji = await self._fetch_parameter(payload.guild_id, "starboard_emoji")
        guild = object_list["guild"]
        lang = await self.bot.get_language(guild)
        channelToPost = guild.get_channel(await self._fetch_parameter(payload.guild_id, "starboard_channel"))
        threshold = await self._fetch_parameter(payload.guild_id, "starboard_threshold")
        message = object_list["message"]
        if await self.starboard_condition_check(payload, message, payload.emoji, check_emoji):
            count = 0 if object_list["reaction"] == None else object_list["reaction"].count
            if count >= threshold-1:  #These would be the only relevant instants
                starboard_entry = None
                if await self.starboard_handler.entry_exists(guild.id,id=message.id):   
                    record = await self.starboard_handler.get_entry(guild.id,message.id)
                    starboard_entry = StarboardEntry(id=record["id"], guild_id = guild.id, starboard_channel = record["starboard_channel"], message=message.content, count=record["count"], author_id=record["author_id"],
                        starboard_message=record["starboard_message"])
                else: 
                    starboard_entry=StarboardEntry(id=message.id, guild_id = guild.id, message=message.content, starboard_channel = channelToPost.id, count=0, author_id=message.author.id)
                
                if starboard_entry.starboard_message == None and count >= threshold:  #If the starboardJson currently does not contain the message, nothing to worry about              
                    embed = self.createStarboardEmbed(message, object_list["reaction"], lang) #We need to create a new embed  
                    starboard_message = await channelToPost.send(embed=embed)  #We need to get the message id of the bot's message so that we can link the original message with the starboard message.
                    starboard_entry.update_starboard_message(starboard_message.id)
                 
                elif count >= threshold:  #If the message already exists, we need to edit the message rather than start from scratch.
                    starboard_message = starboard_entry.starboard_message #We get the associated starboard message from the JSON
                    embed = self.createStarboardEmbed(message, object_list["reaction"], lang) #We need to create a new embed  
                    #If there is no channel saved, we just edit the starboard message assuming it exists.
                    if not getattr(starboard_entry, "starboard_channel", None):
                        try:
                            messageToEdit = await channelToPost.fetch_message(starboard_entry.starboard_message) #Using the id we fetched, we can get the actual message that the bot sent          
                        except discord.errors.NotFound:
                            starboard_message= await channelToPost.send(embed=embed)
                            starboard_entry.update_starboard_message(starboard_message.id)                        
                        else:
                            await messageToEdit.edit(embed=embed) #We edit the message with the new embed containing the latest info.

                    #if there is a mismatch between the channel saved and the actual starboard_channel, we delete the old message and post new message in the actual channel.
                    elif getattr(starboard_entry, "starboard_channel") != channelToPost.id:
                        try:
                            messageToDelete = await guild.get_channel(getattr(starboard_entry, "starboard_channel")).fetch_message(starboard_entry.starboard_message)                           
                        except discord.errors.NotFound:
                            pass     
                        else:
                            await messageToDelete.delete()
                        starboard_message = await channelToPost.send(embed=embed)
                        starboard_entry.update_starboard_message(starboard_message.id)
                        
                    else:
                        embed = self.createStarboardEmbed(message, object_list["reaction"], lang) #We need to create a new embed
                        try:
                            messageToEdit = await channelToPost.fetch_message(starboard_entry.starboard_message) #Using the id we fetched, we can get the actual message that the bot sent          
                        except discord.errors.NotFound:
                            starboard_message = await channelToPost.send(embed=embed)
                            starboard_entry.update_starboard_message(starboard_message.id)                            
                        else:
                            await messageToEdit.edit(embed=embed) #We edit the message with the new embed containing the latest info.
                            
                            
                    increment = starboard_entry.update_count(count)
                    if await self.leaderboard_handler.entry_exists(guild.id, message.author.id):
                        await self.leaderboard_handler.increment_entry(guild.id, message.author.id,increment) #We then update the leaderboard.
                    else:
                        await self.leaderboard_handler.add_entry(guild.id, message.author.id, count)
                    await self.starboard_handler.update_entry(guild.id, starboard_entry)
                    
                elif starboard_entry.starboard_message and count < threshold: #In this case we remove all the associated counts and the post.
                    if not getattr(starboard_entry, "starboard_channel", None):
                        messageToDelete = await channelToPost.fetch_message(starboard_entry.starboard_message)
                        await self.wipe_from_starboard(starboard_entry, object_list["message"], messageToDelete)
                    else: 
                        if guild.get_channel(getattr(starboard_entry, "starboard_channel")):
                            messageToDelete = await guild.get_channel(getattr(starboard_entry, "starboard_channel")).fetch_message(starboard_entry.starboard_message)
                            await self.wipe_from_starboard(starboard_entry, object_list["message"], messageToDelete)
                else:
                    pass

            
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        guild = message.guild
        guild_id = guild.id
        starboard_channel = await self._fetch_parameter(guild_id, "starboard_channel")
        channelToPost = guild.get_channel(starboard_channel) #We obtain the channel that the bot will post to.
        if await self.starboard_handler.entry_exists(guild_id, id=message.id):
            record = await self.starboard_handler.get_entry(guild.id,message.id)
            starboard_entry = StarboardEntry(id=record["id"], guild_id = guild.id, starboard_channel = record["starboard_channel"], message=message.content, count=record["count"], author_id=record["author_id"],
                starboard_message=record["starboard_message"])            
            if not getattr(starboard_entry, "starboard_channel", None):  #For old data.
                messageToDelete = await channelToPost.fetch_message(starboard_entry.starboard_message) #Using the id we fetched, we can get the actual message that the bot sent          
                self.wipe_from_starboard(starboard_entry, message, messageToDelete)
            else:
                if guild.get_channel(starboard_entry.starboard_channel):
                    messageToDelete = await guild.get_channel(starboard_entry.starboard_channel).fetch_message(starboard_entry.starboard_message) #Using the id we fetched, we can get the actual message that the bot sent          
                    await self.wipe_from_starboard(starboard_entry, message, messageToDelete)
