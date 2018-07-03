
_hermes_svn_id_="$Id$"

import multiprocessing
import zipfile
import os
import traceback
import os.path
import sys
import time
import pickle
from contextlib import closing

globDict = {'newDir' : '/home/jim/mnt/hermes/workq/new/',
            'processingDir' : '/home/jim/mnt/hermes/workq/processing/',
            'finishedDir' : '/home/jim/mnt/hermes/workq/finished/',
            'errorDir' : '/home/jim/mnt/hermes/workq/error/',
            'tempDir' : '/tmp/',
            'hermesCmd' : 'python /home/jim/projects/hermes/workq/HERMES2/main.py',
            'workers' : 5}

def smallerOutput(oldOutput, newOutput, hdataPrefix):
    """
    Create an output zipfile from another zipfile without the hdata files
    """
    with closing(zipfile.ZipFile(newOutput, "w", zipfile.ZIP_DEFLATED)) as zo:
        with closing(zipfile.ZipFile(oldOutput)) as zi:
            for fileName in zi.namelist():
                if fileName.startswith(hdataPrefix):
                    continue
                data = zi.read(fileName)
                zo.writestr(fileName, data)

def tempName(baseName, sim):
    return globDict['tempDir'] + baseName + '_' + str(sim) + '.zip'

def procName(baseName, sim):
    return globDict['processingDir'] + baseName + '_' + str(sim) + '.zip'
def finalName(baseName, sim):
    return globDict['finishedDir'] + baseName + '_' + str(sim) + '.zip' 


# since multiprocessing doesn't implement a heap/priority queue, we're going to
# muck around with having two queues, one of which has (imperfect) priority over the other.
# the other way of handling this would be to have the main process specifically manage and 
# dole out processes one at a time to the individual workers.

def worker(arg):
    (jobQ,finalQ,doneQ) = arg
    g =  globDict

    while True:
        while True:
            try:
                (f, sim, finalize) = finalQ.get(False)
                break
            except:
                pass
            try: 
                (f, sim, finalize) = jobQ.get(False)
                break
            except:
                pass
            time.sleep(1)

            
        #(f, sim, finalize) = jobQ.get()
        print "found job on the queue"
        try:
            fInput = g['processingDir'] + f
            if finalize:
                fOut = procName(f,'output')
                cmd = g['hermesCmd'] + ' --use_zip=%s --zip_outputs=%s --merge_outputs'%(fInput,tempName(f,sim))
                for i in xrange(sim):
                    cmd += ' ' + tempName(f,i)
                print "calling " + cmd
                os.system(cmd)
                smallerOutput(tempName(f,sim), fOut, 'hermes_output')
                for i in xrange(sim+1):
                    print "removing " + tempName(f,i)
                    os.unlink(tempName(f,i))
                print "renaming " + fOut + " to " + finalName(f,'output')
                os.rename(fOut, finalName(f, 'output'))
            else:
                fOut = tempName(f,sim)
                cmd = g['hermesCmd'] + ' --use_zip=%s --run_number=%d --zip_outputs=%s'%(fInput,sim,fOut)
                print "calling " + cmd 
                os.system(cmd)
        finally:
            doneQ.put((f,sim,finalize))



newFileDict = {}
def getNewFiles():
    g = globDict
    global newFileDict
    nfd = newFileDict

    ret = []
    files = os.listdir(g['newDir'])
    for f in files:
        fqf = g['newDir'] + f
        if not os.path.isfile(fqf):
            continue
        s = os.stat(fqf)
        if s.st_size == 0:
            continue
        if f in nfd:
            if nfd[f] == s.st_size:
                ret.append(f)
                del(nfd[f])
                os.rename(fqf, g['processingDir'] + f)
            else:
                nfd[f] = s.st_size
        else:
            nfd[f] = s.st_size

    return ret

        

def main():
    g = globDict
    jobQ = multiprocessing.Queue()
    finalQ = multiprocessing.Queue()
    doneQ = multiprocessing.Queue()
    simTab = {}

    for i in xrange(g['workers']):
        p = multiprocessing.Process(target=worker, args=((jobQ,finalQ,doneQ),))
        p.daemon = True
        p.start()

    while True:
        time.sleep(10)
        try:
            fileList = getNewFiles()
            for f in fileList:
                print "found file " + f
                try:
                    with zipfile.ZipFile(g['processingDir'] + f) as z:
                        pickledStats = z.read('input_stats')
                        stats = pickle.loads(pickledStats)
                    print stats
                    ic = stats['inputCount']
                    ic = int(ic)
                except:
                    os.rename('%s%s'%(g['processingDir'],f), '%s%s'%(g['errorDir'], f))
                    errorFile(f)
                simTab[f] = [ic,ic]
                for i in xrange(ic):
                    jobQ.put((f,i,False))
        except:
            pass

        try:
            while True:
                (f,sim,finalize) = doneQ.get_nowait()
                if finalize:
                    print "moving %s%s to %s%s"%(g['processingDir'],f,g['finishedDir'], f)
                    os.rename('%s%s'%(g['processingDir'],f), '%s%s'%(g['finishedDir'], f))
                else:
                    simTab[f][1] -= 1
                    if simTab[f][1] == 0:
                        finalQ.put((f,simTab[f][0],True))
                        del(simTab[f])

        except:
            pass
        
        











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

