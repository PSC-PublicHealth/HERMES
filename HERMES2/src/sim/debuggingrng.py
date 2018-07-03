#! /usr/bin/env python


"""
This is intended to be a plug-in substitute for a random.Random for use in debugging
the use pattern of random number generators
"""

_hermes_svn_id_="$Id$"

import sys, random, types

debug= False
#debug= True

dbgName= None
count= 0

def msg(s):
    global debug, dbgName, count
    if debug: 
        #print "%s at %s %d"%(s,dbgName,count)
        sys.stderr.write("%s at %s %d\n"%(s,dbgName,count))
    count += 1

class DebugRandom(random.Random):
    def __init__(self,name):
        self.name= name
        msg('#### constructor %s'%self.name)
        random.Random.__init__(self)
    def seed(self, a=None):
        msg('#### seed %s %s'%(self.name,a))
        random.Random.seed(self,a)
    def jumpahead(self,n):
        msg('#### jumpahead %s %s'%(self.name,n))
        random.Random.jumpahead(self,n)
    def normalvariate(self,mu,sigma):
        v= random.Random.normalvariate(self,mu,sigma)
        msg('#### normalvariage %s %s %s -> %s'%(self.name,mu,sigma,v))
        return v
    def gauss(self,mu,sigma):
        v= random.Random.gauss(self,mu,sigma)
        #global debug
        #if str(v)=='121.550338958': debug= True
        #elif debug: raise RuntimeError('Ending ondition met')
        global debug
        if str(v)=='9406.44112065': debug= True
        msg('#### gauss %s %s %s -> %s'%(self.name,mu,sigma,v))
        return v
    def random(self):
        global debug
        v= random.Random.random(self)
        #if str(v)=='0.438416613241': debug= True
        #elif debug and str(v)=='0.566369126984': raise RuntimeError('Ending condition met')
        msg('#### random -> %s %s'%(self.name,v))
        #if str(v)=='0.781919937308': 
        #    raise RuntimeError('Here I am!')
        return v
    def betavariate(self, alpha, beta):
        v= random.Random.betavariate(self,alpha,beta)
        msg('#### betavariate %s %s %s -> %s'%(self.name,alpha,beta,v))
        return v
    def choice(self, seq):
        v= random.Random.choice(self,seq)
        msg('#### choice %s -> %s'%(self.name,v))
        return v
    def expovariate(self, lamd):
        v= random.Random.expovariate(self,lamd)
        msg('#### expovariate %s %s -> %s'%(self.name,lamd,v))
        return v
    def gammavariate(self, alpha, beta):
        v= random.Random.gammavariate(self,alpha,beta)
        msg('#### gammavariate %s %s %s -> %s'%(self.name,alpha,beta,v))
        return v
    def lognormvariate(self,mu,sigma):
        v= random.Random.lognormvariate(self,mu,sigma)
        msg('#### lognormvariage %s %s %s -> %s'%(self.name,mu,sigma,v))
        return v
    def paretovariate(self, alpha):
        v= random.Random.paretovariate(self,alpha)
        msg('#### paretovariate %s %s -> %s'%(self.name,alpha,v))
        return v
    def randint(self, a, b):
        v= random.Random.randint(self,a,b)
        msg('#### randint %s %s %s -> %s'%(self.name,a,b,v))
        return v
    def randrange(self, start, stop=None, step=1):
        v= random.Random.randint(self,a,b)
        msg('#### randrange %s %s %s %s -> %s'%(self.name,start,stop,step,v))
        return v
    def sample(self,population,k):
        v= random.Random.sample(self,population,k)
        msg('#### sample %s %s -> %s'%(self.name,k,v))
        return v
    def getstate(self):
        v= random.Random.state(self)
        msg('#### getstate %s -> %s'%(self.name,v))
        return v
    def setstate(self,state):
        msg('#### setstate %s %s-> nothing',self.name,state)
        random.Random.setstate(self,state)
    def shuffle(self,x,random=None,int=types.IntType):
        v= random.Random.shuffle(self,x,random,int)
        msg('#### shuffle %s -> %s'%(self.name,x,v))
        return v
    def triangular(self,low=0.0,high=1.0,mode=None):
        v= random.Random.triangular(self,low,high,mode)
        msg('#### triangular %s %s %s %s -> %s'%(self.name,low,high,mode,v))
        return v
    def uniform(self, a, b):
        v= random.Random.uniform(self,a,b)
        msg('#### uniform %s %s %s -> %s'%(self.name,a,b,v))
        return v
    def vonmisesvariate(self,mu,kappa):
        v= random.Random.vonmisesvariate(self,mu,kappa)
        msg('#### vonmisesvariate %s %s %s -> %s'%(self.name,mu,kappa,v))
        return v
    def weibullvariate(self,alpha,beta):
        v= random.Random.weibullvariate(self,alpha,beta)
        msg('#### weibullvariate %s %s %s -> %s'%(self.name,alpha,beta,v))
        return v

        
        
