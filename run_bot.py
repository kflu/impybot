#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

'''The command line interface for invoking IMPyBot.

python run_bot.py [options] [dir...]

'''

__author__ = 'Kefei Lu <klu1024@gmail.com>'
__website__ = 'http://impybot.sf.net'
__license__ = 'MIT'


from optparse import OptionParser, OptionGroup
import sys, os
import logging
logger = logging.getLogger('impybot.run_bot')

if __name__ == '__main__':
    usage = \
'''usage: %prog [options] [store] ...

[store] ... : the plugin stores where plugin modules and packages are held.'''

    parser = OptionParser(usage = usage)

    # --------- auth ----------
    auth_group= OptionGroup(parser, "Authentication and Connection Options",
            'These options specifies the authentication and connections. '
            'The JID and password MUST be used together.')

    auth_group.add_option('-j', '--jid', dest = 'jid',
            help = 'JID used by the bot to sign in. e.g., who@jb.org/resource. Resouce can be omitted.', default = '')

    auth_group.add_option('-p', '--password', dest = 'password',
            default = '',
            help = 'Password used together with the JID.')

    auth_group.add_option('--server', default = '',
            help = 'Alternative server IP to be used.')

    auth_group.add_option('--port', default = 5222,
            help = 'Alternative server port to be used.')

    parser.add_option_group(auth_group)
    # -------------------------

    # ---------- debug -----------
    debug_group = OptionGroup(parser, "Debug Options",
            "These options specifies the debug levels for IMPyBot and the underlying libraries.")
    debug_group.add_option('--debug', type = 'choice', default = 'info',
            choices = ('debug', 'info', 'warning', 'error', 'critical'),
            help = 'The debug level (debug, info, warning, error, critical)')

    debug_group.add_option('--xmpp-debug', action='store_true', dest = 'xmpp_debug', default = False,
            help = 'Enable debug info. at the XMPPPY level')
    parser.add_option_group(debug_group)
    # ----------------------------

    # --------- misc -------------
    misc_group = OptionGroup(parser, 'Misc. Options')
    misc_group.add_option('-i', '--conf', 
            help = 'Use the specified configuaration file.')

    misc_group.add_option('-m', '--plugins', action = 'append', dest = 'plugins',
            default = [],
            help = 'The path of a plugin module/package that the bot should use. This argument can be used multiple times.')
    parser.add_option_group(misc_group)
    # -----------------------------

    (opts, args) = parser.parse_args()
    # if (not (opts.jid and opts.password)) or (opts.jid or opts.password):
    if (not (opts.jid and opts.password)) and (opts.jid or opts.password):
        parser.error("If one of -j and -p is specified, the other one must also be specified.")

    conf = ''
    if opts.conf:
        conf = opts.conf

    xmpp_debug = []
    if opts.xmpp_debug:
        xmpp_debug = ['always', 'nodebuilder']

    import xmpp
    resource = ''
    if opts.jid:
        try:
            jid = xmpp.JID(opts.jid)
        except Exception, e:
            msg = '\n'.join([str(e), "-j: jid is invalid: %s" % opts.jid])
            parser.error(msg)
        resource = jid.getResource()

    if not args:args = []

    import logging
    debug_levels = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

    debug_level = debug_levels.get(opts.debug)

    logging.basicConfig(format = '%(asctime)s %(levelname)-8s %(name)-10s %(funcName)-16s %(message)s',
            datefmt = '%Y-%m-%d %H:%M:%S',
            level=debug_level, stream = sys.stderr)

    from impybot.bot import IMPyBot
    bot = IMPyBot(
            auth = (opts.jid, opts.password, opts.server, opts.port),
            proxy = None, # TODO add support for using proxy
            conf = conf,
            plugins = opts.plugins,
            plugin_stores = args,
            debug = xmpp_debug
            )
    bot.serve()

# vim:ts=4:ff=unix:
