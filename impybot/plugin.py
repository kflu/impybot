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

'''The plugin framework.

This module implements various plugin classes that bot utility developers can
based on. 

The most base class is Plugin. Derived classes are: SimplePlugin, RePlugin

'''

__author__ = 'Kefei Lu <klu1024@gmail.com>'
__website__ = 'http://impybot.sf.net'
__license__ = 'MIT'

import sys
import re
import logging
try:
    import xmpp
except ImportError:
    print >>sys.stderr, 'xmpppy was not found, which is necessary.'
    raise

import shared

logger = logging.getLogger('plugin')

def set_priority(plugin, priority = shared._PRIORITY_RANGE[1]):
    if not shared.in_priority_range(priority):
        logger.warn('Priority of plugin %s is out of priority range.' % plugin)
    plugin.priority = priority
    return

def register(pl, priority = shared._PRIORITY_RANGE[1]):
    '''Put pl into global plugin list _REGISTERED_PLUGINS.
    
    It must be called after defining a plugin class. We don't use decorator
    because of backward compatibility with older pythons.
    
    '''
    logger.debug('registering %s' % pl.__name__)
    if not issubclass(pl, Plugin):
        logger.warn('%s is not derived from Plugin, ignored.' % pl.__name__)
        return
    if pl.__name__ in [c.__name__ for c in shared._REGISTERED_PLUGINS]:
        logger.warn('%s has already been registered.' % pl.__name__)
        return

    set_priority(pl, priority)

    shared._REGISTERED_PLUGINS.append(pl)
    logger.debug('_REGISTERED_PLUGINS: %s' % [x.__name__ for x in shared._REGISTERED_PLUGINS])

# ============
# Plugin
# ============
class Plugin:
    '''A plugin that is used to match a user input or status change and
    response correspondingly.

    '''

    class Response:
        def __init__(self, reply = '', stop = False):
            '''reply: the object to reply. Either a str or a Message.
            stop: True if the plugin wants the bot to stop executing lower priority plugins'''
            self.__stop = stop
            self.set_reply(reply)

        def __nonzero__(self):
            return bool(self.get_reply())

        def has_reply(self):
            if self.__reply: return True
            return False

        def set_reply(self, reply):
            if reply == None: 
                self.__reply = ''
                return
            if isinstance(reply, (str, unicode, xmpp.Message)):
                self.__reply = reply
                return
            if isinstance(reply, Plugin.Response):
                self.__reply = reply.get_reply()
                self.__stop = reply.stop()
                return
            raise TypeError('argument must be of type str or xmpp.Message: %s' % reply)

        def get_reply(self):
            return self.__reply

        def get_text(self):
            return self.get_reply()

        def stop(self):
            return self.__stop

        def append(self, msg):
            if not isinstance(msg, (str, unicode)):
                self.logger.warn('%s is not a string.' % msg)
                return
            self.__reply = self.__reply + msg
            return self

        def append_line(self, msg):
            self.append('\n')
            self.append(msg)
            self.__reply.strip(u'\n')
            return self

    # ===================================================
    # Plugin information and tunable options and defaults.
    # ===================================================
    author    = ''
    name      = ''   # plugin name
    desc      = ''   # plugin description
    priority  = shared.get_default_priority()

    # matchtype specify how (command or regular expression) and
    # what (user inputs or/and presence change) to match.  By
    # default it is only message match and using command stype
    # match.
    #
    # For MESSAGE only match type, match_presence_pattern will be
    # ignored, for PRESENCE only match, match_pattern will be
    # ignored.
    match_type = shared.MESSAGE

    # For REGEXP, it's a tuple of regexp strings. For COMMAND
    # (non-REGEXP), it's a tuple of command strings appear at the
    # beginning of user inputs.
    match_pattern = ()

    # Specify the presence change pattern you want to match.
    # example:
    # (
    #   ( OFFLINE | DND, AVAILABLE ),
    #   ( ANY, AVAILABLE )
    # )
    match_presence_pattern = None

    # No more match for lower priority plugins. Default to false
    stop_matching = False

    # No more match for these plugins, specify plugins by their names
    # TODO NOT IMPLEMENTED IN BOT FRAMEWORK YET.
    no_more_match_on= ()
    # ===================================================

    def __str__(self):
        return self.__class__.__name__

    def __cmp__(self, other):
        ''' Compare by the sense of priority.'''
        return cmp(self.priority, other.priority)

    def __init__(self, bot, *args, **kwargs):
        '''Constructor of Plugin. It should only be called by a bot.

        bot - an instance of XmppBot. Passed by the bot itself.
        
        '''
        self.logger = logging.getLogger(self.__class__.__name__)

        # TODO compile regex pattern
        self.__bot = bot

    def is_message(self, obj):
        return shared.is_message(obj)

    def is_presence(self, obj):
        return shared.is_presence(obj)

    def get_bot(self):
        return self.__bot

    def action( self, matched, *args, **kwargs ):
        '''The callback method is pattern is matched.

        matched is the object that matches one of the plugin patterns. For a
        plugin that matches both presence change and user inputs, the type of
        match can be told by the type of matched - xmpp.Message or
        xmpp.Presence.

        For user inputs match, the 3rd argument is the pattern that matches.
        If the plugin uses REGEXP style match, it is a compile regular
        expression object.  If the plugin uses COMMAND style match, it is the
        LINE that matches.
        
        For presence change match, the 3rd argument is the old presence object
        before the presence change.
        '''
        return self.Response()

# ================ End of class Plugin ====================

class SimplePlugin(Plugin):
    '''The simplest plugin.

    This plugin matches user inputs of the form: "some_command some arguments".
    Input of multiple lines are supported.
    
    Don't forget to use impybot.register() to register the plugin class after
    defining it.

    Usage
    -----

    Set attribute 'command' as the command string or a tuple of command strings
    you want to catch. Define a method "handle_match". This method is called
    each time the user input contains the command string at the beginning of
    each line.
    
    handle_match() MUST have the following interface:

      def handle_match( self, matched, sender )

    matched: 
        the matched parts of user input (not including command itself)
        this is a tuple of all matches.

    sender: 
        a (unicode) string specifying the sender's JID

    The return value of handle_match() can be a string which will be sent back
    to the sender. If nothing needs to be sent, just return or return None.

    An example:
        if the command is set to ('hello', 'hey'), the user input is as follows:

          hello world line 1(End of line)
          hey world line 2(End of line)
          hello(End of line)
        
        The 'matched' argument passed to handle_match() is a list:
          
          [ 'world line 1', 'world line 2', '' ]

        This means even a simple "hello" will match, but the argument "matched"
        will be an empty string. This could be a useful feature in some cases.

        Also note that if there is only one match, the argument "matched" is
        still a tuple.
            
    '''

    command = ''    # use ('cmd1', 'cmd2') to make aliases

    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        self.__pattern = None
        if not self.command: 
            raise KeyError('A command must be specified for SimplePlugin')
        try:
            if isinstance(self.command, (str, unicode)):
                tmp = '(' + self.command + ')'
            else:
                tmp = '(' + '|'.join(self.command) + ')'

            pattern = ur'^%s(\s+(?P<arg>..*))?\s*$' % tmp
            self.logger.debug('re pattern: %s' % pattern)
            self.__pattern = re.compile(pattern, re.UNICODE)
            # self.__pattern = re.compile(r'^%s\s+(?P<matched>.*)\s*$' % self.command, re.MULTILINE)
        except Exception, e:
            self.logger.warn('Error whiling compiling command as a regular expression: %s' % self.command)
            self.logger.exception(e)
            self.__pattern = None

    def handle_match(self, matched, sender):
        '''handle_match(self, matched, sender) -> str|unicode

        handle_match() is called when command is at the beginning of a user
        input.
        '''
        return

    def action(self, obj, *args, **kwargs):
        self.__message = obj 
        if not self.is_message(obj): return
        if not self.__pattern: return
        body = obj.getBody()
        if not body: return

        found = []
        for line in body.splitlines():
            m = self.__pattern.findall(line)
            if not m: continue
            # if not use findall(), match object indicates no match as None
            # rather than ''. We can't pass None to users.
            found.append(m[0][2].strip())

        if not found: return
        response = self.handle_match( tuple(found), obj.getFrom().getStripped() )
        return self.Response(response)
# ============= class SimplePlugin =================

class RePlugin(Plugin):
    '''Plugin that matches on regular expression patterns.

    Class attributes that should be specified:
        pattern: the regular expression pattern to be used

        flags (optional): flags used when compiling regular expression
            if not specified, use re.MULTILINE as default.

        handle_match( self, matched, sender ):
            matched is a iterator of matched objects returned by re.finditer()
            sender is the bare JID string of the sender
        
    The returned value (MUST be a string/unicode) will be sent back to the
    sender as the replied message.

    '''

    pattern = ''
    flags = None
    def __init__( self, *args, **kwargs ):
        Plugin.__init__(self, *args, **kwargs)
        self.__pattern = None
        try:
            if self.flags:
                self.__pattern = re.compile(self.pattern, self.flags)
            else:
                self.__pattern = re.compile(self.pattern, re.UNICODE|re.MULTILINE)
        except Exception, e:
            self.logger.warn('Error whiling compiling the regular expression pattern: %s' % self.pattern)
            self.exception(e)
            self.__pattern = None

    def handle_match(self, matched, sender):
        return

    def action(self, obj, *args, **kwargs):
        if not self.is_message(obj): return
        if not self.__pattern: return
        body = obj.getBody()
        found = self.__pattern.finditer(body)
        # iterator will never be avaluated to none
        # if not found: return
        response = self.handle_match( found, obj.getFrom().getStripped() )
        return self.Response(response)
# ================= class RePlugin ==========================
