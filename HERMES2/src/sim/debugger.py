#! /usr/bin/env python

########################################################################
# Copyright C 2009, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__=""" main.py
This is the main routine of the vaccine distribution simulator HERMES
"""
_hermes_svn_id_="$Id$"

import sys,os,optparse,traceback,time,string,readline,re,pdb

import input
import globals
import curry
from main import parseCommandLine
# more delayed imports below, so that values in globals can be changed before import

##############
# Notes-
# -We are not tracking temperatures during shipment
# -my 'curry' is doing the case where len(args)<=1 incorrectly
# -There is surely a better way to handle parallel code for freezer,
#  cooler, roomtemp in vaccinetypes.py
# -Are we using the priority values?  I think maybe they are obsolete.
##############

breakConditions= {}
traceConditions= set()

_tokenRe= re.compile(r"""
(\s*(?P<comment>\#.*$))
|\s*(?P<identifier>[a-zA-Z_][a-zA-Z0-9_]*)
|\s*(?P<separator>[,;:])
|\s*(?P<equalsign>\s*=\s*)
|\s*('(?P<string1>[^']*)')
|\s*("(?P<string2>[^"]*)")
|\s*(?P<integer>[+-]?[0-9]+(?![0-9.eE]))
|\s*(?P<float1>[+-]?[0-9]*\.[0-9]*(?![0-9eE]))
|\s*(?P<float2>[+-]?[0-9]*\.[0-9]*[eE][+-]?[0-9]*)
|(?P<trailingblanks>\s+$)
"""
,re.VERBOSE)

def _tokGen(text):
    """
    This returns a generator, each next() of which yields a type/token pair.

    See http://effbot.org/zone/xml-scanner.htm for this nifty little idiom.
    """
    pos = 0
    while True:
        m = _tokenRe.match(text, pos)
        if not m: break
        pos = m.end()
        if m.group('comment'): yield 'comment',m.group('comment')
        elif m.group('identifier'): yield 'identifier',m.group('identifier')
        elif m.group('integer'): yield 'integer',int(m.group('integer'))
        elif m.group('float1'): yield 'float',float(m.group('float1'))
        elif m.group('float2'): yield 'float',float(m.group('float2'))
        elif m.group('separator'): yield 'separator',m.group('separator')
        elif m.group('equalsign'): yield 'equalsign',m.group('equalsign')
        elif m.group('string1'): yield 'string',m.group('string1')
        elif m.group('string2'): yield 'string',m.group('string2')
        elif m.group('trailingblanks'): yield 'trailingblanks',m.group('trailingblanks')
    if pos != len(text):
        raise RuntimeError('tokenizer stopped at pos %r of %r on <%s>' % (
            pos, len(text),text))

def talkToUser(sim, breakList, nextProc):
    global breakConditions, traceConditions
    """
    First argument is a HermesRun
    Second argument is a list of keys into breakConditions which are true at the moment
    Third argument is the next process destined to be activated in that run, 
        or None on the very first call or when the simulation has ended.  
    """
    for k in breakList:
        tfun,msg= breakConditions[k]
        print msg
    if nextProc is not None:
        print "upcoming: %s"%nextProc.name
        
    continueFlag= False
    enterDebuggerFlag= False
    while not continueFlag:
        try:
            line= raw_input("hdb>> ")
            words= [str(token) for toktype,token in _tokGen(line)]
            if len(words)==0: continue
            elif len(words)==1:
                if words[0]=="help": describeSelf()
                elif words[0]=='time': print sim.now()
                elif words[0]=="continue":
                    if 'step' in breakConditions: del breakConditions['step']
                    continueFlag= True
                elif words[0]=="step":
                    breakConditions['step']= (lambda p: True, "Single stepping")
                    continueFlag= True
                elif words[0]=="quit":
                    sys.exit(0)
                elif words[0]=="breakpoints":
                    for k in breakConditions.keys():
                        print k
                elif words[0]=="procinfo":
                    if nextProc is None:
                        print "No current process"
                    else:
                        print "proc: %s"%nextProc.name
                        for attr in dir(nextProc):
                            if attr[:2]!='__' and hasattr(getattr(nextProc,attr),"name"):
                                print "    %s: %s"%(attr,getattr(nextProc,attr).name)
                elif words[0]=="listprocs":
                    for pRef in sim.processWeakRefs:
                        p= pRef()
                        if p is not None: print p.name
                elif words[0]=="pdb":
                    continueFlag= True
                    enterDebuggerFlag= True
                else:
                    print "unknown command or missing argument"
                
            elif len(words)==2 and words[0]=="debug":
                if words[1]=="on": gblDebug=1
                elif words[1]=="off": gblDebug=0
                else: print "second word should be 'on' or 'off'"
            elif words[0]=="listprocs":
                if len(words)==2: regex= re.compile(words[1])
                else:
                    print "Expected 0 or 1 arguments"
                    continue
                for pRef in sim.processWeakRefs:
                    p= pRef()
                    if p is not None and regex.search(p.name): print p.name
            elif words[0]=="break":
                if len(words)==2:
                    try:
                        time= float(words[1])
                        breakConditions[time]= (lambda p: p.sim.now()>=time, "Reached time %f"%time)
                    except ValueError,e:
                        procname= words[1]
                        validNames= []
                        for pRef in sim.processWeakRefs:
                            p= pRef()
                            if p is not None: validNames.append(p.name)
                        if procname in validNames:
                            breakConditions[procname]= (lambda p: p.name==procname, "break on process %s"%procname)
                        else:
                            print "%s is not a valid process name"%procname
                else:
                    print "Expected one argument"
            elif words[0]=="unbreak":
                if len(words)==2:
                    try:
                        time= float(words[1])
                        if time in breakConditions: del breakConditions[time]
                        else: print "No breakpoint at %f"%time
                    except ValueError,e:
                        if words[1] in breakConditions: del breakConditions[words[1]]
                        else: print "No breakpoint at %s"%words[1]
                else:
                    print "Expected one argument"
            elif words[0]=="trace":
                if len(words)==2:
                    procname= words[1]
                    validNames= []
                    for pRef in sim.processWeakRefs:
                        p= pRef()
                        if p is not None: validNames.append(p.name)
                    if procname in validNames:
                        traceConditions.add(procname)
                    else:
                        print "%s is not a valid process name"%procname
                else:
                    print "Expected one argument"
            elif words[0]=="untrace":
                if len(words)==2:
                    if words[1] in traceConditions: traceConditions.discard(words[1])
                    else: print "No tracepoint at %s"%words[1]
                else:
                    print "Expected one argument"
            elif words[0]=="inventory":
                if len(words)==2:
                    attrname= words[1]
                    if hasattr(nextProc,attrname):
                        attr= getattr(nextProc,attrname)
                        if hasattr(attr,'printInventory'):
                            attr.printInventory()
                        else:
                            print "%s has no printInventory method"%str(attr)
                    else:
                        print "%s has no attribute %s"%(str(nextProc),attrname)
                else:
                    print "Expected one argument"
            elif words[0]=="printsupply":
                if len(words)==2:
                    attrname= words[1]
                    if hasattr(nextProc,attrname):
                        attr= getattr(nextProc,attrname)
                        if hasattr(attr,'getSupplySummary'):
                            print attr.getSupplySummary()
                        else:
                            print "%s has no getSupplySummary method"%str(attr)
                    else:
                        print "%s has no attribute %s"%(str(nextProc),attrname)
                else:
                    print "Expected one argument"
            else:
                print "Unrecognized command (try 'help')"
        except Exception,e:
            print '-'*60
            print 'Exception: %s'%e
            print '-'*60
            traceback.print_exc(file=sys.stderr)
            print '-'*60
            print "Continuing; try 'help' or 'quit'"
    
    return enterDebuggerFlag

def stepCallback(sim):
    global breakConditions
    global traceConditions
    
    # Crawl down the heapq until we find the first non-canceled event
    noActiveNotice= True
    index= 0
    try:
        while noActiveNotice:
            if sim._timestamps:
                _tnotice, p, proc, cancelled = sim._timestamps[index]
                noActiveNotice = cancelled
            else:
                simEndFlag= True
                return None
            index += 1
    except IndexError,e:
        simEndFlag= True
        return None
    
    breakList= []
    enterDebuggerFlag= False
    for k,v in breakConditions.items():
        tfun, str= v
        if tfun(proc): breakList.append(k)
    if len(breakList)>0:
        enterDebuggerFlag= talkToUser(sim,breakList,proc)
        
    if proc.name in traceConditions:
        sim.debug= True
        sim.verbose= True
    else:
        sim.debug= False
        sim.verbose= False

    if enterDebuggerFlag:
        print "Dropping into Python debugger; type 'c' to return to this debugging level"
        pdb.set_trace()

def describeSelf():
    print """
Available HERMES debugging commands: 
(Don't confuse these with the commands for the python debugger)

      help
         prints this message
         
      time
         prints the current simulation time

      continue
         starts or continues the simulation
         
      step
         runs one step of one process
         
      procinfo
         print information about the current proc
         
      breakpoints
         lists current breakpoints
         
      pdb
         enter the Python debugger.  To return to the HERMES debugger, type
         'c' for Continue to the Python debugger.
         
      listprocs [regex]
         lists all breakable process names matching regex, or all 
         of them if regex is not given
         
      break <number>
         The argument should be a floating point number giving a time; 
         sets a break at the first proc to become active at or after that time.
         
      unbreak <number>
         Remove the break at time <number>
         
      break <procname>
         The argument should be a breakable process name as returned by
         'listprocs'.  Break when this process is about to become active.
         
      unbreak <procname>
         Remove the break on process <procname>
         
      trace <procname>
         Turn on debug and verbose output when <procname> runs, producing a trace of
         its activity.
         
      untrace <procname>
         Turn off tracing of <procname>
         
      inventory <attrname>
         The argument should be an attribute of the upcoming process, and the
         object given by that attribute should have a printInventory method.  Print the
         inventory of that object.
         
      printsupply <attrname>
         The argument should be an attribute of the upcoming process, and the
         object given by that attribute should have a getSupplySummary method.  Print the
         supplysummary of that object.
         
      quit exits the program

    """



###########
# main
###########

def main():
    global breakConditions
    unifiedInput = input.UnifiedInput()  # pointers to 'unified' files
    userInputList,gblInputs= parseCommandLine()

    globals.deterministic= gblInputs['deterministic']
    nWorkers= gblInputs['workers']
    if nWorkers != 1:
        nWorkers = 1
        print "changing number of workers to 1"

    # Delayed inputs- we wanted to modify globals before causing these modules to load
    import hermes
    import util
    from output_average import create_average_summary_CSV,create_average_report_CSV

    # Any 'grep' requests from the input are interpreted as filters to be applied
    # to stdout, which probably includes verbose or debugging data.
    if gblInputs.has_key('grep') and gblInputs['grep'] is not None:
        print 'Value of grep is %s'%gblInputs["grep"]
        for regex in gblInputs["grep"]:
            sys.stdout= util.FileWithGrep(sys.stdout,regex)

    if nWorkers==1:
#        if len(userInputList)==1:
            perfect = False                # do we run in perfect / gap analysis mode
            if gblInputs['gap']:
                perfect = True
                print 'perfect set'

            hermesRun= hermes.HermesSim(userInputList[0],unifiedInput,0,perfect)
            enterDebuggerFlag= talkToUser(hermesRun,[],None)
            if enterDebuggerFlag:
                print "Dropping into Python debugger; type 'c' to return to this debugging level"
                pdb.set_trace()
            hermesRun.runModelStep(until=hermesRun.model.getTotalRunDays(),
                                   callback=curry.curry(stepCallback,hermesRun))

            hermesRun.printStatistics()
            hermesRun.checkSummary(graph=doGraphics)
 
 #       else:
 #           raise RuntimeError('Only one run at a time is supported when debugging.')
    else:
        raise RuntimeError('Only one worker is supported when debugging.')

                    
            
            
                          
            
############
# Main hook
############

if __name__=="__main__":
    try:
        main()
    except Exception,e:
        print '-'*60
        print 'Exception: %s'%e
        print '-'*60
        traceback.print_exc(file=sys.stderr)


        
