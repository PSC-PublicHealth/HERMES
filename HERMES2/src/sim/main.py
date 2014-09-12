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

import ipath

import sys,os,optparse,traceback,time,string,codecs,locale
#multiprocessing import Process, JoinableQueue, current_process
import multiprocessing
import multiprocessing.forking
import Queue # for Queue.EMPTY
#from HermesOutput import HermesOutputMerged, HermesOutput
try:
    import SimPy
except ImportError as e:
    raise RuntimeError("Simpy is required to run the HERMES simulation tool\n"\
                        "It can be obtained at http://simpy.sourceforge.net/")

## for use with line_profiler, 
#import __builtin__
#try:
#    __builtin__.profile
#except AttributeError:
#    # No line profiler, provide a pass-through version
#    def profile(func): return func
#    __builtin__.profile = profile

import input
import globals
import copy
import pickle
# more delayed imports below, so that values in globals can be changed before import

##############
# Notes-
# -We are not tracking temperatures during shipment
# -my 'curry' is doing the case where len(args)<=1 incorrectly
# -There is surely a better way to handle parallel code for freezer,
#  cooler, roomtemp in vaccinetypes.py
# -Are we using the priority values?  I think maybe they are obsolete.
##############

class _Popen(multiprocessing.forking.Popen):
    def __init__(self, *args, **kw):
        if hasattr(sys, 'frozen'):
            # We have to set original _MEIPASS2 value from sys._MEIPASS
            # to get --onefile mode working.
            # Last character is stripped in C-loader. We have to add
            # '/' or '\\' at the end.
            os.putenv('_MEIPASS2', sys._MEIPASS + os.sep) # @UndefinedVariable
        try:
            super(_Popen, self).__init__(*args, **kw)
        finally:
            if hasattr(sys, 'frozen'):
                # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                # available. In those cases we cannot delete the variable
                # but only set it to the empty string. The bootloader
                # can handle this case.
                if hasattr(os, 'unsetenv'):
                    os.unsetenv('_MEIPASS2')
                else:
                    os.putenv('_MEIPASS2', '')


class Process(multiprocessing.Process):
    _Popen = _Popen


def _addOptions(parser, parserArgs):
    if parserArgs is None:
        return

    for parserArg in parserArgs:
        posArgs =  parserArg['posArgs']
        kwArgs =   parserArg['kwArgs']
        parser.add_option(*posArgs, **kwArgs)

def _retrieveOptions(opts, gblDict, parserArgs):
    if parserArgs is None:
        return
    for parserArg in parserArgs:
        argName =  parserArg['argName']
        gblDict[argName] = getattr(opts, argName)


def parseCommandLine(parserArgs=None, cmdLineArgs=None):
    """
    This routine takes command line input and builds a list of UserInput data structures
    and a dictionary of global arguments (like worker thread count).
    Side effect: stdout is optionally directed to a file and any 'grep' operations are applied.

    parserArgs is optionally a list of dicts with the following elements:
        posArgs:   list of the positional arguments to provide to OptionParser.add_option()
        kwArgs:    dictionary of the keyword arguments to provide to OptionParser.add_option()
        argName:   string defining the attribute of parser to be copied after the options have 
                   been parsed.  This attribute will be copied to gblDict[argName]
                   
    cmdLineArgs is the argument string to parse.  The default action is to use sys.argv[1:]
    """
    parser= optparse.OptionParser(usage="""
    %prog [-v][-d][--input inputFile] [inputFile2] [inputFile3] ...
    """)
    parser.add_option("-v","--verbose",action="store_true",help="verbose output")
    parser.add_option("-d","--debug",action="store_true",help="debugging output")
    parser.add_option("-i","--input",help="input file to the hermes run")
    parser.add_option("--out",
                      help="descriptive output name.  Equivalent to '-Doutputfile=...' when run against CSV files")
    parser.add_option("--grep",action="append",help="Only print output lines matching the given regular expression")
    parser.add_option("-c","--configline",action="append",help="add/override config info with csv record")
    parser.add_option("-D","--define",action="append",help="add/override config info with this definition")
    parser.add_option("--workers","--threads",metavar="nWorkers",type="int",default=1,
                      help="Specify the number of worker processes to use")
    parser.add_option("--average",action="store_true",default=False,help="Create an average summary csv file")
    parser.add_option("--stepper",action="store_true",default=False,help="Turns on Simpy's stepping interface, may be slower")
    parser.add_option("--deterministic",action="store_true",default=False,
                      help="Attempt to make runs fully deterministic.  This includes using ordered dictionaries where needed, and will significantly slow the simulation.")
    parser.add_option("--gap", action='store_true', help="Run the gap analysis tool")
    parser.add_option("--zip_inputs", help="save all inputs into a specified zip file.  Don't run the sim")
    parser.add_option("--use_zip", help="run hermes with inputs from a specified zip file")
    parser.add_option("--use_shadow", help="load shadow network and build model from that",
                      action="store_true", default=False)
    parser.add_option("--use_dbmodel", help="run hermes from database inputs, implies --use_shadow",
                      action="store_true", default=False)
    parser.add_option("--run_number", help="only run the specified run from a list of runs")
    parser.add_option("--zip_outputs", help="save all outputs into a specified zip file")
    parser.add_option("--save_hdata", help="save the internal output structure in a pickle file")
    parser.add_option("--minion", action="store_true", 
                      help="changes format of info written to stderr to make machine parsing easier")

    # the next option "--merge_outputs" is really intended for server use after each sim has been
    # run individually using --run_number and --zip_outputs.  The usage requirements are:
    #      --use_zip is set to the original input zip file,
    #      --zip_outputs is set to our resulting output zip file,
    #      and all of the output zip files are then put on the command line.
    parser.add_option("--merge_outputs", action='store_true', help="server use: load the outputs from several partial runs to finalize")

    # add any supplemental arguments
    _addOptions(parser, parserArgs)

    if cmdLineArgs is None:
        opts,args= parser.parse_args()
    else:
        opts,args= parser.parse_args(args=cmdLineArgs)

    if opts.use_zip is not None:
        import HermesInput
        userInputList, gblDict = HermesInput.extractInputs(opts.use_zip)
        #handle any options that we're going to honor over top of what was specified in the zip file
        gblDict['run_number'] = opts.run_number
        gblDict['zip_outputs'] = opts.zip_outputs
        gblDict['merge_outputs'] = None
        # retrieve any supplemental args
        _retrieveOptions(opts, gblDict, parserArgs)
        if opts.merge_outputs:
            gblDict['merge_outputs'] = args
        parser.destroy()
        return (userInputList, gblDict)


    gblDict= {}

    gblDict['workers']= opts.workers
    if opts.grep:
        gblDict['grep']= opts.grep
    gblDict['average'] = False
    if opts.average:
        gblDict['average'] = opts.average
        
    gblDict['stepper'] = opts.stepper
    if gblDict['stepper']:
        print "WARNING!!! Using SimPy's Stepping interface, this may be slower"
        print "Should only be used if you need intimate control over every step of the simulation"
        
    gblDict['minion'] = opts.minion
    gblDict['deterministic'] = opts.deterministic
    gblDict['zip_inputs'] = opts.zip_inputs
    gblDict['run_number'] = opts.run_number
    gblDict['zip_outputs'] = opts.zip_outputs
    gblDict['save_hdata'] = opts.save_hdata
    gblDict['merge_outputs'] = None
    gblDict['gap'] = opts.gap
    gblDict['use_shadow'] = opts.use_shadow
    gblDict['use_dbmodel'] = opts.use_dbmodel
    if opts.use_dbmodel:
        gblDict['use_shadow'] = True
    # retrieve any supplemental args
    _retrieveOptions(opts, gblDict, parserArgs)

    inputFiles = []
    if opts.input is not None:
        inputFiles = [opts.input]
    inputFiles.extend(args)

    # save a copy of the remainder of the hermes args and opts.input
    # so that HermesInput can get it's grubby hands on them.
    gblDict['input_files'] = inputFiles

    userInputList = []
    firstInputFile = None

    ### Make a results Group
    resultsGroupId = None
    
    
    for inputString in inputFiles:
        inputFile,sep,count = inputString.partition(':')
        if firstInputFile is None:
            firstInputFile = inputFile
        else:
            print "First = %s, input = %s"%(firstInputFile,inputFile)
            if firstInputFile != inputFile:
                if gblDict['use_dbmodel']:  # I really think we should get rid of this if statement
                    raise RuntimeError("Hermes should not be run with multiple models against the DB")
        if count == '': count = 1
        for i in xrange(int(count)):
            userInputList.append(input.UserInput(inputFile, gblDict['use_dbmodel']))


    if gblDict['use_dbmodel'] and opts.minion == False:
        from shadow_db_routines import addResultsGroup
        if opts.out is None:
            raise RuntimeError("--out must be set with a descriptive name when hermes is run against the DB")
        resultsGroupId = addResultsGroup(firstInputFile, opts.out)
    # not sure where to put this but I think this gets it as far as I need it.
    #gblDict['resultsGroupId'] = resultsGroupId
    elif opts.minion:
        resultsGroupId = opts.out

    for userInput in userInputList:
        if opts.minion: 
            userInput['minion'] = True
            userInput['customoutput'] = None
        if gblDict['use_dbmodel']:
            userInput['customoutput'] = None
        if opts.configline is not None:
            userInput.addValues(opts.configline,replace=True,vtype="csv")
        if opts.define is not None:
            userInput.addValues(opts.define,replace=True,vtype="kvp")
        if opts.verbose: userInput['verbose'] = True
        if opts.debug: userInput['debug'] = True
        if opts.out != None:
            # this might need a full string.translate()
            s = opts.out.replace(' ', '_')
            userInput.addValues(["outputfile=%s"%s],replace=True,vtype="kvp")
        userInput['resultsGroupId'] = resultsGroupId
        if userInput.has_key('verbose') and userInput['verbose']:
            print '-'*60
            print 'Inputs:'
            print '-'*60
            userInput.printTable()
            print '-'*60
            # assert Unified Input is right

    # Clean up command line parser
    parser.destroy()

    return userInputList,gblDict

class OutputRedirector():
    def __init__(self, runNumber):
        import util

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        
        if os.environ.has_key('HERMES_DATA_OUTPUT'):
            self.redir = True
            so = util.openOutputFile('stdout.%s'%runNumber, useTempFile=True)
            se = util.openOutputFile('stderr.%s'%runNumber)
        else:
            self.redir = False
            so = sys.stdout
            se = sys.stderr
            
        sys.stdout = codecs.getwriter(util.getPreferredOutputEncoding(so.encoding))(so, 'replace')
        sys.stderr = codecs.getwriter(util.getPreferredOutputEncoding(se.encoding))(se, 'replace')
        
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.cleanup()

    def cleanup(self):
        if self.redir == False:
            return
        sys.stdout.close()
        sys.stdout = self.old_stdout
        sys.stderr.close()
        sys.stderr = self.old_stderr
        self.redir = False

def loadShadowNetwork(userInput, unifiedInput):
    import shadow_network
    if userInput.fromDb:
        from shadow_db_routines import getNetwork
        return getNetwork(userInput.definitionFileName)
    from shadow_network import loadShdNetwork, loadShdTypes
    return loadShdNetwork(userInput, 
                          loadShdTypes(userInput, unifiedInput))

def commitResults(results):
    from shadow_db_routines import commitResultsEntry
    commitResultsEntry(results)

def workerRun(arg):
    import hermes
    q,outQ = arg
    print 'Process %s run'%multiprocessing.current_process().name
    try:
        while True:
            userInput, unifiedInput, gblInputs, runNumber, doGraphics, perfect= q.get()
            with OutputRedirector(runNumber) as o:
                try:
                    output = None
                    shdNet = None
                    if gblInputs['use_shadow']:
                        shdNet = loadShadowNetwork(userInput, unifiedInput)
                    time.sleep(runNumber)
                    r = hermes.HermesSim(userInput, unifiedInput, 
                                         runNumber=runNumber, perfect=perfect, shdNet=shdNet)
                    if gblInputs['stepper']:
                        output = r.runModelStep()
                    else:
                        output = r.runModel()
                    r.printStatistics()
                    r.checkSummary(graph=doGraphics) 
                    r.cleanupOutputs()
                    output.writeOutputs()
                    if gblInputs['save_hdata'] is not None:
                        output.save(gblInputs['save_hdata'])
                    if gblInputs['use_dbmodel']:
                        commitResults(r.results)
                    print 'Process %s finished a task'%multiprocessing.current_process().name
                except Exception as e:
                    print '-'*60
                    print 'Exception: %s'%e
                    print '-'*60
                    traceback.print_exc(file=sys.stderr)
                finally:
                    if output is not None:
                        output.strengthenRefs()
                    outQ.put(output)
            q.task_done()
	    #return
    except Queue.Empty,e:
        pass
    print 'Process %s is out of work'%multiprocessing.current_process().name

###########
# main
###########

def main():
    # make a copy of argv before the options parser trashes it.
    argvcp = copy.deepcopy(sys.argv)

    unifiedInput = input.UnifiedInput()  # pointers to 'unified' files
    userInputList,gblInputs= parseCommandLine()

    if gblInputs['zip_inputs'] is not None:
        from HermesInput import gatherInputs
        gatherInputs(gblInputs['zip_inputs'],
                     userInputList, 
                     gblInputs, 
                     unifiedInput,
                     argvcp)
        return 0

    # Delayed inputs- we wanted to modify globals before causing these modules to load
    import util
    import hermes
    import HermesOutput
    
    simCount = len(userInputList)  # number of hermes runs
    finalizeOutputs = True         # whether to run routines that merge existing outputs
    nWorkers= gblInputs['workers'] # number of worker processes
    onlyRun = None                 # if set this specifies which simulation instance to run
    doGraphics = True              # do we display graphics?
    perfect = False                # do we run in perfect / gap analysis mode
    gapFinalize = False            # do we run the gap analysis finalizations
    mergedOutput = None            # our merged output
    outputList = []                # this is our list of HermesOutput()s.  Instantiated early
                                   # because we might need to pull it from a zip file.

    if simCount <= 1:
        finalizeOutputs = False
    else:
        doGraphics = False

    if gblInputs['gap']:
        perfect = True
        doGraphics = False
        gapFinalize = True

    if gblInputs['run_number'] is not None:
        nWorkers = 1
        onlyRun = int(gblInputs['run_number'])
        finalizeOutputs = False
        if gblInputs['save_hdata'] is None:
            gblInputs['save_hdata'] = 'hermes_output'
        #gapFinalize = False
        doGraphics = False
    
    if gblInputs['merge_outputs'] is not None:
        from HermesInput import mergeOutputs
        nWorkers = 1
        onlyRun = -1
        finalizeOutputs = True
        if gblInputs['save_hdata'] is None:
            gblInputs['save_hdata'] = 'hermes_output'
        outputList = mergeOutputs(gblInputs['zip_outputs'], gblInputs['merge_outputs'], gblInputs['save_hdata'])
        if gblInputs['gap']:
            gapFinalize = True
            doGraphics = False

    if gblInputs['zip_outputs'] is not None:
        if gblInputs['merge_outputs'] is None:
            from HermesInput import gatherInputs
            gatherInputs(gblInputs['zip_outputs'], userInputList, gblInputs, unifiedInput, argvcp)
        util.redirectOutput(zipfileName = gblInputs['zip_outputs'])
    

    with OutputRedirector('main') as mainOutput:

        globals.deterministic= gblInputs['deterministic']

        from output_average import create_average_summary_CSV,create_average_report_CSV,create_average_cost_CSV

        # Any 'grep' requests from the input are interpreted as filters to be applied
        # to stdout, which probably includes verbose or debugging data.
        if gblInputs.has_key('grep') and gblInputs['grep'] is not None:
            print 'Value of grep is %s'%gblInputs["grep"]
            for regex in gblInputs["grep"]:
                sys.stdout= util.FileWithGrep(sys.stdout,regex)

        ValidatePostSimInputs(userInputList[0])

        if nWorkers==1:
            for runNumber, userInput in enumerate(userInputList):
                if onlyRun is not None:
                    if onlyRun != runNumber:
                        continue
                with OutputRedirector(runNumber) as runOutput:
                    output = None
                    try:
                        shdNet = None
                        if gblInputs['use_shadow']:
                            print "using shadow network"
                            shdNet = loadShadowNetwork(userInput, unifiedInput)

                        r = hermes.HermesSim(userInput, unifiedInput, 
                                             runNumber=runNumber, perfect=perfect, shdNet=shdNet)

                        if gblInputs['stepper']:
                            ## Test 
                            count = r.model.getBurninDays()
                            while count < r.model.getTotalRunDays():
                                until = count + 10.0
                                output = r.runModelStep(until)
                                count += 10.0
                        else:
                            output = r.runModel()
                        r.printStatistics()
                        r.checkSummary(graph=doGraphics)
                        r.cleanupOutputs()
                        output.writeOutputs()
                        if gblInputs['save_hdata'] is not None:
                            output.save(gblInputs['save_hdata'])
                        if gblInputs['use_dbmodel']:
                            commitResults(r.results)
                    finally:
                        # optimization to save RAM.  Merge outputs as they come in and then
                        # drop them out of scope as soon as possible.
                        # Don't even merge them if it won't be needed.
                        if finalizeOutputs or (gapFinalize):
                            mergedOutput = _mergeOutput(mergedOutput, output, runNumber)


        else:
            doGraphics= False # since tk doesn't seem to like running in any but the main thread
            workQueue= multiprocessing.JoinableQueue()
            outputQueue = multiprocessing.Queue() #since this is different from Queue.Queue
            runCount = 0
            for runNumber,userInput in enumerate(userInputList):
                workQueue.put((userInput,unifiedInput,gblInputs,runNumber,doGraphics,perfect))
                runCount += 1
            for i in range(nWorkers):
                t= Process(target=workerRun, args=((workQueue,outputQueue),))
                t.daemon= True
                t.start()

            # optimization to save RAM
            # since each HermesOutput can often be large fractions of a GB or more
            # get rid of it as soon as possible
            # this should be the equivalent of
            #for i in xrange(runCount):
            #     outputList.append(outputQueue.get())
            # plus any finalize processing
            if finalizeOutputs or (gapFinalize):
                for i in xrange(runCount):
                    mergedOutput = _mergeOutput(mergedOutput, outputQueue.get(), i)
            else:
                for i in xrange(runCount):
                    outputQueue.get()

            # this is probably no longer critical but one could call this proper.
            workQueue.join()


        
        if finalizeOutputs:
            # Do all of the things where we work with multiple outputs here.
            # create a summary average file
            print "We are finalizing the outputs!!!!!"
            if gblInputs['average'] == True:
                if gblInputs['use_dbmodel'] == True:
                    from shadow_db_routines import averageResultsGroup
                    averageResultsGroup(userInputList[0].definitionFileName,userInputList[0]['resultsGroupId'])
                else:
                    outputFileRoot = userInputList[0]['outputfile']
                    create_average_summary_CSV('./'+outputFileRoot+'.ave_summary.csv',userInputList) 
                    create_average_report_CSV('./'+outputFileRoot+'.ave.csv',userInputList)
                    if userInputList[0]['pricetable'] is not None:
                        create_average_cost_CSV('./'+outputFileRoot+'.ave_cost.csv',userInputList)

            for output in outputList:
                if output is None:
                    print "a run failed, can't create the merged output"
                    return

            # create merged output file
            if gblInputs['average'] == True and gblInputs['use_dbmodel'] == False:
                #mergedOutput = HermesOutput.HermesOutputMerged(outputList)
                mergedOutput.writeOutputs()
                if gblInputs['save_hdata'] is not None:
                    mergedOutput.save(gblInputs['save_hdata'])

        if gapFinalize:
            import HermesGap
            #if simCount > 1:
                #mergedOutput = HermesOutput.HermesOutputMerged(outputList)
            HermesGap.HermesGap(userInputList, unifiedInput, gblInputs, outputList, mergedOutput)
                
        if gblInputs['minion']:
            sys.__stderr__.write('#finished#\n')


def _mergeOutput(mergedOutput, output, num):
    import HermesOutput
    if output is None:
        print "a run failed, can't create the merged output"
        return None

    if mergedOutput is None:
        if num != 0:
            return None
    
        return HermesOutput.HermesOutputMerged([output])
    
    mergedOutput.mergeNewOutput(output)
    return mergedOutput
        

                    
#BUG: This should really be in HermesOutput and should probably not exist in this form.
# ie this is just a duplication of the first part of the code so the two should be merged some how.
def ValidatePostSimInputs(userInput):
    from util import openDataFullPath
    from csv_tools import parseCSV, castColumn, castTypes
    customOutputs = userInput['customoutput']
    if customOutputs is None:
        return
    for output in customOutputs:
        with openDataFullPath(output) as f:
            keys,lines = parseCSV(f)
        castColumn(lines, 'function', castTypes.STRING)
        castColumn(lines, 'field', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'field2', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'name', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'val', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'hide', (castTypes.EMPTY_IS_NONE, castTypes.STRING))

        
            
            
                          
            
############
# Main hook
############

if __name__=="__main__":
    if sys.platform.startswith('win'):
        multiprocessing.freeze_support()
    try:
        main()
    except Exception,e:
        print '-'*60
        print 'Exception: %s'%e
        print '-'*60
        traceback.print_exc(file=sys.stderr)


        
