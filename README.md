IMPyBot: An XMPP Bot and Plug-in Framework in Python
==============================================================

- 01/26/2010: created
- 04/04/2018: migrated from [the old sourceforge repository](http://impybot.sourceforge.net/)


Introduction
--------------------------------------------------------

IMPyBot (impybot) is a bot (IM automatic response) framework for XMPP protocol. It provides a
plug-in system, so that the implementation of a utility is isolated from implementation of the bot.
This provides great convenience to manage the utilities without touching the bot itself. The plug-in
system is sophisticated that it enables developer to write really large and powerful plug-ins.
Meanwhile, it also provides a simple interface such that users with little Python experience can
write useful utilities as well.

The figure below illustrates the structure of IMPyBot framework. As shown, the plug-ins are isolated
from the bot itself. Plugin developers who are only interested in writing utilities like weather
querier or calculators does not need to know the details of the bot at all. What is more important,
this provides an easier way to organize and manage all the plugins.

     +------------------------------------------------------------+
     |                                                            |
     |                     The Plug-ins                           |
     |       +--------------------------------------------+       |
     |       |  +---------+ +------------+ +------------+ |       |
     |       |  | weather | | dictionary | | calculator | |       |
     |       |  +---------+ +------------+ +------------+ |       |
     |       +--------------------------------------------+       |
     |                            |                               |
     |                            | plug in                       |
     |                            v                               |
     |       +--------------------------------------------+       |
     |       |         The XMPP Bot Framework             |       |
     |       +--------------------------------------------+       |
     |                           | ^                              |
     |                           | |                              |
     |                           v |                              |
     |       +--------------------------------------------+       |
     |       |                 Internet                   |       |
     |       +--------------------------------------------+       |
     |                                                            |
     |                                                            |
     +------------------------------------------------------------+

            Figure 1. Illustration of the IMPyBot Framework


Installation
--------------------------------------------------------

1.  Download the package from https://sourceforge.net/projects/impybot
2.  Unzip the package.
3.  Install to the system.
    1.  Unix and Linux systems:

            sudo python setup.py install

    2.  Windows platforms: Open a command window at the unzipped directory, do:

            setup.py install


NOTE for Windows Vista and Windows 7 users: you must open the command windows as administrator.


### Use Without Installation

You can also use IMPyBot without installing it to the system location.

1.  Download the package from https://sourceforge.net/projects/impybot
2.  Unzip the package.
3.  Open a terminal inside the unzipped directory, do:

        run_bot.py -j "username" -p "password"


A Guide for The Impatients
------------------------------------------------

To write your own utilities (we call it a plugin), simply follow these TWO steps:


### Write a plugin module

Create a text file called my_first_plugin.py, with codes look like the following:

```python
import impybot  # make sure it's properly installed

class MyFirstPlugin(impybot.SimplePlugin):

    # If a message has lines begin with ANY of these words, 
    # handle_match() will be called.
    command = ('echo', 'display')
    
    def handle_match( self, matched, sender_jid ):
        msg = 'The strings after the matched commands:'

        # If a line in a message matches ANY words in ``command'',
        # the string after the matched word of that line goes into
        # the ``matched'' tuple. 
        for m in matched:
            msg = msg + '\n' + m

        # The returned string will be sent back as a reply.
        return msg

# DON'T FORGET TO REGISTER THE CLASS!!!
impybot.register(MyFirstPlugin)
```


### Invoke the bot

Invoke the command line tool to run a bot and tell it where your plugin is:

    python -m run_bot -j "jid@server.com" -p "password" -m my_first_plugin.py


### That's it!

Congratulations on your first Instant Messaging Application!
