# -*- coding: utf-8 -*-

# IMPyBot: A Python XMPP Bot framework.
# Copyright (c) 2009 Kefei Lu <klu1024@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

'''The builtin presence manager for the bot.'''

import sys
import xmpp
from impybot.plugin import Plugin, register
from impybot import shared

class PresenceMan(Plugin):
    author = 'Kefei Lu'

    match_type = shared.PRESENCE

    def action(self, inbound, *args, **kwargs):
        if not isinstance(inbound, xmpp.Presence):
            return None

        presence = inbound
        from_= presence.getFrom()
        type_ = presence.getType()
        show = presence.getShow()
        status = presence.getStatus()

        bot = self.get_bot()

        if bot.get_jid().bareMatch(from_):
            # TODO should be also handle myself's subscription?
            return

        try:
            subscription = bot.contacts.roster.getSubscription(unicode(from_))
        except KeyError, e:
            # jid is not in roster
            subscription = 'none'

        self.logger.debug('presence event: from:%s type:%s show:%s subs.:%s' % \
                ( from_, type_, show, subscription ))

        if subscription not in ('both', 'to', 'from', 'none', None):
            raise ValueError('Invalid subscription value: %s' % subscription)

        if type_ == 'subscribe':
            if subscription == ('both', 'from'):
                self.logger.warn('contact %s has already subscribed to me. (subscription: %s)' % \
                        (from_, subscription))
                return None
            elif subscription == 'to':
                # authorize the contact
                bot.contacts.roster.Authorize(from_)
                bot.send_status()
                return None
            else: # ('none', None):
                # Try to subscribe to the user first
                bot.contacts.roster.Subscribe(from_)
                return None

        elif type_ == 'unsubscribe':
            # RFC3921 9.3 tab 4: contact cancells his subscription to me
            self.logger.info('%s has unsubscribed from me.' % from_)
            self.logger.info('Unauthorizing & unscribing from %s' % from_)
            bot.contacts.roster.Unauthorize(from_)
            bot.contacts.roster.Unsubscribe(from_)
            return None

        elif type_ == 'subscribed': # i've been authorized by jid
            # RFC3921 9.3 tab 5: subscription to the contact. But subscription
            # from the contact is not garanteed. If contact does not send a
            # subscribe, there is not point of authorize him
            self.logger.info('%s has authorized my subscription request.'%from_)
            return None

        elif type_ == 'unsubscribed':
            # RFC3921 9.3 tab 6: contact unauthorized me to subscribe to him
            # I should do the same.
            self.logger.info('%s has unauthorized my subscription.' % from_)
            self.logger.info('Unauthorizing %s' % from_)
            bot.contacts.roster.Unauthorize(from_)
            return None

        elif type_ == 'error':
            self.logger.warn('%s: subscription type is "error": %s' % (from_, presence))
            return None

        elif type_ in (None, 'unavailable'):
            try:    # log contact's presence change
                bot.contacts[from_].update_presence(presence)
            except KeyError,e:
                # from_ is not in contacts.
                self.logger.warn('%s is not in contacts, presence: %s' % (from_, (show, status)))
                bot.contacts.update()
                bot.contacts[from_].update_presence(presence)
                return None

        else:
            self.logger.warn('Invalid subscription type: %s %s' % (from_, type_))
            return None

        return None
# ------ class PresenceMan ---------

register(PresenceMan, priority = -sys.maxint -1) # highest pri.
