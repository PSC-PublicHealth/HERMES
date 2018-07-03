#!/usr/bin/env python




__doc__=""" model_niger_generic.py
This is a variant of the Niger model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id: model_chad.py 948 2012-05-04 01:52:22Z welling $"

import sys,os,getopt,types,math

import warehouse, vaccinetypes
import model_generic
import abstractbaseclasses

class Model(model_generic.Model):

    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)   
