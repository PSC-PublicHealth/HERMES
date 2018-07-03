#!/usr/bin/env python



__doc__=""" sampler.py
This class encapsulates a mechanism for drawing a sample from a statistical
distribution.  We have historically used Poisson samples; the goal here is
to provide more generality.
"""

_hermes_svn_id_="$Id$"

import sys, math, random, unittest, StringIO
import util

class Sampler:
    """
    This is a base Sampler class; it is not expected to be directly instantiated by the user.
    It encapsulates a mechanism for drawing a sample from a statistical distribution.
    """
    def __init__(self):
        pass
    def __str__(self):
        return "Sampler"
    def draw(self, expectation,randomNumberGenerator):
        raise RunTimeError('Sampler.draw was called; expected a derived class')
    def cdf(self,mu,k):
        """
        Return the cumulative distribution function for this sampler with parameter
        mu and integration limit k
        """
        raise RunTimeError('Sampler.probOfZeroDraw was called; expected a derived class')
    
class PoissonSampler(Sampler):
    """
    This class encapsulates the drawing of a sample from a Poisson distribution.
    """
    def __init__(self):
        Sampler.__init__(self)
    def __str__(self):
        return "PoissonSampler"
    def __repr__(self):
        return "PoissonSampler()"
    def draw(self,expectation,randomNumberGenerator):
        return util.poisson(expectation,rNG=randomNumberGenerator)
    def cdf(self,mu,k):
        """
        Return the cumulative distribution function for this sampler with parameter
        mu and integration limit k
        """
        kfloor = int(math.floor(k))
        assert kfloor>=0, "Tried to take the Poisson CDF of a negative value"
        assert mu>=0, "cdf parameter mu = %s is invalid"%mu
        term = sum = 1.0
        if kfloor>0:
            for i in xrange(1,kfloor+1):
                term *= mu/i
                sum += term
        return sum *math.exp(-mu)
    
class GaussianSampler(Sampler):
    """
    This class encapsulates the drawing of a sample from a Gaussian distribution.  The
    standard deviation is specified as a fraction of the expectation value- not the
    usual situation for statisticians, but handy for us.
    """

    # These values are for use in the Abramowitz&Stegun approximation to the standard normal CDF
    b0 = 0.2316419
    b1 = 0.319381530
    b2 = -0.356563782
    b3 = 1.781477937
    b4 = -1.821255978
    b5 = 1.330274429
    
    def __init__(self,sigmaFrac,nonNegative=True):
        """
        sigmaFrac is the standard deviation as a fraction of the expectation; for example,
        an expectation of 10.0 will produce a sample of (10.0 + N(0.0,sigmaFrac*10.0)) .
        """
        Sampler.__init__(self)
        assert sigmaFrac > 0.0, "invalid sigmaFrac %s"%sigmaFrac
        self.sigmaFrac= sigmaFrac
        self.nonNegative= nonNegative
    def __str__(self):
        return "GaussianSampler(%g)"%self.sigmaFrac
    def __repr__(self):
        return "GaussianSampler(%g)"%self.sigmaFrac
    def draw(self,expectation,randomNumberGenerator):
        v= expectation+randomNumberGenerator.normalvariate(0.0,expectation*self.sigmaFrac)
        if self.nonNegative:
            return max(v,0.0) 
        else:
            return v
    def _norm_pdf(self,x):
        """
        This is the PDF of the standard normal distribution
        """
        # 0.3989422804014327 is 1/sqrt(2pi)
        return 0.3989422804014327*math.exp(-0.5*x*x)
    def pdf(self,mu,k):
        invSigma = 1.0/(self.sigmaFrac * mu)
        return invSigma*self._norm_pdf(invSigma*(k-mu))
    def _norm_cdf(self,x):
        """
        We use Abramowitz&Stegun's algorithm for the CDF, thanks to Wikipedia.
        """
        if x>=0.0:
            t = 1.0/(1.0+GaussianSampler.b0*x)
            phi = 1.0 - (self._norm_pdf(x)*( (((((GaussianSampler.b5
                                                  * t + GaussianSampler.b4)
                                                 * t + GaussianSampler.b3)
                                                * t + GaussianSampler.b2)
                                               * t + GaussianSampler.b1)
                                              * t) ))
            return phi
        else:
            return 1.0 - self._norm_cdf(-x)
    def cdf(self,mu,k):
        """
        Return the cumulative distribution function for this sampler with parameter
        mu and integration limit k
        """
        invSigma = 1.0/(self.sigmaFrac * mu)
        return self._norm_cdf(invSigma*(k-mu))

class ConstantSampler(Sampler):
    """
    This class draws from a constant distribution.  That is, the value drawn is always
    exactly equal to the expectation.
    """
    def __init__(self):
        """
        Samples drawn with this sampler are always exactly equal to the expectation.
        """
        Sampler.__init__(self)
    def __str__(self):
        return "ConstantSampler"
    def __repr__(self):
        return "ConstantSampler()"
    def draw(self,expectation,randomNumberGenerator):
        return expectation
    def cdf(self,mu,k):
        """
        Return the cumulative distribution function for this sampler with parameter
        mu and integration limit k
        """
        if mu<=k: return 1.0
        else: return 0.0

def describeSelf():
    print \
"""
Testing options:

  test1

     runs a series of tests

  test2

     test CDFs

"""

def main(myargv = None):
    "Provides a few test routines"
    
    if myargv is None:
        myargv = sys.argv

    rng= random.Random()
    rng.seed(1234)
    if len(myargv)<2:
        describeSelf()
    elif myargv[1]=="test1":
        if len(myargv)==2:
            for sampler in [PoissonSampler(), GaussianSampler(0.1), ConstantSampler()]:
                print "Sampler type %s:"%sampler
                print "Drawing 1000 samples"
                sList= [sampler.draw(100.0,rng) for i in xrange(1000)]
                mean= math.fsum(sList)/len(sList)
                devList= [(x-mean)*(x-mean) for x in sList]
                stdv= math.sqrt(math.fsum(devList)/(len(devList)-1))
                print "   mean= %g"%mean
                print "   stdv= %g"%stdv
        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="test2":
        if len(myargv)==2:
            for sampler in [PoissonSampler(), GaussianSampler(0.1), ConstantSampler()]:
                print "Sampler type %s:"%sampler
                print "Drawing 100000 samples"
                sList= [sampler.draw(10.0,rng) for i in xrange(100000)]
                nLow = sum([1 for s in sList if s<=9.0])
                nHigh = sum([1 for s in sList if s>9.0])
                print "nLow: %s High: %s"%(nLow,nHigh)
                cdfVal = sampler.cdf(10.0,9.0)
                sampledCdfVal = float(nLow)/(nLow+nHigh)
                print "cdf: %f prediced vs. %f by sampling"%(cdfVal,sampledCdfVal)
                if cdfVal==sampledCdfVal or abs(cdfVal-sampledCdfVal)/sampledCdfVal < 0.03:
                    print '%s: PASS'%sampler
                else:
                    print '%s: FAIL'%sampler
        else:
            print "Wrong number of arguments!"
            describeSelf()
    else:
        describeSelf()
                

class TestSampler(unittest.TestCase):
    def getReadBackBuf(self, wordList):
        try:
            sys.stdout = myStdout = StringIO.StringIO()
            main(wordList)
        finally:
            sys.stdout = sys.__stdout__
        return StringIO.StringIO(myStdout.getvalue())
    
    def compareOutputs(self, correctStr, readBack):
        correctRecs = StringIO.StringIO(correctStr)
        for a,b in zip(readBack.readlines(), correctRecs.readlines()):
            #print "<%s> vs. <%s>"%(a,b)
            self.assertTrue(a.strip() == b.strip())
    
    def test_sampler_1(self):
        correctStr = """Sampler type PoissonSampler:
Drawing 1000 samples
   mean= 100.07
   stdv= 9.98884
Sampler type GaussianSampler(0.1):
Drawing 1000 samples
   mean= 100.065
   stdv= 9.86044
Sampler type ConstantSampler:
Drawing 1000 samples
   mean= 100
   stdv= 0
        """
        readBack= self.getReadBackBuf(['dummy','test1'])
        self.compareOutputs(correctStr, readBack)

    def test_sampler_2(self):
        correctStr = """Sampler type PoissonSampler:
Drawing 100000 samples
nLow: 45916 High: 54084
cdf: 0.457930 prediced vs. 0.459160 by sampling
PoissonSampler: PASS
Sampler type GaussianSampler(0.1):
Drawing 100000 samples
nLow: 15961 High: 84039
cdf: 0.158655 prediced vs. 0.159610 by sampling
GaussianSampler(0.1): PASS
Sampler type ConstantSampler:
Drawing 100000 samples
nLow: 0 High: 100000
cdf: 0.000000 prediced vs. 0.000000 by sampling
ConstantSampler: PASS
        """
        readBack= self.getReadBackBuf(['dummy','test2'])
        self.compareOutputs(correctStr, readBack)

############
# Main hook
############

if __name__=="__main__":
    main()
