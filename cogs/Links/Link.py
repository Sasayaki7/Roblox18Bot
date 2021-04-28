class Link():



    def __init__(self, guild_id, id, tag, owner):
        self.id = id
        self.tag = tag
        self.owner = owner
        self.guild_id = guild_id
        
        
    def to_dict(self):
        temp_dict = {"id": self.id, "owner": self.owner, "tag": self.tag}
        return temp_dict
      
        
    def get_id(self):
        return self.id
        
        
    def get_owner_id(self):
        return self.owner
        
        
    def get_owner_mention(self):
        return f"<@!{self.owner}>"
    
    def get_tag(self):
        return self.tag
