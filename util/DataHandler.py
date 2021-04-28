
import datetime
import asyncpg

class DataHandler:


    def __init__(self, parameters = None, backup= 99999999, database_name=None):
        self.backup=backup
        self.data = {}
        self.parameters = parameters or {}
        self.debounce = False
        self.database_name = database_name or "r18botdb"



    def _convert_dict_to_keys_and_value_query(self,dict):
        keys = ""
        for key in dict.keys():
            keys=f"{keys},{key}"
        values = ""
        for value in dict.values():
            if isinstance(value, str):
                value = f"'{value}'"
            values=f"{values},{value}"
        return keys[1:], values[1:]

    async def _check_and_create_table_exists(self, tablename, dict):
        connection = await self._get_connection()
        query = ""
        for i in dict:
            query = f"{query},{i} {dict[i]}"
        query = query[1:]
        await connection.execute(f'''IF EXISTS (SELECT FROM INFORMATION_SCHEMA.TABLES
           WHERE TABLE_NAME = {tablename})
        BEGIN
            drop table {tablename};
        END

        ELSE

        BEGIN
        CREATE TABLE {tablename} ({query}
             PRIMARY KEY(id));
        End''')
        await connection.close()


    async def _get_connection(self):
        connection = await asyncpg.connect(f'postgresql://postgres:akemichan4@localhost/{self.database_name}')
        return connection

    async def update_entry(self, tablename, id=None, *,object=None, parameter=None,value=None):
        connection = await self._get_connection()
        entry_id = id
        if object:
            entry_id = object.id
        if await DataHandler.entry_exists(tablename, id=entry_id):
            query=""
            if object:
                query = self._convert_dict_to_string_query(object.to_dict())
            elif index and value:
                if isinstance(value, str):
                    query = f"{index}='{value}'"
                else:
                    query = f"{index}={value}"
            await connection.execute(f'''UPDATE {tablename}
            SET {index}=$1
            WHERE id=$2;''',  parameter, value, entry_id)
            await connection.close()
        else:
            await connection.close()
            await DataHandler.add_entry(tablename, object.to_dict())



    async def add_entry(self, tablename, parameters, parameter_length, *args):
        connection= await self._get_connection()
        #key, value = self._convert_dict_to_keys_and_value_query(dict)
        value=""
        for i in range(parameter_length):
            value=f"{value},${i+1}"
        value=value[1:]
        await connection.execute(f'''INSERT INTO {tablename} ({parameters})
            VALUES ({value});''', args)
        await connection.close()


    async def remove_entry(self, tablename, *, object=None, id=None):
        connection = await self._get_connection()
        entry_id = id
        if object:
            entry_id = object.id
        if await DataHandler.entry_exists(self, tablename, id=entry_id):
            await connection.execute(f'''DELETE FROM {tablename}
            WHERE id=$1;''', entry_id)
            await connection.close()
        else:
            await connection.close()



    async def get_entry(self, tablename, id):
        connection = await self._get_connection()
        entry = await connection.fetchrow(f''' SELECT * FROM {tablename} WHERE id=$1;''', id)
        await connection.close()
        return entry


    async def get_all_where(self, tablename, parameter, condition):
        connection = await self._get_connection()
        """Gets all entries from the table where a certain condition is met. condition must be a valid SQL condition"""
        list = await connection.fetch(f""" SELECT * FROM {tablename} WHERE {parameter}=$1;""", condition)
        await connection.close()
        return list



    async def get_all_data(self, tablename):
        """Gets all entries in the table"""
        connection = await self._get_connection()
        list = await connection.fetch(f"""SELECT * FROM {tablename};""")
        await connection.close()
        return list


    async def entry_exists(self, tablename, *, object=None, id=None):
        connection = await self._get_connection()
        id = id
        if object:
            id = object.id
        TorF= (await connection.execute(f'''SELECT 1
            FROM {tablename}
            WHERE id =$1 LIMIT 1;''', id))
        if TorF=="SELECT 1":
            await connection.close()
            return True
        else:
            await connection.close()
            return False


    async def create_table(self, tablename, parameters):
        connection = await self._get_connection()
        await connection.execute(
            f"CREATE TABLE IF NOT EXISTS {tablename} ({parameters});"
        )
        await connection.close()

class ROBLOXProfileHandler(DataHandler):
    async def entry_exists(self, userId):
        if isinstance(userId, int):
            return await super().entry_exists(f"robloxprofiles", id=userId)

    async def add_entry(self, userId, profileId):
        connection= await self._get_connection()
        await connection.execute(f'''INSERT INTO robloxprofiles (id, profileid)
            VALUES ($1, $2);''', userId ,profileId)
        await connection.close()

    async def update_entry(self, userId, newProfile):
        connection = await self._get_connection()
        await connection.execute(f'''UPDATE robloxprofiles
        SET profileid=$2
        WHERE id=$1;''',  userId, newProfile)
        await connection.close()

    async def get_entry(self, id):
        return await super().get_entry("robloxprofiles", id)

    async def remove_entry(self, id):
        connection = await self._get_connection()
        await connection.execute(f'''DELETE FROM robloxprofiles
                    WHERE id=$1;''', id)
        await connection.close()

class StarboardParameterHandler(DataHandler):

    async def entry_exists(self, guildId):
        if isinstance(guildId, int):
            return await super().entry_exists(f"starboard_parameters",id=guildId)


    async def add_entry(self, guildId, channel):
        connection= await self._get_connection()
        await connection.execute(f'''INSERT INTO starboard_parameters (id, starboard_threshold, starboard_emoji, starboard_channel)
            VALUES ($1, 3, $2 , $3);''', guildId ,"\u2b50", channel)
        await connection.close()

    async def update_entry(self, guildId, parameter, value):
        connection = await self._get_connection()
        entry_id = guildId
        await connection.execute(f'''UPDATE starboard_parameters
        SET {parameter}=$2
        WHERE id=$1;''',  guildId, value)
        await connection.close()

    async def get_entry(self, id):
        return await super().get_entry("starboard_parameters", id)


class ParameterHandler(DataHandler):
    async def entry_exists(self, guildId):
        if isinstance(guildId, int):
            return await super().entry_exists(f"server_parameters",id=guildId)


    async def add_entry(self, guildId, channel):
        connection= await self._get_connection()
        await connection.execute(f'''INSERT INTO server_parameters (id, command_prefix, language, welcome_message, welcome_channel, default_role)
            VALUES ($1, $2, $3, $4, $5, $6);''', guildId , "!", "EN", "Welcome!", channel, None)
        await connection.close()

    async def update_entry(self, guildId, parameter, value):
        connection = await self._get_connection()
        entry_id = guildId
        await connection.execute(f'''UPDATE server_parameters
        SET {parameter}=$2
        WHERE id=$1;''',  guildId, value)
        await connection.close()



    async def get_entry(self, id):
        return await super().get_entry("server_parameters", id)


class StarboardHandler(DataHandler):
    def __init__(self):
        super().__init__()

    async def get_all_data(self, guildId):
        if isinstance(guildId, int):
            return await super().get_all_data(f"starboard_{guildId}")

    async def entry_exists(self, guildId, *, object=None, id=None):
        if isinstance(guildId, int):
            return await super().entry_exists(f"starboard_{guildId}",object=object, id=id)

    async def add_entry(self, guildId, object):
        connection= await self._get_connection()
        await connection.execute(f'''INSERT INTO starboard_{guildId} (id, starboard_message, count, author_id, starboard_channel)
            VALUES ($1, $2, $3, $4, $5);''', object.id, object.starboard_message, object.count, object.author_id, object.starboard_channel)
        await connection.close()

    async def remove_entry(self, guildId, object):
        if isinstance(guildId, int):
            await super().remove_entry(f"starboard_{guildId}",object=object)

    async def update_entry(self, guildId, object):
        connection = await self._get_connection()
        entry_id = object.id
        if await self.entry_exists(guildId, id=entry_id):
            await connection.execute(f'''UPDATE starboard_{guildId}
            SET starboard_message=$1, count=$2, author_id=$3, starboard_channel=$4
            WHERE id=$5;''',  object.starboard_message, object.count, object.author_id, object.starboard_channel, entry_id)
            await connection.close()
        else:
            await connection.close()
            await self.add_entry(guildId, object)

    async def get_all_user_and_count(self, guildId):
        connection = await self._get_connection()
        list= await connection.fetch(f'''SELECT author_id, count FROM starboard_{guildId}''')
        await connection.close()
        return list

    async def get_entry(self, guildId, id):
        return await super().get_entry(f"starboard_{guildId}", id)

    async def create_table(self, guildId):
        await super().create_table(f"starboard_{guildId}", "id bigint, starboard_message bigint, count bigint, author_id bigint, starboard_channel bigint, PRIMARY KEY(id)")
