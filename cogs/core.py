import discord
from discord.ext import commands


mapping = ["cogs.user", "cogs.basic", "cogs.starboard"]
class Core(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(hidden=True)
    async def reload(self, ctx, cog_name):
        if f"cogs.{cog_name}" in mapping:
            self.bot.reload_extension(f"cogs.{cog_name}")
            await ctx.send("Successfully reloaded cog!")
        else:
            await ctx.send("That is not a cog")

def setup(bot):
    bot.add_cog(Core(bot))
    for cog in mapping:
        print(f"{cog} loaded")
        bot.load_extension(cog)
