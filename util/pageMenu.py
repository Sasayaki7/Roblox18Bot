import discord
import math
import asyncio


class PageMenu:
	
    
    
    def __init__(self, ctx, title, lists, subheaders,  author=None,  entry_per_page = 10, page_index = 1, color=0x000000, timeout=120):
        self.page_index = page_index
        self.title = title
        self.entry_per_page = entry_per_page
        self.lists = lists
        self.total_pages = (len(lists[0])-1)//entry_per_page+1    
        self.author = author
        self.color = color
        self.subheaders = subheaders
        self.message = None
        self.timeout = timeout
        self.ctx = ctx
        self.current_page_embed = self._create_Page(1)

    def getOneLineEmbed(self, embedTitle, embedText):
        embed=discord.Embed(title=embedTitle, description=embedText, color=0xff0000)
        return embed

    
    
    def turn_to_prev_page(self):
        if self.is_first_page():
            return self.page_index
        else:
            self.page_index -= 1
            return self._create_Page()

    
    def _get_entries_from_dict(self, list, entry_per_page=None, page_index=None):
        embed_string = ""
        if page_index==None:
            page_index = self.page_index
        if entry_per_page==None:
            entry_per_page=self.entry_per_page
            
        for i in range((page_index-1)*entry_per_page, min((page_index)*(entry_per_page), len(list))):
            embed_string= f"{embed_string}{list[i]}\n"
        
        return embed_string
    
    
    
    def is_last_page(self):
        return self.total_pages == self.page_index
    
    
    def turn_To_page(self, page):
        if page == self.page_index:
            return self.current_page_embed
        else:
            self.page_index=page
            return self._create_Page()
    
    def turn_to_next_page(self):
        if self.is_last_page():
            return self.page_index
        else:
            self.page_index += 1
            return self._create_Page()
        
    
    def is_first_page(self):
        return 1 == self.page_index
    
    
    def _create_Page(self, page=None):
        current_page = page if page else self.page_index
        embed = discord.Embed(title=self.title, color=self.color)
        for list in range(len(self.lists)):
            embed.add_field(name=f"{self.subheaders if isinstance(self.subheaders,str) else self.subheaders[list]}", value=self._get_entries_from_dict(self.lists[list], self.entry_per_page, current_page), inline = True)
        if self.author:
            embed.set_author(self.author)
        if self.total_pages > 1:
            embed.set_footer(text=self.ctx.bot.content_to_lang(f"[JP]:ページ {self.page_index}/{self.total_pages}.\nページ操作は下のリアクトでしてね！\n❌か{self.timeout}秒リアクト無しの場合操作終了します。\
            [EN]:Page {self.page_index}/{self.total_pages}.\nTo turn pages, use reacts below.\nHit ❌ or timeout after {self.timeout} seconds to quit.", self.ctx)) 
        self.current_page_embed = embed
        return embed
        
        
    async def activate(self):
        if self.message == None:
            self.message = await self.ctx.send(embed=self.current_page_embed)
        if self.total_pages > 1:
            await self.message.add_reaction("⏮")
            await self.message.add_reaction("◀")
            await self.message.add_reaction("❌")
            await self.message.add_reaction("▶")
            await self.message.add_reaction("⏭")
            reactionString = ""
            def check(r, u):
                return r.message.id == self.message.id and u == self.ctx.author and (str(r.emoji)=="❌" or str(r.emoji)=="▶" or str(r.emoji)=="⏭" or str(r.emoji)=="◀" or str(r.emoji)=="⏮")

            while True:
                try:
                    reaction, user = await self.ctx.bot.wait_for('reaction_add', check=check, timeout = self.timeout)
                except asyncio.TimeoutError:
                    await self.message.edit(embed=self.getOneLineEmbed(self.ctx.bot.content_to_lang("[JP]:時間切れ[EN]:Timeout", self.ctx), 
                        self.ctx.bot.content_to_lang("[JP]:私これ以上待てないので、また何か欲しかったら呼んでね![EN]:You have timed out", self.ctx)))
                    break
                else:
                    reactionString = str(reaction.emoji)
                    if reactionString == "⏮": 
                        await self.message.edit(embed=self.turn_To_page(1))
                    elif reactionString == "◀":
                        self.turn_to_prev_page()
                        await self.message.edit(embed=self._create_Page())
                    elif reactionString == "▶":
                        self.turn_to_next_page()
                        await self.message.edit(embed=self._create_Page())

                    elif reactionString == "⏭":
                        await self.message.edit(embed=self.turn_To_page(self.total_pages))
                    await reaction.remove(self.ctx.author) 
                if reactionString == "❌":
                    break
            await self.message.clear_reactions()
            



class PageList(PageMenu):
    def __init__(self, ctx, title, subheaders, contents, author=True, page_index = 1, color=0x0000ff, timeout=120, itemsPerPage=1):
        self.page_index = page_index
        self.title = title
        self.subheaders = subheaders
        self.contents = contents
        self.total_pages = math.ceil(len(subheaders)/itemsPerPage)
        self.message = None
        self.timeout = timeout
        self.ctx = ctx
        self.color=color
        self.set_author = author
        self.itemsPerPage = itemsPerPage
        self.current_page_embed = self._create_Page(1)
        
        
    def _create_Page(self, page=None):
        current_page = page if page else self.page_index
        embed = discord.Embed(title=self.title, color=self.color)
        for field in range(self.itemsPerPage):
            embed.add_field(name=self.subheaders[current_page*self.itemsPerPage+field-1], value=self.contents[current_page*self.itemsPerPage+field-1])
        if self.set_author:
            author = self.ctx.bot.user
            embed.set_author(name=" ", url=author.avatar_url)
        if self.total_pages > 1:
            embed.set_footer(text=f'{self.ctx.bot.content_to_lang("[JP]:ページ[EN]:Page", self.ctx)} {self.page_index}/{self.total_pages}')
        self.current_page_embed = embed
        return embed
        
class PageVariableList(PageList):
    def __init__(self, ctx, titles, subheaders, contents, author=True, page_index = 1, color=0x0000ff, timeout=120, footer=""):
        self.page_index = page_index
        self.titles = titles
        self.subheaders = subheaders
        self.contents = contents
        self.total_pages = (len(titles))
        self.color=color
        self.timeout = timeout
        self.message = None
        self.ctx = ctx
        self.set_author = author
        self.footer = footer
        self.current_page_embed = self._create_Page(1)
        
        
    def _create_Page(self, page=None):
        current_page = page if page else self.page_index
        embed = discord.Embed(title=self.titles[current_page-1], color=self.color)
        for field in range(len(self.subheaders[current_page-1])):
            embed.add_field(name=self.subheaders[current_page-1][field], value=self.contents[current_page-1][field], inline=False)
        if self.set_author:
            author = self.ctx.bot.user
            embed.set_author(name=" ", url=author.avatar_url)
        if self.total_pages > 1:
            embed.set_footer(text=f'{self.ctx.bot.content_to_lang("[JP]:ページ[EN]:Page", self.ctx)} {self.page_index}/{self.total_pages}. {self.footer}')
        self.current_page_embed = embed
        return embed