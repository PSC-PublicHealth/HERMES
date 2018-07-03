#!/usr/bin/env python 


__doc__=""" run_unittests.py
This module collects and runs unit tests from other modules, based on the python
module 'unittest'.
"""

_hermes_svn_id_="$Id: run_unittests.py 826 2012-02-16 23:14:57Z welling $"

import sys
import ipath
import unittest

moduleNames = ['util', 'legacycostmodel', 'noteholder', 'sampler', 'reportinghierarchy',
               'kvp_tools', 'demandmodel', 'eventlog', 'packagingmodel']

def main():
    modulesToTest = []
    if len(sys.argv)>1:
        for a in sys.argv[1:]:
            if a in moduleNames: 
                modulesToTest.append(__import__(a))
            else:
                print 'Unknown module %s'%a
    else:
        modulesToTest = [__import__(a) for a in moduleNames]
            
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for m in modulesToTest:
        suite.addTests( loader.loadTestsFromModule(m) )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

############
# Main hook
############

if __name__=="__main__":
    main()

