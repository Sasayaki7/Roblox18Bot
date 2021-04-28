# bot.py
import os
import json
import math
import discord
from discord.ext import commands
from util.DataHandler import ParameterHandler
import datetime


with open('token.txt', 'r', encoding='utf-8') as f:
    token = f.read()


print('token read')
data_getter = ParameterHandler(parameters={})

prefixes = {}

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True

async def getParameters(guildId, parameter):  #function that returns the parameter requested for a given guild stored in a dictionary JSON file. Takes in str parameter and optional ID guildId, returns value stored in dictionary.
    data = await data_getter.get_entry(guildId)
    return data.get(parameter)



async def update_parameter(guildId, parameter,value):
    await data_getter.update_entry(guildId, parameter, value)

#Gets prefix of command for a certain guild
#Because prefix requests are so common, we set up a quick cache system
async def get_prefix(bot, message):
    if not message.guild:
        return "?"
    if message.guild.id in prefixes:
        return prefixes[message.guild.id]
    else:
        prefix = await getParameters(message.guild.id, "command_prefix")
        prefixes[message.guild.id] = prefix
        return prefix

async def set_prefix(ctx, prefix):
    prefixes[ctx.guild.id]=prefix
    await update_parameter(ctx.guild.id, "command_prefix", prefix)

bot = commands.Bot(command_prefix=get_prefix, owner_id=346438466235662338, intents=intents)

@bot.check_once
def blacklist(ctx):
    for role in ctx.author.roles:
        if role.name == 'Muted':
            return False

    return True

bot.starttime=datetime.datetime.now()
bot.data_getter = data_getter
bot.set_prefix = set_prefix
bot.load_extension("cogs.core")




bot.run(token)
