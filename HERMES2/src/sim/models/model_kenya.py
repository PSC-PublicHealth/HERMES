#!/usr/bin/env python




__doc__=""" model_niger_generic.py
This is a variant of the Niger model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id$"

import sys,os,getopt,types,math

import warehouse, vaccinetypes
import model_generic

class Model(model_generic.Model):

    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)
        #self.levelList = ['Central','Province','District','Health Center']
        #self.centralLevelList = ['Central']
        #self.clinicLevelList = ['Health Center']
        if self.daysPerMonth != 28:
            print RuntimeError("The input variable daypermonth must be set to 28 in order to run the Kenya Model")
        
