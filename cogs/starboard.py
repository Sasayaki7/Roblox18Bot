import discord
from discord.utils import get
from discord.ext import commands
from discord.utils import find
import json
from util.DataHandler import StarboardParameterHandler, StarboardHandler
from util.pageMenu import PageMenu
import math
import datetime
from collections import Counter

class Starboard(commands.Cog):


    #The Starboard Cog.

    __slots__=["bot", "starboard_handler", "leaderboard_handler", "parameter_manager"]

    def __init__(self, bot):
        self.bot = bot
        self.starboard_handler = StarboardHandler()
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


    def has_permissions(ctx):
        if ctx.author.id == ctx.bot.owner_id:
            return True
        elif ctx.author.guild_permissions.manage_guild:
            return True
        elif ctx.author.guild_permissions.administrator:
            return True
        elif ctx.author.guild_permissions.manage_roles:
            return True
        else:
            return False

    #Takes a starboard_entry and removes it from the database. Sets the starboard_count for that message to 0.
    #Does not return anything
    async def wipe_from_starboard(self, starboard_entry, original_message, starboard_message):
        increment = starboard_entry.update_count(0)
        await self.starboard_handler.remove_entry(starboard_entry.guild_id, starboard_entry)
        if starboard_message:
            await starboard_message.delete()



    async def get_starboard_message(self, channel, starboard_item):
        """ Takes a starboard entry and returns the actual message associated with the starboard entry"""

        message = await channel.fetch_message(starboard_item.get_starboard_message())
        return message

    def extract_image_from_message(self, message):
        '''Extracts first image found in the message and returns the url
        Looks through the message in the following order:
            -> Checks attachment to see if there is an image
            ->If not found, checks embed to see if there is an associated image/thumbnail.
            ->If found, checks url and proxy_url
        Parameters:
        message: discord.Message

        returns:
        string url'''

        if len(message.attachments) > 0:
            if self._isImage(message.attachments[0].filename):
                return message.attachments[0].url
        elif len(message.embeds) > 0:
            for emb in message.embeds:
                if (not (emb.image is discord.Embed.Empty)) and not ((emb.image.url is discord.Embed.Empty) and  (emb.image.proxy_url is discord.Embed.Empty)):
                    if emb.image.proxy_url is discord.Embed.Empty:
                        return emb.image.url
                    else:
                        return emb.image.proxy_url
                elif (not (emb.thumbnail is discord.Embed.Empty)) and not ((emb.thumbnail.url is discord.Embed.Empty) and  (emb.thumbnail.proxy_url is discord.Embed.Empty)):
                    if emb.thumbnail.proxy_url is discord.Embed.Empty:
                        return emb.thumbnail.url
                    else:
                        return emb.thumbnail.proxy_url
        return None

    def createStarboardEmbed(self, message, reaction, lang):
        title = lang == "JP" and "スターボード" or "Starboard"
        embed=discord.Embed(title= title, color=0x00ff00)
        image = self.extract_image_from_message(message)
        if image:
            embed.set_image(url=image)
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
        lang = self.bot.get_language(ctx)
        print(lang)
        list_A = [f"{i+1}. <@!{keyArray[i][0]}>" for i in range(len(keyArray))]
        list_B = [keyArray[i][1] for i in range(len(keyArray))]
        emoji = await self.get_parameter(ctx.guild.id, 'starboard_emoji')
        if lang == "JP":
            pages = PageMenu(ctx, title=f"{emoji} =====リーダーボード===== {emoji}", lists=[list_A, list_B], subheaders = ["名前", "票数"], color=0xfed8b1, entry_per_page=10)
            await pages.activate()
        elif lang == "EN":
            pages = PageMenu(ctx, title=f"{emoji} =====Leaderboard===== {emoji}", lists=[list_A, list_B], subheaders = ["Name", "Count"], color=0xfed8b1, entry_per_page=10)
            await pages.activate()



    async def get_starboard_entry(self, guildid, messageid):
        record = await self.starboard_handler.get_entry(guildId, messageid)
        entry = Starboard(guild_id=guildid, id=messageid, starboard_message=record["starboard_message"], channel_id=record["channel_id"], count=record["count"],
            author_id = record["author_id"])
        return entry


    async def _fetch_parameter(self, guild_id,  parameter):
        record = await self.parameter_manager.get_entry(guild_id)
        return record.get(parameter)

    def _getOneLineEmbed(self,embedTitle, embedText, guild):
        title=self.bot.content_to_lang(embedTitle, guild)
        embedText=self.bot.content_to_lang(embedText, guild)
        embed=discord.Embed(title=title, description=embedText, color=0x15ee00)
        return embed



    async def botError(self,ctx, type):
        await ctx.send(embed=self._getOneLineEmbed("Error", f"{ctx.command.name} {self.bot.errorList[type]}"))




    @commands.Cog.listener()
    async def on_guild_join(self, guild):  #When the bot joins a server, we initalize certain parameters to avoid KeyError later on.
        await self.starboard_handler.create_table(guild.id)  #If the Server id is not registered in the JSON, we initailize it.
        if not await self.parameter_manager.entry_exists(guild.id):
            starboard = find(lambda x: x.name == 'starboard',  guild.text_channels)  #We try to define the #general channel to be the default channels.
            if starboard and starboard.permissions_for(guild.me).send_messages:  #Making sure we can send messages at all.... If so, we go ahead and set the channels.
                await self.parameter_manager.add_entry(guild.id, starboard.id)
            else:  #Otherwise, we just set up the potatoes to be the first channel that we can identify.
                quick_setup = find(lambda x: x.permissions_for(guild.me).send_messages, guild.text_channels)
                await self.parameter_manager.add_entry(guild.id, quick_setup.id)




    @commands.guild_only()
    @commands.check(has_permissions)
    @commands.command(help="[JP]:setstarboardchannel [チャンネル名]　で私がスターボードに相応しいメッセージを[チャンネル名]に貼ります！[EN]:setstarboardchannel <channel> changes the starboard channel to <channel>", brief="スターボード発言を投稿するチャンネルを変えます。")
    async def setstarboardchannel(self, ctx, args: discord.TextChannel):
        guildId=ctx.guild.id

        async def set_channel(channel):
            await self.parameter_manager.update_entry(guildId, "starboard_channel",  channel.id)
            await ctx.send(embed=self._getOneLineEmbed("[JP]:スターボードチャンネル変えました！[EN]:Starboard channel changed！",
                 f"[JP]:これからは　{channel.mention}　にスターボードメッセージを貼ります！[EN]:From now on all starboard messages will be sent to {channel.mention}", ctx))
        await set_channel(args)


    @setstarboardchannel.error
    async def starboardchannerror(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(self.bot.content_to_lang("[JP]:ごめんなさい、指定されたチャンネル見つけられなかった…[EN]:I couldn't find the specified channel", ctx))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.bot.content_to_lang(f"[JP]:コマンドの入力方法が間違ってるよ！正しい入力方法は``{ctx.prefix}setstarboardchannel [チャンネル名]``だよ！\
                [EN]:Incorrect command format. Correct format is ``{ctx.prefix}setstarboardchannel <channelname>``", ctx))
        elif isinstance(error, commands.MissingPermissions):
            await self.bot.insuff
        elif isinstance(error, commands.NoPrivateMessage):
            await self.bot.nodm(ctx, error)


    @commands.guild_only()
    @commands.group(help="[JP]:threshold: スターボード登録されるまでに必要なリアクション数を教えてあげる！[EN]:reaction: Tells you the number of reactions to reach starboard", brief="スターボード登録の為に必要なリアクション数の提示/変更", invoke_without_command=True)
    async def threshold(self, ctx):
        await ctx.send(self._fetch_parameter(ctx.guild.id, "starboard_threshold"))


    @threshold.error
    async def thresherror(self, ctx,error):
        if isinstance(error, commands.NoPrivateMessage):
            await self.bot.nodm(ctx, error)

    @commands.guild_only()
    @commands.check(has_permissions)
    @threshold.command(help="[JP]:threshold change [整数]: で私がスターボードに貼るまでに必要なリアクション数を [数字] に変えちゃいます！ [EN]:threshold change <number>: Changes the number of reactions to qualify for starboard to <number>", brief="スターボード登録の為に必要なリアクション数の提示/変更")
    async def change(self, ctx, args):
        threshNum = int(args)
        if threshNum and threshNum > 0:
            guildId=ctx.guild.id
            await self.parameter_manager.update_entry(guildId, "starboard_threshold", threshNum)
            await ctx.send(embed=self._getOneLineEmbed("[JP]:設定変更完了！[EN]:Settings successfully changed！",
                f"[JP]:これからはリアクション数　{threshNum} でメッセージをスターボードに貼り付けます！[EN]:The number of reacts required for starboard is now:　{threshNum}", ctx))
        else:
            raise UserInputError

    @change.error
    async def threshchange(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.bot.content_to_lang(f"[JP]:コマンドの入力方法が間違ってるよ！正しい入力方法は``{ctx.prefix}threshold change [数字]``だよ！\
                [EN]:Incorrect command format. Correct format is ``{ctx.prefix}threshold change <number>``", ctx))
        elif isinstance(error, commands.UserInputError):
            await ctx.send(self.bot.content_to_lang("[JP]:0以上の数字で答えてください…[EN]:Please enter an integer greater than 0", ctx))
        elif isinstance(error, commands.MissingPermissions):
            await self.bot.insuff
        elif isinstance(error, commands.NoPrivateMessage):
            await self.bot.nodm(ctx, error)

    @commands.guild_only()
    @commands.group(help="[JP]:reaction: 気に入ったメッセージをスターボードに貼りたいときに使うリアクションを教えちゃおう！[EN]:reaction: Shows the reaction needed to qualify for starboard.", brief="スターボード登録に必要なリアクションを変更/提示", aliases=["react"], invoke_without_command=True)
    async def reaction(self, ctx):
        reaction = await self._fetch_parameter(ctx.guild.id, "starboard_emoji")
        await ctx.send(reaction)


    @reaction.error
    async def reactionerror(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await self.bot.nodm(ctx, error)

    @commands.guild_only()
    @commands.check(has_permissions)
    @reaction.command(help="[JP]:reaction [絵文字]: でやるべきリアクションを [絵文字] に変えちゃうよ～[EN]:reaction <emoji> changes the reaction to qualify for starboard to <emoji>")
    async def to(self, ctx, args: commands.EmojiConverter):
        guildId=ctx.guild.id
        await self.parameter_manager.update_entry(guildId,"starboard_emoji", str(args))
        await ctx.send(embed=self._getOneLineEmbed("[JP]:設定変更完了！[EN]:Settings successfully changed!",
                f"[JP]:これからお気に入りのメッセージには　{args}でリアクションしてね！[EN]:Please react with {args} on messages you want on starboard", ctx))

    @commands.guild_only()
    @to.error
    async def to_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(self.bot.content_to_lang("[JP]:変える対象は絵文字にしてね…[EN]:Please change to an emoji that can be used for a reaction", ctx))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.bot.content_to_lang(f"[JP]:コマンドの入力方法が間違ってるよ！正しい入力方法は``{ctx.prefix}reaction to [絵文字]``だよ！\
                [EN]:Incorrect command format. Correct format is ``{ctx.prefix}reaction to <Emoji>``", ctx))
        elif isinstance(error, commands.MissingPermissions):
            await self.bot.insuff
        elif isinstance(error, commands.NoPrivateMessage):
            await self.bot.nodm(ctx, error)

    @commands.guild_only()
    @commands.command(help="[JP]:今まで一番人気のコメントした人達をランキングで表しちゃう！10位以降の人達見たかったら下のリアクトで操作してね![EN]:Shows the top ranking users on the starboard. To see ranks below 10th, use the reacts at the bottom.", brief="スターボードのトップランキングを提示します。")
    async def leaderboard(self, ctx):
        temparray = await self.starboard_handler.get_all_user_and_count(ctx.guild.id)
        if len(temparray) == 0: #If the guild doesn't have anybody on the starboard, we return a message informing the user.
            embed=discord.Embed(description=self.bot.content_to_lang("[JP]:このサーバーのスターボードは空っぽです。好きなメッセージにリアクションを付けてスターボードを活用させちゃおう！\
                    [EN]:There is nothing on the starboard. Go react to your favorite messages!", ctx), color=0xff0000)
            await ctx.send(embed=embed)

        else:
            c = Counter()
            for record in temparray:
                c[record["author_id"]] += record["count"]
            keyArray = c.most_common()  #Quick code that sorts the leaderboard entries from highest to lowest
            leaderboardEmbed = await self.createLeaderboardEmbed(keyArray, ctx)



    @leaderboard.error
    async def leaderboarderror(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await self.bot.nodm(ctx, error)


    async def starboard_condition_check(self, payload, message, reaction, check):
        reactor = self.bot.get_user(payload.user_id)
        if message.author.bot:
            return False
        if str(reaction) !=str(check):
            return False
        if message.author.id == payload.user_id:
            await message.remove_reaction(payload.emoji, reactor)
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
        if self.bot.get_user(payload.user_id).bot:
            return
        object_list = await self.unpack_payload(payload)
        check_emoji = await self._fetch_parameter(payload.guild_id, "starboard_emoji")
        guild = object_list["guild"]
        if guild == None:
            return
        channelToPost = guild.get_channel(await self._fetch_parameter(payload.guild_id, "starboard_channel"))
        message =object_list["message"]
        lang = self.bot.get_language(guild)
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
                if starboard_entry.author_id == 0:
                    starboard_entry.author_id=message.author.id
                if starboard_entry.starboard_message == None:  #If the starboardJson currently does not contain the message, we create a new message to send to starboard_channel
                    #Perform final check.
                    if await self.starboard_handler.entry_exists(guild.id, id=message.id):
                        record = await self.starboard_handler.get_entry(guild.id,message.id)
                        starboard_message = await channelToPost.fetch_message(starboard_entry.starboard_message)
                        await starboard_message.edit(embed=embed)
                    else:
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


                starboard_entry.update_count(count) #Updates starboardJson with the message and corresponding starboard info, along with the number of reactions.
                await self.starboard_handler.update_entry(guild.id, starboard_entry)


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):  #updates the starboard when the threshold of reactions is met
        if self.bot.get_user(payload.user_id).bot:
            return
        object_list = await self.unpack_payload(payload)
        check_emoji = await self._fetch_parameter(payload.guild_id, "starboard_emoji")
        guild = object_list["guild"]
        if guild == None:
            return
        lang = self.bot.get_language(guild)
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
                if starboard_entry.author_id == 0:
                    starboard_entry.author_id=message.author.id
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
        if guild == None:
            return
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


class StarboardEntry:

    #A Starboard Entry which contains all details of a message that made it onto the Starboard.
    __slots__ = ["id", "message", "starboard_channel", "count", "author_id", "guild_id", "starboard_message", "attachments"]


    def __init__(self, guild_id, id, starboard_channel, count, author_id, message, starboard_message=None, attachments=None):
        self.id = id
        self.message = message
        self.starboard_channel = starboard_channel
        self.count = count
        self.author_id = author_id
        self.guild_id = guild_id
        self.starboard_message = starboard_message
        self.attachments = attachments


    def to_dict(self):
        temp_dict = {"id": self.id, "count": self.count, "author_id": self.author_id, "starboard_channel": self.starboard_channel, "starboard_message": self.starboard_message}
        return temp_dict


    def update_count(self, count):
        difference = count-self.count
        self.count = count
        return difference


    def get_message(self):
        return self.message

    def update_starboard_message(self, starboard_message):
        self.starboard_message = starboard_message

    def get_starboard_message(self):
        return self.starboard_message


    def set_attribute(self, name, value):
        self[name] = value


    def get_channel(self):
        if channel in self:
            return self.channel
        else:
            return None


def setup(bot):
    bot.add_cog(Starboard(bot))
