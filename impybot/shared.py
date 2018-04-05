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

'''The shared things that is required by one or more other modules.'''

__author__ = 'Kefei Lu <klu1024@gmail.com>'
__website__ = 'http://impybot.sf.net'
__license__ = 'MIT'

import sys, os
import imp
import logging
try:
    import xmpp
except ImportError:
    print >>sys.stderr, 'xmpppy was not found, which is necessary.'
    raise

# Module level logger
logger = logging.getLogger('shared')

# =============
# Global Variables
# =============

DEFAULT_PORT = 5222

# match type bit flags
IS_REGEXP = 1 # match type is regular expression, or match type is command
MESSAGE = 2
PRESENCE = 4

# presence show
OFFLINE = 1
AVAILABLE = 2
AWAY = 4
DND = 8
XA = 16
CHAT = 32
ANY = sys.maxint

# XmppBot __halt_reason flags:
KEYBOARD_INTERRUPT = 1
RESTART = 2
EXIT = 4
# more...

# _PRIORITY_RANGE = ( highest_priority, default_priority, lowest_priority )
_PRIORITY_RANGE = ( 0, 10, 20 )

# register() will append plugin classes into this list.
_REGISTERED_PLUGINS = []
# ========= End of Global Var. =============

# ========================================================================
#                               Global Utilities
# ========================================================================

def get_default_priority():
    '''Returns the default priority in _PRIORITY_RANGE.'''
    return _PRIORITY_RANGE[1]

def in_priority_range(p):
    '''Check if the input object is within priority range.

    Input can be a integer indicating a priority.
    '''
    if isinstance(p, int):
        priority = p
    else:
        raise TypeError('Type invalid: %s' % p)
    if priority >= _PRIORITY_RANGE[0] and priority <= _PRIORITY_RANGE[2]:
        return True
    return False

def xor(a, b):
    return (not (a and b)) and (a or b)

def is_message(obj):
    return isinstance(obj, xmpp.Message)

def is_presence(obj):
    return isinstance(obj, xmpp.Presence)

def prsc(status, type_):
    '''Translate the presence status between XMPP standard and IMPyBot internal
    presentation (bit flags)
    
    if type_ is 'std', the return value will always be XMPP standard type.
    if type_ is 'bit', the return value will always be IMPyBot bit flag type.
    
    '''

    m = (
            [OFFLINE, AVAILABLE, AWAY, DND, XA, CHAT],
            ['unavailable', None, 'away', 'dnd', 'xa', 'chat']
        )

    def to_int(status):
        '''Translate XMPP standard => Bit flag'''
        try:
            i = m[1].index(status)
        except ValueError, e:
            raise ValueError('%s is not a supported status.' % status)
        return m[0][i]

    def to_str(status):
        '''Translate Bit flag => XMPP standard'''
        try:
            i = m[0].index(status)
        except ValueError, e:
            raise ValueError('%s is not a supported status. Use one of %s.'% (status,tuple(ANY)))
        return m[1][i]

    if isinstance(status, (str, unicode, type(None))):
        if type_ == 'std': return status
        return to_int(status)
    if isinstance(status, int):
        if type_ == 'bit': return status
        return to_str(status)

    # status is neither XMPP standard nor bit field.
    raise ValueError('Type %s is not recognized as neither XMPP standard status nor bit flag.' % type(status))

def get_module_name(p):
    '''Get the module or package name by its path.
    
    Example: 
    Module: /home/user/Mike/example.py -> example
    Package: /home/user/Mike/pkg/ -> pkg
    '''
    mod_name = ""
    if not os.path.exists(p):
        return None
    if os.path.isfile(p): 
        # a module
        base = os.path.basename(p)
        (root, ext) = os.path.splitext(base)
        # splitext bug < py2.6: root can be '' if base begins with a dot.
        if not root:
            mod_name = ext
        else:
            mod_name = root
    elif os.path.isdir(p):
        # a package
        if os.name in ('nt', 'dos'):
            sep = '\\'
        else:
            sep = '/'
        mod_name = p.strip(sep).split(sep)[-1]
    else:
        # shouldn't reach here.
        raise Exception("get_module_name: You shouldn't reach here.")
    if not mod_name:
        raise Exception("get_module_name: mod_name cannot be empty (%s)" % p)
    return mod_name

def get_ext(p):
    '''Get the extension of path p.'''
    if not os.path.exists(p):
        logger.warn('path not exists: %s' % p)
        return None
    if not os.path.isfile(p):
        logger.warn('path is a directory: %s' % p)
        return None
    (root, ext) = os.path.splitext(p)
    if not root: # e.g., ".vimrc" for older python
        return ""
    return ext

def import_by_path(p, ext_chk = True):
    '''Find and load a module or package by its path
    
    p -- the module/package path
    ext_chk -- If true, check if the extension is .py,
                if not, skip it.
    return: the module object or None on failure
    '''
    if not os.path.isabs(p):
        logger.warn('import_by_path: path is not absolute path, converting... %s' % p)
        p = os.path.abspath(p)
    if not os.path.exists(p):
        logger.warn('import_by_path: path does not exist: %s' % p)
        return None

    mod_name = get_module_name(p)
    if sys.modules.has_key(mod_name):
        # already imported
        logger.warn('%s already imported.' % mod_name)
        return sys.modules[mod_name]

    # We don't allow import of __init__, if it's a package, don't treat it as a store.
    if mod_name == '__init__':
        logger.warn('__init__ is not allowed to be imported.')
        return None

    mod_path = p
    if os.path.isfile(p):
        if ext_chk and get_ext(p) not in ('.py', '.pyc', '.pyo'):
            logger.warn('file extension name is invalid: %s' % p)
            return None
        mod_path = os.path.dirname(p)

    found = imp.find_module(mod_name, [mod_path])
    try:
        mod = imp.load_module(mod_name, *found)
    except Exception, e:
        mod = None
        logger.warn('import_by_path: cannot load module %s at %s (%s)' % (mod_name, p, repr(e)))
        logger.exception(e)
    finally:
        found[0].close()
    if mod: return mod
    return None

def get_show(presence):
    '''Extract the show infomation from an xmpp.Presence object.

    if presence type is unavailable, return OFFLINE.
    '''
    if not isinstance(presence, xmpp.Presence):
        raise ValueError('Input is not of type xmpp.Presence: %s' % type(presence))
    type_ = presence.getType() 
    if type_ not in ('unavailable', None):
        raise ValueError('This presence is not for presence change purpose.')
    if type_ == 'unavailable': return OFFLINE
    if type_ == 'None': return AVAILABLE
    return prsc( presence.getShow(), 'bit' )
    
def get_sys_conf_path():
    if os.name in ('nt', 'dos'):
        return ''
    return '/etc/impybotrc'

def get_usr_conf_path():
    home_path = os.path.expanduser('~')
    if os.name in ('nt', 'dos'):
        conf = 'impybot.ini'
    else:
        conf = '.impybotrc'
    return os.path.join(home_path, conf)

def determine_conf_path():
    '''Locate IMPyBot configuration file. (cross-platform)

    Windows: impybot.ini, Other: .impybotrc
    User level conf is tried first. Then try system level conf.
    If not found, IOError is thrown.

    '''
    home_path = os.path.expanduser('~')
    if os.name in ('nt', 'dos'):
        conf = 'impybot.ini'
    else:
        conf = '.impybotrc'

    # first try to find and use user-level conf
    user_level_conf = os.path.join(home_path, conf)
    if os.path.exists(user_level_conf):
        return user_level_conf
    else:   # find and use system-level conf
        logger.warn('Unable to find user-level conf. Trying system-level conf...')
        system_level_conf = ''
        if os.name in ('nt', 'dos'):
            # TODO use system-level conf for Windows
            raise IOError('Finding system level conf is not supported for Windows yet.')
        else:
            system_level_conf = os.path.join('/etc', conf[1:])  # strip the leading dot
        if not os.path.exists(system_level_conf):
            raise IOError('System level conf cannot be found: %s' % system_level_conf)
        return system_level_conf

def parse_configuration(conf):
    '''parse_configuration(conf) -> dict
    
    Parse the configuration file conf. Return a dict that its keys are
    the nodes of the xml conf file.
    '''

    try:
        from xml.dom import minidom
        conf = minidom.parse(conf)
    except Exception, e:
        logger.error("Error in opening and validating configuration file: %s" % conf)
        raise e
    params = {
            'auth':{'jid':'', 'password':'', 'server':'', 'port': DEFAULT_PORT},
            'proxy':{'host':'', 'port':0, 'user':'', 'password':''},
            'plugins':(),
            'plugin_stores':(),
            }
    try:
        jid = conf.getElementsByTagName('auth')[0].getAttribute('jid')
        password = conf.getElementsByTagName('auth')[0].getAttribute('password')
        server = conf.getElementsByTagName('auth')[0].getAttribute('server')
        port = conf.getElementsByTagName('auth')[0].getAttribute('port')
    except Exception, e:
        logger.warn('Error while parsing for parameters')
        logger.exception(e)
        jid = ''
        password = ''
        server = ''
        port = DEFAULT_PORT

    if not port:
        port = DEFAULT_PORT
    else:
        port = int(port)

    try:
        proxy_host = conf.getElementsByTagName('proxy')[0].getAttribute('host')
        proxy_port = conf.getElementsByTagName('proxy')[0].getAttribute('port')
        proxy_user = conf.getElementsByTagName('proxy')[0].getAttribute('user')
        proxy_password = conf.getElementsByTagName('proxy')[0].getAttribute('password')
    except Exception, e:
        logger.warn('Error while parsing for parameters')
        logger.exception(e)
        proxy_host = ''
        proxy_port = 0
        proxy_user = ''
        proxy_password = ''

    if not proxy_port:
        proxy_port = 0
    else:
        proxy_port = int( proxy_port )

    try:
        plugins = conf.getElementsByTagName('plugin')
    except Exception, e:
        logger.warn('Error while parsing for parameters')
        logger.exception(e)
        plugins = ()

    for i, p in enumerate(plugins[:]):
        plugins[i] = p.data
    plugins = plugins or ()

    try:
        plugin_stores = conf.getElementsByTagName('plugin_store')
    except Exception, e:
        logger.warn('Error while parsing for parameters')
        logger.exception(e)
        plugin_stores = ()

    for i, p in enumerate(plugin_stores[:]):
        plugin_stores[i] = p.data
    plugin_stores = plugin_stores or ()
    
    params['auth']['jid'] = jid or ''
    params['auth']['password'] = password or ''
    params['auth']['server'] = server or ''
    params['auth']['port'] = port or DEFAULT_PORT
    if not params['auth']['jid'] or not params['auth']['password']:
        params['auth'] = None

    params['proxy']['host'] = proxy_host or ''
    params['proxy']['port'] = proxy_port or 0
    params['proxy']['user'] = proxy_user or ''
    params['proxy']['password'] = proxy_password or ''

    if not params['proxy']['user'] or not params['proxy']['password']:
        del params['proxy']['user']
        del params['proxy']['password']

    if not params['proxy']['host'] or not params['proxy']['port']:
        params['proxy'] = None

    params['plugins'] = plugins
    params['plugin_stores'] = plugin_stores
    logger.debug('params: %s' % params)
    return params

# ================== END OF Global Utilities ==============================
