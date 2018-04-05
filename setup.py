from setuptools import setup

long = \
'''IMPyBot (impybot) is a bot (IM automatic response) framework for XMPP
protocol. It provides a plug-in system, so that the implementation of a utility
is isolated from implementation of the bot. This provides great convenience to
manage the utilities without touching the bot itself. The plug-in system is
sophisticated that it enables developer to write really large and powerful
plug-ins. Meanwhile, it also provides a simple interface such that users with
little Python experience can write useful utilities as well.'''

setup(  name='impybot',
        version = '1.2',
        author = 'Kefei Lu',
        author_email = 'kludev@gmail.com',
        maintainer = 'Kefei Lu',
        maintainer_email = 'kludev@gmail.com',
        url = 'http://impybot.sourceforge.net/',
        description = 'An XMPP Bot and Plugin Framework in Python.',
        long_description = long,

        py_modules = ['run_bot'],
        packages = ['impybot', 'impybot.builtins'],
        scripts = ['run_bot.py'],
        package_data =  {'impybot':['LICENSE',
                                    'doc/index.html',
                                    'doc/guide.html',
                                    'doc/impybotrc.example',
                                    'store/*.py']}
        )
