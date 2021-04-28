import discord

class StarboardEntry:

    #A Starboard Entry which contains all details of a message that made it onto the Starboard.
   

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