#! /usr/bin/env python
# -*- coding: utf8 -*-

###################################################################################
# Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################

_hermes_svn_id_="$Id$"

import sys,os,os.path,re,types,unittest,StringIO,chardet,codecs

class TokenizerException(Exception): pass
class ParserException(Exception): pass


class KVPParser:
    """
    This class provides services for parsing and generating key value pair files.
    """
    
    tokenRe= re.compile(r"""
    (\s*(?P<comment>\#.*$))
    |(?P<identifier>[a-zA-Z_][a-zA-Z0-9_]*)
    |(?P<separator>[,;:])
    |(?P<equalsign>\s*=\s*)
    |('(?P<string1>[^']*)')
    |("(?P<string2>[^"]*)")
    |(?P<integer>[+-]?[0-9]+(?![0-9.eE]))
    |(?P<float1>[+-]?[0-9]*\.[0-9]*(?![0-9eE]))
    |(?P<float2>[+-]?[0-9]*\.[0-9]*[eE][+-]?[0-9]*)
    |(?P<trailingblanks>\s+$)
    """
    ,re.VERBOSE)
    
    # States for parser FSM
    START= 0
    COMMENT= 1
    FAILED= 2
    HASKEY= 3
    HASEQ= 4
    HASVAL= 5
    HASLIST= 6
    
    def __init__(self):
        self.verbose= 0
        self.debug= 0

    @staticmethod
    def _tokGen(text,encoding):
        """
        This returns a generator, each next() of which yields a type/token pair.
        
        See http://effbot.org/zone/xml-scanner.htm for this nifty little idiom.
        """
        pos = 0
        if encoding is not None: text = text.decode(encoding)
        while True:
            m = KVPParser.tokenRe.match(text, pos)
            if not m: break
            pos = m.end()
            if m.group('comment'): 
                v = m.group('comment')
                if isinstance(v,types.StringType): v = v.decode(encoding)
                yield 'comment',v
            elif m.group('identifier'): 
                v = m.group('identifier')
                if isinstance(v,types.StringType): v = v.decode(encoding)
                yield 'identifier',v
            elif m.group('integer'): yield 'integer',int(m.group('integer'))
            elif m.group('float1'): yield 'float',float(m.group('float1'))
            elif m.group('float2'): yield 'float',float(m.group('float2'))
            elif m.group('separator'): yield 'separator',m.group('separator')
            elif m.group('equalsign'): yield 'equalsign',m.group('equalsign')
            elif m.group('string1'): 
                v = m.group('string1')
                if isinstance(v,types.StringType): v = v.decode(encoding)
                yield 'string',v
            elif m.group('string2'): 
                v = m.group('string2')
                if isinstance(v,types.StringType): v = v.decode(encoding)
                yield 'string',v
            elif m.group('trailingblanks'): yield 'trailingblanks',m.group('trailingblanks')
        if pos != len(text):
            raise TokenizerException('tokenizer stopped at pos %r of %r on <%s>' % (
                pos, len(text),text))

    def _innerParseKVP( self, iterator, encoding ):
        result= {}
        
        for rec in iterator:
            if self.debug: print 'parsing <%s>'%rec
            tokenizer= KVPParser._tokGen(rec, encoding)
            key= None
            val= None
            valType= None
            state= KVPParser.START
            try:
                for t,v in tokenizer:
                    if self.debug: print "got %s,<%s> in state %d"%(t,v,state)
                    if state==KVPParser.START:
                        if t in ["comment","trailingblanks"]:
                            state= KVPParser.COMMENT
                        elif t=="identifier":
                            key= v
                            state= KVPParser.HASKEY
                        else:
                            state= KVPParser.FAILED
                    elif state==KVPParser.HASKEY:
                        if t=="equalsign":
                            state= KVPParser.HASEQ
                        elif t in ["comment","trailingblanks"]:
                            state= KVPParser.COMMENT
                        else:
                            state= KVPParser.FAILED
                    elif state==KVPParser.HASEQ:
                        if t in ["integer","float","string","identifier"]:
                            val= v
                            valType= t
                            state= KVPParser.HASVAL
                        else:
                            state= KVPParser.FAILED
                    elif state==KVPParser.HASVAL:
                        if t=="separator":
                            if val is None: val= []
                            else: val= [val]
                            valType= "list"
                            state= KVPParser.HASLIST
                        elif t in ["comment","trailingblanks"]:
                            state==KVPParser.COMMENT
                        else:
                            state= KVPParser.FAILED
                    elif state==KVPParser.HASLIST:
                        if t in ["integer","float","string","identifier"]:
                            val.append(v)
                        elif t=="separator":
                            pass
                        elif t in ["comment","trailingblanks"]:
                            state= KVPParser.COMMENT
                        else:
                            state= KVPParser.FAILED
                    elif state==KVPParser.FAILED:
                        pass
                    elif state==KVPParser.COMMENT:
                        pass
                    else:
                        raise RuntimeError("Parser internal error: unexpected state %s"%state)
                if self.debug: print('FSM completed')
                if state==KVPParser.FAILED:
                    raise ParserException("Failed to parse <%s>"%rec)
                if key is not None:
                    if valType is not None:
                        # Handle special cases which translate to booleans
                        if valType=="identifier":
                            if val.lower()=="none":
                                result[key]= None
                            elif val.lower()=="true":
                                result[key]= True
                            elif val.lower()=="false":
                                result[key]= False
                            else:
                                result[key]= val
                        else:
                            result[key]= val
                    else:
                        # an identifier alone is interpreted as a boolean flag to be marked true.
                        # we represent true with a string, though, since that's how other such 
                        # keys appear.
                        result[key]= True
            except TokenizerException,e:
                raise ParserException("failed to lex <%s>; %s"%(rec,e))
        return result

    def parse( self,iteratorOrFilename, encoding=None ):
        """
        The input can be an iterator (typically an open file or a list), or a string to
        be interpreted as a filename.  The optional second parameter is the encoding with which
        to decode strings to unicode.  The return value of parseKVP is a dict containing
        keys and their associated values as defined by the file.
        """
        if isinstance(iteratorOrFilename,types.StringTypes):
            if self.verbose: print "parsing %s"%iteratorOrFilename
            if encoding is None:
                # preparse for encoding
                with open(iteratorOrFilename,"rU") as f:
                    lines = f.readlines()
                    encodingInfo = chardet.detect("".join(lines))
                    if encodingInfo['confidence'] >= 0.9: 
                        encoding = encodingInfo['encoding']
                    else:
                        encoding = sys.getdefaultencoding()
                
            with open(iteratorOrFilename,"rU") as f:
                result= self._innerParseKVP(f,encoding)
        else:
            if self.verbose: print "parsing kvp input"
            if encoding is None: encoding = sys.getdefaultencoding()
            result= self._innerParseKVP(iter(iteratorOrFilename), encoding)
        
        return result

    def _innerWriteKVP(self,ofile,dict):
        for k,v in dict.items():
            if isinstance(v,types.StringTypes):
                if '"' in v: 
                    ofile.write("%s = '%s'\n"%(k,v)) # try to preserve the quoted substring in v
                else:
                    ofile.write('%s = "%s"\n'%(k,v))
            elif isinstance(v,types.ListType):
                if len(v)==0:
                    ofile.write('%s = \n'%k)
                else:
                    vstr= ""
                    for e in v:
                        if isinstance(e,types.StringTypes):
                            if '"' in e:
                                vstr += "'%s',"%e
                            else:
                                vstr += '"%s",'%e
                        else:
                            vstr += '%s,'%e
                    ofile.write('%s = %s\n'%(k,vstr[:-1]))
            else:
                ofile.write('%s = %s\n'%(k,v))
                
    
    def writeKVP( self, ofileOrFilename, dict, encoding=None ):
        """
        Write the dictionary contents to the given open file as a key-value pair table.
        If ofileOrFilename is a string, that string will be treated as the path to the
        output file.
        """
        if isinstance(ofileOrFilename,types.StringType):
            if self.verbose: print "writing to %s"%ofileOrFilename
            with open(ofileOrFilename,"w") as rawFile:
                if encoding is None:
                    if hasattr(rawFile,'encoding'): encoding = rawFile.encoding
                    else: encoding = 'utf8'
                f = codecs.getwriter(encoding)(rawFile, 'replace')
                self._innerWriteKVP(f,dict)
        else:
            if self.verbose: print "writing to %s"%ofileOrFilename.name
            if encoding is None:
                if hasattr(ofileOrFilename,'encoding'):
                    encoding = ofileOrFilename.encoding
            if encoding is None:
                encoding = 'utf8'
            f = codecs.getwriter(encoding)(ofileOrFilename, 'replace')
            self._innerWriteKVP(f,dict)
    

def main():
    "This is a simple test routine which takes kvp files as arguments"
    
    parser= KVPParser()
    parseThese= []
    for a in sys.argv[1:]:
        if a=='-v': parser.verbose= True
        elif a=='-d': parser.debug= True
        else: parseThese.append(a)
        
    if parser.debug:
        # Run some internal tests
        for rec in [a for a,b in TestKVPTools.samples]:
            try:
                d= parser.parse([rec],encoding='utf8') 
                print d  
            except ParserException,e:
                print e
    
    for thing in parseThese:
        print "##### Checking %s"%thing
        d= parser.parse(thing)
        if parser.verbose:
            parser.writeKVP(sys.stdout,d)
        with open('test_kvp_tools.kvp','w') as f:
            parser.writeKVP(f,d)
        with open('test_kvp_tools.kvp','rU') as f:
            testDict= parser.parse(f)
        assert(testDict==d)

class TestKVPTools(unittest.TestCase):
    samples= [
              ("# This is a pure comment",{}),
              ("    # so is this   ",{}),
              ("foo",{'foo':True}),
              ("bar # my comment",{'bar':True}),
              ("thing=124",{'thing':124}),
              ("thing2 =-123",{'thing2':-123}),
              ("thing3= +123",{'thing3':123}),
              ('thing4 = "foo"',{'thing4':'foo'}),
              ("lthing = 12,34;56:'foo' # a list",{'lthing':[12, 34, 56, 'foo']}),
              ("""other='hello',12,'and "more" stuff'\t# comment""",{'other': ['hello', 12, 'and "more" stuff']}),
              ("thing5=-17.2",{'thing5':-17.2}),
              ("thing6= 18.27",{'thing6':18.27}),
              ("thing8=+19.3",{'thing8':19.3}),
              ("thing9=+.8",{'thing9':0.8}),
              ("thing10=.82",{'thing10':0.82}),
              ("thing11=7.",{'thing11':7.0}),
              ("thing12=+8.",{'thing12':8.0}),
              ("lthing2= 0.8e3,7.e3,-4.2E-03",{'lthing2': [800.0, 7000.0, -0.0042]}),
              ("someidentifier,","Failed to parse <someidentifier,>"),
              ("thing13='quoted string with an 0.8 embedded float'",{'thing13': 'quoted string with an 0.8 embedded float'}),
              ("somebool= True",{'somebool': True}),
              ("somebool= false",{'somebool': False}),
              ("something= None",{'something': None}),
              ('utf8sample= "Dépôt Central*"',{'utf8sample':u'Dépôt Central*'}),
              ]
    
    def test_kvptools(self):
        parser = KVPParser()
        totalDict = {}
        for rec,expectedResult in TestKVPTools.samples:
            try:
                d= parser.parse([rec],encoding='utf8')
                self.assertTrue(isinstance(expectedResult, types.DictType))
                if d != expectedResult:
                    print "error: got %s expected %s"%(d,expectedResult)
                self.assertTrue(d == expectedResult)
                totalDict.update(d)
            except ParserException,e:
                self.assertTrue(isinstance(expectedResult, types.StringTypes))
                self.assertTrue(str(e)==expectedResult)
        outSIO = StringIO.StringIO()
        parser.writeKVP(outSIO,totalDict,encoding='utf8')
        inSIO = StringIO.StringIO(outSIO.getvalue())
        testDict= parser.parse(inSIO,encoding='utf8')
        self.assertTrue(testDict == totalDict)
        for k,v in testDict.items():
            #print "<%s>:<%s>"%(k,v)
            self.assertTrue(k in totalDict and totalDict[k]==v)
            
############
# Main hook
############

if __name__=="__main__":
    main()

