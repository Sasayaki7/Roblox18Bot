import discord
from discord.utils import get
from discord.ext import commands
from discord.utils import find
import json
from util.DataHandler import LinkHandler
from Cogs.Links.Link import Link
from util.pageMenu import PageMenu
from discord.ext.commands.cooldowns import BucketType
from fuzzywuzzy import process, fuzz
import asyncio


class LinkCog(commands.Cog):



    def __init__(self, bot):
        self.bot = bot
        self.data_handler = LinkHandler()

		
    async def update_link(self, entry):  #updates starboardJson and returns the number of reactions that changed
        await self.data_handler.update_entry(entry)
        
    
    async def removeFromLinkJson(self, entry): #removes message from starboardJson and returns the number of reactions that changed
        self.data_handler.remove_entry(entry)
        self._writeToLink()



    async def link_exists(self, guildId, id): #checks if link database already contains the given message. returns a boolean
        return await self.data_handler.entry_exists(guildId, id=id)



    async def get_link(self, guildId, id):
        if (await self.link_exists(guildId, id)):
            record= await self.data_handler.get_entry(guildId, id)
            link = Link(guild_id=guildId, id=id, tag=record["tag"], owner=record["owner"])
            return link
        else:
            return None
            
    async def fuzzysearch(self, tag, guildId):
        list = await self.data_handler.get_all_data(guildId)
        choices = [x["id"] for x in list]
        candidates= process.extractBests(tag, choices, scorer=fuzz.partial_ratio, score_cutoff=85)
        return candidates

    async def get_link_owner(self, guildId, id):
        link = await self.get_link(guildId, id)
        if link:
            return link.owner
        else:
            return None
        
    def getOneLineEmbed(self, embedTitle, embedText):
        embed=discord.Embed(title=embedTitle, description=embedText, color=0xff0000)
        return embed
            
    async def set_link(self, guildId, link): 
        await self.data_handler.add_entry(guildId, link)


    async def remove_link(self, guildId, link):
        await self.data_handler.remove_entry(guildId, link)

       

    async def get_all_links(self, guildId):
        list = await self.data_handler.get_all_data(guildId)
        sortedList = sorted(list, key=lambda x: x["id"].lower()) 
        return sortedList
    
    async def get_link_list(self, guildId, tagToStart=None):
        sortedList = await self.get_all_links(guildId)
        if tagToStart == None:
            return sortedList
        else:
            newList = [x for x in sortedList if x["id"].lower()[:len(tagToStart)] == tagToStart.lower() ]
            return newList
     
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild):  #When the bot joins a server, we initalize certain parameters to avoid KeyError later on.
        await self.data_handler.create_table(guild.id)  #If the Server id is not registered in the JSON, we initailize it.


    @commands.group(help="""[JP]:link [タグ] で以前保存したタグを私が引っ張ってきて提示します!
        [EN]:link <tag> gets the word/sentence/phrase/link/image/whatever stored in <tag>.
        """, brief="保存されてるタグを引っ張ってきます。", invoke_without_command=True)
    async def link(self, ctx, *, args):
        lang = await self.bot.get_language(ctx)
        if not args:
            if lang == "JP":
                await ctx.send(f"コマンド入力方法が間違ってるよ！link使うには{ctx.prefix}link [タグ]だよ！[タグ]無しだとアケミ見つけられないな～。")
            elif lang == "EN":
                await ctx.send(f"Incorrect format. Please use {ctx.prefix}link <tag>")
            return
        localLink = await self.link_exists(ctx.guild.id, args)
        if localLink:
            tag =await self.get_link(ctx.guild.id, args)
            await ctx.send(tag.tag)
            return
        fuzzyResults = await self.fuzzysearch(args, ctx.guild.id)    
        if len(fuzzyResults) == 1:
            closeTag = await self.get_link(ctx.guild.id, fuzzyResults[0][0])
            msg = ""
            if lang == "JP":
                msg = await ctx.send(f"``{args}``は見当たらなかったけど…``{fuzzyResults[0][0]}`` なら見つかったよ。これかな？")
            elif msg == "EN":
                msg = await ctx.send(f"I couldn't find a tag matching ``{args}`` but… I found ``{fuzzyResults[0][0]}``. Is this it?")
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
            reaction = ""
            def check(r, u):
                return r.message.id == msg.id and u == ctx.author and (str(r.emoji)=="❌" or str(r.emoji)=="✅")
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', check=check, timeout = 15)
            except asyncio.TimeoutError:
                if lang == "JP":
                    await msg.edit(content=f"{ctx.author.mention}に聞いてるのに答えてくれない...\U0001f62d")
                elif lang == "EN":
                    await msg.edit(content=f"I'm asking {ctx.author.mention} but they won't answer...\U0001f62d")
                await msg.clear_reactions()
            else:
                if str(reaction.emoji) == "✅":
                    await msg.delete()
                    await ctx.send(closeTag.tag)
                else:
                    if lang == "JP":
                        await msg.edit(content="違ったのね...")
                    elif lang == "EN":  
                        await msg.edit(content = "Oh... never mind..")
                    await msg.clear_reactions()
                        
        elif len(fuzzyResults) > 1:
            string = ""
            for i in fuzzyResults:
                string=f"{string}``{i[0]}``\n"
            embed = discord.Embed(description=string)
            if lang == "JP":
                await ctx.send(f"惜しいのがいくつもあったよ…もしかしてこれのどれか？", embed=embed)
            elif lang == "EN":
                await ctx.send(f"I found several similar ones.... is it any of these?", embed=embed)
            else:
                print(lang)

        else:
            if lang == "JP":
                await ctx.send(f"ごめんなさい、``{args}``のタグ見つれられなかった…　\nタグを登録したかったら {ctx.prefix}setlink {args} [内容]で登録できるよ!")
            elif lang == "EN":
                await ctx.send(f"Sorry, I couldn't find link ``{args}``…　\nIf you want to use this link, please use {ctx.prefix}setlink {args} <content>")
            else:
                print(lang)


    @commands.command(help="[JP]:setlink　[タグ] [内容]で使われてないタグに内容を保存することができます。迷惑行為を防ぐ為にメンション付のメッセージは保存できません。[EN]:setlink <tag> <content> stores content. You can call the content by using the link command. To prevent abuse, you cannot store mentions.")
    async def setlink(self, ctx, arg1, *, arg2):
        lang = await self.bot.get_language(ctx)
        guildId = ctx.guild.id
        tagString = ""
        link=None
        if arg2:
            link = Link(guild_id=guildId, id=arg1, tag=arg2, owner=ctx.author.id)
        elif not arg2:
            if lang == "JP":
                await ctx.send(f"コマンドの長さが足りないよ！コマンドは ``{ctx.prefix}setlink {arg1} [内容]`` だよ!")
            elif lang == "EN":
                await ctx.send(f"Command missing argument. Correct format is ``{ctx.prefix}setlink {arg1} <content>``")
            else:
                print(lang)

            return
        if await self.link_exists(guildId, arg1):
            if lang == "JP":
                await ctx.send(f"ごめんなさい、``{arg1}``のタグは既に登録されてます…　別のタグを使って見て登録してご覧!")
            elif lang == "EN":
                await ctx.send(f"Link ``{arg1}`` is already taken. Please try a different tag")
            else:
                print(lang)

        elif len(ctx.message.mentions) > 0 or len(ctx.message.role_mentions) > 0 or (ctx.message.mention_everyone==True):
            if lang == "JP":
                await ctx.send(f"ごめんなさい、メンションのあるメッセージは迷惑だから登録出来ないの。メンションを消してもう一回登録してみて!")
            elif lang == "EN":
                await ctx.send(f"Sorry, you cannot use mentions in tags")                
            else:
                print(lang)

        else:
            await self.set_link(guildId, link)
            if lang == "JP":
                await ctx.send(embed =self.getOneLineEmbed("タグ登録成功しました!", f"``{arg1}``のタグ登録に成功しました！"))
            elif lang == "EN":
                await ctx.send(embed =self.getOneLineEmbed("Tag successfully stored", f"``{arg1}`` has been registered!"))
            else:
                print(lang)

            
    @link.command(help="[JP]:link remove [タグ]で自分が以前作ったタグ、あるいは権限を持ってる方がタグを消すことができます。[EN]:link remove <tag> removes the tag for other people to use.")
    @commands.cooldown(rate=1, per=3, type = BucketType.user)
    async def remove(self, ctx, *, args):
        lang = await self.bot.get_language(ctx)
        if not args:
            if lang == "JP":
                await ctx.send(f"コマンドの長さが足りないよ！コマンドは ``{ctx.prefix}link remove [タグ]`` だよ!")
            elif lang == "EN":
                await ctx.send(f"Insufficient command length! Command should be ``{ctx.prefix}link remove <tag>``")
            return
        guildId = ctx.guild.id
        tag = await self.get_link(guildId, args)
        if tag and (tag.owner==ctx.message.author.id or self.bot.has_permissions(ctx)):
            await self.remove_link(guildId, tag)
            if lang == "JP":
                await ctx.send(embed =self.getOneLineEmbed("タグを削除しました!", f"{args}　のタグは消しておきました！"))
            elif lang == "EN":
                await ctx.send(embed =self.getOneLineEmbed("Tag deleted!", f"Tag {args}　has been successfully deleted!"))
            else:
                print(lang)

        elif not tag:
            if lang == "JP":
                await ctx.send(f"このタグ最初から存在しなかったので、一応消えてるよ!")
            elif lang == "EN":
                await ctx.send("This tag didn't exist anyways.")
            else:
                print(lang)

        else:
            if lang == "JP":
                await ctx.send(f"ごめんなさい、このタグは別の方が持っています。タグを削除したかったら<@!{tag.owner}>かサーバーの管理人さんに聞いてね!")
            elif lang == "EN":
                await ctx.send(f"This tag is owned by someone else. If you want this tag gone, please ask <@!{tag.owner}> or a server mod.")
            else:
                print(lang)



    @commands.command(help="[JP]:linklist で今登録されてるタグ一覧を教えてあげる。\nlinklist [文字]すれば[文字]から始まるタグ一覧を引っ張ってくるよ！[EN]:linklist shows the list of tags. \nlinklist <string> shows all the links that start with <string>")
    async def linklist(self, ctx, *args):
        if len(args) > 0:
            tagString = ctx.message.content[len(ctx.prefix)+9:]
            sortedListOfRecords = await self.get_link_list(ctx.guild.id, tagString)
        else:   
            sortedListOfRecords = await self.get_link_list(ctx.guild.id)
        sortedListOfLinks = [records["id"] for records in sortedListOfRecords]
        lang = await self.bot.get_language(ctx)
        if len(sortedListOfLinks) == None:
            if lang == "JP":
                await ctx.send(f"このサーバーにはタグがまだ無いみたいよ！ {ctx.prefix}setlink [タグ] [内容]でタグ作ってみようよ！")
            elif lang == "EN":
                await ctx.send(f"This server has no tags. Create the first by using ``{ctx.prefix}setlink <tag> <content>")
            return
        elif len(sortedListOfLinks) == 0:
            if lang == "JP":
                await ctx.send(f"この条件に当てはまるタグは見当たらなかったな…")
            elif lang == "EN":
                await ctx.send(f"Could not find tags meeting specified condition")
            return
        if lang == "JP":
            link_menu = PageMenu(ctx=ctx, title="タグ一覧", lists = [sortedListOfLinks], subheaders = "タグ", lang = lang)
            await link_menu.activate()
        elif lang == "EN":
            link_menu = PageMenu(ctx=ctx, title="Tag List", lists = [sortedListOfLinks], subheaders = "Tags", lang = lang)
            await link_menu.activate()

