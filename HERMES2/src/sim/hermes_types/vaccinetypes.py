#!/usr/bin/env python

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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


__doc__=""" vaccinetypes.py
This module produces object instances which know the characteristics of
different types of vaccines.
"""

_hermes_svn_id_="$Id$"

import sys,math,types,random
from abstractbaseclasses import Shippable, GroupedShippable, GroupedShippableType, Trackable, Costable
from abstractbaseclasses import Deliverable, DeliverableType, HasOVW
import storagetypes
import packagetypes
import trackabletypes
import storagemodel
import warehouse 
import util
from enums import TimeUnitsEnums
from enums import StorageTypeEnums as ST

allVaccineTypes= [] #: List of all VaccineType instances
activeVaccineTypes= [] #: List of currently active VaccineType instances
_dosesToVialsVC= None 
_vialsToDosesVC= None 

class VaccineGroup(GroupedShippable,Trackable, Costable):
    "Represents a group of vials of the same type with the same history"
    def __init__(self, nVials, vaccineType, storage, storeWithDiluent, name=None, currentAge=0.0, tracked=False, history=1):
        """This constructor is not meant to be called by the user- use VaccineType.createInstance(wh) instead!"""
        if name is None:
            name= vaccineType.sim.getUniqueString("%s_vg"%vaccineType.name)
        if type(nVials) != types.IntType:
            raise RuntimeError("VaccineGroup creation with non-integer nVials")
        if nVials<0:
            raise RuntimeError("Init negative size group: %s of type %s has %d vials"%(name,vaccineType,nVials))
        super(VaccineGroup,self).__init__()
        self.nVials= nVials
        self.vaccineType= vaccineType
        self.currentAge= currentAge
        self.creationTime = self.ageCurrentAtTime= self.vaccineType.sim.now()
        self.storage= storage
        self.storeWithDiluent = storeWithDiluent
        self.name= name
        self.tracked= tracked
        self.history= history # we will encode split history in this int
        self.debug= False
        self.place= None # not currently owned by anything
        self.tags= set()
        if self.history==1:
            self.maybeTrack("creation")
    @staticmethod
    def makeBitString(i):
        result= ""
        while i>0:
            if i&1: result= "1"+result
            else: result= "0"+result
            i= i>>1
        return result
    def maybeTrack(self,info):
        if self.tracked and self.currentAge is not None:
            print '\n%g, "%s", "%s"\n'%(self.vaccineType.sim.now(),self,info)
    def updateAge(self):
        timeNow= self.vaccineType.sim.now()
        if self.ageCurrentAtTime==timeNow: 
            return
        else:
            if self.place is None: 
                raise RuntimeError('The vaccine group %s spent %g days in no place, ending at time %f'%\
                                    (self.getUniqueName(),(timeNow-self.ageCurrentAtTime),timeNow))
            newAge= self.vaccineType.updateAge(self.currentAge,
                                               timeNow-self.ageCurrentAtTime,
                                               self.storage,
                                               self.nVials)
            if newAge is None and self.currentAge is not None:
                self.maybeTrack("expired")
                if self.place is not None and hasattr(self.place,'noteHolder') and self.place.noteHolder is not None:
                    self.place.noteHolder.addNote({'%s_expired'%self.vaccineType.name:self.nVials})
                self.getAge= lambda: None
            self.currentAge= newAge
            self.ageCurrentAtTime= timeNow
    def __repr__(self):
        return "<VaccineGroup(%d,%s,%s,%s,%s,%s,%s,%#x)>"%(self.nVials,
                                                           repr(self.vaccineType),
                                                           repr(self.storage.name),
                                                           self.packageType,
                                                           self.bName,
                                                           self.currentAge,
                                                           self.tracked,
                                                           self.history)
    def __str__(self):
        return "<VaccineGroup(%d,%s,%s,%s,%s,%#x,%s)>"%(self.nVials,
                                                        str(self.vaccineType),
                                                        str(self.storage.name),
                                                        self.packageType,
                                                        self.bName,
                                                        self.history,
                                                        self.currentAge)
    def getStatus(self):
        return "%d vials, age %s, storage %s"%(self.nVials,self.currentAge,
                                               self.storage.name)
    def getAge(self):
        "This will return None for expired VaccineGroups"
        self.updateAge()
        return self.currentAge
    def merge(self,otherVaccineGroup):
        raise RuntimeError("Merging groups is no longer supported")
        #if self.getAge() != otherVaccineGroup.getAge():
        #    raise RuntimeError("Can't merge %s and %s; age mismatch"%\
        #                           (self,otherVaccineGroup))
        #self.nVials += otherVaccineGroup.nVials
        #if otherVaccineGroup.tracked: self.tracked= True
        #otherVaccineGroup.nVials= 0
        #otherVaccineGroup.storage= None
    def split(self,nVials):
        assert self.nVials>nVials ,"%s: Can't take %d vials from %d"%\
               (self,nVials,self.nVials)
        if self.tracked:
            trackNew= False
            self.history= self.history<<1
            newHistory= self.history+1
            if self.tracked:
                frac= float(nVials)/float(self.nVials)
                if self.vaccineType.rndm.random()<frac:
                    trackNew= True
                    self.tracked= False
            newGroup = self.vaccineType.createInstance(0,self.name,self.getAge(),tracked=trackNew) # 0 count prevents double counting
            newGroup.nVials = nVials
            newGroup.setStorage( self.storage, self.getStorageOtherData() )
            newGroup.setPackageType( self.packageType )
            newGroup.creationTime = self.creationTime
            newGroup.history = newHistory
            self.nVials -= nVials
            if self.place is not None: newGroup.attach(self.place,None)
            newGroup.setArrivalTime( self.getArrivalTime() )
            if self.nVials==0:
                raise RuntimeError("Split to empty group %s"%self)
            if self.debug:
                newGroup.debug= self.debug
                print "%s split: %d -> %d + %s, history %s"%\
                      (self.name,nVials+self.nVials,self.nVials,
                       newGroup,self.makeBitString(newHistory))
            newGroup.maybeTrack("split_new")
            self.maybeTrack("split_old")
        else:
            self.history= self.history<<1
            newGroup = self.vaccineType.createInstance(0,self.name,self.getAge(),tracked=False) # 0 count prevents double counting
            newGroup.nVials = nVials
            newGroup.setStorage( self.storage, self.getStorageOtherData() )
            newGroup.setPackageType( self.packageType )
            newGroup.creationTime = self.creationTime
            newGroup.history = self.history+1
            self.nVials -= nVials
            if self.place is not None: newGroup.attach(self.place, None)
            newGroup.setArrivalTime( self.getArrivalTime() )
            if self.debug:
                newGroup.debug= self.debug
                print "####%s split: %d -> %d + %s, history %s"%\
                      (self.name,nVials+self.nVials,self.nVials,
                       newGroup,self.makeBitString(self.history))
        return newGroup
    def setStorage(self,storage,storeWithDiluent):
        self.storeWithDiluent = storeWithDiluent
        if self.storage != storage:
            self.updateAge() 
            self.storage= storage
            self.maybeTrack("stored")
    def getStorage(self):
        return self.storage
    def getStorageOtherData(self):
        """Returns 'other' storage data, in this case the value of withDiluent"""
        return self.storeWithDiluent
    def getStorageVolume(self, storageType, withDiluent):
        """
        Output is in CCs.  This is the total volume needed to store this VaccineGroup,
        including packaging.
        """
        if self.packageType is None: # implied singleton package
            return self.getCount()*self.getType().getSingletonStorageVolume(withDiluent)
        else:
            totVol = 0.0
            n = self.getCount()
            pT = self.packageType
            while pT is not None and n>0:
                nPkg = int(n/pT.count)
                totVol += nPkg * pT.volumeCC
                n -= nPkg*pT.count
                pT = pT.getNextSmaller()
            totVol += n * self.getType().getSingletonStorageVolume(withDiluent)
            return totVol
    def kill(self):
        raise RuntimeError("VaccineGroup.kill() is no longer necessary")
        pass
    def attach(self, place, callingProc):
        assert self.place is None, "%s:%d is already attached"%(self.name,self.history)
        self.place= place
        place.attachStock(self)
    def detach(self, callingProc):
        assert self.place is not None, "%s:%x is not attached"%(self.name,self.history)
        self.place.detachStock(self)
        self.place= None
    def getType(self):
        return self.vaccineType
    def getCount(self):
        return self.nVials
    def getUniqueName(self):    
        """
        Provides an opportunity for the class to give a more unique response when the '.name' attribute is
        not unique.
        """ 
        return "%s:0x%x"%(self.name,self.history)
    def setTag(self,tag):
        """
        tag can be any hashable- set the tag to 'true'.  Tags which have never been set are false.
        """
        self.tags.add(tag)
    def clearTag(self,tag):
        """
        tag can be any hashable- set the tag to 'false'.  Tags which have never been set are false.
        """
        self.tags.discard(tag)
    def getTag(self,tag):
        """
        tag can be any hashable- return true if that tag has been set, false if it has been cleared or never was set.
        """
        return tag in self.tags
    def getTagList(self):
        """
        return a list of all true tags.
        """
        return [t for t in self.tags]
    def getPendingCostEvents(self):
        return []

class DeliverableVaccineGroup(VaccineGroup, Deliverable):
    def __init__(self, nVials, vaccineType, storage, storeWithDiluent, name, currentAge, tracked, history):
        VaccineGroup.__init__(self, nVials, vaccineType, storage, storeWithDiluent, name, currentAge, tracked, history)
        Deliverable.__init__(self)

    def _allocateGroups(self, groupList, desiredVC, debug=False):
        if debug:
            print "_allocateGroups: getting %s from %s"%([(v.name,n) for v,n in desiredVC.items()],
                                                         [(g.getType().name,g.getCount()) for g in groupList])
        result= []
        for v,nDesired in desiredVC.items():
            if nDesired==0: continue
            candidates= [g for g in groupList 
                         if g.getType()==v and not g.getTag(Shippable.DO_NOT_USE_TAG)]
            for g in candidates:
                #print 'considering %s %s'%(g.getType().name,g.getCount())
                if g.getAge() is None: 
                    #print 'hit expired group %s %s'%(g.getType().name,g.getCount())
                    continue # skip expired vials
                elif g.getCount()>nDesired:
                    #print 'covered %d clause 1'%nDesired
                    result.append(g.split(nDesired))
                    nDesired = 0
                    break
                elif g.getCount()==nDesired:
                    #print 'covered %d clause 2'%nDesired
                    result.append(g)
                    groupList.remove(g)
                    nDesired = 0
                    break
                else:
                    #print 'covered %d clause 3'%g.getCount()
                    result.append(g)
                    groupList.remove(g)
                    nDesired -= g.getCount()
            if nDesired>0:
                # Failed to cover this request
                groupList += result
                if debug: 
                    print "_allocateGroups: failed to find groups for %s in %s"%\
                    ([(v.name,n) for v,n in desiredVC.items()],[(g.getType().name,g.getCount()) for g in groupList])
                return None,groupList
        if debug:
            print "_allocateGroups: took %s leaving %s"%([(g.getType().name,g.getCount()) for g in result],
                                                         [(g.getType().name,g.getCount()) for g in groupList])
        return result, groupList
        
    def prepForDelivery(self, shippableList ):
        """
        Using material from shippableList, prepare this Deliverable for delivery.  The method returns a
        tuple of lists, (listOfUnusedShippables, listOfConsumedShippables).  The former list contains
        input shippables from shippableList which were not needed to prep this Deliverable; the latter
        contains shippables which were used up in the process.
        """
        reqSC = self.vaccineType.getRequiredToPrepSC(self.getCount())
        if reqSC.totalCount() > 0:
            consumeThese,shippableList= self._allocateGroups(shippableList, reqSC)
            if consumeThese is None:
                raise Deliverable.PrepFailure("%d*%s"%(self.getCount(),self.getType().name))
            else:             
                return shippableList, consumeThese
        else:
            return shippableList, []

GroupedShippable.register(DeliverableVaccineGroup) # @UndefinedVariable because PyDev doesn't know about abc.register()
Trackable.register(DeliverableVaccineGroup) # @UndefinedVariable because PyDev doesn't know about abc.register()
Costable.register(DeliverableVaccineGroup) # @UndefinedVariable because PyDev doesn't know about abc.register()

class VaccineType(GroupedShippableType, HasOVW):
    typeName= 'vaccine'
    def __init__(self, name, displayName, dosesPerVial, ccPerDose, ccDiluentPerDose,
                 dosesPerPerson, storagePriorityList,
                 freezerFac,coolerFac,roomtempFac,openVialFac,
                 maxAge,lifetimeOpenDays,keepOpenVials=False,rand_key=None, recDict=None):
        """
        dosesPerVial and dosesPerPerson must be integers;
        storagePriorityList is a list of StorageType instances;
        freezerFac, coolerFac, roomtempFac and maxAge are floats
        keepOpenVials is a bool.
        rand_key is an integer or None.  If None, the value will
           be generated from the hash of the vaccine name.  This value
           gives the 'seed offset' of the random number generator for
           this vaccine from the base RNG, so one might want to set 
           different versions of the same vaccine (e.g. Measles and 
           Measles-unidose) to have to same offset.  If this is done AND
           the seed value for the run is kept constant, the same patient
           population will be generated for the two variants of the
           vaccine.
        """
        GroupedShippableType.__init__(self)
        HasOVW.__init__(self)
        self.name= name
        self.dosesPerVial = int(dosesPerVial)
        self.ccPerDose = float(ccPerDose)
        self.ccDiluentPerDose = float(ccDiluentPerDose)
        self.dosesPerPerson = int(dosesPerPerson)
        self.storagePriority = storagePriorityList
        self.freezerFac= float(freezerFac)
        self.coolerFac= float(coolerFac)
        self.roomtempFac= float(roomtempFac)
        self.openVialFac= float(openVialFac)
        self.lifetimeOpenDays = float(lifetimeOpenDays)
        self.maxAge= float(maxAge)
        self.keepOpenVials= bool(keepOpenVials)
        self.displayName = displayName
        self.patientsTreated= 0
        self.patientsApplied= 0
        self.nVialsCreated= 0
        self.nVialsUsedForTreatment= 0
        self.nVialsExpired= 0
        self.nVialsBroken= 0
        self.storageHistoryDict= {}
        self.totalVialKilometers= 0.0
        self.totalVialTravelDays= 0.0
        self.totalKilometers= 0.0
        self.totalTravelDays= 0.0
        self.absoluteNVialsCreated = 0
        self.absoluteNVialsUsedForTreatment = 0
        self.absoluteNVialsExpired = 0
        self.absoluteNVialsBroken = 0
        self.totalTransitHisto = util.HistoVal([])
        self.rndm= random.Random()
        if rand_key is None: self.rndm_jumpahead= hash(self.name)
        else: self.rndm_jumpahead= rand_key
        self.packageTypes = []
        self.activatedFlag = False
        self.recDict = recDict
        allVaccineTypes.append(self)

    @staticmethod
    def _parseLifetime(preface, rec):
        if preface.lower()+'LifetimeUnits' in rec:
            key = preface.lower()+'Lifetime'
            uKey = preface.lower()+'LifetimeUnits'
            assert key in rec, _("Missing or invalid time value in record for {0} lifetime").format(preface)
            tvChar = rec[uKey]
            assert tvChar in TimeUnitsEnums.eStr.keys(), _("Invalid time unit identifier {0} in record for {1} lifetime").format(tvChar,preface)
            units = tvChar
            val = float(rec[key])
            return val,units
        else:
            for k,v in TimeUnitsEnums.eStr.items():
                key = 'Lifetime' +preface + v.capitalize()
                if key in rec.keys():
                    units = k
                    val = float(rec[key])
                    return val,units
            else:
                raise RuntimeError('No %s lifetime info available in %s'%(preface,rec))

    @staticmethod            
    def _parseLifetimeToDays(preface, rec, userInput):
        val, units = VaccineType._parseLifetime(preface, rec)
        if units == 'D': return val
        else:
            daysPerMonth = userInput['dayspermonth']
            twentyEightDayMonths = userInput['twentyeightdaymonths']
            if twentyEightDayMonths and daysPerMonth!=28:
                raise RuntimeError('User inputs for dayspermonth and twentyeightdaymonths do not agree')
            if units == 'M':
                return val*daysPerMonth
            elif units == 'W':
                return val*int(daysPerMonth/4)
            else:
                raise RuntimeError("Time interval identifier '%s' is not valid"%units)
        
    @classmethod
    def fromRec(cls,recDict, typeManager):
        """
        Call the constructor based on an input record dictionary of the type returned
        by csv_tools.parseCSV()
        """
        name = recDict['Name']
        displayName = recDict['DisplayName']
        dosesPerVial = recDict['Doses per vial']
        ccPerDose = recDict['Packed vol/dose(cc) of vaccine']
        if 'Packed vol/dose(cc) of diluent' in recDict:
            ccDiluentPerDose = recDict['Packed vol/dose(cc) of diluent']
            if ccDiluentPerDose=="":
                ccDiluentPerDose= 0 # for vaccines requiring no diluent
        else:
            ccDiluentPerDose= 0 # for vaccines requiring no diluent
        userInput = typeManager.sim.userInput
        lifetimeFreezerDays= VaccineType._parseLifetimeToDays('Freezer', recDict, userInput)
        lifetimeCoolerDays= VaccineType._parseLifetimeToDays('Cooler', recDict, userInput)
        lifetimeRoomTempDays= VaccineType._parseLifetimeToDays('RoomTemp', recDict, userInput)
        lifetimeOpenDays= VaccineType._parseLifetimeToDays('Open', recDict, userInput)
        dosesPerPerson = recDict['Doses/person']
        if recDict.has_key('RandomKey') and recDict['RandomKey']!='': 
            rand_key= int(recDict['RandomKey'])
        else: rand_key= None
        pairList= [(lifetimeFreezerDays,"freezer"),
                   (lifetimeCoolerDays,"cooler"),
                   (lifetimeRoomTempDays,"roomtemperature")]
        pairList.sort(None,None,True)
        storagePriorityList= [ typeManager.getTypeByName(s) for (t,s) in pairList ]
        maxAge,junk= pairList[0]
        freezerFac= float(maxAge)/float(lifetimeFreezerDays)
        coolerFac= float(maxAge)/float(lifetimeCoolerDays)
        roomtempFac= float(maxAge)/float(lifetimeRoomTempDays)
        mdvp = typeManager.sim.userInput.getValue("mdvp")
        openVialFac = float(maxAge)/float(lifetimeOpenDays)
        return cls(name, displayName, dosesPerVial, ccPerDose, ccDiluentPerDose,
                   dosesPerPerson, storagePriorityList,
                   freezerFac,coolerFac,roomtempFac,openVialFac,maxAge,
                   lifetimeOpenDays,mdvp,rand_key=rand_key,recDict=recDict)

    def __repr__(self):
        return "<VaccineType(%s,%d,%g,%d,%s,%g,%g,%g,%g,%g)>"%\
               (self.name,self.dosesPerVial,self.ccPerDose,self.dosesPerPerson,
                self.storagePriority,
                self.freezerFac,self.coolerFac,self.roomtempFac,self.openVialFac,self.maxAge)

    def __str__(self):
        return self.name

    stFac = { ST.STORE_WARM : 'roomtempFac',
              ST.STORE_COOL : 'coolerFac',
              ST.STORE_FREEZE : 'freezerFac',
          }

    def getFac(self, storageType):
        return getattr(self, self.stFac[storageType])

    def canStore(self, storageType):
        try:
            return self.getFac(storageType) < 10.0
        except:
            return False

    def wantStore(self, storageType):
        try: 
            return self.getFac(storageType) < 1.5
        except:
            return False

    def preferredStore(self):
        preferred = None
        facDict = {}
        for st in (ST.STORE_FREEZE, ST.STORE_COOL, ST.STORE_WARM):
            fac = self.getFac(st)
            if fac == 1.0:
                preferred = st
                continue;
            facDict[st] = fac

        return preferred, facDict

    def canKeepOpenVials(self,howLongOpen):
        if self.keepOpenVials:# and howLongOpen<2.0: # keep two days max
            return True
        else:
            return False

    def recordTreatment(self,nTreated,nApplied,nVialsUsedForTreatment):
        self.patientsTreated += nTreated
        self.patientsApplied += nApplied
        self.nVialsUsedForTreatment += nVialsUsedForTreatment
        self.absoluteNVialsUsedForTreatment += nVialsUsedForTreatment

    def recordBreakage(self,nVials):
        self.nVialsBroken += nVials
        self.absoluteNVialsBroken += nVials

    def randSeed(self,seed=None):
        # We want random numbers that differ from all other
        # vaccines, but don't depend on placement of
        # this vaccine in the vaccine name list.
        self.rndm.seed(seed)
        self.rndm.jumpahead(self.rndm_jumpahead) 

    def summarystring(self):
        return self.name \
               + '\n   Display name: '+ unicode(self.displayName) \
               + '\n   Doses per vial : ' +unicode(self.dosesPerVial) \
               + '\n   Packed vol per dose(cc) : ' +unicode(self.ccPerDose) \
               + '\n   Packed vol diluent per dose(cc) : ' \
               + unicode(self.ccDiluentPerDose) \
               + '\n   Doses per person : ' +unicode(self.dosesPerPerson) \
               + '\n   Storage preferences : ' + unicode([st.name for st in self.storagePriority]) \
               + '\n   Maximum useful age : ' + unicode(self.maxAge) \
               + '\n   freezer aging rate : ' + unicode(self.freezerFac) \
               + '\n   cooler aging rate : ' + unicode(self.coolerFac) \
               + '\n   room temp aging rate : ' + unicode(self.roomtempFac) \
               + '\n   open vial aging rate : ' + unicode(self.openVialFac) \
               + '\n   can keep open vials: ' + unicode(self.keepOpenVials) \
               + '\n   rand_key: ' + unicode(self.rndm_jumpahead) \
               + '\n   packaging types: ' + unicode([p.name for p in self.packageTypes]) \
               +'\n\n'
    def computeWastage(self):
        dosesUsed = self.nVialsUsedForTreatment*self.dosesPerVial
        dosesWasted = dosesUsed - self.patientsTreated
        if dosesUsed > 0:
            dosesWasteFrac = (float(dosesWasted)/float(dosesUsed))
        else:   
            dosesWasteFrac = 0.0

        return dosesWasteFrac

    def statisticsstring(self):
        d= self.getSummaryDict()
        str= "%s \n"%self.name
        str += "   Total storage history %g vial days\n"%d['StorageHistoryVialDays']
        keyList= self.storageHistoryDict.keys()
        keyList.sort()
        for k in keyList:
            str += "      %6.2f%% %s \n"%(100.0*d['%sStorageFrac'%k], k)
        str += "   Total shipping time %g days, %g vial-days\n"%(d['ShipTimeDays'],d['ShipVialDays'])
        str += "   Total shipping distance %g km, %g vial-km\n"%(d['ShipKm'],d['ShipVialKm'])
        str += "   Treated %d of %d patients = %6.2f%%\n"%(d['Treated'],d['Applied'],100.0*d['SupplyRatio'])
        str += "   Used %d vials; open vial waste %d of %d doses = %6.2f%%\n"%\
               (d['VialsUsed'],
                (d['VialsUsed']*d['DosesPerVial'])-d['Treated'], 
                d['VialsUsed']*d['DosesPerVial'],
                100.0*d['OpenVialWasteFrac'])
        str += "   Expired %d vials = %d doses\n"%(d['VialsExpired'], d['VialsExpired']*d['DosesPerVial'])
        str += "   Broke %d vials = %d doses\n"%\
               (d['VialsBroken'], d['VialsBroken']*d['DosesPerVial'])
        if d['TransitTime_count'] > 0:
            str += "   Histogram of transit time in days (%d counts): min = %f, q1 = %f, median = %f, q3 = %f, max = %f"%\
                    (d['TransitTime_count'],d['TransitTime_min'], d['TransitTime_q1'], d['TransitTime_median'], d['TransitTime_q3'], d['TransitTime_max'])
        str += "\n"
        return str

    def getSummaryDict(self):
                    
        d= util.TagAwareDict(util.HistoVal,
                             [('_mean',util.HistoVal.mean),
                              ('_stdv',util.HistoVal.stdv),
                              ('_min',util.HistoVal.min),
                              ('_max',util.HistoVal.max),
                              ('_median',util.HistoVal.median),
                              ('_count',util.HistoVal.count),
                              ('_q1',util.HistoVal.q1),
                              ('_q3',util.HistoVal.q3)],
                              innerDict= {'Type':'vaccinetype', 'Name':self.name, 'DisplayName':self.displayName,
                                          'DosesPerVial':self.dosesPerVial})
        storageHistoryWeight= 0.0
        keyList= self.storageHistoryDict.keys()
        for k in keyList:
            storageHistoryWeight += self.storageHistoryDict[k]
        d['StorageHistoryVialDays']= storageHistoryWeight
        if storageHistoryWeight>0.0:
            for k in keyList:
                d['%sStorageFrac'%k]= self.storageHistoryDict[k]/storageHistoryWeight
        else:
            for k in keyList:
                d['%sStorageFrac'%k]= 0.0
        d['ShipTimeDays']= self.totalTravelDays
        d['ShipVialDays']= self.totalVialTravelDays
        d['ShipKm']= self.totalKilometers
        d['ShipVialKm']= self.totalVialKilometers
        if self.patientsApplied>0:
            p= float(self.patientsTreated)/float(self.patientsApplied)
        else:
            p= 0.0
        d['Applied']= self.patientsApplied
        d['Treated']= self.patientsTreated
        d['SupplyRatio']= p
        dosesUsed= self.nVialsUsedForTreatment*self.dosesPerVial
        dosesWasted= dosesUsed - self.patientsTreated
        if dosesUsed>0:
            doseWasteFrac= (float(dosesWasted)/float(dosesUsed))
        else:
            doseWasteFrac= 0.0
        d['OpenVialWasteFrac']= doseWasteFrac
        d['VialsUsed']= self.nVialsUsedForTreatment
        d['VialsExpired']= self.nVialsExpired
        d['VialsBroken']= self.nVialsBroken
        d['VialsCreated']= self.nVialsCreated
        d['VialsUsedAbsolute']= self.absoluteNVialsUsedForTreatment
        d['VialsExpiredAbsolute']= self.absoluteNVialsExpired
        d['VialsBrokenAbsolute']= self.absoluteNVialsBroken
        d['VialsCreatedAbsolute']= self.absoluteNVialsCreated
        d['TransitTime']= self.totalTransitHisto
        return d

    def updateAge(self,age,deltaT,storageType,nVials):
        if age is None: return None # already expired
        #assert(isinstance(storageType,storagetypes.StorageType))
        if not storageType in self.storageHistoryDict:
            self.storageHistoryDict[storageType]= 0.0
        self.storageHistoryDict[storageType] += nVials*deltaT
        discard = False
        if storageType==self.sim.storage.frozenStorage():
            fac= self.freezerFac
        elif storageType==self.sim.storage.roomtempStorage():
            fac= self.roomtempFac
        elif storageType==self.sim.storage.outdoorDiscardStorage():
            discard = True
            fac = 1.0
        elif storageType in self.sim.storage.coolStorageList():
            fac= self.coolerFac
        else:
            raise RuntimeError("Internal error; inappropriate vaccine storage type")
        newAge= age+(deltaT*fac)
        if newAge<=self.maxAge and not discard: return newAge
        else:
            # this vial just expired
            self.nVialsExpired += nVials
            self.absoluteNVialsExpired += nVials
            return None


    def getStoragePriorityList(self):
        return self.storagePriority
        
    def getSingletonStorageVolume(self, diluentFlagOrStorageModel):
        """
        Returns the storage volume of nCount instances of this ShippableType with no packaging.  Thus for 
        vaccine vials it is the packed storage volume of nCount of the bare vials themselves.  This method
        is used to track total delivered volume of goods, which by convention is the unpackaged volume of
        the goods.
        """
        if isinstance(diluentFlagOrStorageModel, storagemodel.StorageModel):
            withDiluent = diluentFlagOrStorageModel.getStoreVaccinesWithDiluent(self)
        else:
            withDiluent = diluentFlagOrStorageModel
        if withDiluent:
            return self.dosesPerVial * (self.ccPerDose + self.ccDiluentPerDose)
        else:
            return self.dosesPerVial*self.ccPerDose
    
    def getNDosesPerVial(self):
        return self.dosesPerVial
    
    def getLifetimeOpenDays(self):
        return self.lifetimeOpenDays

    def resetCounters(self):
        self.patientsTreated= 0
        self.patientsApplied= 0
        self.nVialsCreated= 0
        self.nVialsUsedForTreatment= 0
        self.nVialsExpired= 0
        self.nVialsBroken= 0
        self.totalVialKilometers= 0.0
        self.totalKilometers= 0.0
        self.totalVialTravelDays= 0.0
        self.totalTravelDays= 0.0
        for k in self.storageHistoryDict.keys():
            self.storageHistoryDict[k]= 0.0
        self.totalTransitHisto = util.HistoVal([])

    def recordTransport(self, nVials, fromWH, toWH, transitTimeDays, level, conditions):
        km= fromWH.getKmTo(toWH, level, conditions)
        self.totalKilometers += km
        self.totalVialKilometers += nVials*km
        self.totalTravelDays += transitTimeDays
        self.totalVialTravelDays += nVials*transitTimeDays

    def createInstance(self,count=1,name=None,currentAge=0.0,tracked=False):
        """
        Create and return a VaccineGroup of this VaccineType.
        """
        self.nVialsCreated += count
        self.absoluteNVialsCreated += count
        return VaccineGroup(count,self,self.getStoragePriorityList()[0],False,
                            name=name,currentAge=currentAge,tracked=tracked,history=1)

    def addPackageType(self, packageType):
        """
        Assert that this ShippableType may come in the given packageType.  Neither the
        ShippableType nor packageType is made active as a result of this call.
        """
        assert packageType.containsStr == self.name, "%s cannot contain %s"%(packageType.name, self.name)
        if packageType not in self.packageTypes:
            self.packageTypes.append(packageType)
            
    def getLargestPackageType(self):
        """
        returns the packagetypes.PackageType value corresponding to the largest valid package for this
        ShippableType, or 'None' if no PackageTypes are defined.  The 'None' value thus corresponds to
        the implied singleton package.
        """
        assert self.activatedFlag, "Requested getLargestPackageType for %s before activation"%self.name
        if len(self.packageTypes) > 0: return self.packageTypes[0]
        else: return None
       
    def getPackageTypeList(self):
        """
        Returns (a shallow copy of) the list of all valid package types for this Shippable, in order.
        """
        assert self.activatedFlag, "Requested getPackageTypeList for %s before activation"%self.name
        return self.packageTypes[:] # shallow copy
    
    def activate(self, **keywords):
        """
        Take this opportunity to integrate the chain of package types, if there is one.
        """
        retval = super(VaccineType,self).activate(**keywords)
        if len(self.packageTypes) > 0:
            l = [ (-p.count, p) for p in self.packageTypes ]
            l.sort()
            #print '%s: %s'%(self.name,l)
            self.packageTypes = [p for n,p in l]
            for p,nextP in zip(self.packageTypes[:-1],self.packageTypes[1:]):
                p.setNextSmaller(nextP)
            self.packageTypes[-1].setNextSmaller(None)  # None implies the singleton 'package'
        self.activatedFlag = True
        return retval

class DeliverableVaccineType(VaccineType, DeliverableType):
    def __init__(self, name, displayName, dosesPerVial, ccPerDose, ccDiluentPerDose, dosesPerPerson,
                 storagePriorityList, freezerFac, coolerFac, roomtempFac, openVialFac, maxAge,
                 lifetimeOpenDays, keepOpenVials=False, rand_key=None, recDict=None):
        VaccineType.__init__(self, name, displayName, dosesPerVial, ccPerDose, ccDiluentPerDose, 
                             dosesPerPerson, storagePriorityList, freezerFac, coolerFac, roomtempFac, openVialFac, maxAge, 
                             lifetimeOpenDays, keepOpenVials, rand_key, recDict=recDict)
        DeliverableType.__init__(self)
    
    def createInstance(self,count=1,name=None,currentAge=0.0,tracked=False):
        """
        Create and return a VaccineGroup of this VaccineType.
        """
        self.nVialsCreated += count
        self.absoluteNVialsCreated += count
        return DeliverableVaccineGroup(count,self,self.getStoragePriorityList()[0],False,
                                       name=name,currentAge=currentAge,tracked=tracked,history=1)

    def activate(self, **keywords): 
        """
        We must take this opportunity to make sure any required types are also activated.
        """
        retval = super(DeliverableVaccineType,self).activate(**keywords)
        assert retval==self, "Internal error: there is a problem with the Deliverable inheritance hierarchy"
        for reqType in self.getRequiredToPrepSC(1).keys():
            #print "reqType %s"%reqType
            self.manager.getTypeByName(reqType.name)
        return retval
        
class VaccineTypeManager(trackabletypes.TrackableTypeManager):
    """
    A specialization of TypeManager just for Shippables.  (Formerly just for Vaccines)
    """

    subTypeKey = "vaccines"

    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the simulation-wide TypeManager,
        passed in here as typeManager.
        All VaccineTypes have presumably already been defined within the sim-wide TypeManager.
        """
        trackabletypes.TrackableTypeManager.__init__(self, typeManager)
        self._dosesToVialsVC= None
        self._vialsToDosesVC= None
        self.typeClass= VaccineType

    def getDosesToVialsVC(self):
        """
        Returns a VaccineCollection containing scale factors for all
        active vaccines, such that multiplying a VC containing (floating
        point) doses will return a VC containing (floating point) vials.
        The result of the multiplication will not in general be an integer
        numbers of vials!
        """
        if self._dosesToVialsVC is None:
            tupleList= [(v,1.0/float(v.getNDosesPerVial()))
                        for v in self.getActiveTypes()]
            self._dosesToVialsVC= self.tm.sim.vaccines.getCollection(tupleList)
        return self._dosesToVialsVC
    
    def getVialsToDosesVC(self):
        """
        Returns a VaccineCollection containing scale factors for all
        active vaccines, such that multiplying a VC containing (floating
        point) vials will return a VC containing (floating point) doses.
        """
        if self._vialsToDosesVC is None:
            tupleList= [(v,float(v.getNDosesPerVial()))
                        for v in self.getActiveTypes()]
            self._vialsToDosesVC= self.tm.sim.vaccines.getCollection(tupleList)
        return self._vialsToDosesVC
