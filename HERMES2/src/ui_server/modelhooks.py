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

_hermes_svn_id_="$Id$"

import sys,os,os.path,time,json,math,types
import bottle
from sqlalchemy.exc import SQLAlchemyError
import ipath
import site_info
from serverconfig import rootPath
from preordertree import PreOrderTree
from upload import uploadAndStore, makeClientFileInfo
import htmlgenerator
import typehelper
from typeholdermodel import allTypesModelName
import shadow_network_db_api
import privs
import session_support_wrapper as session_support
import shadow_network as shd
import util
from HermesServiceException import HermesServiceException
from gridtools import orderAndChopPage
from model_edit_hooks import updateDBRouteType
from transformation import setLatenciesByNetworkPosition, setUseVialLatenciesAsOffsetOfShipLatencyFromRoute
import crumbtracks
import runhooks

from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError, _smartStrip, b64E, b64D

## If executing under mod_wsgi, we need to add the path to the source
## directory of this script.
sI = site_info.SiteInfo()
#try:
#    cwd = os.path.dirname(__file__)
#    if cwd not in sys.path:
#        sys.path.append(cwd)
#
#    if sI.srcDir() not in sys.path:
#        sys.path.append(sI.srcDir())
#except:
#    pass

#sqlite = bottle_sqlite.SQLitePlugin(dbfile='/tmp/test.db')
#bottle.install(sqlite)

inlizer=session_support.inlizer
_=session_support.translateString

def getParm(parm):
    return _safeGetReqParam(bottle.request.params, parm)

def addCrumb(uiSession, label, noInlize=False):
    if not noInlize:
        label = _(label)
    if uiSession.getCrumbs().currentLabel() == label:
        return uiSession.getCrumbs()
    url = bottle.request.path + '?' + bottle.request.query_string
    crumb = (url, label)
    crumbTrack = uiSession.getCrumbs().push(crumb)
    return crumbTrack

def isSystemDBModel(model):
    if model.name == allTypesModelName:
        return True
    return False

def sortModelList(models):
    pairs = []
    for m in models:
        if isSystemDBModel(m):
            pairs.append((False, m))
        else:
            pairs.append((m.name, m))
    pairs.sort()
    keys, models = zip(*pairs)
    return models

@bottle.route('/models-top')
def modelsTopPage(uiSession):
    crumbTrack = addCrumb(uiSession, 'Models')
    return bottle.template("models_top.tpl",
                           {
                            "breadcrumbPairs":crumbTrack
                            })

@bottle.route('/model-edit-params')
def modelsEditParams(db, uiSession):
#    crumbTrack = uiSession.getCrumbs().push((bottle.request.path + "?" + bottle.request.query_string,_("Params")))

    crumbTrack = addCrumb(uiSession, "Params")
    try:
        modelId = int(getParm('id'))
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        uiSession['selectedModelId'] = modelId
        uiSession['modelIdBeingEdited'] = modelId
    
        return bottle.template("run_edit_parms.tpl",
                               {"modelId":modelId,
                                "breadcrumbPairs" : crumbTrack})
#                                "breadcrumbPairs":[("top",_("Welcome")),("models-top",_("Models")),
#                                                  ("model-edit-params",_("Edit parameters"))]})
    
    except Exception, e:
        return bottle.template("problem.tpl", {"comment":str(e),
                                               "breadcrumbPairs" : crumbTrack})
#                                               "breadcrumbPairs":[("top",_("Welcome")),("models-top",_("Models")),
#                                                                  ("model-edit-params",_("Edit parameters"))]})


@bottle.route('/model-add-types')
def modelsAddTypes(db, uiSession):
    crumbTrack = addCrumb(uiSession, 'Edit Model Components')
    try:
        modelId = int(getParm('id'))
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)
        uiSession['selectedModelId'] = modelId
        uiSession['modelIdBeingEdited'] = modelId
        if 'startClass' in bottle.request.params:
            startClass = getParm('startClass')
        else:
            startClass = 'vaccines'
    
        return bottle.template("types_top.tpl",
                               {"modelId":modelId,
                                "modelName":model.name,
                                "startClass":startClass,
                                "breadcrumbPairs": crumbTrack,
                                "baseURL":'model-add-types'},createpipe=False,pagehelptag='types')

    except Exception,e:
        _logStacktrace()
        return bottle.template("problem.tpl", {"comment": str(e),
                                               "breadcrumbPairs":crumbTrack})



@bottle.route('/model-show-structure')
def modelShowStructurePage(db,uiSession):
    crumbTrack = addCrumb(uiSession, 'Show Structure')
    if "id" in bottle.request.params:
        modelId = int(bottle.request.params['id'])
        uiSession['selectedModelId'] = modelId
        uiSession['modelIdBeingEdited'] = modelId
    elif 'modelIdBeingEdited' in uiSession:
        modelId = uiSession['modelIdBeingEdited']
    else:
        return bottle.template("problem.tpl",{"comment":_("We have somehow forgotten which model to show."),
                                              "breadcrumbPairs":crumbTrack})

    uiSession.getPrivs().mayReadModelId(db,modelId)
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)
    return bottle.template("model_show_structure.tpl",
                           {"slogan":"Supply Chain Structure Of %s"%m.name,
                            "modelId":m.modelId,
                            "breadcrumbPairs":crumbTrack})

@bottle.route('/loops-top')
def generateLoopsTop(db,uiSession):
    try:
        crumbTrack = addCrumb(uiSession,'Loop Generator')
        modelId = _safeGetReqParam(bottle.request.path,'modelId',isInt=True)
        if modelId is None:
            modelId = uiSession['selectedModelId']
        uiSession.getPrivs().mayReadModelId(db,modelId)
        uiSession['modelIdBeingEdited'] = modelId
        return bottle.template("loop_creation.tpl",{"breadcrumbPairs":crumbTrack},modelId=modelId)
    except bottle.HTTPResponse:
        raise # bottle will handle this
       
def _doModelEditPage(db, uiSession):
    crumbTrack = addCrumb(uiSession, 'Advanced Model Editor')
    if "id" in bottle.request.params:
        modelId = int(bottle.request.params['id'])
        uiSession['selectedModelId'] = modelId
        uiSession['modelIdBeingEdited'] = modelId
        uiSession.save()
    elif 'modelIdBeingEdited' in uiSession:
        modelId = uiSession['modelIdBeingEdited']
    else:
        return bottle.template("problem.tpl",{"comment":"We have somehow forgotten which model to edit.",
                                             "breadcrumbPairs":crumbTrack})

    nr = ''
    if "nr" in bottle.request.params:
        nr = '_nr'
    
    modify = False
    read = False
    try:
        uiSession.getPrivs().mayModifyModelId(db,modelId)
        modify = True
        read = True
    except:
        pass

    if not read:
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except:
            comment = _("This is an invalid model.  Either it doesn't exist or " + \
                            "you do not have permission to view it")
            return bottle.template("problem.tpl", {'comment' : comment,
                                                   "breadcrumbPairs":crumbTrack})


    # we should have a better page than this, possibly the editor with editing
    # disabled.
    if not modify:
        comment = _("This model is read-only.  You may edit a copy of the model " + \
                        "by copying the model and editing that one instead.")
        return bottle.template("problem.tpl", {'comment' : comment,
                                               "breadcrumbPairs":crumbTrack})
        
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)
    template = 'model_edit_structure.tpl'

    return bottle.template(template, {"slogan":_("Advanced Model Editor: ")+" %s"%m.name,
                                      "modelId":m.modelId,
                                      "nr":nr,
                                      "breadcrumbPairs":crumbTrack
                                      })

@bottle.route('/model-edit')
@bottle.route('/model-edit-structure')
def modelEditStructurePage(db, uiSession):
    return _doModelEditPage(db, uiSession)


def _createModel(db,uiSession):
    import copy
    if 'newModelInfo' not in uiSession :
        raise bottle.BottleException(_("There is new model data in session."))
    if 'currentModelName' not in uiSession['newModelInfo']:
        raise bottle.BottleException(_("There is no current model in the new model data in session."))
    if uiSession['newModelInfo']['currentModelName'] not in uiSession['newModelInfo'].keys():
        raise bottle.BottleException(_("The currently selected model {0} has no data in session".format(uiSession['newModelInfo']['currentModelName'])))
    if not all([key in uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']]
        for key in ['name','levelnames','pottable','potrecdict',
            'shiptransittimes','shiptransitunits']]):
        raise bottle.BottleException(_("Model creation data table is missing or corrupted"))
    newModelInfoCN = uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']]
    shdTypes = shd.ShdTypes()
    shdNetwork = shd.ShdNetwork(None, None, None,shdTypes, newModelInfoCN['name'] )
    original_pottable = copy.copy(newModelInfoCN['pottable'])                     
    pot = PreOrderTree(newModelInfoCN['pottable'])
    potRecDict = newModelInfoCN['potrecdict']
    #print "---------------------------------------------------------------HERE"
    storeStack = []
    storeDict = {}
    prevLevel = -1
    prevId = None
    pot.table.sort() # Sort to depth-first
    for lkey,rkey,lvl,idcode in pot.table:
        #print "lstuff: {0} {1} {2} {3}".format(lkey,rkey,lvl,idcode)
        rec = potRecDict[idcode]
        category = newModelInfoCN['levelnames'][lvl]
        isLeaf = (rkey==lkey+1)
        if isLeaf: 
            fctn = 'Administration'
            useVialsInterval = 1.0
        else: 
            fctn = 'Distribution'
            useVialsInterval = 1.0 # it may get an attached clinic, so we need a valid value
        useVialsLatency = 0.0
        store = shd.ShdStore({'CATEGORY':category, 'FUNCTION':fctn, 'NAME':rec['name'], 'idcode':idcode,
                                         'Inventory':'','Device Utilization Rate':1.0,
                                         'UseVialsInterval':useVialsInterval, 'UseVialsLatency':useVialsLatency},
                                        shdNetwork)
        shdNetwork.addStore(store)
        storeDict[idcode] = store
        if lvl>prevLevel:
            storeStack.append(prevId)
        elif lvl<prevLevel:
            storeStack = storeStack[:-(prevLevel-lvl)]
        #print "storeStack"
        #print storeStack
        if storeStack != []:
            supplierId = storeStack[-1]
            if supplierId is not None:
                #print "idcode = " + str(idcode)
                #print 'supplierId = ' + str(supplierId)
                #print rec
                if rec['issched'] == 'true':
                    if rec['isfetch'] == 'true':
                        if rec['isfixedam'] == 'true':
                            routeType = "schedfetch"
                        else:
                            routeType = 'schedvarfetch'
                    else:
                        if rec['isfixedam'] == 'true':
                            routeType = 'push'
                        else:
                            routeType = 'varpush'
                else:
                    if rec['isfetch'] == 'true':
                        if rec['isfixedam']:
                            routeType = 'demandfetch'
                        else:
                            routeType = 'demandfetch'
                    else:
                        if rec['isfixedam'] == 'true':
                            routeType = 'pull'
                        else:
                            routeType = 'pull'
                routeName = 'r%d'%idcode
                if rec['ymw'] == 'year':
                    shipIntervalDays = math.floor((12.*28.)/rec['howoften'])
                elif rec['ymw'] == 'month':
                    shipIntervalDays = math.floor(28./rec['howoften'])
                else:
                    shipIntervalDays = math.floor(7./rec['howoften'])
                shipLatencyDays = 0.0
                #print "RouteType = " + routeType
                route = shdNetwork.addRoute({'RouteName':routeName, 'Type':routeType,
                                             'ShipIntervalDays':shipIntervalDays,
                                             'ShipLatencyDays':shipLatencyDays}, noStops=True)
                ignoredNumber = 17
                transitUnits = newModelInfoCN['shiptransitunits'][len(storeStack)-2]
                transitTimeRaw = newModelInfoCN['shiptransittimes'][len(storeStack)-2]
                transitDistance = newModelInfoCN['shiptransitdist'][len(storeStack)-2]
                transitHours = {'hour':1.0, 'day':24.0, 'week':168.0, 'month':4704.0, 'year':56448.0}[transitUnits] * transitTimeRaw
                if rec['isfetch']=='true':
                    #print "fetching"
                    route.addStop({'idcode':idcode, 'RouteName':routeName, 'RouteOrder':0,
                                   'TransitHours':transitHours,'DistanceKM':transitDistance,
                                   'PullOrderAmountDays':shipIntervalDays},
                                  storeDict)
                    route.addStop({'idcode':supplierId, 'RouteName':routeName, 'RouteOrder':1,
                                   'TransitHours':transitHours,'DistanceKM':transitDistance,
                                   'PullOrderAmountDays':shipIntervalDays},
                                  storeDict)
                else:
                    #print "not fetching"
                    route.addStop({'idcode':supplierId, 'RouteName':routeName, 'RouteOrder':0,
                                   'TransitHours':transitHours,'DistanceKM':transitDistance,
                                   'PullOrderAmountDays':shipIntervalDays},
                                  storeDict)
                    route.addStop({'idcode':idcode, 'RouteName':routeName, 'RouteOrder':1,
                                   'TransitHours':transitHours,'DistanceKM':transitDistance,
                                   'PullOrderAmountDays':shipIntervalDays},
                                  storeDict)
                route.linkRoute()
                #shdNetwork.addRoute(route.createRecords())
        prevLevel = lvl
        prevId = idcode

    setLatenciesByNetworkPosition(shdNetwork, stagger=True)
    setUseVialLatenciesAsOffsetOfShipLatencyFromRoute(shdNetwork)

    db.add(shdNetwork)
    db.commit()
    uiSession.getPrivs().registerModelId(db, shdNetwork.modelId, 
                                         uiSession.getDefaultReadGroupID(),uiSession.getDefaultWriteGroupID())
    
    shdNetwork.addModelD3Json()
    db.commit()

    quotedLevelNames = ["'%s'"%nm for nm in newModelInfoCN['levelnames']]
    shdNetwork.addParm(shd.ShdParameter('levellist',','.join(quotedLevelNames)))
    shdNetwork.addParm(shd.ShdParameter('cliniclevellist',quotedLevelNames[-1]))
    shdNetwork.addParm(shd.ShdParameter('centrallevellist',quotedLevelNames[0]))
    shdNetwork.addParm(shd.ShdParameter('model','model_generic'))
    shdNetwork.addParm(shd.ShdParameter('demandfile','demand_from_db'))

    # All models have copies of a few standard types from AllTypesModel
    aM = typehelper._getAllTypesModel(db)
    for tpName, tp in [(u'OUTDOORS', shd.ShdStorageType),
                       (u'Std_PerDiem_None', shd.ShdPerDiemType),
                       (u'Std_WarehouseStaff', shd.ShdStaffType),
                       (u'Std_Driver', shd.ShdStaffType)]:
        attrRec = {'_inmodel': False, 'modelId': aM.modelId}
        shd._copyAttrsToRec(attrRec, aM.types[tpName])
        newTp = tp(attrRec.copy())
        db.add(newTp)
        shdNetwork.types[tpName] = newTp

    # All models need a copy of the currencyConversion table- grab it from the AllTypesModel
    shdNetwork.addCurrencyTable( aM.getCurrencyTableRecs()[1] )
    newModelInfoCN['pottable'] = original_pottable
    _logMessage("Created the model '%s'"%newModelInfoCN['name'])
    return shdNetwork.name,shdNetwork.modelId

def _addLevel(pot, recDict, ngList, countsList, otherList, parent, recBuilder):
    #print '##### _addlevel %s %s %s %s #######'%(ngList,countsList,otherList,parent)
    countsThisLevel = countsList[0]
    baseCountsList = [c/countsThisLevel for c in countsList[1:]]
    leftovers = countsList[1:][:]# copy of the slice
    #print countsList[0]
    for i in xrange(countsThisLevel):
        name,index = ngList[0].get()
        pot.add(index, parent)
        if len(ngList)>1:
            if i==(countsThisLevel-1):
                _addLevel(pot,recDict,ngList[1:],leftovers,otherList[1:],index,recBuilder)
                nKids = leftovers[0]
            else:
                _addLevel(pot,recDict,ngList[1:],baseCountsList,otherList[1:],index,recBuilder)
                leftovers = [a-b for a,b in zip(leftovers,baseCountsList)]
                nKids = baseCountsList[0]
        else:
            nKids = 0
        recDict[index] = recBuilder(name, nKids, otherList[0])
    #print '##### _addlevel exit %s %s %s %s #######'%(ngList,countsList,otherList,parent)

class NumberedNameGenerator:
    totCount = 0
    def __init__(self,baseName,count=1):
        self.name = baseName
        self.count = count
    def get(self):
        newName = "%s_%d"%(self.name,self.count)
        self.count += 1
        NumberedNameGenerator.totCount += 1
        return (newName,NumberedNameGenerator.totCount)
    def __str__(self):
        return "NumberedNameGenerator(%s)"%self.name
    def __repr__(self):
        return "<NumberedNameGenerator(%s,%d)"%(self.name,self.count)
    @classmethod
    def resetCounter(cls):
        NumberedNameGenerator.totCount = 0

def _buildTreeRec(name, nKids, other):
    if other == (): # true at top level of tree
        isfixedam = "false" 
        isfetch = "false" 
        issched = "true"
        howoften = 0
        ymw = "year"
    else:
        isfixedam,isfetch,issched,howoften,ymw = other
        print "other = " + str(other)
    return { 'name':name, 'isfixedam':isfixedam,'isfetch':isfetch, 'issched':issched, 'howoften':howoften, 'ymw':ymw}

def _buildPreOrderTree(info,pot_in=None,recDict_in=None,parent_in=None,baseLvl=0):
    if pot_in is None:
        pot = PreOrderTree()
    else:
        pot = pot_in
    if recDict_in is None:
        recDict = {}
    else:
        recDict = recDict_in
    NumberedNameGenerator.resetCounter()
    nameGenList = [NumberedNameGenerator(lname) for lname in info['levelnames']]
    parent = parent_in
    _addLevel(pot, recDict, nameGenList[baseLvl:], info['levelcounts'][baseLvl:],info['shippatterns'][baseLvl:],
              parent,_buildTreeRec)
    #pot.emit()
    return (pot,recDict)


'''
STB To Do, I think many of these have been deprecated
'''
def _checkDefAndNewDict(reqParams,defDict,name1):
    """ This function takes a parameters of name1 to the bottle request and 
        creates an dictionary entry with the name1 parameter inside it.
        This makes it so that we can have multiple session entries 
        underneath one, such as in newModelInfo.
    """
    if name1 in reqParams:
        if reqParams[name1] not in defDict.keys():
            defDict[reqParams[name1]] = {name1:reqParams[name1]}
         
        return reqParams[name1]
    else:
        return None


def _copyStoreProvisions(fromStore, toStore):
    #toStore.copyAttrsFromInstance(fromStore,excludeThese=['NAME','idcode','modelId'])
    toStore.copyAttrsFromRec(fromStore.createRecord(),excludeThese=['NAME','idcode','modelId'])

def _copyRouteProvisions(fromRoute, toRoute, backwards=False):
    if fromRoute==toRoute: return
    assert len(fromRoute.stops)==len(toRoute.stops), _("Route {0} has the wrong number of stops for provisioning").format(toRoute.RouteName)
    for key in ['TruckType','ShipIntervalDays','ShipLatencyDays','Conditions','PerDiemType']:
        setattr(toRoute, key, getattr(fromRoute, key))
    updateDBRouteType(toRoute, fromRoute.Type)
    if backwards:
        matchedStops = zip(fromRoute.stops,toRoute.stops)
    else:
        matchedStops = zip(fromRoute.stops,toRoute.stops)
    for fromStop,toStop in matchedStops:
        for key in ['TransitHours', 'DistanceKM', 'PullOrderAmountDays']:
            setattr(toStop, key, getattr(fromStop, key))

def _provisionModel(db, modelId):
    """
    Provisions and store details have been specified for the 'canonical' stores at each level
    of this newly created model.  Copy them to the other stores.
    """
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    canonicalStoreIdDict = _findCanonicalStores(model)
    canonicalStoreDict = { k:model.getStore(v) for k,v in canonicalStoreIdDict.items() }
    for idcode,store in model.stores.items():
        if idcode not in canonicalStoreIdDict.values(): 
            _copyStoreProvisions(canonicalStoreDict[store.CATEGORY],store)

    # We now must recalculate the shipping schedule, because the user may have
    # changed the available trucks or other characteristics.
    setLatenciesByNetworkPosition(model,incrementDays=2,stagger=True,
                                  doNotModifySet=set(canonicalStoreIdDict.values()))
    # But we will leave the UseVialsLatencies alone, because they are generally set by explicit policy
            
def _provisionModelRoutes(db, modelId):
    """
    Provisions and route details have been specified for the 'canonical' routes between each 
    pair of levels of this newly created model.  Copy them to the other routes.
    
    Fortunately, at this stage of model generation, all routes are just two stops long.
    """
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    canonicalRouteDict = _findCanonicalRoutes(model)
    canonicalStoreIdDict = _findCanonicalStores(model)
    for rt in model.routes.values():
        l0 = rt.stops[0].store.CATEGORY
        l1 = rt.stops[1].store.CATEGORY
        processed = False
        #if (l0,l1) in canonicalRouteDict:
        if l0 in canonicalRouteDict.keys():
            if l1 in canonicalRouteDict[l1].keys():
                srcRouteId = canonicalRouteDict[l0][l1]
                if srcRouteId is None:
                    continue
                srcRoute=model.routes[srcRouteId]
                processed = True
                #assert srcRoute is not None, _("There is no canonical route matching {0}".format(rt.RouteName))
                _copyRouteProvisions(srcRoute, rt)
        #elif (l1,l0) in canonicalRouteDict:
        if l1 in canonicalRouteDict.keys():
            if l0 in canonicalRouteDict[l1].keys():
                srcRouteId = canonicalRouteDict[l1][l0]
                if srcRouteId is None: continue
                srcRoute = model.routes[srcRouteId]
                process = True
                #assert srcRoute is not None, _("There is no canonical route matching {0} backwards".format(rt.RouteName))
                _copyRouteProvisions(srcRoute, rt, backwards=True)
        if process is False:
            raise bottle.BottleException(_("There is no route for these level {0} {1}".format(l0,l1)))
        else:
            raise bottle.BottleException(_("Route {0} unexpectedly spans categories {1} and {2}").format(rt.RouteName,l0,l1))
        
    # We now must recalculate the shipping schedule, because the user may have
    # changed the available trucks or other characteristics.
    setLatenciesByNetworkPosition(model,incrementDays=2,stagger=True,
                                  doNotModifySet=set(canonicalStoreIdDict.values()))
    # But we will leave the UseVialsLatencies alone, because they are generally set by explicit policy
    
def _findCanonicalStores(model):
    """
    During the model creation process, one store at each level is chosen to be 'generic' and is
    edited by the user during the provisioning step.  The provisions for that store are then propagated
    to the other stores at the same level.  Because the routing tree is generated from a pre-order list,
    one would think that the idcodes of the levels down the left edge of the tree could provide those
    generic models.  Unfortunately the user may have edited the tree after creation and before
    provisioning, so we have to explicitly walk the tree looking for stores to use as generics.
    """
    idcodeList = model.stores.keys()[:]
    idcodeList.sort()
    levelNames = _smartStrip(model.getParameterValue('levellist'))
    count = len(levelNames)
    d = { nm:None for nm in levelNames}
    for idcode in idcodeList:
        lvl = model.getStore(idcode).CATEGORY
        if d[lvl] is None:
            d[lvl] = idcode
            count -= 1
            if count==0: break
        else:
            badNames = [ nm for nm,v in d.items() if v is None ]
            raise bottle.BottleException(_("Found no stores of level(s) {0}").format(str(badNames)))
    #print d
    return d

def _findCanonicalRoutes(model):
    """
    During the model creation process, one route at each pair of levels is chosen to be 'generic' and is
    edited by the user during the provisioning step.  The provisions and values for that route are then propagated
    to the other routes between the same pair of level.  Because the routing tree is generated from a pre-order list,
    one would think that the idcodes of the levels down the left edge of the tree could provide those
    generic models.  Unfortunately the user may have edited the tree after creation and before
    provisioning, so we have to explicitly walk the tree looking for routes to use as generics.
    
    Fortunately, at this stage of model generation, all routes are just two stops long.
    """
    levelNames = _smartStrip(model.getParameterValue('levellist'))
    d = {}
    for i in xrange(len(levelNames)):
        d[levelNames[i]] = {}
        for j in xrange(0,len(levelNames)):
            d[levelNames[i]][levelNames[j]] = None

    for rt in model.routes.values():
        assert len(rt.stops)==2, _("Route {0} unexpectedly has more than two stops").format(rt.RouteName)
        l0 = rt.stops[0].store.CATEGORY
        l1 = rt.stops[1].store.CATEGORY
        #if (l0,l1) in d:
        #print "------------------------------------------------------------------"
        #print "L0: " + str(l0)
        #print "Keys" + str(d[l0].keys())
        if l0 in d.keys():
            #print "L1: " + str(l1)
            if l1 in d[l0].keys():
                #print "Adding " + rt.RouteName
                if d[l0][l1] is None: d[l0][l1] = rt.RouteName
        #elif (l1,l0) in d:
        elif l1 in d.keys():
            #print "L1: " + str(l1)
            #print "l1 Keys" + str(d[l1].keys())
            if l0 in d[l1].keys():
                #print "Adding " + rt.RouteName
                if d[l1][l0] is None: d[l1][l0] = rt.RouteName
        else:
            raise bottle.BottleException(_("Route {0} unexpectedly spans categories {1} and {2}").format(rt.RouteName,l0,l1))
        
    return d

@bottle.route('/model-create/<step>/next')
def modelCreateNext(db,uiSession,step="unknown"):
    bottle.redirect('%smodel-create/next'%rootPath)

@bottle.route('/model-create/<step>/back')
def modelCreateBack(db,uiSession,step="unknown"):
    bottle.redirect('%smodel-create/back'%rootPath)

@bottle.route('/model-create')
@bottle.route('/model-create/<step>')
def modelCreatePageNew(db,uiSession,step="unknown"):
    ''' Not sure why this is needed '''
    formVals = { 'breadcrumbPairs':uiSession.getCrumbs() }
    try:
        '''
        -------------------------------------------------------------------------------
        Step 1: Setup the crumbtracks for the overall page
        --------------------------------------------------------------------------------
        '''
        crumbTrack = uiSession.getCrumbs()
        stepPairs = [('nlevels',_('Edit Supply Chain Structure')),
                     ('interlevel',_('Edit Shipping Policy')),                 
                     ('interleveltimes',_('Edit Shipping Times')),                 
                     ('done',_('Make Adjustments')),                 
                     #('people',_('Population')),                 
                     #('fridges',_('Storage')),                 
                     #('trucks',_('Transport')),                 
                     ('types',_('Add/Remove Components')),
                     ('setdemand',_('Vaccine Dose Schedule')),                 
                     ('provision',_('Assign Equipment')),                 
                     ('provisionroutes',_('Assign Transport Vehicles')),    
                     ]
        namedStepList = [a for a,b in stepPairs] # @UnusedVariable
        '''
        -------------------------------------------------------------------------------
        Step 2: Imitialize and setup the modelInfo for session updating
        --------------------------------------------------------------------------------
        '''
        ### come in cold with no screen defined for below
        screen = None
        
        ### If there is no new model info in ui session create it
        if 'newModelInfo' not in uiSession:
            uiSession['newModelInfo'] = {}
        
        newModelInfo = uiSession['newModelInfo']
        reqParams = bottle.request.params
        
        ### new names specific dict
        ### There needs to be a current model, otherwise, there is no way to comeback from this.
        if 'currentModelName' not in newModelInfo.keys():
            newModelInfo['currentModelName'] = "none"
        
        cName = _checkDefAndNewDict(reqParams,newModelInfo,'name')

        if cName:
            newModelInfo['currentModelName'] = cName
            
        curName = newModelInfo['currentModelName']
        ### Else current name stays the same
        
        ### Catch this, if we are running through this and there is no current name, then bad
        if newModelInfo['currentModelName'] == "none":
            raise RuntimeError(_("Entered into here without a model set, so new model Info cannot work."))
        
        ### Finally, we need the new ModelInfo for the current name
        ### This should be updated from the page that this was created on,
        ### eliminating almost all of the logic from before
        if newModelInfo['currentModelName'] not in newModelInfo:
            # This can happen if the user jumps to the advanced editor and then back
            del newModelInfo['currentModelName']
            crumbTrack.pop()  # whatever sent us here
            crumbTrack.pop()  # our own crumb
            bottle.redirect(crumbTrack.currentPath())
        newModelInfoCN = newModelInfo[newModelInfo['currentModelName']]
        if not newModelInfoCN.has_key('firstTime'): newModelInfoCN['firstTime'] = 'T'
        #print '-0-0-0-0-0-0-0-0-0-'
        #print newModelInfoCN
        ''' Translation from screen name to tpl to use '''
        screenToTpl = {"nlevels":"model_create_begin.tpl",
                       "interlevel":"model_create_interlevel.tpl",
                       "interleveltimes":"model_create_interlevel_timings.tpl",
                       "done":"model_create_done.tpl",
                       ### Want to get to here first
                       "provision":"model_create_provision.tpl",
                       "provisionroutes":"model_create_provision_routes.tpl",
                       'types':'type_top.tpl',
                       #'people':'people_top.tpl',
                       #'vaccines':'vaccine_top.tpl',
                       #'fridges':'fridge_top.tpl',
                       #'trucks':'truck_top.tpl',
                       'setdemand':'demand_top.tpl'
                       }
        
        ''' What variables are actually required to be at this level '''
        screenRequires = {"countsbylevel":["levelnames"],
                          "provision":["modelId"],
                          "provisionroutes":["modelId"],
                          "types":['modelId'],
                          #"people":["modelId"],
                          #"vaccines":["modelId"],
                          #"fridges":["modelId"],
                          #"trucks":["modelId"],
                          "setdemand":["modelId"],
                          }
        '''
        -------------------------------------------------------------------------------
        Step 3: Update the crumb track information
        --------------------------------------------------------------------------------
#         '''
        if "subCrumbTrack" in newModelInfoCN:
            #print "SubCrumb----------------------------------------------------------------------"
            
            subCrumbTrack = newModelInfoCN['subCrumbTrack']
            #print str(subCrumbTrack._toJSON())
            #print crumbTrack._toJSON()
            crumbTrack.push(subCrumbTrack)  # no-op if it is already there
            #print crumbTrack._toJSON()
        else:
            subCrumbTrack = None
        #subCrumbTrack = None
        #### Begin processing based on the step that comes from the 
        #### url
        #### unknown means we are entering the pipeline from outside
        #### next means we are moving from one page inside the chain to the next
        #### back means we are moving from one page inside the chaing to the previous
        #print "Step = " + str(step)
        if step=="unknown":
            '''
            Step: unknown
            This means we are coming from outside, so we need to check the 
            crumbtrack to see if we are already inside the chain.  If there
            is no crumb tracks, we are entring the thing from the beginning
            '''
            if subCrumbTrack is None:
                subCrumbTrack = crumbtracks.TrackCrumbTrail(bottle.request.path, 
                                                            "Create Model")
                for a,b in stepPairs:
                    subCrumbTrack.append((a,b))
                newModelInfoCN['subCrumbTrack'] = subCrumbTrack
                crumbTrack.push(subCrumbTrack)
            ## we assume a new model is being born
            step = screen = subCrumbTrack.current()
        
        elif step=='next':
            '''
            Step: next
            This means we have a crumb track and are moving on, so update accordingly
            '''
            screen = subCrumbTrack.next()
            if screen is None:
                # We just finished the track
                del newModelInfoCN['subCrumbTrack']
                crumbTrack.pop()
                #screen = 'models-top'
                screen = 'model-open'
        elif step=='back':
            screen = subCrumbTrack.back()
            if screen is None:
                # We just backed off the start of the track
                crumbTrack.pop()
                screen = 'models-top'
        else:
            #print "HERE------------"
            #print crumbTrack._toJSON()
            if not crumbTrack.jump(step):
                raise bottle.BottleException("Invalid step %s in model create"%step)
            screen = crumbTrack.current()
            
        '''
        -------------------------------------------------------------------------------
        Step 4: Handle model creation, jumping to expert, or provisioning of the model
        --------------------------------------------------------------------------------
        '''
        if 'create' in bottle.request.params and bottle.request.params['create'] == 'true':
            ''' 
            HERE We actually create a model in the database
            '''
#             if 'modelId' in newModelInfoCN:
#                 # the user is messing around with the back/next buttons
#                 #  we can add some logic here to allow the user to delete the previous model
#                 pass
#             else:
            #print "Going into create"
            #print str(newModelInfoCN['pottable'])
            nameTmp,modelIdTmp = _createModel(db,uiSession)
            newModelInfoCN['name2'] = nameTmp
            newModelInfoCN['modelId'] = modelIdTmp
        ''' STB TODO This part needs to be fixed '''
        if 'expert' in bottle.request.params and bottle.request.params['expert'] == 'true':
            from serverconfig import rootPath
            if 'modelId' in newModelInfoCN and newModelInfoCN['modelId'] != -1:
                # the user is messing around with the back/next buttons
                del crumbTrack.trail[-1]
                bottle.redirect('{0}model-edit-structure?id={1}'.format(rootPath,newModelInfoCN['modelId'])) 
            else:
                # fake the remaining unfilled pages so the PreOrderTree can get created
                if 'levelcounts' not in newModelInfoCN: newModelInfoCN['levelcounts'] = [1 for x in xrange(newModelInfo['nlevels'])]
                if 'shiptransitunits' not in newModelInfoCN: newModelInfoCN['shiptransitunits'] = ['hour' for x in xrange(newModelInfoCN['nlevels']-1)]
                if 'shiptransittimes' not in newModelInfoCN: newModelInfoCN['shiptransittimes'] = [1.0 for x in xrange(newModelInfoCN['nlevels']-1)]
                if 'shippatterns' not in newModelInfoCN: newModelInfoCN['shippatterns'] = [() if x==0 else (False,False, True, 1, 'year') for x in xrange(newModelInfoCN['nlevels'])]
                else: 
                    if len(newModelInfoCN['shippatterns'][0]) > 0:
                        newModelInfoCN['shippatterns'].insert(0,())
                
                if not newModelInfoCN.has_key('modelId') or newModelInfoCN['modelId'] == -1 or len(newModelInfoCN['pottable']) == 0:
                #if 'pottable' not in newModelInfoCN:
                    pot,recDict = _buildPreOrderTree(newModelInfoCN)
                    newModelInfoCN['pottable'] = pot.table
                    newModelInfoCN['potrecdict'] = recDict
                    newModelInfoCN['maxidcode'] = NumberedNameGenerator.totCount
                newModelInfoCN['name'],newModelInfoCN['modelId'] = _createModel(db,uiSession)
                # clean up current model creation session
                createdModelId = newModelInfoCN['modelId']
                del uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']]['subCrumbTrack']
                #crumbTrack.pop()
                del uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']]
                uiSession.changed()
                # open the model editor
                p = bottle.request.path
                fp = bottle.request.fullpath
                offset = fp.find(p)
                rootPath = fp[:offset+1] # to include slash      
                del crumbTrack.trail[-1]             
                bottle.redirect('{}model-edit-structure?id={}'.format(rootPath,createdModelId))        
        
        ''' STB TODO Make this throw more meaningful and easier to parse errors'''
        if 'provision' in bottle.request.params and bottle.request.params['provision'] == 'true':
            if 'modelId' in newModelInfoCN:   
                _provisionModel(db, newModelInfoCN['modelId'])
            else:
                raise RuntimeError(_("The model is not ready for provisioning"))
        if 'provisionroutes' in bottle.request.params and bottle.request.params['provisionroutes'] == 'true':
            if 'modelId' in newModelInfoCN:
                _provisionModelRoutes(db, newModelInfoCN['modelId'])
            else:
                raise RuntimeError(_("The routes are not ready for provisioning"))    
        
        '''
        -------------------------------------------------------------------------------
        Step 5: Setup session variables that are needed for the screens
        --------------------------------------------------------------------------------
        '''
        formVals = {"breadcrumbPairs":crumbTrack,'name':newModelInfoCN['name']}
        
        ''' Check if we have the required variables in the modelInfo session structure '''
        
        if screen in screenRequires:
            for req in screenRequires[screen]:
                if req not in newModelInfoCN.keys():
                    raise RuntimeError(_("Expected to know the value of {0} by now").format(req))
        
        ''' Handle the special cases '''
        
        if screen=="provision":
            newModelInfoCN['canonicalStoresDict'] = _findCanonicalStores(shadow_network_db_api.ShdNetworkDB(db, newModelInfoCN['modelId']))
        elif screen=="provisionroutes":
            
            newModelInfoCN['canonicalRoutesDict']  = _findCanonicalRoutes(shadow_network_db_api.ShdNetworkDB(db, newModelInfoCN['modelId']))
            #print newModelInfoCN['canonicalRoutesDict']
        elif screen in ["people","vaccines","fridges","trucks","setdemand"]:
            uiSession['selectedModelId'] = newModelInfoCN['modelId']
            newModelInfoCN.update({'backNextButtons':True,
                             'title_slogan':_("Create A Model"),
                             'topCaption':{'setdemand':_("What are the vaccine requirements of each population type?")}[screen]#'people':_("Select population types to be used in your model."),
                                           #'vaccines':_("Select vaccine types to be used in your model."),
                                           #'fridges':_("Select cold storage equipment types to be used in your model."),
                                           #'trucks':_("Select trucks and other transport equipment types to be used in your model."),
                                           #'setdemand':_("What are the vaccine requirements of each population type?")
                                           #}[screen]
                             })
        elif screen=="done":
            ### add a tuple to make sure that Joels stuff works
            if len(newModelInfoCN['shippatterns'][0]) > 0:
                newModelInfoCN['shippatterns'].insert(0,())
            #print newModelInfoCN.keys()
            #if 'pottable' in newModelInfoCN.keys():
#             if 'pottable' not in newModelInfoCN.keys():
#                 print "------------------------------------------------------------------resetting"
#                 newModelInfoCN[u'pottable'] = None
#                 newModelIntoCN[u'potrecdict'] = None
            
            if not newModelInfoCN.has_key('modelId') or newModelInfoCN['modelId'] == -1 or len(newModelInfoCN['pottable']) == 0:
                    #print "--------------------------------------------------------------------going home"
                    pot,recDict = _buildPreOrderTree(newModelInfoCN)
                    newModelInfoCN['pottable'] = pot.table
                    newModelInfoCN['potrecdict'] = recDict
                    newModelInfoCN['maxidcode'] = NumberedNameGenerator.totCount
        
        ''' Make sure that we have updated the session so that all of this groovy work is saved '''
        uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']] = newModelInfoCN
        uiSession.changed()
        
        '''
        -------------------------------------------------------------------------------
        Step 6: finally, call the bottle template for the appropriate screen
        --------------------------------------------------------------------------------
        '''
        if screen in screenToTpl:
            import json,copy
            newModelJsonNCT = copy.copy(newModelInfoCN)
            ### Need to remove crumbs, as they will not serialize and are not necessary
            if newModelJsonNCT.has_key('subCrumbTrack'):
                del newModelJsonNCT['subCrumbTrack']
            newModelJson = json.dumps(newModelJsonNCT)
            if screen == "types":
                return bottle.template('types_top.tpl',{'modelId':newModelInfoCN['modelId'],
                                                        'modelName':newModelInfoCN['name'],
                                                        'startClass':'vaccines',
                                                        'breadcrumbPairs':crumbTrack,
                                                        'baseURL':'model-create/types'},
                                                        formVals,pagehelptag=screen,createpipe=True)
                                                        #original baseURL was:
                                                        #'baseURL':'model-add-types'},
                                                        #hack fix above to manually route to the proper URL
                                                        #because I didn't understand how it was being reached
                                                        
            else:
                if newModelInfoCN.has_key('modelId'):
                    formVals['modelId']=newModelInfoCN['modelId']
#                 for key,item in formVals.items():
#                     print "-------------------------------------------{0} = {1}".format(key,item)
                return bottle.template(screenToTpl[screen],formVals,pagehelptag=screen,createpipe=True,modJson = newModelJson)
        elif screen=="models-top":
            ''' If we have no subcrumbtrack, then we can't do anything with this and 
                we should delete it. '''
            if 'subCrumbTrack' not in newModelInfoCN:
                # we're done, or we never started
                if newModelInfoCN['name'] in uiSession['newModelInfo']: 
                    del uiSession['newModelInfo'][newModelInfoCN['name']]
            p = bottle.request.path
            fp = bottle.request.fullpath
            offset = fp.find(p)
            rootPath = fp[:offset+1] # to include slash
            bottle.redirect("%smodels-top"%rootPath)
        elif screen=="model-open":
            #modelId = int(bottle.request.params['id'])
            #newModelInfoCN['modelId']
            #uiSession['modelIdBeingEdited']
            #uiSession['selectedModelId']
            if 'subCrumbTrack' not in newModelInfoCN:
                # we're done, or we never started
                if newModelInfoCN['name'] in uiSession['newModelInfo']: 
                    del uiSession['newModelInfo'][newModelInfoCN['name']]
            p = bottle.request.path
            fp = bottle.request.fullpath
            offset = fp.find(p)
            rootPath = fp[:offset+1] # to include slash
            bottle.redirect("{0}model-open?modelId={1}".format(rootPath,uiSession['selectedModelId']))
        else:
            raise RuntimeError(_("Lost track of which step we are on"))
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        formVals['comment'] = _("An error occurred while provisioning your model: {0}".format(str(e)))
        return bottle.template("problem.tpl",formVals)
        

            
@bottle.route('/list/select-model')
def handleListModel(db,uiSession):
    selectedModelName = None
    if 'selectedModelId' in uiSession:
        selectedModelId = int(uiSession['selectedModelId']) # should be int already, but just in case
    else:
        selectedModelId = None
    if 'selectModel' in bottle.request.params:
        selectedModelId = getParm('selectModel')
        if selectedModelId == 'AllTypesModel':
            selectedModelId = -1
        else:
            selectedModelId = int(selectedModelId)

    includeRef = False
    if 'includeRef' in bottle.request.params:
        includeRef = True
    writeableOnly = _safeGetReqParam(bottle.request.params, 'writeable', isBool=True)
    if includeRef:
        mList = db.query(shd.ShdNetwork)
    else:
        mList = db.query(shd.ShdNetwork).filter(shd.ShdNetwork.refOnly != True)
    mList = mList[:]
    mList = sortModelList(mList)

    s = ""
    prv = uiSession.getPrivs()
    allowedPairs = []

    for m in mList:
        thisId = m.modelId
        name = m.name

        try:
            prv.mayReadModelId(db, thisId) # Exclude models for which we don't have read access
            if writeableOnly:
                prv.mayModifyModelId(db, thisId) # Exclude models for which we don't have read access
            if isSystemDBModel(m):
                name = _("HERMES Database")
                if selectedModelId == -1:
                    selectedModelId = thisId
            allowedPairs.append((thisId,name))
            if selectedModelId is None:
                selectedModelId = thisId
                uiSession['selectedModelId'] = selectedModelId = thisId
                s += "<option value=%d selected>%s</option>\n"%(thisId,name)
                selectedModelName = name
            elif thisId == selectedModelId or selectedModelId is None:
                s += "<option value=%d selected>%s</option>\n"%(thisId,name)
                selectedModelName = name
            else:
                s += "<option value=%d>%s</option>\n"%(thisId,name)
        except privs.PrivilegeException:
            pass
    result = {"menustr":s,"pairs":allowedPairs,"selid":selectedModelId,"selname":selectedModelName}
    # Caller is expected to commit the DB
    return result

@bottle.route('/list/select-model-list')
def handleModelList(db, uiSession):
    """
    this is very similar to select-model but will show models including the system models
    but only models that have anything in the selected types dictionaries and allows you 
    to exclude a model.
    """
    curType = getParm('curType')
    curModel = getParm('curModel')
    ignoreModel = getParm('ignoreModel')
    try: 
        curModel = int(curModel)
    except: pass
    try: 
        ignoreModel = int(ignoreModel)
    except: pass

   
    mList = db.query(shd.ShdNetwork)
     ### Make it so that the all types model is the default to appear
    if not curModel:
         atm = db.query(shd.ShdNetwork).filter(shd.ShdNetwork.name==allTypesModelName).one()
         curModel = atm.modelId
         
    # query objects aren't subclasses of lists so do a shallow copy
    mList = mList[:]
    mList = sortModelList(mList)
    s = ""
    prv = uiSession.getPrivs()
    allowedModels = []
    selModelId = None
    selModelName = None
    allowedPairs = []
    for m in mList:
        try:
            if ignoreModel == m.modelId:
                continue

            prv.mayReadModelId(db, m.modelId) # Exclude models for which we don't have read access
            # get rid of anything that doesn't have appropriate types
            if len(getattr(m, curType)) == 0:
                continue
            
            allowedPairs.append((m.modelId,m.name))
            thisName = m.name
            if isSystemDBModel(m):
                thisName = _("HERMES Database")
            if curModel == m.modelId:
                selModelId = m.modelId
                selModelName = m.name
                s += "<option value=%d selected>%s</option>\n"%(m.modelId,thisName)
            else:
                s += "<option value=%d>%s</option>\n"%(m.modelId,thisName)
        except privs.PrivilegeException:
            pass

    if selModelId is None:
        (selModelId, selModelName) = allowedPairs[0]
    result = {"menustr":s,"pairs":allowedPairs,"selid":selModelId,"selname":selModelName}
    return result
    

@bottle.route('/edit/edit-models.json',method='POST')   
@bottle.route('/edit/edit-models.json')
def jsonEditModels(db,uiSession):
    try:
        if bottle.request.params['oper']=='edit':
            modelId = int(bottle.request.params['id'])
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            if 'name' in bottle.request.params:
                m.name = bottle.request.params['name']
            if 'note' in bottle.request.params:
                m.note = bottle.request.params['note']
            return {'success':True}
        elif bottle.request.params['oper']=='add':
            raise bottle.BottleException("Adding a model is not that simple!")
        elif bottle.request.params['oper']=='del':
            modelId = int(bottle.request.params['id'])
            uiSession.getPrivs().mayWriteModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
            _logMessage("Deleting %s"%m.name)
            db.delete(m)
            return {'success':True}
        else:
            raise bottle.BottleException("Bad parameters to "+bottle.request.path)
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        return {'success':False, 'msg':str(e)}

@bottle.route('/edit/edit-create-model.json',method='POST')        
def editCreateModel(db,uiSession):
    if 'newModelInfo' not in uiSession:
            raise bottle.BottleException(_("We are not creating a new model right now."))
    if 'currentModelName' not in uiSession['newModelInfo'].keys() or uiSession['newModelInfo']['currentModelName'] == "none":
            raise bottle.BottleException(_("We have lost track of the new model you were creating"))
        
    newModelInfoCN = uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']] 
    if 'levelnames' not in newModelInfoCN.keys() or 'pottable' not in newModelInfoCN.keys() or 'potrecdict' not in newModelInfoCN.keys():
        raise bottle.BottleException("Model creation data table is missing")
    
    pot = PreOrderTree(newModelInfoCN['pottable'])
    #print str(pot.table)
    potRecDict = newModelInfoCN['potrecdict']
    needsReload = False
    if bottle.request.params['oper']=='edit':
        if 'idcode'in bottle.request.params:
            idcode = int(bottle.request.params['idcode'])
            lft = int(bottle.request.params['lft'])
            rgt = int(bottle.request.params['rgt'])
            lvl = int(bottle.request.params['level'])
            rec = potRecDict[idcode]

            for k,v in rec.items():
                if k in bottle.request.params:
                    if isinstance(v,types.IntType): rec[k] = int(bottle.request.params[k])
                    else: rec[k] = bottle.request.params[k]
            if 'kids' in bottle.request.params:
                # This edit changes the number of children of this node
                newNKids = int(bottle.request.params['kids'])
                oldNKids = pot.nKids(idcode)
                _logMessage('Changing the number of clients for %d from %d to %d'%(idcode,oldNKids,newNKids))
                needsReload = True
                if oldNKids < newNKids:
                    pot.emit()
                    if lvl < newModelInfoCN['nlevels']-1:
                        cloneLvl = lvl+1
                        for _ in xrange(newNKids-oldNKids):
                            parentId = idcode
                            for lvl,name,count in zip(xrange(cloneLvl,newModelInfoCN['nlevels']),
                                                      newModelInfoCN['levelnames'][cloneLvl:],
                                                      newModelInfoCN['levelcounts'][cloneLvl:]):
                                newModelInfoCN['maxidcode'] += 1
                                newIdcode = newModelInfoCN['maxidcode']
                                pot.add(newIdcode,parentId)
                                newModelInfoCN['levelcounts'][lvl] += 1
                                name = u"%s_%d"%(newModelInfoCN['levelnames'][lvl],newModelInfoCN['levelcounts'][lvl])
                                rec = _buildTreeRec(name,1,newModelInfoCN['shippatterns'][lvl])
                                #print '###### add %d below %d, rec %s'%(newIdcode,parentId,rec)
                                potRecDict[newIdcode] = rec
                                parentId = newIdcode
                        pot.emit()
                    else: raise bottle.BottleException("Requested to add a level below lowest parent")
                elif oldNKids > newNKids:
                    kidList = pot.getKids(idcode)
                    assert len(kidList)==oldNKids, "Inconsistent number of kid nodes"
                    for k in kidList[newNKids:]:
                        _logMessage('Deleting subtree rooted at %d'%k)
                        for deletedNode in pot.removeRecursively(k):
                            del potRecDict[deletedNode]
            # force uiSession to notice the change, and save
            newModelInfoCN['potrecdict'] = potRecDict
            newModelInfoCN['pottable'] = pot.table
            uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']] = newModelInfoCN
            uiSession.changed()
            return {'reload':needsReload}
        else:
            raise bottle.BottleException("Bad parameters to %s"%bottle.request.path)
    else:
        raise bottle.BottleException("Bad parameters to %s"%bottle.request.path)

@bottle.route('/model-open')
def openModel(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        mincrumb = _safeGetReqParam(bottle.request.params,'mincrumb',isBool=True)
        if not mincrumb:
            mincrumb = False
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d' % modelId)
        
        uiSession['selectModelId'] = modelId
        if mincrumb:
            uiSession.getCrumbs().pop()
        uiSession.save()
        
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = m.name
        
        ## Get whether this model may be modified
        modify = False
        try:
            uiSession.getPrivs().mayModifyModelId(db,modelId)
            modify = True
        except:
            pass

        crumbTrack = addCrumb(uiSession,name)
        return bottle.template("model_open.tpl",
                               {"breadcrumbPairs":crumbTrack,
                               'modelId':modelId,
                               'maymodify':modify,
                               'name':name})
    except Exception as e:
        _logStacktrace()
        raise bottle.BottleException(_("Unable to load Open Models Page: {0}".format(str(e))))
    
def _getStoreJITJSON(store):
    return { 'data' : { 'leaf':(store.clients() == []), 'isstore':True },
            'id' : 'store_%d'%store.idcode,
            'name' : '%s'%store.NAME,
            'children' : []
            }

def _getRouteJITJSON(route):    
    return { 'data' : { 'isstore':False, 'routetype':route.Type },
            'id' : 'route_%s'%route.RouteName,
            'name' : '%s'%route.RouteName,
            'children' : []
            }

@bottle.route('/json/model-create-timing-formvals')
def jsonModelCreateTimingFormVals(db, uiSession):
    try:
        if 'newModelInfo' not in uiSession:
            raise bottle.BottleException(_("We are not creating a new model right now."))
        if 'currentModelName' not in uiSession['newModelInfo'].keys() or uiSession['newModelInfo']['currentModelName'] == "none":
            raise bottle.BottleException(_("We have lost track of the new model you were creating"))
        
        newModelInfo = uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']]
        if 'nlevels' not in newModelInfo:
            raise bottle.BottleException(_("We have lost track of the number of levels"))
        if 'shippatterns_transittimes' not in newModelInfo:
            newModelInfo['shippatterns_transittimes'] = [1.0 for i in xrange(newModelInfo['nlevels']-1)] # @UnusedVariable
            uiSession.changed()
        if 'shippatterns_transitunits' not in newModelInfo:
            newModelInfo['shippatterns_transitunits'] = ['hour' for i in xrange(newModelInfo['nlevels']-1)] # @UnusedVariable
            uiSession.changed()
        return {'success':True, 
                'times':newModelInfo['shippatterns_transittimes'],
                'units':newModelInfo['shippatterns_transitunits']
                }
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        return {'success':False, 'msg':str(e)}    

@bottle.route('/json/model-create-timing-verify-commit')
def jsonModelCreateTimingVerifyCommit(db, uiSession):
    try:
#         for k,v in bottle.request.params.items():
#             print '%s: %s'%(k,v)
        if 'newModelInfo' not in uiSession:
            raise bottle.BottleException(_("We are not creating a new model right now."))
        if 'currentModelName' not in uiSession['newModelInfo'].keys() or uiSession['newModelInfo']['currentModelName'] == "none":
            raise bottle.BottleException(_("We have lost track of the new model you were creating"))
        newModelInfo = uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']]
        if 'nlevels' not in newModelInfo:
            raise bottle.BottleException(_("We have lost track of the number of levels"))
        if 'shippatterns_transittimes' not in newModelInfo:
            newModelInfo['shippatterns_transittimes'] = [1.0 for i in xrange(newModelInfo['nlevels']-1)] # @UnusedVariable
        if 'shippatterns_transitunits' not in newModelInfo:
            newModelInfo['shippatterns_transitunits'] = ['hour' for i in xrange(newModelInfo['nlevels']-1)] # @UnusedVariable
        times = []
        units = []
        for i in xrange(newModelInfo['nlevels']-1):
            t = _getOrThrowError(bottle.request.params, 'model_create_timing_%s'%i, isFloat=True)
            if t<=0.0: raise bottle.BottleException(_("Transit times must be greater than zero"))
            times.append( t )
            u = _getOrThrowError(bottle.request.params, 'model_create_timing_units_%s'%i, isTimeUnit=True)
            units.append( u )
        newModelInfo['shippatterns_transittimes'] = times
        newModelInfo['shippatterns_transitunits'] = units
        #uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']]= newModelInfo
        uiSession.changed()
        return {'success':True, 'value':True}
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        return {'success':False, 'msg':str(e)}

@bottle.route('/json/get-selected-model')
def jsonGetSelectedModel(db, uiSession):
    if 'selectedModelId' in uiSession:
        modelId = uiSession['selectedModelId']
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        result = { 'id':modelId, 'name':m.name }
    else:
        result = { 'id':None, 'name':None }
    return result

@bottle.route('/json/set-selected-model')
def jsonSetSelectedModel(db, uiSession):
    try:
        modelId = int(bottle.request.params['id'])
        uiSession['selectedModelId'] = modelId
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = m.name
        if isSystemDBModel(m):
            name = "HERMES Database"
        result = { 'success':True,'id':modelId, 'name':name }
        return result
    except Exception,e:
        return {'success':False, 'msg':str(e)}
        
@bottle.route('/json/manage-models-table')
def jsonManageModelsTable(db, uiSession):
    mList = []
    prv = uiSession.getPrivs()
    for m in db.query(shd.ShdNetwork).filter(shd.ShdNetwork.refOnly != True):
        try:
            prv.mayReadModelId(db, m.modelId)
            mList.append(m)
        except privs.PrivilegeException:
            pass
    nPages,thisPageNum,totRecs,mList = orderAndChopPage([m for m in mList],
                                                        {'modelid':'modelId', 'name':'name', 'notes':'note',
                                                         'id':'modelId'},
                                                        bottle.request)
  
    result = {
              "total":nPages,    # total pages
              "page":thisPageNum,     # which page is this
              "records":totRecs,  # total records
              "rows": [ {"id":m.modelId, 
                         "cell":[m.name, m.modelId, m.note, 
                                 '<a href="%sdownload-model?model=%d&form=zip">%s_%d.zip</a>'%\
                                 (rootPath,m.modelId,m.name,m.modelId),
                                 m.modelId]} 
                       for m in mList ]
              }
    return result


@bottle.route('/json/types-manage-grid')
def jsonGetTypesGrid(db, uiSession):
    modelId = getParm('modelId')
    try:
        modelId = int(modelId)
    except:
        return {
            "total":1,    # total pages
              "page":1,     # which page is this
              "records":0,  # total records
              "rows": [],
              }
       
    uiSession.getPrivs().mayReadModelId(db, modelId)
    model = shadow_network_db_api.ShdNetworkDB(db, modelId)
    flags = 'R'
    try: 
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        flags = 'W'
    except:
        pass

    getType = getParm('type')

    types = getattr(model, getType)
    rowList = []
    for t in types.values():
        if t.Name in typehelper.hiddenTypesSet:
            continue
        row = {}
        row['dispName'] = t.DisplayName
        row['name'] = t.Name
        row['modelId'] = t.modelId
        row['flags'] = flags
        rowList.append(row)

    #rowList = [{'dispName':'disp', 'modelId':'5', 'flags':'R', 'name':'nm'}, 
    #           {'dispName':'disp2', 'modelId':'5', 'flags':'R', 'name':'nm2'},
    #           ]

    (nPages,thisPageNum,totRecs,mList) = orderAndChopPage(rowList,
                                                          {'dispName':'dispName',
                                                           'name':'name',
                                                           'flags':'flags',
                                                           'modelId':'modelId'},
                                                          bottle.request)

    result = {
              "total":nPages,    # total pages
              "page":thisPageNum,     # which page is this
              "records":totRecs,  # total records
              "rows": [ {"id": "%s:%s"%(modelId,b64E(r['name'])), 
                         "cell":[r['dispName'], r['name'], r['modelId'], r['flags']]
                         }
                        for r in mList ]
              }
    return result

@bottle.route('/json/removeD3Model')
def jsonRemoveD3Model(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        m.modelD3Json = None
        db.commit()
        return {'success':True}
    except Exception, e:
        return {'success': False,
                'msg': str(e)}

@bottle.route('/json/copyTypeToModel')
def jsonCopyTypeToModel(db, uiSession):
    try:
        modelId = int(getParm('modelId'))
        srcModelId = int(getParm('srcModelId'))
        typeName = getParm('typeName')

        uiSession.getPrivs().mayModifyModelId(db, modelId)
        dest = shadow_network_db_api.ShdNetworkDB(db, modelId)
        src = shadow_network_db_api.ShdNetworkDB(db, srcModelId)

        typehelper.addTypeToModel(db, dest, typeName, src, True)
    except Exception, e:
        return {'success': False,
                'msg': str(e)}

    return {'success': True}


@bottle.route('/json/removeTypeFromModel')
def jsonRemoveTypeFromModel(db, uiSession):
    try:
        modelId = int(getParm('modelId'))
        typeName = getParm('typeName')
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)

        typehelper.removeTypeFromModel(db, m, typeName, True)
        
        return { 'success' : True }
    except Exception, e:
        _logMessage('Error in jsonRemoveTypeFromModel: %s'%str(e))
        _logStacktrace()
        return { 'success' : False }

@bottle.route('/json/adjust-models-table')
def jsonAdjustModelsTable(db,uiSession):
    if 'newModelInfo' not in uiSession :
        raise bottle.BottleException(_("There is new model data in session."))
    if 'currentModelName' not in uiSession['newModelInfo']:
        raise bottle.BottleException(_("There is no current model in the new model data in session."))
    if uiSession['newModelInfo']['currentModelName'] not in uiSession['newModelInfo'].keys():
        raise bottle.BottleException(_("The currently selected model {0} has no data in session".format(uiSession['newModelInfo']['currentModelName'])))
    if  'levelnames' not in uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']] \
            or 'pottable' not in uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']] \
            or 'potrecdict' not in uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']]:
        raise bottle.BottleException("Model creation data table is missing")
    newModelInfoCN = uiSession['newModelInfo'][uiSession['newModelInfo']['currentModelName']]
    pot = PreOrderTree(newModelInfoCN['pottable'])
    potRecDict = newModelInfoCN['potrecdict']
    _logMessage('For output, potRecDict is %s'%potRecDict)
    if 'nodeid' in bottle.request.params and bottle.request.params['nodeid'] != '':
        nodeId = int(bottle.request.params['nodeid'])
        reqLft = int(bottle.request.params['n_left'])
        reqRgt = int(bottle.request.params['n_right'])
        reqLvl = int(bottle.request.params['n_level']) + 1
        mList = []
        for tblRec in pot.table:
            lkey, rkey, lvl, idcode = tblRec
            if ( lkey>reqLft and rkey<reqRgt ):
                if reqLvl == lvl:
                    r = {'levelname':newModelInfoCN['levelnames'][lvl], 'idcode':idcode, 
                         'level':lvl, 'lft':lkey, 'rgt':rkey, 'isLeaf':(rkey==lkey+1),'expanded':(lvl<2),
                         'kids':pot.nKids(idcode,tpl=(lkey,rkey,lvl))}
                    r.update(potRecDict[idcode])
                    mList.append(r)
    else: # Initial request for root
        lkey, rkey, lvl, idcode = pot.getRoot(returnAll=True)
        r = {'levelname':newModelInfoCN['levelnames'][lvl], 'idcode':idcode, 
             'level':lvl, 'lft':lkey, 'rgt':rkey, 'isLeaf':(rkey==lkey+1),'expanded':(lvl<2),
             'kids':pot.nKids(idcode,tpl=(lkey,rkey,lvl))}
        #print potRecDict[idcode]
        #r.update({'name':potRecDict[idcode]['name'],'ymw':'','isfetch':'','issched':'',
        #          'isfixedam':'','howoften':0})
        r.update(potRecDict[idcode])
        mList=[r]
    nPages = 1
    thisPageNum = 1
    totRecs = len(mList)
    sortKey = bottle.request.params['sidx']
    if bottle.request.params['sord'] == 'asc':
        mList.sort(key=(lambda (x): x[sortKey]))
    else:
        mList.sort(key=(lambda (x): x[sortKey]), reverse=True)
    result = {
              "total":nPages,    # total pages
              "page":thisPageNum,     # which page is this
              "records":totRecs,  # total records
              "rows": [ {"idcode":m['idcode'], "cell":[m['levelname'], m['name'], m['idcode'], 
                                                       fetchdeliver(m['isfetch']),#m['isfetch'],
                                                       scheduleddemand(m['issched']),
                                                       fixedvariable(m['isfixedam']),
                                                       m['howoften'],m['ymw'],m['kids'],
                                                       m['level'],m['lft'],m['rgt'],m['isLeaf']]} 
                       for m in mList ]
              }
    return result

def fetchdeliver(value):
    if value is True or value=="true":
        return _("pick up")
    else:
        return _("recieve")

def fixedvariable(value):
    if value is True or value == "true":
        return _("fixed")
    else:
        return _("variable")
    
def scheduleddemand(value):
    if value is True or value=="true" or value == "scheduled":
        return _("scheduled")
    else:
        return _("demand-based")

def yesNo(value):
    if value == "true":
        return _("yes")
    else:
        return _("no")

@bottle.route('/json/copy-model')
def jsonCopyModel(db,uiSession):
    try:
        srcModelId = int(bottle.request.params['srcModelId'])
        uiSession['selectedModelId'] = srcModelId
        dstName = bottle.request.params['dstName']  
        _logMessage("Request to copy model %d to %s"%(srcModelId,dstName))
        uiSession.getPrivs().mayReadModelId(db, srcModelId)
        srcModel = shadow_network_db_api.ShdNetworkDB(db,srcModelId)
        newModel = srcModel.copy()
        newModel.name = dstName
        db.add(newModel)
        db.flush()
        db.refresh(newModel,['modelId'])
        uiSession.getPrivs().registerModelId(db, newModel.modelId,
                                         uiSession.getDefaultReadGroupID(),uiSession.getDefaultWriteGroupID())                                             
        result = {'success':True, 'value':newModel.modelId}
        return result
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        return {'success':False, 'msg':str(e)}

@bottle.route('/json/add-type-to-model')
def jsonAddTypeToModel(db, uiSession):
    # the UI prevents type name collisions
    modelId = int(bottle.request.params['modelId'])
    typeName = bottle.request.params['name']
    try:
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        typehelper.addTypeToModel(db, modelId, typeName, force=True)
        result = { 'success':True }
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except privs.PrivilegeException:
        result = { 'success':False, 'msg':_('User cannot modify this model')}
    except Exception,e:
        result = { 'success':False, 'msg':str(e)}
    return result
    
@bottle.route('/json/type-check-dependent-types')
def jsonTypeCheckDependentTypes(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        typeName = _getOrThrowError(bottle.request.params,'name')
        return { 'success':True, 'value':typehelper.checkDependentTypes(db, m, typeName) }
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        return { 'success':False, 'msg':str(e)}

@bottle.route('/json/type-check-type-dependencies')
def jsonTypeCheckTypeDependencies(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        typeName = _getOrThrowError(bottle.request.params,'name')
        #print typeName
        return { 'success':True, 
                'value':typehelper.checkTypeDependencies(db, None, m, typeName)}
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        return { 'success':False, 'msg':str(e)}

@bottle.route('/json/remove-type-from-model')
def jsonRemoveTypeFromModelV2(db, uiSession):
    modelId = int(bottle.request.params['modelId'])
    typeName = bottle.request.params['name']
    try:
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        typehelper.removeTypeFromModel(db, modelId,typeName,force=True)
        result = { 'success':True }
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except privs.PrivilegeException:
        result = { 'success':False, 'msg':_('User cannot modify this model')}
    except Exception,e:
        result = { 'success':False, 'msg':str(e)}
    return result
    
@bottle.route('/json/model-info')
def jsonModelInfo(db, uiSession):
    try:
        modelId = int(bottle.request.params['modelId'])
        htmlStr, titleStr = htmlgenerator.getModelInfoHTML(db,uiSession,modelId)
        result = {'success':True, "htmlstring":htmlStr, "title":titleStr}
        return result
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception, e:
        _logStacktrace()
        result = {'success':False, 'msg':str(e)}
        return result
    
@bottle.route('/json/model-store-info')
def jsonModelStoreInfo(db, uiSession):
    modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    nodeRawId = _safeGetReqParam(bottle.request.params,'nodeId')
    if nodeRawId is None:
        raise bottle.BottleException("Ill-formed model-store-info request (node is None)")
    elif nodeRawId.startswith('store_'):
        storeId = int(nodeRawId[6:])
        htmlStr,titleStr = htmlgenerator.getModelStoreInfoHTML(db,uiSession,modelId,storeId)
        result = {"htmlstring":htmlStr, "title":titleStr}
    elif nodeRawId.startswith('route_'):
        routeName = nodeRawId[6:]
        htmlStr,titleStr = htmlgenerator.getModelRouteInfoHTML(db,uiSession,modelId,routeName)
        result = {"htmlstring":htmlStr, "title":titleStr}
    else:
        raise bottle.BottleException("Ill-formed model-store-info request")
    return result


@bottle.route('/json/store-info')
def jsonStoreInfo(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        storeId = _getOrThrowError(bottle.request.params, 'storeId', isInt=True)
        htmlStr, titleStr = htmlgenerator.getModelStoreInfoHTML(db, uiSession, modelId, storeId)
        result = {"success": True, "htmlstring": htmlStr, "title": titleStr}
        return result
    except Exception, e:
        return {"success": False, "msg": str(e)}


@bottle.route('/json/route-info')
def jsonRouteInfo(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        routeName = _getOrThrowError(bottle.request.params, 'routeName')
        htmlStr, titleStr = htmlgenerator.getModelRouteInfoHTML(db, uiSession, modelId, routeName)
        result = {"success": True, "htmlstring": htmlStr, "title": titleStr}
        return result
    except Exception, e:
        return {"success": False, "msg": str(e)}


@bottle.route('/json/model-structure-tree-d3')
def jsonModelStructureTreeD3(db,uiSession):
    try:
        #import locale
        modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        json = model.getModelD3Json()
        if json is None:
            model.addModelD3Json()
            db.commit()
            json = model.getModelD3Json()
        json['success']=True
        
        return json
    except Exception,e:
        return {'success':False,
                'msg':str(e)
                }
        
@bottle.route('/json/model-structure-tree')
def jsonModelStructureTree(db, uiSession):
    modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    nodeRawId = _safeGetReqParam(bottle.request.params,'nodeId')
    level = _safeGetReqParam(bottle.request.params,'level',isInt=True) # value does not seem reliable @UnusedVariable
    nLevels = _safeGetReqParam(bottle.request.params,'nlevels',isInt=True) # @UnusedVariable
    if modelId is None:
        raise bottle.BottleException("modelId is missing")
    else:
        uiSession.getPrivs().mayReadModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        if nodeRawId is None:
            store = model.rootStores()[0]
            result = _getStoreJITJSON(store)
        elif nodeRawId.startswith('store_'):
            storeId = int(nodeRawId[6:])
            store = model.getStore(storeId)
            #store = model.stores[storeId]
            d = {}
            for kidStore,kidRoute in store.clients():
                if kidRoute.RouteName not in d: 
                    d[kidRoute.RouteName] = (kidRoute,[kidStore])
                else:
                    r,sList = d[kidRoute.RouteName]
                    sList.append(kidStore)
                    d[kidRoute.RouteName] = (r,sList)
            result = _getStoreJITJSON(store)
            if not result['data']['leaf']:
                for k,vTuple in d.items():
                    r,sList = vTuple
                    if len(sList) == 1:
                        result['children'].append(_getStoreJITJSON(sList[0]))
                    else:
                        result['children'].append(_getRouteJITJSON(r))
        elif nodeRawId.startswith('route_'):
            routeName = nodeRawId[6:]
            #route = model.routes[routeName]
            route = model.getRoute(routeName)
            result = _getRouteJITJSON(route)
            for store in route.clients():
                result['children'].append(_getStoreJITJSON(store))
    return result

        
@bottle.post('/json/add-loops-to-model',method='POST')
def makeLoopsForModel(db,uiSession):
    try:
        from transformation import makeLoopsOptimizedByDistanceBetweenLevels,setLatenciesByNetworkPosition
        
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        levelFrom = _getOrThrowError(bottle.request.params,'levelFrom',isInt=False)
        levelTo = _getOrThrowError(bottle.request.params,'levelTo',isInt=False)
        numPerLoop = _getOrThrowError(bottle.request.params,'numperloop',isInt=True)
        vehicleType = _getOrThrowError(bottle.request.params,'vehicleToAdd',isInt=False)
        
        uiSession.getPrivs().mayReadModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        makeLoopsOptimizedByDistanceBetweenLevels(model,levelFrom,levelTo,numPerLoop,
                                                 vehicleType=vehicleType)
        
        setLatenciesByNetworkPosition(model,3,stagger=True)
        
        return {'success':True}
    except Exception,e:
        return {'success':False,'msg':str(e)}
@bottle.post('/upload-model')
def uploadModel(db,uiSession):
    _logMessage('Model file upload is happening')
    #uiSession['notes'] += ', upload request'
    fileKey = None
    try:
        info = uploadAndStore(bottle.request, uiSession)
        clientData= makeClientFileInfo(info)
        clientData['code']= 0
        clientData['message']= ""
        clientData['files'] = [{
                                "name": info['shortName'],
                                "size": os.path.getsize(info['serverSideName'])
        }]
        import HermesInput
        from input import UnifiedInput
        unifiedInput = UnifiedInput()
        userInputList,gblDict = HermesInput.extractInputs(info['serverSideName']) # @UnusedVariable
        userInput = userInputList[0]
        shdTypes = shd.ShdTypes()
        shdTypes.loadShdNetworkTypeManagers(userInput, unifiedInput)
        net = shd.loadShdNetwork(userInput, shdTypes, name=info['shortName'])
        net.attachParms(userInput.definitionFileName)
        db.add(net)
        db.flush()
        db.refresh(net,['modelId'])
        uiSession.getPrivs().registerModelId(db, net.modelId,
                                         uiSession.getDefaultReadGroupID(),uiSession.getDefaultWriteGroupID())
        _logMessage("Database insertion was successful!")
        # We now delete the uploaded file.
        #### Create Jsons that will not be reloaded then
        net.addModelD3Json()
        db.commit()
        with uiSession.getLockedState() as state:
            os.remove(info['serverSideName'])
            state.fs().removeFileInfo(info['uploadKey'])
        
        return json.dumps(clientData)
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        _logMessage("\nException: %s"%e)
        _logStacktrace()
        # We could return text which would go into a browser window set as the 'target'
        # for this upload, but there doesn't seem to be much point.
        if fileKey:
            try:
                with uiSession.getLockedState() as state:
                    try:
                        os.remove(info['serverSideName'])
                    except:
                        pass
                    state.fs().removeFileInfo(fileKey)
            except:
                pass
        db.rollback()
        mdata = { 'code': 1, 'message': str(e) }            
        return json.dumps(mdata)

@bottle.route('/json/prepare-download-model')
def prepareDownloadModel(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'model',isInt=True)
        filename = _safeGetReqParam(bottle.request.params,'fname',isInt=False)
        form = _safeGetReqParam(bottle.request.params,'form',isInt=False)
    
        if not form:
            form = "zip"
        
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        
        if not filename:
            filename = "{0}_{1}".format(m.name,modelId)
    
        zipFileName = "{0}.zip".format(filename)
        with uiSession.getLockedState() as state:
            (fileKey, fullZipFileName) = \
                state.fs().makeNewFileInfo(shortName = zipFileName,
                                           fileType = 'application/zip',
                                           deleteIfPresent = True)

        oldHDO = util.redirectOutput(fullZipFileName)
        m.writeCSVRepresentation()
        util.redirectOutput(None,oldHDO)
        return {'success':True,'filename':fullZipFileName,'zipname':zipFileName}
    except Exception as e:
        return {'success':False,'type':'error','msg':str(e)}
    
@bottle.route('/download-model')
def downloadModel(db,uiSession):
    try:
        filename = _getOrThrowError(bottle.request.params,'filename',isInt=False)
        zipFileName = _getOrThrowError(bottle.request.params,'zipfilename',isInt=False)
        
        return bottle.static_file(zipFileName,os.path.dirname(filename),
                                  mimetype='application/zip',download=zipFileName)
    except Exception as e:
        raise bottle.BottleException(e)
        

''' 
Returns a json that gives the names of all of the models in the database
'''
@bottle.route('/json/get-existing-model-names')
def jsonGetExistingModelNames(db,uiSession):
    try:
        mList = []
        idList = []
        #prv = uiSession.getPrivs()

        for m in db.query(shd.ShdNetwork).filter(shd.ShdNetwork.refOnly != True):
            try:
                #prv.mayReadModelId(db, m.name)
                mList.append(m.name)
                idList.append(m.modelId)
            except privs.PrivilegeException:
                pass
        result = {'names':mList,'ids':idList,'success':True}
        return result
    except bottle.HTTPResponse:
        raise
    except Exception as e:
        result = {'success':False, 'msg':str(e)}
        return result  

'''
Returns a json that gives both the models being created in the UISession
and in the database
'''    
@bottle.route('/json/get-existing-models-creating')
def jsonGetModelsBeingCreated(db,uiSession):
    try:
        mList = []
        mmList = []
        if 'newModelInfo' in uiSession:
            mList = uiSession['newModelInfo'].keys()
        
        for m in db.query(shd.ShdNetwork):
            try:
                mmList.append(m.name)
            except privs.PrivilegeException:
                pass
        return {'success':True,'names':mList,'dbnames':mmList}
    except bottle.HTTPResponse:
        raise
    except Exception as e:
        result = {'success':False, 'type':'error', 'msg':str(e)}
        return result 

@bottle.route('/json/get-model-name')
def jsonGetModelName(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        result = {'name':m.name,
                  'success':True}    
        return result
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result    
     
@bottle.route('/json/model-parms-edit')
@bottle.route('/json/model-parms-edit', method='POST')
def jsonRunParmsEdit(db, uiSession):
    modelId = _getOrThrowError(bottle.request.params, 'modelId',isInt=True)
    uiSession.getPrivs().mayModifyModelId(db, modelId)
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)

    badParms,deltas = runhooks._parseRunParms(db, uiSession, m, bottle.request.params)
                
    badStr = None
    if badParms:
        badStr = _("The following parameters are invalid: ")
        for p in badParms: badStr += "%s, "%p
        badStr = badStr[:-2] # trim trailing comma
    if badStr:
        result = {'success':True, 'value':False, 'msg':badStr}
    else:
        parms = m.parms

        for d in deltas:
            (key, typeString, value) = d
            if key in parms:
                parms[key].setValue(value)
            else:
                parms[key] = shd.ShdParameter(key, value)


        result = {'success':True, 'value':True}
    return result

'''
----------------------------------------------------------------------------
These functions create forms for the model creation pipline 
either from a json or from a session dictionary

Currently only the json ones are used, but the session ones are provided for
completeness
----------------------------------------------------------------------------
'''            
@bottle.route('/json/model-create-name-levels-form-from-session')
def jsonCreateLevelsFormFromSession(db,uiSession):
    try:
        name = _getOrThrowError(bottle.request.params,'name',isInt=False)
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'type':'error', 'msg':_("Parameter name not given in this request: ")+str(e)}  
    
    try:
        newModelInfo = jsonGetNewModelInfoFromSession(db,uiSession)['data']
        newModelInfoCN = newModelInfo[name]
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'type':'noname','msg':_("Model Name {0} not in the session: ".format(name))+str(e)}
    
    try:
        import htmlgenerator
        return {'htmlString':"<h5 style='margin-top:0.2px;margin-bottom:0.2px;'>"+_('What are the levels called?')+"</h5>" \
                +"<h6 style='margin-top:0.2px;margin-bottom:1.5px;'>"+_('(e.g., Four level supply chains, the levels may be named Central, Region, District, Health Post)')+"</h6>" \
                + htmlgenerator._buildNameLevelsFormFromSession("model_create", levelInfo = newModelInfoCN),
                'success':True}
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'type':'error','msg':str(e)}
        
@bottle.route('/json/model-create-name-levels-form-from-json',method='post')
def jsonCreateLevelsFromFromJson(db,uiSession):
    try:
        import json
        modelInfoJson = json.load(bottle.request.body)
        
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error', 'msg':_("Problem Updating Session Model parsing json: ") + str(e)}
        return result  
    try:
        import htmlgenerator
        return {'success':True,
                'htmlString':'<span class="levelnames-head">'+ _('Please give each of the levels a name') + '</span>'\
                +'<span class="levelnames-note"><br>'+_('(e.g., Level 1 could be called Central, Level 2 called Regional, etc.)')+'</span>' \
                + htmlgenerator._buildNameLevelsFormFromSession("model_create", levelInfo=modelInfoJson)}
    
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'type':'error','msg':str(e)}
    
@bottle.route('/json/model-create-number-places-per-level-form-from-session')
def jsonCreatePlacesPerLevelFormFromSession(db,uiSession):
    try:
        name = _getOrThrowError(bottle.request.params,'name',isInt=False)
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Parameter name not given in this request: ")+str(e)}  
    
    try:
        newModelInfo = jsonGetNewModelInfoFromSession(db,uiSession)['data']
        newModelInfoCN = newModelInfo[name]
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Model Name {0} not in the session: ".format(name))+str(e)}
    
    try:
        import htmlgenerator
        
        return {'htmlString':'<span class="levelcount-head">'+_("What are the total number of locations within each level?") + "</span>"\
                    +"<span class='levelcount-note'><br>"+_('Include all storage, immunizating and outreach locations')+"</span>" \
                    + htmlgenerator._buildNumberPlacesPerLevelsFormFromSession("model_create_", newModelInfoCN),'success':True}
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':str(e)}

@bottle.route('/json/model-create-number-places-per-level-form-from-json',method='POST')
def jsonCreatePlacesPerLevelFromFromJson(db,uiSession):
    try:
        import json
        modelInfoJson = json.load(bottle.request.body)
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error', 'msg':_("Problem Updating Session Model parsing json: ") + str(e)}
        return result  
    try:
        import htmlgenerator
        return {'htmlString':'<span class="levelcount-head">'+_("Please enter the total number of locations (e.g., storage, immunization, and outreach) for each level.") + "</span>"\
                    + htmlgenerator._buildNumberPlacesPerLevelsFormFromSession("model_create_", modelInfoJson),'success':True}
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':str(e)}    

@bottle.route('/json/model-create-interl-info-form-from-session')
def jsonCreateInterlInfoFormFromSession(db,uiSession):
    try:
        name = _getOrThrowError(bottle.request.params,'name',isInt=False)
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Parameter name not given in this request: ")+str(e)}  
    
    try:
        newModelInfo = jsonGetNewModelInfoFromSession(db,uiSession)['data']
        newModelInfoCN = newModelInfo[name]
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Model Name {0} not in the session: ".format(name))+str(e)}
    
    try:
        ### This is here to check if these things exist as prerequisites to building this table
        levelnames = newModelInfoCN['levelnames']
        levelcounts = newModelInfoCN['levelcounts']
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Model Name {0} prerequisites levelnames and levelcounts not in the session: ".format(name))+str(e)}
    
    try:
        import htmlgenerator
        return{'htmlString':htmlgenerator._buildInterLevelInfoFormFromSession("model_create_",newModelInfoCN),
               'success':True}
        
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Model Name {0} problem creating the interlevelinfo table: ".format(name))+ str(e)} 

@bottle.route('/json/model-create-interl-info-form-from-json',method='POST')
def jsonCreateInterlInfoFormFromJson(db,uiSession):
    try:
        import json
        modelInfoJson = json.load(bottle.request.body)
        name = modelInfoJson['name']
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error', 'msg':_("Problem Updating Session Model parsing json: ") + str(e)}
        return result 
     
    try:
        ### This is here to check if these things exist as prerequisites to building this table
        levelnames = modelInfoJson['levelnames']
        levelcounts = modelInfoJson['levelcounts']
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'type':'error','msg':_("Model Name {0} prerequisites levelnames and levelcounts not in the session: ".format(name))+str(e)}
    
    try:
        import htmlgenerator
        return{'htmlString':htmlgenerator._buildInterLevelInfoFormFromSession("model_create_",modelInfoJson),
               'success':True}
        
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'type':'error','msg':_("Model Name {0} problem creating the interlevelinfo table: ".format(name))+ str(e)} 
    
@bottle.route('/json/model-create-interl-timing-form-from-session')
def jsonCreateInterlTimingFormFromSession(db,uiSession):
    try:
        name = _getOrThrowError(bottle.request.params,'name',isInt=False)
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Parameter name not given in this request: ")+str(e)}  
    
    try:
        newModelInfo = jsonGetNewModelInfoFromSession(db,uiSession)['data']
        newModelInfoCN = newModelInfo[name]
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Model Name {0} not in the session: ".format(name))+str(e)}
    
    try:
        ### This is here to check if these things exist as prerequisites to building this table
        levelnames = newModelInfoCN['levelnames']
        levelcounts = newModelInfoCN['levelcounts']
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Model Name {0} prerequisites levelnames and levelcounts not in the session: ".format(name))+str(e)}
    
    try:
        import htmlgenerator
        return{'htmlString':htmlgenerator._buildInterLevelTimingFormFromSession("model_create_",newModelInfoCN),
               'success':True}
        
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'msg':_("Model Name {0} problem creating the inter level timings table: ".format(name))+ str(e)} 
    
@bottle.route('/json/model-create-interl-timing-form-from-json',method='POST')
def jsonCreateInterlTimingFormFromJson(db,uiSession):
    try:
        import json
        modelInfoJson = json.load(bottle.request.body)
        name = modelInfoJson['name']
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error', 'msg':_("Problem Updating Session Model parsing json: ") + str(e)}
        return result 
     
    try:
        ### This is here to check if these things exist as prerequisites to building this table
        levelnames = modelInfoJson['levelnames']
        levelcounts = modelInfoJson['levelcounts']
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'type':'error','msg':_("Model Name {0} prerequisites levelnames and levelcounts not in the session: ".format(name))+str(e)}
    
    try:
        import htmlgenerator
        return{'htmlString':htmlgenerator._buildInterLevelTimingFormFromSession("model_create_",modelInfoJson),
               'success':True}
        
    except bottle.HTTPResponse:
        raise
    except Exception,e:
        return {'success':False,'type':'error','msg':_("Model Name {0} problem creating the inter level timings table: ".format(name))+ str(e)} 
    
'''
----------------------------------------------------------------------------
Call to update the session from a json
----------------------------------------------------------------------------
'''
@bottle.route('/json/update-uisession-modelInfo',method='post')
def jsonUpdateUISessionModelInfo(db,uiSession):
    try:
        import json
        newModelInfo = json.load(bottle.request.body)
        name = newModelInfo['name']
    
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error', 'msg':_("Problem Updating Session Model parsing json: ") + str(e)}
        return result     
    
    ### Now get the current Session that exists
    try:
        newModelDict = uiSession['newModelInfo']
    
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error', 'msg':_("Problem getting newModelInfo from Session: ") + str(e)}
        return result 
    
    try:
        newModelDictCN = newModelDict[name]
        
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error','msg':_("Updating modelInfo: Session has no model named {0}: ".format(name)) + str(e)}
        return result  
    
    for key in newModelInfo.keys():
        if key == 'modelId':
            if newModelInfo[key] == -1:
                continue
        if key == 'potrecdict':
            ### we have to make sure that the keys are integers as they seem to come through as string
            newPotRecDict = {}
            for pkey,value in newModelInfo['potrecdict'].items():
                newPotRecDict[int(pkey)] = value
            newModelDictCN['potrecdict'] = newPotRecDict
        else:
            newModelDictCN[key] = newModelInfo[key]
    
    uiSession['newModelInfo'][name] = newModelDictCN
    uiSession.changed()
    
    return {'success':True}
      
'''
---------------------------------------------------------------------------
Utility Function that allow one to get a json of the model UISession
---------------------------------------------------------------------------
'''
@bottle.route('/json/get-uisession-modelInfo')
def jsonGetUISessionModelInfo(db,uiSession):
    try:
        newModelDict = uiSession.getDictSummary()['newModelInfo']
            
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error', 'msg':_("Problem getting newModelInfo from Session: ") + str(e)}
        return result 
    
    try:
        name = _getOrThrowError(bottle.request.params,'name',isInt=False)
        newModelDictCN = newModelDict[name]
        return {'success':True,'data':newModelDictCN}
     
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'noname','msg':_("Problem getting {0} model in newModelInfo from Session: ".format(name)) + str(e)}
        return result 

'''
Utility Function to get number of Results Groups for a given modelId (0 means no results available)
'''
@bottle.route('/json/get-results-avail')
def jsonGetModelInfoFromSession(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',isInt=True)
        numberResultsGroups = db.query(shd.HermesResultsGroup).filter(shd.HermesResultsGroup.modelId==modelId).count()
        return {'data':numberResultsGroups,'success':True}
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result   

'''
Utility Function that will get a ModelInfo structure from the uiSession
'''

@bottle.route('/json/get-newmodelinfo-from-session')
def jsonGetNewModelInfoFromSession(db,uiSession):
    try:
        newModelDict = {}
        if 'newModelInfo' in uiSession:
            newModelDict = uiSession.getDictSummary()['newModelInfo']
        
        return {'data':newModelDict,'success':True}
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result    

'''
Utility that deletes a model from the database,
note a model creation has to have begun to use this function
or it will not delete anything
'''
@bottle.route('/json/delete-model-from-newmodelinfo-session')   
def jsonDeleteModelFromNewModelInfo(db,uiSession):
    try:
        modelName = _getOrThrowError(bottle.request.params,'name',isInt=False)
        modelExists = False
        if 'newModelInfo' in uiSession:
            if modelName in uiSession['newModelInfo']:
                del uiSession['newModelInfo'][modelName]
                uiSession.changed()
                mList = []
                #prv = uiSession.getPrivs()
                for m in db.query(shd.ShdNetwork).filter(shd.ShdNetwork.refOnly != True):
                    try:
                        #if m.name == userTypesModelName:
                        #    continue
                            #prv.mayReadModelId(db, m.name)
                        mList.append(m.name)
                
                    except privs.PrivilegeException:
                        pass
                if modelName in mList:
                    modelExists = True 
        return {'success':True,'modelExists':modelExists}
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/get-levels-in-model')
def jsonGetModelLevels(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        levels = m.getLevelList()
        
        return {'success':True,'levels':levels}
    
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

### this is a last minute hack
@bottle.route('/json/get-transport-type-names-in-model')
def jsonGetTransportModelNames(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        nameList = []
        valueList = []
        for key,device in m.types.items():
            if type(device) == shd.ShdTruckType:
                nameList.append(device.getDisplayName())
                valueList.append(device.Name)
    
        return {'success':True,'names':nameList,'values':valueList}
    
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result
    
@bottle.route('/json/does-model-have-coordinates')
def jsonDoesModelHaveCoordinates(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        return {'success':True,'hascoord':m.hasGeoCoordinates()}
    
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result
@bottle.route('/edit/update-model-name-note',method="POST")
def editUpdateModelNameAndNote(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        newName = _getOrThrowError(bottle.request.params,'newName',isInt=False)
        newNote = _getOrThrowError(bottle.request.params,'newNote',isInt=False)
        
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
         
        if m.name != newName:
        ### Check if name exists
            namesJson = jsonGetExistingModelNames(db, uiSession)
            if newName in namesJson['names']:
                return {'success':False,"type":'nameExists',
                        'msg':_('Model Name {0} already exists in the database, please choose another'.format(newName))}
           
            else:
                m.name = newName
        if m.note != newNote:
            m.note = newNote
   
        db.commit()
        return {'success':True}

    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error','msg':str(e)}
        return result    

@bottle.route('/json/get-model-notes',method="POST")
def getModelnotes(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        return {'success':True,'notes':m.note}
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error','msg':str(e)}
        return result   
     
@bottle.route('/json/table-for-store-provision')
def populateTableforStoreProvision(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        levelList = m.getLevelList()
        
        storageList = []
        peopleList = []
        transportList = []
        
        for key,device in m.types.items():
            if type(device) == shd.ShdStorageType:
                if(device.Name != "OUTDOORS"):
                    storageList.append((device.Name,device.getDisplayName()))
            if type(device) == shd.ShdPeopleType:
                peopleList.append((device.Name,device.getDisplayName()))
            if type(device) == shd.ShdTruckType:
                transportList.append((device.Name,device.getDisplayName()))
        
        rows = []
        
        for id,name in storageList:
            rows.append({'type':_('Devices to Store Vaccines at this Level'),'id':id,'name':name})
        for id,name in peopleList:
            rows.append({'type':_('Population To Vaccinate at this Level'),'id':id,'name':name})
        #for id,name in transportList:
        #    rows.append({'type':_('Transport Modes to Use at this Level'),'id':id,'name':name})
            
        ### Make the Level columns
        
        for row in rows:
            for level in levelList:
                row["{0}".format(level)] = 0
                
        return {'success':True,'levels':levelList,'data':{'total':1,'page':1,'records':len(rows),'rows':rows}}
    
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error','msg':str(e)}
        return result  

@bottle.route('/json/provision-stores',method="post")
def provisionStoresFromGrid(db,uiSession):
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        typeDataJSON= _getOrThrowError(bottle.request.params,'itemData')
        resetStores = _safeGetReqParam(bottle.request.params,'reset',isBool=True)
        
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        levelList = m.getLevelList()
        
        typeData = json.loads(typeDataJSON)
        for storeId,store in m.stores.items():
            print storeId
            if not store.isAttached():
                if resetStores:
                    store.clearInventory()
                    store.clearDemand()
                for row in typeData:
                    store.addInventory(row['id'],
                                       int(row[store.CATEGORY]),
                                       row['type']=="Population To Vaccinate at this Level")
                        
        return {'success':True}
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error','msg':str(e)}
        return result  

@bottle.route('/json/provision-routes',method='post')
def assignVehiclesToRoutes(db,uiSession):
    ### This only works with routes that are not loops, would have to make something a bit more complicated to do loops
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        routeDataJSON = _getOrThrowError(bottle.request.params,'routeData')
        
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        routeData = json.loads(routeDataJSON)
        
        ## lets put this is somethign a little easier to parse
        routeDict = {}
        for r in routeData:
            routeDict[(r['l1'],r['l2'])] = (r['vName'],int(r['vcount']))
        
        ### clear all of the transport from the system
        for storeId,store in m.stores.items():
            if not store.isAttached():
                store.clearTransport()
        
        timeDict = {}        
        ## Ok now the logic
        for routeId,route in m.routes.items():
            if len(route.stops) > 2:
                raise "Not written for loops"
            
            if route.Type != 'attached':
                supplierLevel = route.stops[0].store.CATEGORY
                clientLevel = route.stops[1].store.CATEGORY
                vehicle = routeDict[(supplierLevel,clientLevel)][0]
                vcount = routeDict[(supplierLevel,clientLevel)][1]
                
                if route.stops[0].store.countInventory(vehicle) == 0:
                    route.stops[0].store.addInventory(vehicle,vcount)
                route.TruckType = vehicle
                
        return {'success':True}
    
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error','msg':str(e)}
        return result  

        
        
        
        