#!/usr/bin/env python
__doc__=""" demandmodel.py
A map between a collection of people and their vaccine needs. 
"""

########################################################################
# Copyright C 2010, Pittsburgh Supercomputing Center (PSC).            #
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

_hermes_svn_id_="$Id$"

import sys, types, random, util, unittest, StringIO, re
import csv_tools
import abstractbaseclasses
from peopletypes import genericPeopleTypeName
import sampler as SamplerModule
import math
import vaccinetypes
import fridgetypes
import trackabletypes
from util import listify
import shadow_network as shd
import copy
import globals as G

class DemandModel:
    """
    A map between a collection of people and their vaccine needs.
    """
    def __init__(self,sim,recDict={},sampler=None):
        """
        This is the base class; the user is not expected to instantiate
        this type directly.  The constructor parameters are:

        recDict: a dictionary {v:rec, ...}
          where v is a VaccineType and rec is itself a dict
          of form {PeopleType:nDosesPerPerson,...}

        ****************************************
        ***                                  ***
        ***   READ THIS BEFORE SUBCLASSING   ***
        ***                                  ***
        ****************************************
        A Note on Subclassing DemandModel
        Regarding control flow for getDemand(), it is expected
        by many of the subclasses that the base class getDemand() 
        will be called which will start by calling the top level
        getDemandExpectation().  Thus the top level getDemandExpectation()
        must get registered with the lowest level.

        Both getDemand() and getDemandExpectation() expect to have
        the following arguments: self, peopleCollection, deltaTime, 
        timeNow=None and **kwargs.  **kwargs is necessary for
        subclassing for when the base level getDemand() calls the
        top level getDemandExpectation().


        Expected calls are:
        __init__()
        __str__(self)
        __repr__(self)
        registerTopGDE(self,gde)
        getVaccineTypeNameList(self)
        getDemandExpectation(self,peopleCollection,deltaTimeDays,timeNow=None, **kwargs)
        getDemand(self,peopleCollection,deltaTime,timeNow=None, **kwargs)

        """
        self.sim= sim
        if sampler==None:
            self.sampler= SamplerModule.PoissonSampler()
        else:
            self.sampler= sampler
        # self.gde is the top level getDemandExpectation that will be called by getDemand()
        self.gde = self.getDemandExpectation
        
        self.recDict = recDict
        self.perfectfied = False
        
    def __str__(self):
        st= ""
        for v,d in self.recDict.items():
            st += "%s:%s,"%(v.name,d)
        st= st[:-1]
        return "<DemandModel(%s)>"%st
    def __repr__(self):
        st= ""
        for v,d in self.recDict.items():
            st += "%s:%s,"%(v.name,d)
        st= st[:-1]
        return "<DemandModel(%s),sampler=%s>"%(st,repr(self.sampler))

    def getSampler(self):
        """
        Provided to make duck-typed derived classes a little more convenient.
        """
        return self.sampler

    def registerTopGDE(self, gde):
        self.gde = gde
        pass
    
    def setPerfectCanStore(self):
        if self.perfectfied:
            return
        for v in self.recDict.keys():
            if isinstance(v,abstractbaseclasses.CanStoreType):
                vPerfect = self.sim.tms['fridges'].getPerfectFridge(v)
                recTemp = copy.copy(self.recDict[v])
                self.recDict[vPerfect] = recTemp
                for rec in self.recDict[v].keys():
                    #print str(self.recDict[v][rec])
#                    print "ReC = " + str(rec)
                    self.recDict[v][rec] = 0.0
            #rec = self.recDict[v]
        self.perfectfied = True
        for key,rec in self.recDict.items():
            print str(key) + ": " + str(rec)          
    def getVaccineTypeNameList(self):
        """
        Returns a list of the name strings of the vaccine types known
        to this DemandModel.
        """
        return [v.name for v in self.recDict.keys()]
    
    
    def getDemandExpectation(self,peopleCollection,deltaTimeDays,timeNow=None, **kwargs):
        """
        Produce a VaccineCollection giving an estimate of the number
        of doses for each vaccine type given the number of people in
        the input PeopleCollection.  Dose counts in the result are
        expected to be floating point numbers; for example an
        expectation of 3.51 doses of some VaccineType is perfectly
        reasonable.  deltaTimeDays is the interval over which demand
        accumulates, for example the time since the clinic was last
        open.
        """
        vtList= []
        for v in self.recDict.keys():
            rec= self.recDict[v]

            doseTot= 0.0
            if isinstance(v,abstractbaseclasses.NonScalingType):
                for peopleType,nDosesPerPerson in rec.items():
                    nPeopleThisType = peopleCollection[peopleType]
                    doseTot += nDosesPerPerson*nPeopleThisType
            else:
                for peopleType,nDosesPerPerson in rec.items():
                    nPeopleThisType = peopleCollection[peopleType]
                    doseTot += nDosesPerPerson*nPeopleThisType*deltaTimeDays
            vtList.append((v,doseTot))
        return self.sim.shippables.getCollection(vtList)

    def getDemandExpectationVials(self, peopleCollection, groupingInterval,
                                  deltaTimeDays, timeNow=None, **kwargs):
        """
        Produce a VaccineCollection giving an estimate of the number
        of VIALS for each vaccine type given the number of people in
        the input PeopleCollection.  Vial counts in the result are
        expected to be floating point numbers; for example an
        expectation of 3.51 vials of some VaccineType is perfectly
        reasonable.

        groupingInterval is the interval for the consuming process, which presumably groups
                      people into sessions.  For example, this might be the interval of the
                      consuming UseVials process.
        deltaTimeDays is the interval over which demand accumulates, for example the time since
                      the last order was shipped.
        timeNow is the time to assume for the calculation, defaulting to sim.now()
        """
        dosesVC = self.getDemandExpectation(peopleCollection, deltaTimeDays, timeNow=timeNow, **kwargs)
        nIntervalsDict = {}
        for v,mu in dosesVC.items():
            if hasattr(v,"lifetimeOpenDays"):
                nIntervalsDict[v] = max(1.0,float(deltaTimeDays)/float(max(float(groupingInterval),float(v.getLifetimeOpenDays()))))
            else:
                nIntervalsDict[v] = max(1.0,float(deltaTimeDays)/float(groupingInterval)) # a float
        vialCounts = []
        for v,mu in dosesVC.items():
            if mu>0.0:
                if isinstance(v, abstractbaseclasses.NonScalingType):
                    vialCounts.append((v,mu))                    
                else:
                    nIntervals = nIntervalsDict[v]
                    muPerGroup = mu/nIntervals
                    pZero = self.getSampler().cdf(muPerGroup,0)
                    scaledMu = muPerGroup/(1.0-pZero) # since the remaining draws must make up the same mean
                    nNonZero = nIntervals*(1.0-pZero)
                    vialsPerNonZeroSession = math.ceil(max(1.0,scaledMu/v.getNDosesPerVial()))
                    #print "v: %s mu: %f muPerGroup: %f pZero: %f scaledMu: %f vialsPer: %f nNonZero: %f"%\
                    (v.name,mu,muPerGroup,pZero,scaledMu,vialsPerNonZeroSession,nNonZero)
                    vialCounts.append((v,vialsPerNonZeroSession*nNonZero))
        return self.sim.shippables.getCollection(vialCounts)
    
    def getDemand(self,peopleCollection,deltaTime,timeNow=None, **kwargs):
        """
        Like getDemandExpectation(), but returns an actual instance of
        the random variable in question.  For example, if for some
        VaccineType the expectated number of doses was 3.51, the
        VaccineCollection produced by this method might be 3 or 4.
        Integer outputs are expected.
        """
        vc= self.gde(peopleCollection,deltaTime, timeNow=timeNow, **kwargs)
        if(self.sim.staticDemand):
            return self.sim.shippables.getCollection([(v,int(self.sim.randomRounder.round(e)))  for v,e in vc.items()])
        else:
            l= []
            for v,e in vc.items():
                if isinstance(v,vaccinetypes.VaccineType):
                    l.append((v,int(round(self.sampler.draw(e,v.rndm)))))
                else:
                    l.append((v,int(round(e))))
            return self.sim.shippables.getCollection(l)

#hmm, this doesn't _actually_ have to subclass DemandModel
class ScaleVaxDemandModel(DemandModel):
    """
    This demand model scales the Vaccine demand of another demand model by a set of factors.
    it _only_ scales the vaccines (leaving non-vax types alone).
    """
    def __init__(self, demandModel, scaleActual=1.0, scaleExpected=1.0):
        self.demandModel = demandModel
        self.scaleActual = float(scaleActual)
        self.scaleExpected = float(scaleExpected)
        demandModel.registerTopGDE(self.getDemandExpectation)
    
    def __str__(self):
        return "<ScaleVaxDemandModel(%s, scaleActual=%f, scaleExpected=%f)>"\
            %(self.demandModel, self.scaleActual, self.scaleExpected)

    def __repr__(self):
        return "<ScaleVaxDemandModel(%s, scaleActual=%f, scaleExpected=%f)>"\
            %(self.demandModel, self.scaleActual, self.scaleExpected)

    def setPerfectCanStore(self):
        for v in self.demandModel.recDict.keys():
            print str(v)
    def getSampler(self):
        return self.demandModel.getSampler()
    
    def registerTopGDE(self, gde):
        self.demandModel.registerTopGDE(gde)

    def getVaccineTypeNameList(self):
        return self.demandModel.getVaccineTypeNameList()

    def getDemandExpectation(self, *args, **kwargs):
        c = self.demandModel.getDemandExpectation(*args, **kwargs)
        vax = c.splitOut(vaccinetypes.VaccineType)
        if 'scaleFactor' in kwargs:
            sf = kwargs['scaleFactor']
        else:
            sf = self.scaleExpected
        #print "scaling vax demand by %f"%sf
        vax *= sf
        return c + vax

    def getDemandExpectationVials(self, *args, **kwargs):
        c = self.demandModel.getDemandExpectationVials(*args, **kwargs)
        vax = c.splitOut(vaccinetypes.VaccineType)
        if 'scaleFactor' in kwargs:
            sf = kwargs['scaleFactor']
        else:
            sf = self.scaleExpected
        #print "scaling vax demand by %f"%sf
        vax *= sf
        return c + vax

    def getDemand(self, *args, **kwargs):
        kwargs['scaleFactor'] = self.scaleActual
        return self.demandModel.getDemand(*args, **kwargs)

class ScaleVaxDemandByTypeModel(DemandModel):
    """
    This model scales the demand of another demand model by a linear factor but scaled by type.
    """
    def __init__(self, sim, demandModel, scaleActualList=None, scaleExpectedList=None):
        self.demandModel = demandModel
        self.sim = sim
        self.scaleActualList = listify(scaleActualList)
        self.scaleExpectedList = listify(scaleExpectedList)
        self.scalingActual =   self._convertScaleList(self.scaleActualList)
        self.scalingExpected = self._convertScaleList(self.scaleExpectedList)
        demandModel.registerTopGDE(self.getDemandExpectation)

    def _convertScaleList(self, scaleList):
        scaleList = listify(scaleList)

        types = {}
        
        # is there ever a demand for storage, trucks or people?
        for typeManager in [self.sim.vaccines, self.sim.fridges]: #, self.storage, self.trucks, self.people]:
            for t in typeManager.getActiveTypes():
                types[t.name] = t
                        
        ret = {}

        for line in scaleList:
            (t,f) = line.split(':',1)
            f = float(f)
            if t in types:
                ret[types[t]] = f
            else:
                pass
                #raise RuntimeError("type %s unknown in request for demand scaling"%t)
        return ret


    def __str__(self):
        return "<ScaleVaxDemandByTypeModel(%s)>"%self.demandModel

    def __repr__(self):
        return "<ScaleVaxDemandByTypeModel(%s, scaleActual=%s, scaleExpected=%s)>"\
            %(self.demandModel, self.scaleActualList, self.scaleExpectedList)

    def setPerfectCanStore(self):
        self.demandModel.setPerfectCanStore()

    def getSampler(self):
        return self.demandModel.getSampler()
    
    def registerTopGDE(self, gde):
        self.demandModel.registerTopGDE(gde)

    def getVaccineTypeNameList(self):
        return self.demandModel.getVaccineTypeNameList()

    def getDemandExpectation(self, *args, **kwargs):
        c = self.demandModel.getDemandExpectation(*args, **kwargs)

        if 'typeScaleFactor' in kwargs:
            sf = kwargs['typeScaleFactor']
        else:
            sf = self.scalingExpected

        for k in c.keys():
            if k in sf:
                #print "scaling %f of %s by %f"%(c[k], k.name, sf[k])
                c[k] *= sf[k]

        return c

    def getDemandExpectationVials(self, *args, **kwargs):
        c = self.demandModel.getDemandExpectationVials(*args, **kwargs)

        if 'typeScaleFactor' in kwargs:
            sf = kwargs['typeScaleFactor']
        else:
            sf = self.scalingExpected

        for k in c.keys():
            if k in sf:
                #print "scaling %f of %s by %f"%(c[k], k.name, sf[k])
                c[k] *= sf[k]

        return c

    def getDemand(self, *args, **kwargs):
        kwargs['typeScaleFactor'] = self.scalingActual
        return self.demandModel.getDemand(*args, **kwargs)

class SumDemandModel(DemandModel):
    """
    This demand model simply combines the demand of the DemandModels passed to
    its constructor.  
    """
    def __init__(self,demandModelList):
        if len(demandModelList)<2:
            raise RuntimeError("SumDemandModel needs at least two sub-models to sum!")
        sim= demandModelList[0].sim
        assert all([dm.sim==sim for dm in demandModelList]),"Tried to mix demand models from different simulations!"
        DemandModel.__init__(self,sim)
        self.demandModelList= demandModelList
        self.typeNameList= []
        for dm in self.demandModelList:
            l= dm.getVaccineTypeNameList()
            if l.name not in self.typeNameList:
                self.typeNameList.append(l.name)

    def getVaccineTypeNameList(self):
        """
        Returns a list of the name strings of the vaccine types known
        to this DemandModel.
        """
        return self.typeNameList

    def __str__(self):
        st= ""
        for dm in self.demandModelList:
            st += "%s,"%str(dm)
        st= st[:-1] # drop trailing comma
        return "<SumDemandModel(%s)>"%st

    def __repr__(self):
        st= ""
        for dm in self.demandModelList:
            st += "%s,"%repr(dm)
        st= st[:-1] # drop trailing comma
        return "<SumDemandModel([%s],sampler=%s)>"%(st,repr(self.sampler))

    def getSampler(self):
        raise RuntimeError("getSampler is not implemented for SumDemandModel")
    
    def getDemandExpectation(self,peopleCollection,deltaTimeDays, timeNow=None, **kwargs):
        """
        Produce a VaccineCollection giving an estimate of the number
        of doses for each vaccine type given the number of people in
        the input PeopleCollection.  Dose counts in the result are
        expected to be floating point numbers; for example an
        expectation of 3.51 doses of some VaccineType is perfectly
        reasonable.  deltaTimeDays is the interval over which demand
        accumulates, for example the time since the clinic was last
        open.
        """

        # this could be rewritten in one line as reduce but I don't want
        # to think about it right now.

        vc= self.demandModelList[0].getDemandExpectation(peopleCollection, deltaTimeDays, timeNow, **kwargs)
        for dm in self.demandModelList[1:]:
            vc += dm.getDemandExpectation(peopleCollection, deltaTimeDays, timeNow, **kwargs)
        return vc

    def getDemandExpectationVials(self,peopleCollection, groupingInterval,
                                  deltaTimeDays, timeNow=None, **kwargs):
        """
        Produce a VaccineCollection giving an estimate of the number
        of vials for each vaccine type given the number of people in
        the input PeopleCollection.  Vial counts in the result are
        expected to be floating point numbers; for example an
        expectation of 3.51 vials of some VaccineType is perfectly
        reasonable.  deltaTimeDays is the interval over which demand
        accumulates, for example the time since the clinic was last
        open.
        """

        # this could be rewritten in one line as reduce but I don't want
        # to think about it right now.

        vc= self.demandModelList[0].getDemandExpectationVials(peopleCollection, groupingInterval, 
                                                              deltaTimeDays, timeNow, **kwargs)
        for dm in self.demandModelList[1:]:
            vc += dm.getDemandExpectationVials(peopleCollection, groupingInterval,
                                               deltaTimeDays, timeNow, **kwargs)
        return vc

class SimpleDemandModel(DemandModel):
    """
    This demand model is for backward compatibility.  It produces a
    demand by 'generic people' equal to the total number of doses
    required for each vaccine type.
    """
    def __init__(self,sim,vaccineTypeNameList,daysPerYear,sampler=None):
        """
        The parameter vaccineTypeNameList is simply a list of names of
        all vaccine types to be included in the simulation.  Sim is
        the current HermesSim instance.
        """
        recDict= {}
        genericPeople= sim.people.getTypeByName(genericPeopleTypeName)
        for vN in vaccineTypeNameList:
            v= sim.shippables.getTypeByName(vN)
            if isinstance(v,vaccinetypes.VaccineType):
                recDict[v]= {genericPeople:float(v.dosesPerPerson)/daysPerYear}
        DemandModel.__init__(self,sim,recDict,sampler=sampler)
                                                       
class TabularDemandModel(DemandModel):
    """
    This demand model is read from a .csv file.  The column names of
    the file must include 'VaccineType' and the names of
    specific known PeopleTypes, and may also include 'Notes'. The
    'VaccineType' column of each row must be a known vaccine type
    name; the entries for each PeopleType are expected demand per
    year for that VaccineType and PeopleType.
    """
    def __init__(self, sim, fnameOrFile, daysPerYear, sampler=None,
                 demandType='U'):
        """
        fnameOrFile must be the name of a .csv file or an open .csv file.
        The column names of the file must include 'VaccineType' and the
        names of specific known PeopleTypes, and may also include 'Notes'.
        The 'VaccineType' column of each row must be a known vaccine type
        name; the entries for each PeopleType are expected demand per
        year for that VaccineType and PeopleType.
        """
        if isinstance(fnameOrFile,types.StringType):
            self.demandFname= fnameOrFile
        else:
            self.demandFname= "*Unknown*"
        if sim.shdNet is not None:
            keyList, recList = sim.shdNet.getDemandRecs(demandType)
        else:
            with util.openFileOrHandle(fnameOrFile) as f:
                keyList,recList= csv_tools.parseCSV(f)
        recDict= {}
        peopleTypeList= []
        if not 'VaccineType' in keyList:
            raise RuntimeError("Demand file %s has no column for VaccineType"%self.demandFname)
        for k in keyList:
            if k not in ['VaccineType','Notes']:
                if sim.people.validTypeName(k):
                    peopleTypeList.append(sim.people.getTypeByName(k))
                    csv_tools.castColumn(recList, k,
                                         [csv_tools.castTypes.CastFloat, csv_tools.castTypes.CastEmptyIsZero], 
                                         self.demandFname)
                else:
                    raise RuntimeError("Demand file %s specifies invalid PeopleType %s"%\
                                       (self.demandFname,k))
        for rec in recList:
            vN= rec['VaccineType']
            v= sim.shippables.getTypeByName(vN)
            if not isinstance(v,abstractbaseclasses.ShippableType):
                raise RuntimeError("The demand model includes demand for %s, which is not shippable."%vN)
            
            if recDict.has_key(v):
                raise RuntimeError("Demand file %s has duplicate entries for %s"%(self.demandFname,vN))
            vacDict= {}
            if isinstance(v,abstractbaseclasses.NonScalingType):
                # Demand for fridges gets special treatment
                for k,r in rec.items():
                    if k not in ['VaccineType','Notes']: 
                        pType= sim.people.getTypeByName(k)
                        vacDict[pType]= r
            else:
                for k,r in rec.items():
                    if k not in ['VaccineType','Notes']: 
                        pType= sim.people.getTypeByName(k)
                        vacDict[pType]= float(r)/daysPerYear
            if len(vacDict)==0:
                raise RuntimeError("Cannot find any actual PeopleTypes in %s"%self.demandFname)
            recDict[v]= vacDict
        DemandModel.__init__(self,sim,recDict,sampler=sampler)
        self.peopleTypeList= peopleTypeList
        
    def __str__(self):
        return "<TabularDemandModel(\'%s\')>"%(self.demandFname)

    def __repr__(self):
        return "<TabularDemandModel(\'%s\',sampler=%s)>"%(self.demandFname,repr(self.sampler))

class CatchupDemandModel(TabularDemandModel):
    """
    This demand model is intended to be used for catchup campaigns.
    For this demand model, two .csv files are needed.
    
    The __init__ parameter sim is the current instance of hermes.HermesSim .
    The filename is that of a .csv file.  The column names of
    the file must include 'VaccineType' and the names of
    specific known PeopleTypes, and may also include 'Notes'. The
    'VaccineType' column of each row must be a known vaccine type
    name; the entries for each PeopleType are expected demand per
    year for that VaccineType and PeopleType.  This file must include
    all of the dosage parameters for the catchup campaign recipients.
    
    The second file is a .csv file denotes the population to add for the 
    catchup campaign, and this needs to be implemented at this point on a 
    model by model basis.  See AddedCatchup in model_thailand for more information
    
    """
    def __init__(self,sim,demandFname,cudemandFname,vaccineNamesForCatchup,
                 catchupNumberOfDays,catchupStartDay,daysOfSimulation,daysPerYear,
                 sampler=None):
        raise RuntimeError("CatchupDemandModel has been deprecated")
#        TabularDemandModel.__init__(self,sim,demandFname,daysPerYear,sampler=sampler)
#
#        self.catchupDemandFileName = cudemandFname
#        self.vaccineNamesForCatchup = vaccineNamesForCatchup
#        self.catchupStartDay = catchupStartDay
#        self.catchupNumberOfDays = catchupNumberOfDays
#        self.rateFactor = float(daysPerYear)/float(self.catchupNumberOfDays)
#        self.catchupEndDay = self.catchupStartDay + self.catchupNumberOfDays
        
#     def getDemandExpectation(self,peopleCollection,deltaTimeDays,timeNow=None):
#         """
#         Produce a VaccineCollection giving an estimate of the number
#         of doses for each vaccine type given the number of people in
#         the input PeopleCollection.  Dose counts in the result are
#         expected to be floating point numbers; for example an
#         expectation of 3.51 doses of some VaccineType is perfectly
#         reasonable.  deltaTimeDays is the interval over which demand
#         accumulates, for example the time since the clinic was last
#         open.
#         """
#         if timeNow is None:
#             timeNow = self.sim.now()
            
#         vtList= []
#         for v in self.recDict.keys():
#             rec= self.recDict[v]
#             doseTot= 0.0
#             if isinstance(v,vaccinetypes.VaccineType):
#                 # Let's do the regular demand first
#                 for peopleType,nDosesPerPerson in rec.items():
#                     if str(peopleType).count('cu_') is 0:
#                         nPeopleThisType= peopleCollection[peopleType]
#                         doseTot += nDosesPerPerson*nPeopleThisType*deltaTimeDays
                
#                 if v.name in self.vaccineNamesForCatchup:
#                     for peopleType,nDosesPerPerson in rec.items():
#                         ## Need to determine how much of the current order is 
#                         ## a part of the demand
#                         if str(peopleType).count('cu_') == 1:
#                             nPeopleThisType = peopleCollection[peopleType]
#                             portionOfDeltaDays = -1000.0
#                             dayStart = timeNow
#                             dayEnd = timeNow + deltaTimeDays
#                             if dayStart > self.catchupEndDay or dayEnd < self.catchupStartDay:
#                                 ## No days overlap with catchup period
#                                 portionOfDeltaDays = 0.0
#                             else:
#                                 overlapStart = max(dayStart,self.catchupStartDay)
#                                 overlapEnd = min(dayEnd,self.catchupEndDay)
#                                 portionOfDeltaDays = float(float(overlapEnd-overlapStart)/float(deltaTimeDays))
#                             doseTot += nDosesPerPerson*self.rateFactor*portionOfDeltaDays*nPeopleThisType*deltaTimeDays          
#             else:
#                 for peopleType,nDosesPerPerson in rec.items():
#                     nPeopleThisType= peopleCollection[peopleType]
#                     doseTot += nDosesPerPerson*nPeopleThisType
#             vtList.append((v,doseTot))
#         return self.sim.vaccines.getCollection(vtList)
    
    
class TabularCalendarScaleDemandModel(TabularDemandModel):
    """
    This demand model is read from two .csv files, a demand file and a calendar
    file.  Each can be given by either a filename or an open file object.
    The column names of the demand file must include 'VaccineType' and
    the names of specific known PeopleTypes, and may also include 'Notes'. The
    'VaccineType' column of each row must be a known vaccine type
    name; the entries for each PeopleType are expected demand per
    year for that VaccineType and PeopleType.
    
    The second file acts as a calendar to scale the first.  It should contain
    the column 'StartDate', columns for some or all of the population types
    from the first file, and optionally a column 'Notes'.  The entries in the
    spreadsheet give the fraction of the yearly demand which is to occur 
    between this start date and the next (or the cycle time).  For example,
    if a row has a StartDate of 28, the next StartDate or the cycle time
    is 56, and the value for a given vaccine is 0.2, the demand for that
    28 day period will be (0.2*daysPerYear)/(56-28) times the
    baseline demand specified by the demand spreadsheet.  There is no
    checking to make sure that the total demand over the course of a year
    adds up to what is specified in the demand file; that is the user's
    responsibility.
    """
    def __init__(self,sim,demandFname,calendarFname,cycleTimeDays,daysPerYear,sampler=None, 
                 demandType='U'):
        """
        The __init__ parameter sim is the current instance of hermes.HermesSim .
        The filenames are that of a pair of .csv files, the demand file and the
        calendar file.  cycleTimeDays is the interval over which the entire
        pattern repeats.
        
        The column names of the file must include 'VaccineType' and the names of
        specific known PeopleTypes, and may also include 'Notes'. The
        'VaccineType' column of each row must be a known vaccine type
        name; the entries for each PeopleType are expected demand per
        year for that VaccineType and PeopleType.
        
        The second file acts as a calendar to scale the first.  It should
        contain the column 'StartDate', columns for some or all of the
        population types from the first file, and optionally a column 'Notes'.
        The entries in the spreadsheet give the fraction of the yearly demand
        which is to occur between this start date and the next (or the cycle
        time).  For example, if a row has a StartDate of 28, the next StartDate
        or the cycle time is 56, and the value for a given vaccine is 0.2, the
        demand for that 28 day period will be
        (0.2*daysPerYear)/(56-28) times the baseline demand specified
        by the demand spreadsheet.  There is no checking to make sure that the
        total demand over the course of a year adds up to what is specified in
        the demand file; that is the user's responsibility.
        
        demandType is for loading from the ShdNet structure.  It should be one
        of shd.DemandEnums.TYPE_* .  Without this it would be difficult (though 
        not impossible) to determine which calendar recs to use here.
        """
        TabularDemandModel.__init__(self,sim,demandFname,daysPerYear,sampler=sampler,
                                    demandType=demandType)
        if isinstance(calendarFname,types.StringType):
            self.calendarFname= calendarFname
        else:
            self.calendarFname= "*Unknown*"
        self.cycleTimeDays= cycleTimeDays
        self.daysPerYear= daysPerYear
        if sim.shdNet is not None:
            keyList,recList = sim.shdNet.getCalendarRecs(demandType)
        else:
            with util.openFileOrHandle(calendarFname) as f:
                keyList,recList= csv_tools.parseCSV(f)
        if not 'StartDate' in keyList:
            print keyList
            raise RuntimeError('Calendar file %s has no column for StartDate'%self.calendarFname)
        calendarRecArray= []
        for k in keyList:
            if k not in ['StartDate','Notes'] \
                   and not sim.people.validTypeName(k):
                raise RuntimeError("Calendar file %s specifies invalid PeopleType %s"%\
                                   (self.calendarFname,k))
        for rec in recList:
            sDate= float(rec['StartDate'])
            thisDict= {}
            for k,v in rec.items():
                if k not in ['StartDate','Notes']: 
                    pType= sim.people.getTypeByName(k)
                    if pType in self.peopleTypeList:
                        thisDict[pType]= v
            calendarRecArray.append((sDate,thisDict))
        calendarRecArray.sort()
        
        # Reformat the calendar so that it matches the interval 0.0-to-cycletime
        nEntries= len(calendarRecArray)
        firstValid= 0
        lastValid= None
        for i in xrange(nEntries):
            date, _= calendarRecArray[i]
            if date<=0.0: firstValid= i
            if date<=cycleTimeDays: lastValid= i
        if firstValid>=nEntries-1 or lastValid is None:
            raise RuntimeError("There are no valid dates in %s - all are less than zero or greater than the cycle time"%\
                               self.calendarFname)
        # Patch the start time of the front of the array
        date,vDict= calendarRecArray[firstValid]
        if date>0.0:
            if firstValid>0: 
                firstValid -= 1
                date,vDict= calendarRecArray[firstValid]
            calendarRecArray[firstValid]= (0.0,vDict)
        # Patch the start time of the end of the array
        if lastValid==nEntries-1:
            # Copy first record to the end of the list
            date,vDict= calendarRecArray[firstValid]
            calendarRecArray.append((cycleTimeDays,vDict))
            lastValid += 1
        else:
            # Use a segment of the interval which includes the cycle end
            lastValid += 1
            date,vDict= calendarRecArray[lastValid]
            calendarRecArray[lastValid]= (cycleTimeDays,vDict)
        # Keep only the valid part of the array
        calendarRecArray= calendarRecArray[firstValid:lastValid]
        newRecArray= []
        for i in xrange(len(calendarRecArray)):
            startDate,vDict= calendarRecArray[i]
            endDate,_= calendarRecArray[(i+1)%len(calendarRecArray)]
            if endDate>startDate:
                interval= endDate-startDate
            else:
                interval= cycleTimeDays-startDate
            newRecArray.append((startDate,interval,vDict))
        self.calendarRecArray= newRecArray

    def __str__(self):
        return "<TabularCalendarScaleDemandModel(\'%s\',\'%s\')>"%(self.demandFname,self.calendarFname)
            
    def __repr__(self):
        return "<TabularCalendarScaleDemandModel(\'%s\',\'%s\',sampler=%s)>"%\
               (self.demandFname,self.calendarFname,repr(self.sampler))

    def _getCalSegmentList(self, timeNow, deltaTimeDays):
        """
        The calendar describes a series of intervals, with constant demand in each interval.
        The goal here is to find all those intervals intersected by the time interval
        from timeNow to timeNow+deltaTimeDays and return an appropriately scaled list of
        calendar entries.

        The format of the return value is [(factor, interval, vDict),...] where vDict is
        a calendar file record, factor is the fraction of the total interval for that record,
        and interval is the total interval for the record.
        """
        calendarDictList = []

        # Break the demand interval into sub-intervals that fit within the calendar cycle
        #print 'timeNow: %s delta: %s cycleTimeDays: %s'%(timeNow,deltaTimeDays,self.cycleTimeDays)
        startCycle = int(math.floor(timeNow/self.cycleTimeDays))
        startOffset = timeNow - (startCycle*self.cycleTimeDays)
        timeEnd = timeNow + deltaTimeDays
        endCycle = int(math.floor(timeEnd/self.cycleTimeDays))
        endOffset = timeEnd - (endCycle*self.cycleTimeDays)
        #print "Starts on cycle %d offset %f"%(startCycle,startOffset)
        #print "Ends on cycle %d offset %f"%(endCycle,endOffset)
        segList = []
        if endCycle>startCycle:
            segList.append((startOffset,self.cycleTimeDays))
            for _ in xrange(startCycle+1, endCycle):
                segList.append((0.0,self.cycleTimeDays))
            segList.append((0.0, endOffset))
        else:
            segList.append((startOffset,endOffset))
        
        ### Must find all of the intervals within the time that this demand expectation is needed
        
        for startOffset, endOffset in segList:
            #print 'Entry %s %s'%(startOffset, endOffset)
            for date,ivl,vDict in self.calendarRecArray:
                ## If date falls within timeNow and timeNow + deltaTimeDays
                ## Must make sure the interval falls within the sampled period
                endDate   = date + ivl
                if  endDate>=startOffset and ivl!=0.0 and date<=endOffset:
                    beginDate = date
                    beginSamp = startOffset
                    endSamp   = endOffset
                    beginInt  = max(beginDate,beginSamp)
                    endInt    = min(endDate,endSamp)   
                    factor    = float(endInt-beginInt)/float(ivl)
                    #print 'adding %s %s %s'%(factor,ivl,vDict)
                    calendarDictList.append((factor,ivl,vDict))
                if date>endOffset: break

        if not calendarDictList:
            raise RuntimeError("Internal error: cannot find time %g in calendar array")

        return calendarDictList
            
    def getDemandExpectation(self,peopleCollection,deltaTimeDays,timeNow=None,**kwargs):
        """
        Produce a VaccineCollection giving an estimate of the number
        of doses for each vaccine type given the number of people in
        the input PeopleCollection.  Dose counts in the result are
        expected to be floating point numbers; for example an
        expectation of 3.51 doses of some VaccineType is perfectly
        reasonable.  deltaTimeDays is the interval over which demand
        accumulates, for example the time since the clinic was last
        open.
        """
        if timeNow is None:
            timeNow= self.sim.now()
        
        #print "called for %s interval %s"%(timeNow,deltaTimeDays),
        calendarDictList = self._getCalSegmentList(timeNow, deltaTimeDays)

        vtList= []
        for v in self.recDict.keys():
            rec= self.recDict[v]
            doseTot= 0.0
            if isinstance(v,abstractbaseclasses.NonScalingType):
                for peopleType,nDosesPerPerson in rec.items():
                    nPeopleThisType = self.sim.randomRounder.round(peopleCollection[peopleType])
                    doseTot += nDosesPerPerson*nPeopleThisType
            else:
                for peopleType,nDosesPerPerson in rec.items():
                    nPeopleThisType = self.sim.randomRounder.round(peopleCollection[peopleType])
                    scale = None
                    for calEntry in calendarDictList:
                        if calEntry[2].has_key(peopleType):
                            factor = float(calEntry[2][peopleType])*calEntry[0]*self.daysPerYear/deltaTimeDays
                            if scale is None:
                                scale = factor
                            else:
                                scale += factor
                    if scale is None:
                        scale= 1.0
                    doseTot += nDosesPerPerson*scale*nPeopleThisType*deltaTimeDays
            vtList.append((v,doseTot))
        return self.sim.shippables.getCollection(vtList)

    def getDemandExpectationVials(self, peopleCollection, groupingInterval,
                                  deltaTimeDays, timeNow=None, **kwargs):
        """
        Produce a VaccineCollection giving an estimate of the number
        of VIALS for each vaccine type given the number of people in
        the input PeopleCollection.  Vial counts in the result are
        expected to be floating point numbers; for example an
        expectation of 3.51 vials of some VaccineType is perfectly
        reasonable.

        The mathematical shortcut used in the superclass implementation assumes constant
        demand over time, so there is no choice but to re-implement things the hard way
        for Calendar-based DemandModels.

        groupingInterval is the interval for the consuming process, which presumably groups
                      people into sessions.  For example, this might be the interval of the
                      consuming UseVials process.
        deltaTimeDays is the interval over which demand accumulates, for example the time since
                      the last order was shipped.
        timeNow is the time to assume for the calculation, defaulting to sim.now()
        """

        if timeNow is None:
            timeNow= self.sim.now()
        
        #print "timeNow= %s, deltaTimeDays= %s"%(timeNow,deltaTimeDays)
        
        vialCounts= []
        calRecCache = {}
        for v in self.recDict.keys():
            rec= self.recDict[v]

#             if hasattr(v,"lifetimeOpenDays"):
#                 nIntervals = max(1.0,float(deltaTimeDays)/float(max(float(groupingInterval),float(v.getLifetimeOpenDays()))))
#             else:
#                 nIntervals = max(1.0,float(deltaTimeDays)/float(groupingInterval)) # a float
            
            if isinstance(v,abstractbaseclasses.NonScalingType):
                doseTot= 0.0
                for peopleType,nDosesPerPerson in rec.items():
                    nPeopleThisType = self.sim.randomRounder.round(peopleCollection[peopleType])
                    doseTot += nDosesPerPerson*nPeopleThisType
                vialCounts.append((v,int(math.ceil(float(doseTot)/v.getNDosesPerVial()))))
            else:
                tStart = 0.0
                doseTot= 0.0
                liveIntervals = 0
                while tStart<deltaTimeDays:
                    tEnd = tStart + groupingInterval
                    live = False
                    if tStart in calRecCache:
                        calendarDictList = calRecCache[tStart]
                    else:
                        calendarDictList = self._getCalSegmentList(tStart+timeNow, tEnd-tStart)
                        calRecCache[tStart] = calendarDictList
                    for peopleType,nDosesPerPerson in rec.items():
                        nPeopleThisType = self.sim.randomRounder.round(peopleCollection[peopleType])
                        scale = None
                        for calEntry in calendarDictList:
                            if calEntry[2].has_key(peopleType):
                                factor = float(calEntry[2][peopleType])*calEntry[0]*self.daysPerYear/(tEnd-tStart)
                                if scale is None:
                                    scale = factor
                                else:
                                    scale += factor
                        if scale is None: scale= 1.0
                        if scale>0.0: live = True
                        doseTot += nDosesPerPerson*scale*nPeopleThisType*(tEnd-tStart)
                    tStart = tEnd
                    if live: liveIntervals += 1
            
                if doseTot > 0.0:
                    if hasattr(v,"lifetimeOpenDays"):
                        nIntervals = max(1.0,min(float(liveIntervals), float(deltaTimeDays)/float(v.getLifetimeOpenDays())))
                    else:
                        nIntervals = max(1.0,float(liveIntervals)) # a float

                    muPerGroup = doseTot/nIntervals
                    pZero = self.getSampler().cdf(muPerGroup,0) # prob that any session will have 0 clients
                    scaledMu = muPerGroup/(1.0-pZero) # since the remaining draws must make up the same mean
                    nNonZero = nIntervals*(1.0-pZero) # estimated number of non-zero sessions
                    vialsPerNonZeroSession = math.ceil(max(1.0,scaledMu/v.getNDosesPerVial()))
                    #print "v: %s mu: %f muPerGroup: %f pZero: %f scaledMu: %f vialsPer: %f product: %f"%\
                    #      (v.name,doseTot,muPerGroup, pZero,scaledMu,vialsPerNonZeroSession,
                    #       vialsPerNonZeroSession*nNonZero)
                    vialCounts.append((v,vialsPerNonZeroSession*nNonZero))

                else:
                    #print 'v: %s no doses'%v.name
                    pass
            

        return self.sim.shippables.getCollection(vialCounts)

class CalendarStringScaleDemandModel(TabularCalendarScaleDemandModel):
    """
    This demand model is functionally equivalent to a TabularCalendarScaleDemandModel,
    but the .csv file providing the calendar is replaced by a string or
    set of strings providing a simple repeating calendar pattern.  
    The column names of the demand file must include 'VaccineType' and
    the names of specific known PeopleTypes, and may also include 'Notes'. The
    'VaccineType' column of each row must be a known vaccine type
    name; the entries for each PeopleType are expected demand per
    year for that VaccineType and PeopleType.
    
    The format of a calendar string is 'xxxxxxx:xxxx:xxxxxxxxxxxx' where each
    x represents one of the digits '0' or '1'.  The first 7 digits specify a
    pattern which is repeated each week, the second 4 specify a pattern over weeks
    which is repeated each month, and the final 12 specify a value for each 
    month.  For any day of the year (which must be 7*4*12=336 days long), the
    month, week, and day of the week are calculated by applying the appropriate
    modulo operations.  If the digits associated with that day, week, and month
    are all '1', demand is 'on' for that date; otherwise demand is 'off'.  The
    demand rate for the 'on' days is scaled so that the total demand matches
    that specified in the demand csv file.
    
    For example, the pattern 0101010:1111:111111111111 specifies that vaccinations
    will occur on Monday, Wednesday, and Friday of every week in every month.
    The pattern 0101010:1010:111111111111 specifies Monday, Wednesday, Friday service,
    but only during the first and third weeks of every month.
    """
    def __init__(self,sim,demandFname,calendarPattern,daysPerYear,sampler=None, 
                 demandType='U'):
        """
        The __init__ parameter sim is the current instance of hermes.HermesSim .
        The filename is that of a .csv files, the demand file and the
        calendar file.  cycleTimeDays is the interval over which the entire
        pattern repeats.
        
        The column names of the file must include 'VaccineType' and the names of
        specific known PeopleTypes, and may also include 'Notes'. The
        'VaccineType' column of each row must be a known vaccine type
        name; the entries for each PeopleType are expected demand per
        year for that VaccineType and PeopleType.
        
        calendarPattern may be a single calendar pattern string, or a dict
        of calendar pattern strings indexed by PeopleType names.  If a dict
        is used, it is an error for a PeopleType to appear in the demand file but 
        not in the dict.
        
        demandType is for loading from the ShdNet structure.  It should be one
        of shd.DemandEnums.TYPE_* .  Without this it would be difficult (though 
        not impossible) to determine which calendar recs to use here.
        """
        assert daysPerYear==(7*4*12), "Days per year does not match treatment calendar pattern"
        TabularDemandModel.__init__(self,sim,demandFname,daysPerYear,sampler=sampler,
                                    demandType=demandType)
        if isinstance(calendarPattern,types.DictType):
            assert all([(tp.name in calendarPattern) for tp in self.peopleTypeList])
            self.calGenDict = {tp:self._stringToCalGenerator(calendarPattern[tp.name])
                               for tp in self.peopleTypeList}
            self.calStr = '*byPeopleType*'
        else:
            self.calGenDict = {tp:self._stringToCalGenerator(calendarPattern)
                               for tp in self.peopleTypeList}
            self.calStr = calendarPattern
        self.calendarFname= "*None*" # in case parent class accesses it
        self.cycleTimeDays= self.daysPerYear= daysPerYear
        calendarRecArray= []
        for i in xrange(self.daysPerYear):
            tNow = float(i)
            rec = {}
            for tp in self.peopleTypeList:
                t,v = self.calGenDict[tp].next()
                assert t==tNow, "Generator for %s is not synchronized"%tp.name
                rec[tp] = v
            calendarRecArray.append((tNow,1.0,rec))
        for tp,gen in self.calGenDict.items():
            done = False
            try:
                gen.next()
            except StopIteration:
                done = True
            if not done:
                raise RuntimeError('Iterator for %s had too many items!'%tp.name)

        self.calendarRecArray = calendarRecArray        

    def __str__(self):
        return "<CalendarStringScaleDemandModel(\'%s\',\'%s\')>"%(self.demandFname,self.calStr)
            
    def __repr__(self):
        return "<CalendarStringScaleDemandModel(\'%s\',\'%s\',sampler=%s)>"%\
               (self.demandFname,self.calStr,repr(self.sampler))

    def _stringToCalGenerator(self,calString):
        for c in ["'", '"', "'"]:
            if calString.startswith(c) and calString.endswith(c):
                calString = calString.strip(c)
        assert len(re.sub(u'[01:]', '', calString))==0, \
            "Bad characters in calendar string {0}".format(calString)    
        parts = calString.split(':')
        assert len(parts)==3 and len(parts[0])==7 and len(parts[1])==4 and len(parts[2])==12, \
            "Bad format for calendar string {0}".format(calString)
        days = parts[0]
        weeks = parts[1]
        months = parts[2]
        
        daySum = sum([int(n) for n in days])
        assert daySum != 0, "Calendar pattern %s has no active days"%calString
        weekSum = sum([int(n) for n in weeks])
        assert weekSum != 0, "Calendar pattern %s has no active weeks"%calString
        monthSum = sum([int(n) for n in months])
        assert monthSum != 0, "Calendar pattern %s has no active months"%calString
        weight = (1.0/float(daySum))*(1.0/float(weekSum))*(1.0/float(monthSum))
        
        tNow = 0.0
        totWeight = 0.0
        for m in xrange(12):
            for w in xrange(4):
                for d in xrange(7):
                    state = ( int(days[d]) and int(weeks[w]) and int(months[m]) )
                    if state: wHere = weight
                    else: wHere = 0.0
                    #print (tNow,wHere)
                    yield (tNow,wHere)
                    #if state: totWeight += weight
                    tNow += 1.0
        #print 'totWeight = %f'%totWeight

def describeSelf():
    print \
"""
Testing options:

  testSimple

     runs a test of SimpleDemandModel

  testTabular

     runs a test of TabularDemandModel

  testTabular2

     runs a test of TabularDemandModel, with trickier math

  testCalendar

     runs a test of CalendarStringScaleDemandModel

  testCalString

     runs a test of TabularCalendarScaleDemandModel

"""
        
def main(myargv=None):
    "Provides a few test routines"
    import sampler
    import typemanager
    import storagetypes
    import trucktypes
    import icetypes
    import peopletypes
    G.deterministic = True

    class _mockUserInput:
        """
        This is used to mock the sim.userInput parameter needed by DemandModels during testing.
        """
        d = {'dayspermonth':28,
             'mdvp':False
             }
        def getValue(self,k): return main._mockUserInput.d[k]

    class _mockSim:
        """
        This is used to mock the sim parameter needed by DemandModels during testing.
        """
        def __init__(self):
            self.userInput = _mockUserInput()
            self.typeManager= typemanager.TypeManager([], verbose=False, debug=False, sim=self)

            for rec in [{"Name":stn} for stn in storagetypes.storageTypeNames]: 
                self.typeManager.addType(rec, storagetypes.StorageType, False, False)
            self.storage= storagetypes.StorageTypeManager(self.typeManager)
            # Force the storage type names to be active; they are needed in parsing files below.
            for stn in storagetypes.storageTypeNames: self.storage.getTypeByName(stn)

            self.buildTypeRecords([{"Name":"People1","SortOrder":1,"Notes":""},
                                   {"Name":"People2","SortOrder":2,"Notes":""},
                                   {"Name":"People3","SortOrder":3,"Notes":""},
                                   {"Name":"People4","SortOrder":4,"Notes":""},
                                   {"Name":genericPeopleTypeName,"SortOrder":4,"Notes":""}],
                                   peopletypes.PeopleType)
            self.people= peopletypes.PeopleTypeManager(self.typeManager)

            self.typeManager.addType({"Name":"default", "CoolVolumeCC":1.0e9, "Note":"default truck type"},
                                     trucktypes.TruckType, False, False)
            self.trucks= trucktypes.TruckTypeManager(self.typeManager)
            
            self.shippables= trackabletypes.TrackableTypeManager(self.typeManager)
            
            self.shippables.importRecords([([{"Name":"VAC1","DisplayName":"V1",
                                              "Doses per vial":2,"Packed vol/dose(cc) of vaccine":1.23,
                                              "Packed vol/dose(cc) of diluent":4.46,"Doses/person":1,"LifetimeFreezerDays":1.23,
                                              "LifetimeCoolerDays":672,"LifetimeRoomTempDays":0.02,"LifetimeOpenDays":0.25,
                                              "RandomKey":1000},
                                             {"Name":"VAC2","DisplayName":"V2",
                                              "Doses per vial":5,"Packed vol/dose(cc) of vaccine":1.23,
                                              "Packed vol/dose(cc) of diluent":4.46,"Doses/person":2,"LifetimeFreezerDays":1.23,
                                              "LifetimeCoolerDays":672,"LifetimeRoomTempDays":0.02,"LifetimeOpenDays":0.25,
                                              "RandomKey":1000},
                                             {"Name":"VAC3","DisplayName":"V3",
                                              "Doses per vial":10,"Packed vol/dose(cc) of vaccine":1.23,
                                              "Packed vol/dose(cc) of diluent":4.46,"Doses/person":3,"LifetimeFreezerDays":1.23,
                                              "LifetimeCoolerDays":672,"LifetimeRoomTempDays":0.02,"LifetimeOpenDays":0.25,
                                              "RandomKey":1000},
                                             {"Name":"VAC4","DisplayName":"V4",
                                              "Doses per vial":20,"Packed vol/dose(cc) of vaccine":1.23,
                                              "Packed vol/dose(cc) of diluent":4.46,"Doses/person":4,"LifetimeFreezerDays":1.23,
                                              "LifetimeCoolerDays":672,"LifetimeRoomTempDays":0.02,"LifetimeOpenDays":0.25,
                                              "RandomKey":1000}],
                                              vaccinetypes.VaccineType,vaccinetypes.DeliverableVaccineType)])

            self.vaccines= vaccinetypes.VaccineTypeManager(self.typeManager)
            self.ice= icetypes.IceTypeManager(self.typeManager)
            self.fridges= None # to avoid a dependency on userInput in the constructor
            
            self.staticDemand = False
            self.randomRounder = util.RandomRounder(1234)
            self.verbose = False
            self.debug = False
            self.shdNet = None

        def buildTypeRecords(self, recList, whatType):
            for rec in recList: self.typeManager.addType(rec, whatType, False, False)

    def stringFromVC(vc):
        l = [(v.name,v) for v in vc.keys()]
        l.sort()
        l = [v for _,v in l]
        s = ""
        for v in l: s += "%s:%s,"%(v.name,vc[v])
        if len(s): s= s[:-1]
        return s

    if myargv is None: 
        myargv = sys.argv
        
    sim = _mockSim()
    random.seed(1234)
    mySampler = sampler.PoissonSampler()
    if len(myargv)<2:
        describeSelf()
    elif myargv[1]=="testSimple":
        if len(myargv)==2:
            d = SimpleDemandModel(sim, ['VAC1','VAC2','VAC3'], 12*28,sampler=mySampler)
            for v in sim.vaccines.getActiveTypes(): v.randSeed(1234)
            print "str: %s"%str(d)
            print "repr: %s"%repr(d)
            l = d.getVaccineTypeNameList()
            l.sort()
            print "getVaccineTypeNameList: %s"%l
            p1 = sim.people.getTypeByName(genericPeopleTypeName)
            p2 = sim.people.getTypeByName("People2")
            p3 = sim.people.getTypeByName("People3")
            pc = sim.people.getCollection( [(p1,17),(p2,103),(p3,2)] )
            print "demandExpectation: %s"%stringFromVC(d.getDemandExpectation(pc, 75.0,102.0))
            print "demand with staticDemand==False: %s"%stringFromVC(d.getDemand(pc, 75.0,102.0))

        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="testTabular":
        if len(myargv)==2:
            tableF = StringIO.StringIO("""\
"VaccineType","People1","People3","People2","Notes"
"VAC3",1,0,0,
"VAC2",0,2,1,
"VAC1",0,1,0,
""")
            tableF.name = 'mocked'
            d = TabularDemandModel(sim, tableF, 12*28,sampler=mySampler)
            for v in sim.vaccines.getActiveTypes(): v.randSeed(1234)
            print "str: %s"%str(d)
            print "repr: %s"%repr(d)
            l = d.getVaccineTypeNameList()
            l.sort()
            print "getVaccineTypeNameList: %s"%l
            p1 = sim.people.getTypeByName("People1")
            p2 = sim.people.getTypeByName("People2")
            p3 = sim.people.getTypeByName("People3")
            pc = sim.people.getCollection( [(p1,17),(p2,103),(p3,2)] )
            print "demandExpectation: %s"%stringFromVC(d.getDemandExpectation(pc, 75.0,102.0))
            print "demand with staticDemand==False: %s"%stringFromVC(d.getDemand(pc, 75.0,102.0))

        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="testTabular2":
        if len(myargv)==2:
            tableF = StringIO.StringIO("""\
"VaccineType","People1","People2","People3","People4","Notes"
"VAC1",1,0,0,0,
"VAC2",0,1,0,0,
"VAC3",0,0,1,0,
"VAC4",0,0,0,1,
""")
            tableF.name = 'mocked'
            d = TabularDemandModel(sim, tableF, 12*28,sampler=mySampler)
            for v in sim.vaccines.getActiveTypes(): v.randSeed(1234)
            print "str: %s"%str(d)
            print "repr: %s"%repr(d)
            l = d.getVaccineTypeNameList()
            l.sort()
            print "getVaccineTypeNameList: %s"%l
            p1 = sim.people.getTypeByName("People1")
            p2 = sim.people.getTypeByName("People2")
            p3 = sim.people.getTypeByName("People3")
            p4 = sim.people.getTypeByName("People4")
            # The following PC is contrived to put 13 people in the 28 day interval
            pc = sim.people.getCollection( [(p1,13*12),(p2,13*12),(p3,13*12),(p4,13*12)] )
            print "demandExpectation: %s"%stringFromVC(d.getDemandExpectation(pc, 28.0,103.0))
            print '--------------------'
            print "demandExpectationVials, cycle=1: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 28.0, 103.0))
            print "demandExpectationVials, cycle=2: %s"%stringFromVC(d.getDemandExpectationVials(pc, 2.0, 28.0, 103.0))
            print "demandExpectationVials, cycle=4: %s"%stringFromVC(d.getDemandExpectationVials(pc, 4.0, 28.0, 103.0))
            print "demandExpectationVials, cycle=7: %s"%stringFromVC(d.getDemandExpectationVials(pc, 7.0, 28.0, 103.0))
            print '--------------------'
            print "demand with staticDemand==False: %s"%stringFromVC(d.getDemand(pc, 28.0,103.0))

        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="testCalendar":
        if len(myargv)==2:
            tableF = StringIO.StringIO("""\
"VaccineType","People1","People3","People2","Notes"
"VAC3",1,0,0,
"VAC2",0,2,1,
"VAC1",0,1,0,
""")
            tableF.name = 'mocked'
            tableC = StringIO.StringIO("""\
"StartDate","People1","People2","Notes"
0,0.00034722222222222229,0,"20% over 7 days"
7,0.0,0,"0% over 7 days"
14,4.960317460317461e-05,0,"20% over 1 days"
15,0.0,0.0,"0% over 6 days"
21,0.0013888888888888892,0.0,"80% over 7 days"
28,0.0,0.0,"end of cycle"
""")
            tableC.name = 'mocked'
            d = TabularCalendarScaleDemandModel(sim, tableF, tableC, 28, 12*28,sampler=mySampler)
            for v in sim.vaccines.getActiveTypes(): v.randSeed(1234)
            print "str: %s"%str(d)
            print "repr: %s"%repr(d)
            l = d.getVaccineTypeNameList()
            l.sort()
            print "getVaccineTypeNameList: %s"%l
            p1 = sim.people.getTypeByName("People1")
            p2 = sim.people.getTypeByName("People2")
            p3 = sim.people.getTypeByName("People3")
            pc = sim.people.getCollection( [(p1,17),(p2,103),(p3,2)] )
            print "demandExpectation: %s"%stringFromVC(d.getDemandExpectation(pc, 175.0,102.0))
            print '--------------------'
            print "demandExpectationVials, day=84: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 7.0, 84.0))
            print "demandExpectationVials, day=91: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 7.0, 91.0))
            print "demandExpectationVials, day=98: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 7.0, 98.0))
            print "demandExpectationVials, day=105: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 7.0, 105.0))
            print "daily demand vials, day=98: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 98.0))
            print "daily demand vials, day=99: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 99.0))
            print "daily demand vials, day=100: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 100.0))
            print "daily demand vials, day=101: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 101.0))
            print "daily demand vials, day=102: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 102.0))
            print "daily demand vials, day=103: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 103.0))
            print "daily demand vials, day=104: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 104.0))
            print '--------------------'
            print "demand with staticDemand==False: %s"%stringFromVC(d.getDemand(pc, 175.0,102.0))

        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="testCalString":
        if len(myargv)==2:
            tableF = StringIO.StringIO("""\
"VaccineType","People1","People3","People2","Notes"
"VAC3",1,0,0,
"VAC2",0,2,1,
"VAC1",0,1,0,
""")
            tableF.name = 'mocked'
            calStr = '0101010:0101:111111111111'
            d = CalendarStringScaleDemandModel(sim, tableF, calStr, 12*28, sampler=mySampler)
            for v in sim.vaccines.getActiveTypes(): v.randSeed(1234)
            print "str: %s"%str(d)
            print "repr: %s"%repr(d)
            l = d.getVaccineTypeNameList()
            l.sort()
            print "getVaccineTypeNameList: %s"%l
            p1 = sim.people.getTypeByName("People1")
            p2 = sim.people.getTypeByName("People2")
            p3 = sim.people.getTypeByName("People3")
            pc = sim.people.getCollection( [(p1,17),(p2,103),(p3,2)] )
            print "demandExpectation: %s"%stringFromVC(d.getDemandExpectation(pc, 75.0,102.0))
            print '--------------------'
            print "demandExpectationVials, day=84: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 7.0, 84.0))
            print "demandExpectationVials, day=91: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 7.0, 91.0))
            print "demandExpectationVials, day=98: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 7.0, 98.0))
            print "demandExpectationVials, day=105: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 7.0, 105.0))
            print "daily demand vials, day=105: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 105.0))
            print "daily demand vials, day=106: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 106.0))
            print "daily demand vials, day=107: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 107.0))
            print "daily demand vials, day=108: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 108.0))
            print "daily demand vials, day=109: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 109.0))
            print "daily demand vials, day=110: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 110.0))
            print "daily demand vials, day=111: %s"%stringFromVC(d.getDemandExpectationVials(pc, 1.0, 1.0, 111.0))
            print '--------------------'
            print "demand with staticDemand==False: %s"%stringFromVC(d.getDemand(pc, 75.0,102.0))

        else:
            print "Wrong number of arguments!"
            describeSelf()
    else:
        describeSelf()

class TestDemandFuncs(unittest.TestCase):
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
            if a.strip() != b.strip(): 
                print "\nExpected: <%s>"%b
                print "Got:      <%s>"%a
            self.assertTrue(a.strip() == b.strip())
    
    def test_Simple(self):
        correctStr = """str: <DemandModel(VAC1:{<PeopleType(GenericPeople)>: 0.002976190476190476},VAC2:{<PeopleType(GenericPeople)>: 0.0059523809523809521},VAC3:{<PeopleType(GenericPeople)>: 0.0089285714285714281})>
repr: <DemandModel(VAC1:{<PeopleType(GenericPeople)>: 0.002976190476190476},VAC2:{<PeopleType(GenericPeople)>: 0.0059523809523809521},VAC3:{<PeopleType(GenericPeople)>: 0.0089285714285714281}),sampler=PoissonSampler()>
getVaccineTypeNameList: ['VAC1', 'VAC2', 'VAC3']
demandExpectation: VAC1:3.79464285714,VAC2:7.58928571429,VAC3:11.3839285714
demand with staticDemand==False: VAC1:1,VAC2:4,VAC3:9
        """
        readBack= self.getReadBackBuf(['dummy','testSimple'])
        self.compareOutputs(correctStr, readBack)

    def test_Tabular(self):
        correctStr = """str: <TabularDemandModel('*Unknown*')>
repr: <TabularDemandModel('*Unknown*',sampler=PoissonSampler())>
getVaccineTypeNameList: ['VAC1', 'VAC2', 'VAC3']
demandExpectation: VAC1:0.446428571429,VAC2:23.8839285714,VAC3:3.79464285714
demand with staticDemand==False: VAC1:1,VAC2:24,VAC3:1
        """
        readBack= self.getReadBackBuf(['dummy','testTabular'])
        self.compareOutputs(correctStr, readBack)

    def test_Tabular2(self):
        correctStr = """str: <TabularDemandModel('*Unknown*')>
repr: <TabularDemandModel('*Unknown*',sampler=PoissonSampler())>
getVaccineTypeNameList: ['VAC1', 'VAC2', 'VAC3', 'VAC4']
demandExpectation: VAC1:13.0,VAC2:13.0,VAC3:13.0,VAC4:13.0
--------------------
demandExpectationVials, cycle=1: VAC1:10.3996498648,VAC2:10.3996498648,VAC3:10.3996498648,VAC4:10.3996498648
demandExpectationVials, cycle=2: VAC1:8.46835134142,VAC2:8.46835134142,VAC3:8.46835134142,VAC4:8.46835134142
demandExpectationVials, cycle=4: VAC1:11.8143473656,VAC2:5.90717368279,VAC3:5.90717368279,VAC4:5.90717368279
demandExpectationVials, cycle=7: VAC1:7.68980633735,VAC2:3.84490316867,VAC3:3.84490316867,VAC4:3.84490316867
--------------------
demand with staticDemand==False: VAC1:10,VAC2:10,VAC3:10,VAC4:10
        """
        readBack= self.getReadBackBuf(['dummy','testTabular2'])
        self.compareOutputs(correctStr, readBack)

    def test_Calendar(self):
        correctStr = """str: <TabularCalendarScaleDemandModel('*Unknown*','*Unknown*')>
repr: <TabularCalendarScaleDemandModel('*Unknown*','*Unknown*',sampler=PoissonSampler())>
getVaccineTypeNameList: ['VAC1', 'VAC2', 'VAC3']
demandExpectation: VAC1:1.04166666667,VAC2:2.08333333333,VAC3:0.195634920635
--------------------
demandExpectationVials, day=84: VAC1:0.0408105428909,VAC2:0.0799555853707,VAC3:0.00588539061271
demandExpectationVials, day=91: VAC1:0.0408105428909,VAC2:0.0799555853707
demandExpectationVials, day=98: VAC1:0.0408105428909,VAC2:0.0799555853707,VAC3:0.000842898529542
demandExpectationVials, day=105: VAC1:0.0408105428909,VAC2:0.0799555853707,VAC3:0.0233345497435
daily demand vials, day=98: VAC1:0.00593470063028,VAC2:0.011834180589,VAC3:0.000842898529542
daily demand vials, day=99: VAC1:0.00593470063028,VAC2:0.011834180589
daily demand vials, day=100: VAC1:0.00593470063028,VAC2:0.011834180589
daily demand vials, day=101: VAC1:0.00593470063028,VAC2:0.011834180589
daily demand vials, day=102: VAC1:0.00593470063028,VAC2:0.011834180589
daily demand vials, day=103: VAC1:0.00593470063028,VAC2:0.011834180589
daily demand vials, day=104: VAC1:0.00593470063028,VAC2:0.011834180589
--------------------
demand with staticDemand==False: VAC1:1,VAC2:1,VAC3:1
        """
        readBack= self.getReadBackBuf(['dummy','testCalendar'])
        self.compareOutputs(correctStr, readBack)
        
    def test_CalString(self):
        correctStr = """str: <CalendarStringScaleDemandModel('*Unknown*','0101010:0101:111111111111')>
repr: <CalendarStringScaleDemandModel('*Unknown*','0101010:0101:111111111111',sampler=PoissonSampler())>
getVaccineTypeNameList: ['VAC1', 'VAC2', 'VAC3']
demandExpectation: VAC1:0.444444444444,VAC2:23.7777777778,VAC3:3.77777777778
--------------------
demandExpectationVials, day=84: 
demandExpectationVials, day=91: VAC1:0.0799555853707,VAC2:0.988418350039,VAC3:0.507535712325
demandExpectationVials, day=98: 
demandExpectationVials, day=105: VAC1:0.0799555853707,VAC2:0.988418350039,VAC3:0.507535712325
daily demand vials, day=105: 
daily demand vials, day=106: VAC1:0.0273955228837,VAC2:0.773749188826,VAC3:0.2103070746
daily demand vials, day=107: 
daily demand vials, day=108: VAC1:0.0273955228837,VAC2:0.773749188826,VAC3:0.2103070746
daily demand vials, day=109: 
daily demand vials, day=110: VAC1:0.0273955228837,VAC2:0.773749188826,VAC3:0.2103070746
daily demand vials, day=111: 
--------------------
demand with staticDemand==False: VAC1:1,VAC2:24,VAC3:1
        """
        readBack= self.getReadBackBuf(['dummy','testCalString'])
        self.compareOutputs(correctStr, readBack)


############
# Main hook
############

if __name__=="__main__":
    main()
