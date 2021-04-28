import discord
from discord.utils import get
from discord.ext import commands
from discord.utils import find
import json
import datetime
import math
import asyncio
import re
from util.pageMenu import PageList, PageVariableList
import sys
import traceback
from discord.ext.commands.cooldowns import BucketType
import time

class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):


        super().__init__(command_attrs = dict(help="[JP]:help: この画面を表示します。 \nhelp [コマンド]： コマンドの詳細情報を表示します。[EN]:help: shows this screen. \nhelp <command>: shows details of that command"))

    async def send_bot_help(self, mapping):
        helplist_subheaders = []
        helplist_headers = []
        helplist_contents = []
        counter = -1
        for cogs in mapping:
            counter = counter+1
            helplist_headers.insert(counter, cogs.qualified_name if cogs else "Misc")
            helplist_subheaders.insert(counter, [])
            helplist_contents.insert(counter, [])
            command_count = 0
            for cmds in mapping[cogs]:
                if command_count > 0 and command_count%6 == 0 and not cmds.hidden:
                    counter = counter+1
                    helplist_headers.insert(counter, f"{cogs.qualified_name if cogs else 'Misc'} (Part {command_count/4+1})")
                    helplist_contents.insert(counter, [self.context.bot.content_to_lang(cmds.help, self.context.guild)])
                    helplist_subheaders.insert(counter, [cmds.name])
                    command_count +=1
                elif not cmds.hidden:
                    helplist_contents[counter].append(self.context.bot.content_to_lang(cmds.help, self.context.guild))
                    helplist_subheaders[counter].append(cmds.name)
                    command_count +=1
                if not cmds.hidden and isinstance(cmds, commands.Group):
                    for subcmd in cmds.commands:
                        helplist_contents[counter].append(self.context.bot.content_to_lang(subcmd.help, self.context.guild))
                        helplist_subheaders[counter].append(f"{cmds.name} {subcmd.name}")
                        command_count +=1

            if command_count == 0:
                helplist_subheaders.pop(counter-1)
                helplist_contents.pop(counter-1)
                helplist_headers.pop(counter-1)
                counter = counter-1


        help_menu = PageVariableList(self.context, titles=helplist_headers, subheaders= helplist_subheaders, contents=helplist_contents, footer= self.get_command_signature(), color=0xffff00)
        await help_menu.activate()



    async def send_command_help(self, command):
        lang = await self.context.bot.get_language(self.context)
        embed = discord.Embed(title=command.name, description = self.context.bot.content_to_lang(command.help, self.context.guild))
        msg = await self.context.send(embed=embed)
        await msg.add_reaction("✅")
        def check(r, u):
                return r.message.id == msg.id and u == self.context.author and  str(r.emoji)=="✅"
        reaction, user = await self.context.bot.wait_for('reaction_add', check=check)
        await msg.delete()

    def get_command_signature(self):
        return self.context.bot.content_to_lang(f"[JP]:わからないコマンドがあったら{self.context.prefix}help [コマンド名]ってやってね！詳細教えてあげる！\
            [EN]:If you need further details on a command, use {self.context.prefix}help <commandname>", self.context.guild)


class Basic(commands.Cog):


    __slots__ = ["bot", "r18version", "__changelog", "versions", "__changelog_en", "data_getter", "languages", "prefixes"]


    def __init__(self, bot):
        self.bot = bot
        self.r18version = "0.0.0"
        self.__changelog=["[JP]:ボット作成[EN]:Created bot"]
        self.versions = [f"[JP]:**変更ログ v{x}**[EN]:**Change Log v{x}**" for x in ["0.0.0"]]
        self.bot.help_command = CustomHelpCommand()
        self.bot.get_language = self.get_language
        self.data_getter = self.bot.data_getter
        self.bot.insuff = self.insuffpermission
        #self.bot.on_command_error = self.on_command_error
        self.bot.on_error = self.on_error
        self.bot.content_to_lang = self.content_to_lang
        self.bot.nodm=self.nodm
        self.bot.languages = {}
        self.bot.loop.create_task(self.lang_setup())




    def extract_context(self, args):
        for item in args:
            if isinstance(item, commands.Context):
                return item

    async def on_command_error(self, ctx, error, *args, **kwargs):
        if isinstance(error, commands.MissingRequiredArgument):
            pass
        elif isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.BadArgument):
            pass
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.NotOwner):
            pass
        elif isinstance(error, commands.NoPrivateMessage):
            pass
        elif isinstance(error, commands.CommandOnCooldown):
            pass
        else:
            await ctx.send(self.content_to_lang("[JP]:コマンドエラー発生。製作者に報告しました。[EN]:Command error: The creator has been notified",ctx))
            embed=discord.Embed(title=f"{ctx.command.name}においてエラーが発生しました！")
            embed.add_field(name="Args", value=f"{ctx.command}", inline=True)
            if hasattr(error, 'message'):
                embed.add_field(name="エラーメッセージ", value=f"{error.message.content}")
            embed.timestamp=datetime.datetime.now()
            embed.add_field(name="種類", value=type(error).__name__, inline=True)
            if ctx.guild:
                embed.add_field(name="鯖", value=f"{ctx.guild.id}, {ctx.guild.name}", inline=True)
            embed.add_field(name="発言者", value=f"{ctx.message.author}")
            embed.add_field(name="traceback", value=f"{''.join(traceback.format_exception(type(error), error, error.__traceback__))}"[-1023:], inline=False)
            await self.bot.get_user(self.bot.owner_id).send(embed=embed)


    async def on_error(self, event, *args, **kwargs):
        embed = discord.Embed(title="エラーが発生しました")
        embed.add_field(name="イベント", value=f"{event}")
        error_trace = sys.exc_info()
        embed.add_field(name="種類", value=error_trace[1], inline=True)
        #if args and isinstance(args[0], commands.Context):
         #   embed.add_field(name="args", value='\n'.join(args[0].args) if args else 'None', inline=True)
        #embed.add_field(name="args", value='\n'.join(args) if args else 'None', inline=True)
        if kwargs:
            str=""
            for key in kwargs.keys():
                str=f"{key}: {kwargs[key]}\n"
            embed.add_field(name="kwargs", value= str, inline=True)
        embed.add_field(name="traceback", value=traceback.format_exc()[-1023:], inline=False)

        await self.bot.get_user(self.bot.owner_id).send(embed=embed)


    def basic_embed():
        pass


    async def nodm(self, ctx, error):
        await ctx.send("このコマンドはサーバーでしか使えないよ！/You can only use this command in a server")


    def content_to_lang(self, text, ctx):
        lang=None
        if ctx:
            lang= self.bot.get_language(ctx)
        if lang == "JP" or not lang:
            return re.search("(?<=\[JP\]\:).+(?=\[EN\])", text, flags=(re.DOTALL | re.UNICODE)).group(0)
        elif lang == "EN":
            return re.search("(?<=\[EN\]\:).+", text, flags=re.DOTALL).group(0)

    async def getParameters(self, guildId, parameter):  #function that returns the parameter requested for a given guild stored in a dictionary JSON file. Takes in str parameter and optional ID guildId, returns value stored in dictionary.
        data = await self.data_getter.get_entry(guildId)
        return data.get(parameter)

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


    @commands.command(help="[JP]:ボットの反応をミリ秒単位で表示します![EN]:Returns ping of bot", brief="ピング時間を出します")
    async def ping(self, ctx):
        author = self.bot.user
        start = time.perf_counter()
        message = await ctx.send("Ping...")
        end = time.perf_counter()
        duration = (end - start) * 1000
        pingInMs= self.bot.latency*1000
        embed=discord.Embed(color=0x0000ef, title="Ping")
        embed.add_field(name=self.bot.content_to_lang("[JP]:ラグ[EN]:Latency", ctx), value= '{:.2f}ms'.format(pingInMs))
        embed.add_field(name=self.bot.content_to_lang('[JP]:反応[EN]:Response', ctx), value= '{:.2f}ms'.format(duration))
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.timestamp = datetime.datetime.now()
        await message.edit(embed=embed, content="")

    async def lang_setup(self):
        for guild in self.bot.guilds:
            lang=await self.getParameters(guild.id, "language")
            self.bot.languages[guild.id]=lang
            for channels in guild.text_channels:
                if await self.data_getter.entry_exists(channels.id):
                    lang=await self.getParameters(channels.id, "language")
                    self.bot.languages[channels.id]=lang

    @commands.Cog.listener()
    async def on_ready(self):
        await self.lang_setup()

    @commands.command(help="[JP]:私が働き続けている時間を表示します。[EN]:Shows uptime of アケミ", brief="再起動からの時間提示")
    async def uptime(self, ctx):
        guildId=ctx.guild.id
        author = self.bot.user
        newDatetime = datetime.datetime.now()
        difference = newDatetime-self.bot.starttime
        embed=discord.Embed(color=0x0000ef, description= self.bot.content_to_lang(f"[JP]:私は{ctx.guild.name if ctx.guild else ''}の皆さんの為に{difference.days}日{difference.seconds//3600}時間{(difference.seconds%3600)//60}分{int(difference.seconds%60)}秒休まず働いてます。\
        [EN]:I've been working nonstop for {difference.days} days {difference.seconds//3600} hours {(difference.seconds%3600)//60} min. {int(difference.seconds%60)} sec for the people of {ctx.guild.name if ctx.guild else ''}", ctx))
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)


    @commands.command(help="[JP]:私のverを表示します。[EN]:Shows the current version of R18Bot", aliases=["ver"])
    async def version(self, ctx):
        author = self.bot.user
        embed=discord.Embed(color=0x0000ef, description=self.bot.content_to_lang(f"[JP]:私はversion{self.r18version}です。[EN]:Current version: {self.r18version}", ctx))
        embed.set_author(name=author.name, icon_url=author.avatar_url)
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    def _getOneLineEmbed(self,embedTitle, embedText, ctx):
        embedTitle=self.bot.content_to_lang(embedTitle, ctx)
        embedText=self.bot.content_to_lang(embedText, ctx)
        embed=discord.Embed(title=embedTitle, description=embedText, color=0x15ee00)
        return embed



    @commands.command(help="[JP]:私の自己紹介をします。[EN]:Shows info about myself.")
    async def about(self, ctx):
        author = self.bot.user
        embed=discord.Embed(color=0x0000ef, title=self.bot.content_to_lang("[JP]:自己紹介[EN]:About myself",ctx),
            description=self.bot.content_to_lang(f"[JP]:私はROBLOX Discord鯖内での会話を便利に使えるため作り上げられたボットです。\
            \nコマンド表は　``{ctx.prefix}help``で閲覧できます。\
            \n提案、バグなどがあれば<@!346438466235662338>へDMお願いします。24時間以内に返答します。\
            [EN]:I was created to assist in ROBLOX discord servers be more enjoyable.\
            \nA list of commands can be seen by typing {ctx.prefix}help.\
            \nAny suggestions and feedback should go to <@!346438466235662338>. I will respond within 24 hours", ctx))

        embed.set_author(name=author.name, icon_url=author.avatar_url)
        invite_link="https://discord.com/api/oauth2/authorize?client_id=795827495651901451&permissions=93248&scope=bot"
        embed.add_field(name=self.bot.content_to_lang("[JP]:サーバーへの招待[EN]:Invite", ctx),
            value=self.bot.content_to_lang(f"[JP]:R18Botをあなたのサーバーに誘いたい場合は[こちら]({invite_link})をクリックください！\
                [EN]:If you want to invite me to your server, please click [here]({invite_link})", ctx))
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)


    @commands.command(help="[JP]:私に実装された最新の改造を表示いたします。[EN]:Will show the latest changes", aliases=["changelist"])
    async def changelog(self, ctx):
        changelog = PageList(ctx, title=self.bot.content_to_lang("[JP]:変更ログ[EN]:Change Log", ctx), subheaders=self.versions, contents=self.__changelog, author=True, page_index = 1, color=0x0000ff, timeout=120)
        await changelog.activate()


#    @commands.Cog.listener()
#    async def on_member_join(self, member):   #When a member joins, we send them a nice welcome message that is set by the guild using the welcome command to the specified welcome_channel
#        welcomechannel = await self.getParameters(member.guild.id, 'welcome_channel')
#        defaultRole = await self.getParameters(member.guild.id, 'default_role')
#        await asyncio.sleep(5)
#        await member.guild.get_channel(welcomechannel).send(f"{member.mention}, {await self.getParameters(member.guild.id, 'welcome_message')}")
#        def checkm(m):
#            return m.author == member and m.channel.id == welcomechannel
#        rAcc =  await self.bot.wait_for('message', check=checkm)
#        await member.add_roles(member.guild.get_role(defaultRole))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):  #When the bot joins a server, we initalize certain parameters to avoid KeyError later on.
        if not await self.data_getter.entry_exists(guild.id):  #If the Server id is not registered in the JSON, we initailize it.
            general = find(lambda x: x.name == 'general',  guild.text_channels)  #We try to define the #general channel to be the default channels.
            if general and general.permissions_for(guild.me).send_messages:  #Making sure we can send messages at all.... If so, we go ahead and set the channels.
                await self.data_getter.add_entry(guild.id, general.id)
            else:  #Otherwise, we just set up the potatoes to be the first channel that we can identify.
                quick_setup = find(lambda x: x.permissions_for(guild.me).send_messages)
                await self.data_getter.add_entry(guild.id, quick_setup.id)
        lang= await self.getParameters(guild.id, "language")
        self.bot.languages[guild.id]=lang


    @commands.guild_only()
    @commands.group(help="[JP]:これで新人に送る歓迎メッセージを教えちゃいます！[EN]:Gives you the greeting message",brief="歓迎メッセージを表示します。", invoke_without_command=True)
    async def welcome(self, ctx):
        await ctx.send(f'{ctx.author.mention} {await self.getParameters(ctx.guild.id, "welcome_message")}')


    @commands.guild_only()
    @commands.command(help="[JP]: owo [EN]: defrole <role> changes role to new role")
    async def defrole(self, ctx):
        if len(ctx.message.role_mentions) == 0:
            await ctx.send("Please mention a role to set as default role")
            return
        else:
            await self.data_getter.update_entry(ctx.guild.id, "default_role", ctx.message.role_mentions[0].id)
            await ctx.send(f"Default role successfully updated to <@!{ctx.message.role_mentions[0].id}>")

    @commands.guild_only()
    @welcome.command(help="[JP]:welcome change [メッセージ] で私が新人さんへ送る歓迎メッセージを変えます！[EN]:welcome change <message> to change the greeting message to <message> towards new members", brief="歓迎メッセージの内容を変えます")
    @commands.check(has_permissions)
    async def change(self, ctx, *, args):
        guildId=ctx.guild.id
        welcome_message = args
        await self.data_getter.update_entry(guildId, "welcome_message", welcome_message)
        await ctx.send(embed=self._getOneLineEmbed("[JP]:歓迎メッセージ変更完了！[EN]:Greeting message successfully changed!",
            f"[JP]:新たな歓迎メッセージは: \n {ctx.author.mention} {welcome_message}　\nになります！[EN]:The new gretting message will be:\n {ctx.author.mention} {welcome_message}", ctx))

    @change.error
    async def changeerror(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.bot.content_to_lang(f"[JP]:コマンドの長さが足りないよ！コマンドは ``{ctx.prefix}welcome change [メッセージ]`` だよ!\
				[EN]:Command missing argument. Correct format is ``{ctx.prefix}welcome change <newmessage>``", ctx))
        elif isinstance(error, commands.MissingPermissions):
            await self.insuffpermission(ctx, error)
        elif isinstance(error, commands.NoPrivateMessage):
            await self.nodm(ctx, error)



    @commands.guild_only()
    @welcome.command(help=f"[JP]:歓迎メッセージを送るチャンネルを変えます。 welcome channel [チャンネル名]で設定することが出来ます。新人さんが来たらこのチャンネルで歓迎致します！[EN]:welcome channel <channelName> Changes the channel where the greeting message towards newcomers will be sent.", brief="歓迎メッセージを送るチャンネルを変えます。")
    @commands.check(has_permissions)
    async def channelchange(self, ctx, ch: discord.TextChannel):
        guildId=ctx.guild.id
        async def set_channel(ch):
            await self.data_getter.update_entry(guildId, "welcome_channel", ch.id)
            await ctx.send(embed=self._getOneLineEmbed("[JP]:歓迎メッセージを送るチャンネル変えました！[EN]:Greeting channel changed!",
                f"[JP]:これからは歓迎メッセージは{ch.mention}に送ります！[EN]:The gretting message will now be sent to {ch.mention}", ctx))
        await set_channel(ch)

    @channelchange.error
    async def channelerror(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(self.bot.content_to_lang("[JP]:ごめんなさい、指定されたチャンネル見つけられなかった…[EN]:I couldn't find the specified channel", ctx))
        elif isinstance(error, commands.MissingPermissions):
            await self.insuffpermission(ctx, error)
        elif isinstance(error, commands.NoPrivateMessage):
            await self.nodm(ctx, error)


    @commands.guild_only()
    @commands.check(has_permissions)
    @commands.command(help="[JP]:prefix [文字]: で私を呼ぶ時のPrefixを[文字]に変えます！[EN]:prefix <string> changes the prefix to <string>", brief="コマンドに必要な時のPrefixを提示/変更")
    async def prefix(self, ctx, *, args=None):
        guildId = ctx.guild.id
        if not args:
            await ctx.send(ctx.prefix)
        elif len(args) >= 10:
            await ctx.send(embed=discord.Embed(description= self.bot.content_to_lang("[JP]:Prefixは9文字以内でお願いします。[EN]:Please keep the prefix 9 letters or less.", ctx)))
        else:
            await self.bot.set_prefix(ctx, args)
            await ctx.send(embed=self._getOneLineEmbed("[JP]:Prefix変更完了![EN]:Prefix successfully changed!",f"[JP]:私にコマンドする時には {args} command としてください!\
                [EN]:To use a command use ``{args}command``", ctx))

    @commands.command(help="[JP]:feedback [message]: 作成者にメッセージを送ります。1時間に2回しか使えないので注意！[EN]:feedback <message>: Sends feedback message to creator. Beware, you can only use this command twice an hour")
    @commands.cooldown(rate=2, per=3600, type = BucketType.user)
    async def feedback(self, ctx, *, args):
        embed=discord.Embed(title=f"{ctx.author.name}#{ctx.author.discriminator}からのフィードバックです。", description=args)
        await self.bot.get_user(self.bot.owner_id).send(embed=embed)
        await ctx.message.delete()
        await ctx.send("Feedback successfully sent!")


    @feedback.error
    async def feedbackerror(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.bot.content_to_lang(f"[JP]:コマンドの長さが足りないよ！コマンドは ``{ctx.prefix}feedback [メッセージ]`` だよ!\
				[EN]:Command missing argument. Correct format is ``{ctx.prefix}feedback <message>``", ctx))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(self.bot.content_to_lang(f"[JP]:このコマンドはまだ使えないよ！コマンド使えるまで後{error.retry_after}秒待ってね！\
				[EN]:Wait {error.retry_after} seconds until you can use this command again.", ctx))


    @commands.guild_only()
    @commands.check(has_permissions)
    @commands.group(help="[JP]:language: Changes language for server/アケミちゃんの言語を変えます。[EN]:language: Changes language for server/アケミちゃんの言語を変えます。", invoke_without_command=True)
    async def language(self, ctx):
        guildId = ctx.guild.id
        embed=discord.Embed(description="Select your language/言語を選んでください。")
        msg=await ctx.send(embed=embed)
        await msg.add_reaction("🇯🇵")
        await msg.add_reaction("🇬🇧")
        reaction = ""
        def check(r, u):
                return r.message.id == msg.id and u == ctx.author and (str(r.emoji)=="🇯🇵" or str(r.emoji)=="🇬🇧")
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', check=check, timeout = 15)
        except asyncio.TimeoutError:
            await msg.delete()
        else:
            if str(reaction.emoji) == "🇬🇧":
                await self.data_getter.update_entry(guildId, "language", "EN")
                self.bot.languages[guildId] = "EN"
                await ctx.send(embed=discord.Embed(title="Language changed!", description=f"English is now the default langauge!", color=0x00ff00))
            elif str(reaction.emoji)=="🇯🇵":
                await self.data_getter.update_entry(guildId, "language", "JP")
                self.bot.languages[guildId] = "JP"
                await ctx.send(embed=discord.Embed(title="言語変更成功！", description=f"このサーバーでの言語は日本語になりました！", color=0x00ff00))
            await msg.clear_reactions()





    @commands.guild_only()
    @commands.check(has_permissions)
    @language.command(help="[JP]:language chan: Changes language for this channel only/このチャンネルのみR18Botの言語を変えます。[EN]:language chan: Changes language for this channel only/このチャンネルのみR18Botの言語を変えます。")
    async def chan(self, ctx):
        channelId = ctx.channel.id
        embed=discord.Embed(description="Select your language/言語を選んでください。")
        msg=await ctx.send(embed=embed)
        await msg.add_reaction("🇯🇵")
        await msg.add_reaction("🇬🇧")
        reaction = ""
        def check(r, u):
                return r.message.id == msg.id and u == ctx.author and (str(r.emoji)=="🇯🇵" or str(r.emoji)=="🇬🇧")
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', check=check, timeout = 15)
        except asyncio.TimeoutError:
            await msg.delete()
        else:
            if not await self.data_getter.entry_exists(channelId):
                await self.data_getter.add_entry(channelId, 0)
            if str(reaction.emoji) == "🇬🇧":
                await self.data_getter.update_entry(channelId, "language", "EN")
                self.bot.languages[channelId] = "EN"
                await ctx.send(embed=discord.Embed(title="Channel language changed!", description=f"English is now the default langauge!", color=0x00ff00))
            elif str(reaction.emoji)=="🇯🇵":
                await self.data_getter.update_entry(channelId, "language", "JP")
                self.bot.languages[channelId] = "JP"
                await ctx.send(embed=discord.Embed(title="チャンネル言語変更成功！", description=f"このチャンネルでの言語は日本語になりました！", color=0x00ff00))
            await msg.clear_reactions()




    async def insuffpermission(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            new_embed = discord.Embed(title=self.bot.content_to_lang("[JP]:権限が足りません！[EN]:Insufficient Permissions", ctx),
                description=self.bot.content_to_lang("[JP]:あなたはこのコマンドを使う権限を持っていません！[EN]:You do not have the sufficient permissions to use this command!", ctx))
            await ctx.send(embed=new_embed)



    def get_language(self, ctx):
        guild = ctx
        if isinstance(ctx, commands.Context):
            channel = ctx.channel
            if not channel.id in self.bot.languages:
                guild=ctx.guild
            else:
                return self.bot.languages[channel.id]
            if guild.id in self.bot.languages:
                return self.bot.languages[guild.id]
        else:
            return self.bot.languages[guild.id]



    def getOneLineEmbed(self, embedTitle, embedText):
        embed=discord.Embed(title=embedTitle, description=embedText, color=0xff0000)
        return embed



    async def botError(self, ctx, type):
        await ctx.send(embed=self._getOneLineEmbed("Error", ctx.command.name+errorList[type]))






    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild == None:
            return
        if message.reference:
            return
        if self.bot.user.mentioned_in(message) and (message.mention_everyone==False):
            value = (re.search("こんにち", message.content) or re.search("こんち", message.content))
            if value:
                await message.channel.send(f"{message.author.mention}さん、こんにちは！")
            else:
                pfx = await self.bot.get_prefix(message)
                await message.channel.send(self.bot.content_to_lang(f"[JP]:{message.author.mention}さん、私に何かして欲しい時は　``{pfx}`` の後にコマンドを追加してください。コマンド表は ``{pfx}help``で出てきます！\
					[EN]:{message.author.mention}, use ``{pfx}``command to give me a command. A list of commands is available by chatting ``{pfx}help``", message.guild))
        #elif re.search("おやす", message.content):
        #    if not (message.channel.id in sleepChannel):
         #       sleepChannel[message.channel.id] = {"sleepMessageCounter": 0, "sleepMessageTime": datetime.datetime.now()}
          #      await message.channel.send("おやすみなさい!")
        #    elif sleepChannel[message.channel.id]["sleepMessageCounter"] > nonsleepMessageThreshold or (sleepChannel[message.channel.id]["sleepMessageCounter"] > 1 and (datetime.datetime.now()-sleepChannel[message.channel.id]["sleepMessageTime"]).seconds > sleepMessageTime):
         #       sleepChannel[message.channel.id]["sleepMessageCounter"] = 0
          #      sleepChannel[message.channel.id]["sleepMessageTime"] =datetime.datetime.now()
           #     await message.channel.send("おやすみなさい!")
        #else:
         #   if message.channel.id in sleepChannel:
          #      sleepChannel[message.channel.id]["sleepMessageCounter"] = sleepChannel[message.channel.id]["sleepMessageCounter"] +1
           #     if sleepChannel[message.channel.id]["sleepMessageCounter"] > nonsleepMessageThreshold or (sleepChannel[message.channel.id]["sleepMessageCounter"] > 1 and (datetime.datetime.now()-sleepChannel[message.channel.id]["sleepMessageTime"]).seconds > sleepMessageTime):
            #        del sleepChannel[message.channel.id]




    @commands.is_owner()
    @commands.command(hidden=True)
    async def core_reload(self, ctx):
        try:
            self.bot.reload_extension("cogs.core")
        except:
            await ctx.send("Something went wrong")
        else:
            await ctx.send("core successfully reloaded!")

    @language.error
    @prefix.error
    async def generic_error(self, ctx, error):
        if isinstance(error,  commands.MissingPermissions):
            await self.insuffpermission(ctx, error)
        elif isinstance(error, commands.NoPrivateMessage):
            await self.nodm(ctx, error)


    #@bot.command()
    #async def tostring(ctx, args, help="Gets the name of the emote (developmental use only)"):
    #    await ctx.send(str(args[0]))






def setup(bot):
    bot.add_cog(Basic(bot))
