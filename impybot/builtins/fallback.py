import sys
from impybot.plugin import Plugin, register
from impybot import shared
import xmpp

class FallbackPlugin(Plugin):
    '''Called when no plugin match on the event.
    
    Matches on any thing for either presence change or user inputs.
    '''

    # priority = -sys.maxint - 1
    match_type = shared.MESSAGE | shared.PRESENCE

    def __init__(self, bot):
        Plugin.__init__(self,bot)

    def action(self, matched, *args, **kwargs):
        if self.get_bot().get_matched(): return
        if isinstance(matched, xmpp.protocol.Message):
            return '\n'.join(["I can't understand what you just said.",
                "%s" % matched.getBody()])
        if isinstance(matched, xmpp.protocol.Presence):
            return None
        raise TypeError('The type of the second argument is invalid.')
# ------ End of XmppBot.FallbackPlugin------
register(FallbackPlugin, priority = sys.maxint)
