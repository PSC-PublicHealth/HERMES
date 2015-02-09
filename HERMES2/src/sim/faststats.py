#!/usr/bin/env python

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

__doc__=""" faststats.py
This module holds miscellaneous utility functions that don't have
a natural home elsewhere.
"""

_hermes_svn_id_="$Id$"

import sys,os,math,types,numpy,scipy,scipy.stats
import matplotlib.pyplot as plt

BCache= {}
lim= 1001

def getBProb_unsafe(p,k,n):
    "We want to return n!/(k!(n-k)!)p^k (1-p)^(n-k) using recursion"
    #print "unsafe: %g %d %d"%(p,k,n)
    a= BCache[p]
    if a[k,n]>=0.0:
        #print "clause 0"
        return a[k,n]
    elif k==1 and n==1:
        #print "clause 1"
        a[1,1]= p
        return p
    elif k==0:
        #print "clause 2"
        a[0,n]= math.pow((1.0-p),n)
        return a[0,n]
    elif a[k,n-1]>=0.0:
        "calc from (n-1)!/(k!(n-(k+1))!)p^k (1-p)^(n-(k+1))"
        #print "clause 3"
        v= (float(n)/float(n-k))*(1.0-p)*a[k,n-1]
        a[k,n]= v
        return v
    elif a[k-1,n]>=0.0:
        "calc from n!/((k-1)!(n+1-k)!)p^(k-1) (1-p)^(n+1-k)"
        #print "clause 4"
        v= (float(n+1-k)/float(k))*(p/(1.0-p))*a[k-1,n]
        a[k,n]= v
        return v
    else:
        "calc from (n-1)!/((k-1)!(n-k)!)p^(k-1)(1-p)^(n-k)"
        #print "clause 5"
        v= (float(n)/float(k))*p*getBProb_unsafe(p,k-1,n-1)
        a[k,n]= v
        return v
        
def getBProb(p,k,n):
    if n>=lim:
        raise RuntimeError("only n up to %d is supported"%(lim-1))
    if k>n:
        raise RuntimeError("k=%d is greater than n=%d"%(k,n))
    if type(k)!=types.IntType or type(n)!=types.IntType:
        raise RuntimeError("k and n must be integers")
    if not BCache.has_key(p):
        a= numpy.zeros((lim,lim))
        a[:,:]= -1.0
        BCache[p]= a
    result= getBProb_unsafe(p,k,n)
    #print BCache[p]
    return result



def main():
    "Provides a few test routines"
    n= 1000
    p= 0.02

    x= numpy.arange(n)
    
    a= numpy.zeros(n)
    b= numpy.zeros(n)
    c= scipy.stats.binom.pmf(x,n,p)
    d= scipy.stats.binom.cdf(x,n,p)
    sum= 0.0
    for i in xrange(n):
        a[i]= getBProb(p,i,n)
        sum += a[i]
        b[i]= sum
        print "%d: %g vs %g -> %g vs %g"%(i,a[i],c[i],sum,d[i])
        if b[i]==b[i-1] and i>0:
            print "done at %d; %g"%(i,b[i])
    h= plt.plot(numpy.arange(n),a,'-',label="pmf")
    h2= plt.plot(numpy.arange(n),b,'--',label="cdf")
    h3= plt.plot(numpy.arange(n),c,'x',label="scipy pmf")
    h4= plt.plot(numpy.arange(n),d,'+',label="scipy cdf")
    plt.legend()
    plt.show()

############
# Main hook
############

if __name__=="__main__":
    main()

