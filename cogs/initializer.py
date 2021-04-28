import asyncpg
import json
import asyncio

    
with open('parameters.json', 'r', encoding='utf-8') as f:
    parameterJson = json.load(f)

with open('starboard.json', 'r', encoding='utf-8') as f:
    starboardJson = json.load(f)

with open('link.json', 'r', encoding='utf-8') as f:
    linkJson = json.load(f)

        

async def main():
    conn = await asyncpg.connect('postgresql://postgres:akemichan4@localhost/botdb')
    
    
    await conn.execute('''DROP TABLE IF EXISTS server_parameters;
                 CREATE TABLE server_parameters (id bigint, welcome_channel bigint, welcome_message text, command_prefix text, PRIMARY KEY(id));''')
    await conn.execute('''DROP TABLE IF EXISTS starboard_parameters;
        CREATE TABLE starboard_parameters (id bigint, starboard_threshold int, starboard_emoji text, starboard_channel bigint, PRIMARY KEY(id));''')
        
    for servers in parameterJson:
        tempDict = parameterJson[servers]
        await conn.execute(f'''INSERT INTO server_parameters (id, welcome_channel, welcome_message, command_prefix)
            VALUES ({0 if servers=="default" else int(servers)}, {0 if not ("welcome_channel" in tempDict) else tempDict["welcome_channel"]}, '{tempDict["welcome_message"]}', '{tempDict["command_prefix"]}');''')
        await conn.execute(f'''INSERT INTO starboard_parameters (id, starboard_threshold, starboard_emoji, starboard_channel)
            VALUES ({0 if servers=="default" else int(servers)}, {5 if not ("starboard_threshold" in tempDict) else tempDict["starboard_threshold"]}, '{tempDict["starboard_emoji"]}', '{0 if not ("starboard_channel" in tempDict) else tempDict["starboard_channel"]}');''')

    for servers in starboardJson:
        await conn.execute(f'''DROP TABLE IF EXISTS starboard_{servers};
            CREATE TABLE starboard_{servers}
                (id bigint, starboard_message bigint, count bigint, author_id bigint, starboard_channel bigint, PRIMARY KEY(id));''')
        await conn.execute(f'''DROP TABLE IF EXISTS leaderboard_{servers};
            CREATE TABLE leaderboard_{servers} (id bigint, count int, PRIMARY KEY (id));''')
        for item in starboardJson[servers]:
            await conn.execute(f'''INSERT INTO starboard_{servers} (id, starboard_message, count, author_id, starboard_channel)
                VALUES ({int(item)}, {starboardJson[servers][item]["link"]}, {starboardJson[servers][item]["count"]},
                    {starboardJson[servers][item]["author"] if "author" in starboardJson[servers][item] else 0}, 
                    {starboardJson[servers][item]["channel"] if "channel" in starboardJson[servers][item] else 0});''')
        
        for item in parameterJson[servers]["leaderboard"].keys():
            await conn.execute(f'''INSERT INTO leaderboard_{servers} (id, count)
                VALUES ({int(item)}, {int(parameterJson[servers]["leaderboard"][item])})''')
                
    for servers in linkJson:
        await conn.execute(f'''DROP TABLE IF EXISTS links_{servers};
            CREATE TABLE links_{servers} (id text, tag text, owner bigint, PRIMARY KEY(id));''')
        for item in linkJson[servers]:
            await conn.execute(f'''INSERT INTO links_{servers} (id, tag, owner)
                VALUES ('{item}', '{linkJson[servers][item]["tag"]}', {linkJson[servers][item]["owner"]});''')
    
asyncio.get_event_loop().run_until_complete(main())