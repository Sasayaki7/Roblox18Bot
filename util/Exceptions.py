
class BotErrors(Exception):
	pass
	
class LanguageError(BotErrors):
	"""Raise when there is an issue with the specified Language"""
	pass

class InsufficientPermError(BotErrors):
	"""Raise when user has insufficient permission to use command"""
	pass

class NoArgumentError(BotErrors):
	"""Raise when command doesn't have sufficient arguments in command"""
	pass

class NoChannelError(BotErrors):
    """Raise when channel specified does not exist"""
    pass
    
class NoMessageError(BotErrors):
    """Raise when message specified does not exist"""
    pass