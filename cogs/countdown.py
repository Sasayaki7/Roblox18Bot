import discord
from discord.utils import get
from discord.ext import commands
from discord.utils import find
import datetime
import math

endTime = datetime.datetime(year=2021, month=5, day=27, hour=3, minute=59, second=59)

class Countdown(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def convertToDaysHoursMinutesSeconds(self, secs):
        return math.floor(secs/(24*3600)), math.floor((secs%(24*3600))/3600), math.floor((secs%(3600))/60), math.floor((secs%60))

    @commands.command(help="[JP]:lol[EN]:Joy...")
    async def countdown(self, ctx):
        currentTime = datetime.datetime.now()
        td = endTime-currentTime
        embed=discord.Embed(title='Time until Joy posts a selfie... or else...', color=0xff0000)
        day, hour, min, secs = self.convertToDaysHoursMinutesSeconds(td.total_seconds())
        embed.set_thumbnail(url='https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Dialog-error-round.svg/1200px-Dialog-error-round.svg.png')
        if endTime < currentTime:
            embed.add_field(name='Time up!', value="If the 70 year old hasn't posted a selfie bye bye (:")
            embed.set_image(url='https://external-preview.redd.it/72WcE6z9ObtSc65ghwcLwjS_ZoJwFojpFaZtTSP9P4o.png?s=3a13aa79a790d7d71e27136910e14bd28023fa3a')
        else:
            embed.add_field(name='Time Left:', value=f'{day} days, {hour} hr {min} min {secs} seconds...')
            embed.set_image(url='https://th.bing.com/th/id/Rf385e9d8bf117715617583d0f7d7d688?rik=szt5LPrNjXxsdw&riu=http%3a%2f%2fwww.bridgepointgroup.com.au%2fwp-content%2fuploads%2f2016%2f06%2fTime-Bomb-msyqxzmabidgu6vgxo67qkcr5bxbwuy4vd0mej6md4.jpg&ehk=vu8GYwyepcPH4E6W9ME%2fUpJJDzBhaPrpcQYlBaDI48Y%3d&risl=&pid=ImgRaw')
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Countdown(bot))
