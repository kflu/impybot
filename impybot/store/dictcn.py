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
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import urllib2,re
from urllib import quote_plus
from xml.dom import minidom

class Dict:
    """Class to get EN2CN & CN2EN translation from dict.cn"""

    def __init__( self, word="Della" ):
        """initializing the word and the url received"""   
        self.setWord(word)
        self.setUrl()


    def setWord( self, word ):
        """function to set the word"""
        # self.__word=word
        self.__word=quote_plus(word)


    def setUrl(self):
        """function to set the url"""
        self.__url="http://dict.cn/ws.php?utf8=true&q=%s"%self.__word


    def getPage(self):
        """function to get the content of the web page.return the string page content"""        
        url=self.__url
        try:
            page = urllib2.urlopen(url)
            page_content = page.read()
            page.close()
        except:
            return ""
        return page_content


    def getWord(self):
        """function get the info what we needed from the web page.return a list reply"""
        page_content=self.getPage().replace("\n"," ")
        page_content=unicode(page_content,"utf-8") # set the page content encoding to unicode
        regex=r'<def>(.*)</def>' 
        match=re.findall( regex , page_content )     
        return match

    def getResult(self):
        """ Parse the xml result, format and then return it."""
        page_content=self.getPage()
        dom = minidom.parseString(page_content)
        definition = "%s" % dom.getElementsByTagName("def")[0].firstChild.data
        if definition == "Not Found":
            return ''
        word = "Word: %s" % dom.getElementsByTagName("key")[0].firstChild.data
        # pron...
        examples = []
        for ex in dom.getElementsByTagName("sent"):
            examples.append( "%s %s" % (ex.getElementsByTagName("orig")[0].firstChild.data, ex.getElementsByTagName("trans")[0].firstChild.data) )

        examples = "\n".join(examples)
        result = []
        result.append(definition)
        if examples.strip() != "":
            result.extend(["Examples:", examples])
        return "\n".join(result)

import re
from impybot import Plugin, register
import traceback
class DictPlugin(Plugin):

    pattern = re.compile(ur'^(cha|dict|lookup|查)(\s)(?P<word>..*)\s*$', re.M)

    def action(self, obj, *args, **kwargs):
        try:
            if not self.is_message(obj): return
            body = obj.getBody()
            if not body: return
            # TODO only use the first match.
            r = self.pattern.search(body)
            if not r: return
            word = r.group('word')
            d = Dict(word.encode('utf-8'))
            result = d.getResult()
            if not result:
                return self.Response('%s was not found.' % word)
            return self.Response(result)
        except Exception, e:
            self.logger.warning(e)
            self.logger.warning(traceback.format_exc(e))
            return self.Response(traceback.format_exc(e))
register(DictPlugin)
