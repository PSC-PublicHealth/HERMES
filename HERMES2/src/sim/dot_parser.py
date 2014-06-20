#! /usr/bin/env python

########################################################################
# Copyright C 2011, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################

__doc__=""" 
This is a library for converting graphvis dot files to a python
dictionary of dictionaries.
"""

_hermes_svn_id_="$Id$"

import types,re


class dot_parse_exception(Exception):
    def __init__(self, dp, exceptString):
        self.exceptString = exceptString
        self.dp = dp
    def __str__(self):
        return "*** graphviz dot parsing exception: %s ***\ncontext:%s"%(self.exceptString, self.dp.getContext())



# taken and modified from 
# http://code.activestate.com/recipes/502304-iterator-wrapper-allowing-pushback-and-nonzero-tes/
class iter_wrapper(object):
    """
    Allows equivalent of ungetc() on an iterator
    """
    
    def __init__(self, it):
        self.it = it
        self.pushed_back = []
        self._index = 0
        #if the last entry was tasted we wish to show one value higher
        self.tasteModifier = 0  

    def __iter__(self):
        return self
    
    def __nonzero__(self):
        if self.pushed_back:
            return True
        
        try:
            self.pushed_back.insert(0, self.it.next())
        except StopIteration:
            return False
        else:
            return True
    
    def next(self):
        self._index += 1
        self.tasteModifier = 0
        try:
            return self.pushed_back.pop()
        except IndexError:
            return self.it.next()

    def taste(self):
        # this will still throw a StopIteration Exception
        if self.pushed_back:
            self.tasteModifier = 1
            return self.pushed_back[-1]
        self._index += 1
        n = self.it.next()
        self.pushback(n)
        self.tasteModifier = 1
        return n
        
    def pushback(self, item):
        self._index -= 1
        self.tasteModifier = 0
        self.pushed_back.append(item)

    def index(self):
        # this points to the _next_ item on the list
        return self._index + self.tasteModifier

class dot_parser():
    """
    Parses graphviz dot file format and returns it in a python-esque data structure.
    This will only try to read the first graph in a dot file.
    """

    def __init__(self):
        pass

    def parse(self, dot):
        # First off lose any "\\\n" that are used to keep lines from being too long.
        # Python don't care 'bout no long lines.
        self.dot = re.sub(r"\\\n", "", dot)

        # [\[\];{}=,]     matches any of the following tokens: [ ] ; { } = ,
        # ->              matches ->
        # --              matches --
        # (?s)\".*?(?<!\\)\"  matches a quoted string, ie "some text here"
        # [a-zA-Z\200-\377_][a-zA-Z\200-\3770-9_]*  
        #                 matches a bare word
        # -?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?) 
        #                 matches numeric
        #self.tokens = re.findall(r'[\[\];{}=,]|\-\>|\"[^\"]*\"|[^\s\[\];{}=,]+', dot)
        self.tokens = re.findall(r"""(?x)(?s)  # extended, dot matches newline
                                     [\[\];{}=,] | # matches the tokens [ ] ; { } = ,
                                     -> | -- |  # matches -> or --
                                     \".*?(?<!\\)\" |  # quoted string handling escaped quotes
                                     [a-zA-Z\200-\377_][a-zA-Z\200-\3770-9_]* | #numeric
                                     -?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?) # simple identifier """,
                                 dot)
        self.tokenIter = iter_wrapper(iter(self.tokens))

        graphType = self.validate_label(self.tokenIter.next())
        graphName = self.validate_label(self.tokenIter.next())
        self.validate(self.tokenIter.next(), '{')

        graph = {}

        # now read the records
        while self.tokenIter.taste() != '}':
            # read the label
            label = self.validate_label(self.tokenIter.next())
            if self.tokenIter.taste() == '->' or self.tokenIter.taste() == '--':
                label += self.tokenIter.next()
                label += self.validate_label(self.tokenIter.next())
            self.validate(self.tokenIter.next(), '[')

            element_attribs = {}
            # now read the attributes
            while self.tokenIter.taste() != ']':
                key = self.validate_label(self.tokenIter.next())
                self.validate(self.tokenIter.next(), '=')
                val = self.validate_label(self.tokenIter.next(), 'strip')
                if self.tokenIter.taste() == ',':
                    self.tokenIter.next()
                element_attribs[key] = val

            self.tokenIter.next()
            self.validate(self.tokenIter.next(), ';')
            graph[label] = element_attribs

        return (graph, graphType)

    def getContext(self, count=30):
        index = self.tokenIter.index() - 1
        start = index - count
        if start < 0: start = 0
        end = index + count
        if end > len(self.tokens): end = len(self.tokens)
        context = ""
        for i in xrange(start,end):
            if i == index:
                context += "**" + self.tokens[i] + "**"
            else:
                context += self.tokens[i]
            if i != end - 1:
                context += " / "
        return context

    def validate(self, val, opts):
        if isinstance(opts, types.StringTypes):
            if val == opts:
                return val
            raise dot_parse_exception(self, "token %s not expected (wanted %s)"%(val,opts))

        for opt in opts:
            if val == opt:
                return val
        raise dot_parse_exception(self, "token %s not expected"%val)

    def validate_label(self, val, quotes=False):
        # by defaulted, quoted strings are not allowed
        # if quotes is True, allow quotes
        # if quotes == "strip" then quotes are stripped
        if val[0] in "[];{}=,-":
            raise dot_parse_exception(self, "token %s, not expected, wanted label"%val)
        if val[0] != '"':
            return val

        if quotes == 'strip':
            return val[1:-1]
        if quotes is True:
            return val
        raise dot_parse_exception(self, "expected unquoted string")

def parse_dot_text(dot):
    dp = dot_parser()
    return dp.parse(dot)

