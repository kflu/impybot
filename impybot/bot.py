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

'''The bot framework.

This module implements the core bot funcationalities.

'''

__author__ = 'Kefei Lu <klu1024@gmail.com>'
__website__ = 'http://impybot.sf.net'
__license__ = 'MIT'

import sys, os
import datetime
import logging
try:
    import xmpp
except ImportError:
    print >>sys.stderr, 'xmpppy was not found, which is necessary.'
    raise

from plugin import Plugin
import shared

logger = logging.getLogger('bot')

# ================== Begin Declaration of classes ========================
class Contact:

    def __init__(self, jid):
        self.logger = logging.getLogger(self.__class__.__name__)
        if isinstance(jid, (str, unicode)):
            self.jid = xmpp.JID(jid)
        elif isinstance(jid, xmpp.JID):
            self.jid = jid
        else:
            raise ValueError('Invalid JID type %s' % jid)
        # TODO presence[-1] is the current one, presence[-2,...,0] is the older one.
        self.show = [ shared.OFFLINE, shared.OFFLINE ]
        self.timestamp = None

    def __repr__(self):
        return repr(self.jid)

    def __str__(self):
        return str(self.jid)

    def __eq__(self, other):
        if not isinstance( other, (str, Contact) ):
            return False
        if str(other) == self.jid:
            return True
        return False

    def show_changed(self, presence_or_show):
        '''Determine if the most recent show is different from the one from the argument.
        
        The argument can be an xmpp.Presence object, a presence bit, or a show string.
        '''
        if isinstance(presence_or_show, xmpp.Presence):
            show = shared.get_show(presence_or_show)
        elif isinstance(presence_or_show, (int, str, unicode, type(None))):
            show = shared.prsc(presence_or_show, 'bit')
        return not show & self.show[-1]

    def update_presence(self, presence):
        ''' If the show value is changed. We log it, otherwise ignore it.
        
        None return value indicates no change.
        '''
        self.logger.debug('updating presence for %s: %s' % (self.jid, shared.get_show(presence)))
        show = shared.get_show( presence )
        if not self.show_changed(show): return None
        self.timestamp = datetime.datetime.now()
        self.show[0] = self.show[1]
        self.show[1] = show
        return show
# ============= class Contact =================

class Contacts:
    '''An extended class of xmpp.Roster. It keeps track of user presence change.'''
    def __init__(self, rost):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.roster = rost
        self.__contacts = []
        jids = self.roster.getItems()
        if jids:
            for jid in jids:
                self.__contacts.append(Contact(jid))

    def __find(self, key):
        '''Find index in __contacts for key'''
        if isinstance(key, xmpp.JID):
            for i, c in enumerate(self.__contacts):
                if c.jid.bareMatch(key):
                    return i
            raise KeyError('%s is not a valid key' % key)

        if isinstance(key, str):
            for i, c in enumerate(self.__contacts):
                if c.jid.bareMatch(xmpp.JID(key)): 
                    return i
            raise KeyError('%s is not a valid key' % key)

        raise KeyError('%s is not a valid key' % key)

    def __getitem__(self, key):
        '''contacts['jid'] or contacts[jid].'''
        return self.__contacts[ self.__find(key) ]

    def __setitem__(self, key, value):
        '''contacts['jid'] = value, or contains[jid] = vlaue'''
        self.__contacts[ self.__find(key) ] = value
        return

    def __repr__(self):
        return repr(self.roster)

    def __str__(self):
        return str(self.roster)

    def update(self):
        '''Update __contacts according to new roster list'''
        self.logger.debug('updating contact list...')
        all = self.roster.getItems()
        # remove deleted items from __contacts
        for i,c in enumerate(self.__contacts):
            if str(c) not in self.all:
                self.logger.debug('%s not in __contacts' % c)
                del self.__contacts[i]
        # add newly created items to __contacts
        for i,c in enumerate(all):
            if c not in self.__contacts:
                self.logger.debug('adding %s to __contacts.' % c)
                self.__contacts.append(Contact(c))
        self.logger.debug('..done.')
# ============= class Contacts =====================

# =======
# XmppBot
# =======
class XmppBot():
    '''A basic XMPP bot.

    An instance from this class can log in using a JID and password, can search
    for plugins and register them to act on user inputs or user status changes.

    It is able to log users' inputs and presence changes. It is able to handle
    and manage its roster. It is robust to unpredicted connection loss.

    '''
    def get_jid( self, bare = False ):
        if bare: return self.__jid.getStripped()
        return self.__jid

    def set_jid( self, jid ):
        self.__jid = xmpp.JID(jid)

    def set_password(self, password):
        if not password:
            raise ValueError('password is empty.')
        self.__password = password

    def get_password(self):
        return self.__password

    def get_server(self):
        return self.__server

    def __init__( self, jid, password,
            server = '', port = shared.DEFAULT_PORT,
            proxy = None,
            plugins = (), plugin_stores = (),
            debug = []):
        '''
        plugins - list of disk locations of individual plugin packages and modules.
        plugin_stores - list of directories that contains plugin packages and modules.
        '''
        
        self.logger = logging.getLogger(self.__class__.__name__)

        self.set_jid(jid)
        self.__server = server

        if not self.__server:
            self.__server = self.get_jid().getDomain()

        if not proxy:
            self.__proxy = proxy

        self.__port = port
        self.set_password(password)
        self.__debug = debug

        self.__halt_reason = 0  # indicates why bot should halt.

        if not self.get_jid().getResource():
            self.get_jid().setResource(self.__class__.__name__)
        self.conn = None

        self.contacts = None

        self.__show = shared.OFFLINE
        self.__status = ''

        self.__fallback_plugin = None

        # During a loop of plugin execution, indicates if some plugin has had a
        # match on the input.  Used by the default plugin to determine action
        # on a input.
        self.__matched = False

        self.__msg_plugins = []
        self.__prsc_plugins = []

        # import and instantiate builtin plugins
        shared._REGISTERED_PLUGINS = []
        dir = os.path.dirname(__file__)
        self.__import_from_store(os.path.join(dir, 'builtins'))
        self.register_plugins(priority_check = False)

        # import and instantiate the plugins from __plugins and __plugin_stores
        self.__plugins = list(plugins)
        self.__plugin_stores = list(plugin_stores)

        shared._REGISTERED_PLUGINS = []
        for p in self.__plugins:
            shared.import_by_path(p)

        for store in self.__plugin_stores:
            self.__import_from_store(store)
        
        self.register_plugins(priority_check = True)
        # ---- done importing and instantiating ----


    def __call_action(self, plugin, *args, **kwargs):
        '''Call plugin's action. and pass the args.'''
        try:
            response = plugin.action(*args, **kwargs)
        except Exception, e:
            response = None
            self.logger.warn('__call_action: Error while calling plugin %s action: %s' % (plugin.__class__.__name__, e))
            self.logger.exception(e)

        return response

    def __handle_halt_reason(self):
        self.logger.info('Halt reason: %s' % self.__halt_reason)

    def set_matched(self):
        self.__matched = True
        return

    def unset_matched(self):
        self.__matched = False
        return

    def get_matched(self):
        return self.__matched

    def __instantiate_plugin(self, pclass, priority_check = True):
        '''Instantiate a plugin object and check its priority.
        
        pclass -- a plugin class
        priority_check -- If true, check pclass is in range

        returns the plugin object or None on failure
        '''
        if not issubclass(pclass, Plugin):
            raise TypeError('pclass is not a plugin class: %s' % pclass)
        self.logger.info('Instantiating plugin %s' % pclass.__name__)
        try:
            obj = pclass(self)
        except Exception, e:
            self.logger.error('Error while instantiating %s' % pclass.__name__)
            self.logger.exception(e)
            return None

        if priority_check and not shared.in_priority_range(obj.priority):
            set_priority(obj)

        return obj

    def register_plugins(self, priority_check = True):
        '''Register plugin classes listed in _REGISTERED_PLUGINS to the bot.'''

        self.logger.debug('_REGISTERED_PLUGINS: %s' % shared._REGISTERED_PLUGINS)

        for p in shared._REGISTERED_PLUGINS:
            inst = self.__instantiate_plugin(p, priority_check)

            if not hasattr(inst, 'match_type'):
                self.logger.debug('This plugin is not properly instantiated.')
                continue

            if inst.match_type & shared.MESSAGE:
                self.__msg_plugins.append(inst)

            if inst.match_type & shared.PRESENCE:
                self.__prsc_plugins.append(inst)

        # sort the two lists
        self.logger.debug('sorting plugin list...')
        self.__msg_plugins = sorted(self.__msg_plugins)
        self.__prsc_plugins = sorted(self.__prsc_plugins)
        self.logger.debug('__msg_plugins: %s' % \
                [ p.__class__.__name__ for p in self.__msg_plugins ])
        self.logger.debug('__prsc_plugins: %s' % \
                [ p.__class__.__name__ for p in self.__prsc_plugins ])

    def __import_from_store(self, store):
        '''Import plugin modules/packages from the store directory.
        
        store: the store directory
        return: None
        '''
        self.logger.debug('store: %s' % store)
        store = os.path.abspath(store)
        if not os.path.exists(store): 
            self.logger.warn('%s does not exists' % store)
            return
        if not os.path.isdir(store): 
            self.logger.warn('%s is not a directory' % store)
            return
        # search through plg_dir and find all packages and modules to import
        ldir = os.listdir(store)
        self.logger.debug('in %s:' % store)
        for o in ldir:
            o = os.path.join(store, o)
            self.logger.debug('importing %s' % o)
            shared.import_by_path(o)

    def handle_message(self, conn, msg):
        type = msg.getType()
        jid = msg.getFrom()
        props = msg.getProperties()
        body = msg.getBody()
        self.logger.debug('handling incoming message: %s' % str((type, jid, body)))

        # we don't handle msg sent before bot logs in
        if xmpp.NS_DELAY in props: return

        # TODO ignore myself's msg?

        # body can be None if the format is not supported
        if not body: return

        # match body against each plugin
        self.unset_matched()    # reset the matched flag
        for p in self.__msg_plugins:
            self.logger.debug('calling plugin: %s' % p.__class__.__name__)

            response = self.__call_action(p, msg)
            if not response:
                continue
            self.set_matched()
            if isinstance(response, (str, unicode)):
                # simple text reply to send
                self.send_text(jid, response)
            elif isinstance( response, Plugin.Response ):
                if response.has_reply():
                    self.send_text(jid, response.get_text())
                if response.stop():
                    break

    def handle_presence(self, conn, presence):
        '''Call each registered presence plugin to handle events.'''
        for p in self.__prsc_plugins:
            response = self.__call_action( p, presence, )
            if not response:
                continue
            if isinstance(response, str):
                # simple text reply to send
                self.send_text(jid, response)
            elif isinstance( response, Plugin.Response ):
                if response.has_reply():
                    self.send_text(jid, response.get_text())
                if response.stop():
                    break

        return

    def get_show(self):
        return self.__show

    def set_show(self, show):
        # TODO check first
        if self.__show == show: return
        self.__show = show
        self.send_status()

    def get_status(self):
        return self.__status

    def set_status(self, status):
        # TODO check first
        if self.__status ==  status: return
        self.__status = status
        self.send_status()

    def send_status(self):
        self.conn.send(xmpp.protocol.Presence(
            show= shared.prsc(self.__show, 'str'), 
            status = self.__status))

    def send_text(self, to, text):
        '''Send a text message to jid string 'to'.'''
        self.logger.debug('sending text: %s' % str((to, text)))
        self.conn.send(xmpp.protocol.Message(to, text, 'chat'))

    def connect( self ):
        '''Connect to the server, authenticate user, register callbacks.'''
        if not self.conn:
            cl = xmpp.Client( self.get_server(), self.__port, debug = self.__debug)
            self.logger.debug('connecting to server...')
            conn_type = cl.connect((self.__server, self.__port), self.__proxy )
            if not conn_type:
                raise IOError('Cannot connect to the domain: %s' % self.get_server())
            if conn_type != 'tls':
                self.logger.warn('TLS connection is not established.')
            self.logger.debug('done.')

            auth = cl.auth(self.get_jid().getNode(), self.get_password(), self.get_jid().getResource())
            if not auth:
                raise IOError('Cannot authorize the user: %s' % self.get_jid())
            if auth != 'sasl':
                self.logger.warn('Cannot perform SASL type authentication.')

            cl.RegisterHandler('message', self.handle_message)
            cl.RegisterHandler('presence', self.handle_presence)
            self.logger.debug('sending init. presence...')
            cl.sendInitPresence()
            self.conn = cl
            self.logger.debug('getting roster...')
            rost = self.conn.getRoster()
            for r in rost.getItems():
                self.logger.debug('..%s' % r)
            self.contacts = Contacts(rost)

            self.set_show(shared.AVAILABLE)

        return self.conn

    def serve(self, on_connect = None, on_disconnect = None):
        conn = self.connect()
        if not conn:
            raise IOError('Unable to connect to the server.')

        self.logger.info('Serving...')
        
        if on_connect:
            on_connect()

        while not self.__halt_reason:
            try:
                conn.Process(1)
            except KeyboardInterrupt:
                self.logger.info('Bot halted by keyboard interrupt. Exiting...')
                self.__halt_reason = shared.KEYBOARD_INTERRUPT

        self.__handle_halt_reason()

        if on_disconnect:
            on_disconnect()

# ============= END OF class XmppBot =====================================

class IMPyBot(XmppBot):
    '''A wrapper of XmppBot with a better user interface.
    
    The priority of the parameters specified:
        __init__ argument > conf file in __init__ args > user-level conf > system-level conf.
    
    '''
    def __init__(self, 
            auth = (),
            proxy = None,
            plugins = (), plugin_stores = (),
            conf = '', # configuration file to be used
            debug = [],
            ):
        '''auth should be ( jid, password, server, ip )'''

        _auth = None
        _proxy = None
        _plugins = list(plugins)
        _plugin_stores = list(plugin_stores)

        sys_params = {}
        sys_conf = shared.get_sys_conf_path()
        if os.path.exists(sys_conf):
            sys_params = shared.parse_configuration(sys_conf)
            _plugins.extend(sys_params['plugins'])
            _plugin_stores.extend(sys_params['plugin_stores'])
            _auth = sys_params['auth']
            _proxy = sys_params['proxy']

        usr_params = {}
        usr_conf = shared.get_usr_conf_path()
        if os.path.exists(usr_conf):
            usr_params = shared.parse_configuration(usr_conf)
            _plugins.extend(usr_params['plugins'])
            _plugin_stores.extend(usr_params['plugin_stores'])

            if usr_params['auth']:
                _auth = usr_params['auth']
            if usr_params['proxy']:
                _auth = usr_params['proxy']

        if conf:
            params = shared.parse_configuration(conf)
            _plugins.extend(params['plugins'])
            _plugin_stores.extend(params['plugin_stores'])

            if params['auth']:
                _auth = params['auth']
            if params['proxy']:
                _auth = params['proxy']

        if _auth:
            _auth = (_auth['jid'], _auth['password'], _auth['server'], _auth['port'])

        if auth:
            if auth[0] and auth[1]:
                _auth = auth

        if proxy:
            if proxy[0] and proxy[1]:
                _proxy = proxy

        if not _auth:
            raise ValueError('No authentication data was found. Bot cannot be initialized.')

        # TODO we should also provide settings to disable/enable loading "official" plugins from this store.
        dir = os.path.dirname(__file__)
        _plugin_stores.append(os.path.join(dir, "store"))

        # call base class init
        XmppBot.__init__( self,
                _auth[0], _auth[1],
                _auth[2], _auth[3],
                _proxy,
                _plugins, _plugin_stores,
                debug )

# =========== class IMPyBot =================

# vim:ts=4:ff=unix:
