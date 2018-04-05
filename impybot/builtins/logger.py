import sys, os
from impybot.plugin import Plugin, register
from impybot import shared
import xmpp

import logging
# import logging.handlers

class LoggerPlugin(Plugin):
    '''Matches any incoming event and log them to somewhere. '''

    match_type = shared.MESSAGE | shared.PRESENCE

    def __init__(self, bot):

        Plugin.__init__(self,bot)

        home = os.path.expanduser("~")
        log_file = os.path.join(home, "impybot.log")

        self.event_logger = logging.getLogger('EventLogger')

        fhandler = logging.FileHandler(
                log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s %(message)s', '%Y-%m-%d %H:%M:%S')
        fhandler.setFormatter(formatter)

        self.event_logger.addHandler(fhandler)

    def action(self, inbound, *args, **kwargs):
        if isinstance(inbound, xmpp.Message):
            self.event_logger.info('%s: MESSAGE: %s' % \
                    (inbound.getFrom().getStripped(), 
                        inbound.getBody()) )
            return None

        elif isinstance(inbound, xmpp.Presence):
            self.event_logger.info('%s: PRESENCE: %s %s %s' %\
                    (   inbound.getFrom().getStripped(),
                        inbound.getType(),
                        inbound.getShow(),
                        inbound.getStatus() ) )
            return None

        else:
            self.logger.info('Unknown type: %s' % type(inbound))
            return None

# ------ End of XmppBot.FallbackPlugin------
register(LoggerPlugin, priority = -1)
