#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
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
import shadow_network_db_api
import privs
import session_support_wrapper as session_support
import shadow_network
import util
from HermesServiceException import HermesServiceException
from gridtools import orderAndChopPage
from model_edit_hooks import updateDBRouteType
from transformation import setLatenciesByNetworkPosition, setUseVialLatenciesAsOffsetOfShipLatencyFromRoute
import crumbtracks

from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError, _smartStrip

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

@bottle.route('/models-top')
def modelsTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Models")))
    return bottle.template("models_top.tpl",
                           {
                            "breadcrumbPairs":crumbTrack
                            })

@bottle.route('/model-show-structure')
def modelShowStructurePage(db,uiSession):
    if "id" in bottle.request.params:
        modelId = int(bottle.request.params['id'])
        uiSession['selectedModelId'] = modelId
        uiSession['modelIdBeingEdited'] = modelId
    elif 'modelIdBeingEdited' in uiSession:
        modelId = uiSession['modelIdBeingEdited']
    else:
        return bottle.template("problem.tpl",{"comment":_("We have somehow forgotten which model to show."),
                                              "breadcrumbPairs":[("top",_("Welcome")),("models-top",_("Models")),
                                                                 ("model-show-structure",_("Show Structure"))]})
    uiSession.getPrivs().mayReadModelId(db,modelId)
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)
    return bottle.template("model_show_structure.tpl",
                           {"slogan":"Supply Chain Structure Of %s"%m.name,
                            "modelId":m.modelId,
                            "breadcrumbPairs":[("top",_("Welcome")),("models-top",_("Models")),
                                               ("model-show-structure",_("Show Structure"))]})
    
def _doModelEditPage(db, uiSession, editStructure=False):
    if "id" in bottle.request.params:
        modelId = int(bottle.request.params['id'])
        uiSession['selectedModelId'] = modelId
        uiSession['modelIdBeingEdited'] = modelId
        uiSession.save()
    elif 'modelIdBeingEdited' in uiSession:
        modelId = uiSession['modelIdBeingEdited']
    else:
        return bottle.template("problem.tpl",{"comment":"We have somehow forgotten which model to edit.",
                                             "breadcrumbPairs":[("top",_("Welcome")),
                                                                ("models-top",_("Models")),
                                                                ("model-edit",_("Edit"))]})
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
                                                   "breadcrumbPairs":[("top",_("Welcome")),
                                                                      ("models-top",_("Models"))]})

    # we should have a better page than this, possibly the editor with editing
    # disabled.
    if not modify:
        comment = _("This model is read-only.  You may edit a copy of the model " + \
                        "by copying the model and editing that one instead.")
        return bottle.template("problem.tpl", {'comment' : comment,
                                               "breadcrumbPairs":[("top",_("Welcome")),
                                                                  ("models-top",_("Models"))]})
        
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)
    if editStructure:
        template = 'model_edit_structure.tpl'
        lastCrumb = ("model-edit-structure", _("Edit Supply Chain"))
    else:
        template = 'model_edit.tpl'
        lastCrumb = ("model-edit", _("Edit"))

    return bottle.template(template, {"slogan":_("Editing")+" %s"%m.name,
                                      "modelId":m.modelId,
                                      "nr":nr,
                                      "breadcrumbPairs":[("top",_("Welcome")),
                                                         ("models-top",_("Models")),
                                                         lastCrumb]})

@bottle.route('/model-edit')
def modelEditPage(db,uiSession):
    return _doModelEditPage(db, uiSession)

@bottle.route('/model-edit-structure')
def modelEditStructurePage(db, uiSession):
    return _doModelEditPage(db, uiSession, editStructure=True)


def _createModel(db,uiSession):
    if 'newModelInfo' not in uiSession \
            or not all([key in uiSession['newModelInfo'] 
                        for key in ['name','levelnames','pottable','potrecdict',
                                    'shippatterns_transittimes','shippatterns_transitunits']]):
        raise bottle.BottleException(_("Model creation data table is missing or corrupted"))
    newModelInfo = uiSession['newModelInfo']
    shdTypes = shadow_network.ShdTypes()
    shdNetwork = shadow_network.ShdNetwork(None, None, None,shdTypes, newModelInfo['name'] )
    pot = PreOrderTree(newModelInfo['pottable'])
    potRecDict = newModelInfo['potrecdict']
    storeStack = []
    storeDict = {}
    prevLevel = -1
    prevId = None
    pot.table.sort() # Sort to depth-first
    for lkey,rkey,lvl,idcode in pot.table:
        rec = potRecDict[idcode]
        category = newModelInfo['levelnames'][lvl]
        isLeaf = (rkey==lkey+1)
        if isLeaf: 
            fctn = 'Administration'
            useVialsInterval = 1.0
        else: 
            fctn = 'Distribution'
            useVialsInterval = 1.0 # it may get an attached clinic, so we need a valid value
        useVialsLatency = 0.0
        store = shadow_network.ShdStore({'CATEGORY':category, 'FUNCTION':fctn, 'NAME':rec['name'], 'idcode':idcode,
                                         'Inventory':'','Device Utilization Rate':1.0,
                                         'UseVialsInterval':useVialsInterval, 'UseVialsLatency':useVialsLatency},
                                        shdNetwork)
        shdNetwork.addStore(store)
        storeDict[idcode] = store
        if lvl>prevLevel:
            storeStack.append(prevId)
        elif lvl<prevLevel:
            storeStack = storeStack[:-(prevLevel-lvl)]
        if storeStack != []:
            supplierId = storeStack[-1]
            if supplierId is not None:
                if rec['issched']:
                    if rec['isfetch']:
                        routeType = 'schedvarfetch'
                    else:
                        routeType = 'varpush'
                else:
                    if rec['isfetch']:
                        routeType = 'demandfetch'
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
                route = shdNetwork.addRoute({'RouteName':routeName, 'Type':routeType,
                                             'ShipIntervalDays':shipIntervalDays, 'PullOrderAmountDays':shipIntervalDays,
                                             'ShipLatencyDays':shipLatencyDays}, noStops=True)
                ignoredNumber = 17
                transitUnits = newModelInfo['shippatterns_transitunits'][len(storeStack)-2]
                transitTimeRaw = newModelInfo['shippatterns_transittimes'][len(storeStack)-2]
                
                transitHours = {'hour':1.0, 'day':24.0, 'week':168.0, 'month':4704.0, 'year':56448.0}[transitUnits] * transitTimeRaw
                if rec['isfetch']:
                    route.addStop({'idcode':idcode, 'RouteName':routeName, 'RouteOrder':ignoredNumber,
                                   'TransitHours':transitHours},
                                  storeDict)
                    route.addStop({'idcode':supplierId, 'RouteName':routeName, 'RouteOrder':ignoredNumber,
                                   'TransitHours':transitHours},
                                  storeDict)
                else:
                    route.addStop({'idcode':supplierId, 'RouteName':routeName, 'RouteOrder':ignoredNumber,
                                   'TransitHours':transitHours},
                                  storeDict)
                    route.addStop({'idcode':idcode, 'RouteName':routeName, 'RouteOrder':ignoredNumber,
                                   'TransitHours':transitHours},
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

    quotedLevelNames = ["'%s'"%nm for nm in newModelInfo['levelnames']]
    shdNetwork.addParm(shadow_network.ShdParameter('levellist',','.join(quotedLevelNames)))
    shdNetwork.addParm(shadow_network.ShdParameter('cliniclevellist',quotedLevelNames[-1]))
    shdNetwork.addParm(shadow_network.ShdParameter('centrallevellist',quotedLevelNames[0]))
    shdNetwork.addParm(shadow_network.ShdParameter('model','model_generic'))
    shdNetwork.addParm(shadow_network.ShdParameter('demandfile','demand_from_db'))

    # All models have a copy of the OUTDOORS fridge type
    aM = typehelper._getAllTypesModel(db)
    attrRec = {'_inmodel':False, 'modelId':aM.modelId}
    shadow_network._copyAttrsToRec(attrRec, aM.fridges['OUTDOORS'])
    newFridge = shadow_network.ShdStorageType(attrRec.copy()) 
    db.add(newFridge)
    shdNetwork.types[attrRec['Name']] = newFridge
    
    # All models need a copy of the currencyConversion table- grab it from the AllTypesModel
    shdNetwork.addCurrencyTable( aM.getCurrencyTableRecs()[1] )
    
    _logMessage("Created the model '%s'"%newModelInfo['name'])
    return shdNetwork.name,shdNetwork.modelId

def _addLevel(pot, recDict, ngList, countsList, otherList, parent, recBuilder):
    #print '##### _addlevel %s %s %s %s #######'%(ngList,countsList,otherList,parent)
    countsThisLevel = countsList[0]
    baseCountsList = [c/countsThisLevel for c in countsList[1:]]
    leftovers = countsList[1:][:] # copy of the slice
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
        isfetch = False
        issched = True
        howoften = 0
        ymw = "year"
    else:
        isfetch,issched,howoften,ymw = other
    return { 'name':name, 'isfetch':isfetch, 'issched':issched, 'howoften':howoften, 'ymw':ymw }

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
    #print recDict
    return (pot,recDict)

def _checkDefAndInvalidate(reqParams,defDict,name1,name2,invalidateName=None):
    #print '###### check and invalidate <%s> <%s> <%s>'%(name1,name2,invalidateName)
    if name1 in reqParams:
        if name2 in defDict:
            if reqParams[name1]!=defDict[name2]:
                defDict[name2] = reqParams[name1]
                if invalidateName is not None and invalidateName in defDict:
                    del defDict[invalidateName]
        else:
            defDict[name2] = reqParams[name1]
            if invalidateName is not None and invalidateName in defDict:
                del defDict[invalidateName]

def _intCheckDefAndInvalidate(reqParams,defDict,name1,name2,invalidateName=None):
    #print '###### int check and invalidate <%s> <%s> <%s>'%(name1,name2,invalidateName)
    if name1 in reqParams:
        if name2 in defDict:
            if int(reqParams[name1])!=defDict[name2]:
                defDict[name2] = int(reqParams[name1])
                if invalidateName is not None and invalidateName in defDict:
                    del defDict[invalidateName]
        else:
            defDict[name2] = int(reqParams[name1])
            if invalidateName is not None and invalidateName in defDict:
                del defDict[invalidateName]

def _getAscendingList(reqParams,baseName,baseCount=1):
    l = []
    for _ in xrange(baseCount-1): l.append(())
    i = baseCount
    while True:
        s = baseName%i
        if s in reqParams:
            l.append(reqParams[s])
            i += 1
        else:
            break
    return l
        
def _checkAscendingListAndInvalidate(reqParams,defDict,baseName,name2,invalidateName=None,baseCount=1):
    newList = _getAscendingList(reqParams,baseName,baseCount)
    if newList != [] and newList != [()]:
        if name2 in defDict:
            if newList != defDict[name2]:
                defDict[name2] = newList
                if invalidateName is not None and invalidateName in defDict:
                    del defDict[invalidateName]
        else:
            defDict[name2] = newList
            if invalidateName is not None and invalidateName in defDict:
                del defDict[invalidateName]
                
def _intCheckAscendingListAndInvalidate(reqParams,defDict,baseName,name2,invalidateName=None,baseCount=1):
    newList = _getAscendingList(reqParams,baseName,baseCount)
    if newList != [] and newList != [()]:
        l = []
        for term in newList:
            if isinstance(term,types.StringTypes): l.append(int(term))
            else: l.append(term)
        newList = l
        if name2 in defDict:
            if newList != defDict[name2]:
                defDict[name2] = newList
                if invalidateName is not None and invalidateName in defDict:
                    del defDict[invalidateName]
        else:
            defDict[name2] = newList
            if invalidateName is not None and invalidateName in defDict:
                del defDict[invalidateName]

def _boolCheckAscendingListAndInvalidate(reqParams,defDict,baseName,name2,invalidateName=None,baseCount=1):
    newList = _getAscendingList(reqParams,baseName,baseCount)
    if newList != [] and newList != [()]:
        l = []
        for term in newList:
            if isinstance(term,types.StringTypes): 
                if term.lower()=='true': l.append(True)
                elif term.lower()=='false': l.append(False)
                else: raise bottle.BottleException(_('Client returned invalid boolean string {0}').format(term))
            else: l.append(term)
        newList = l
        if name2 in defDict:
            if newList != defDict[name2]:
                defDict[name2] = newList
                if invalidateName is not None and invalidateName in defDict:
                    del defDict[invalidateName]
        else:
            defDict[name2] = newList
            if invalidateName is not None and invalidateName in defDict:
                del defDict[invalidateName]

def _copyStoreProvisions(fromStore, toStore):
    #toStore.copyAttrsFromInstance(fromStore,excludeThese=['NAME','idcode','modelId'])
    toStore.copyAttrsFromRec(fromStore.createRecord(),excludeThese=['NAME','idcode','modelId'])

def _copyRouteProvisions(fromRoute, toRoute, backwards=False):
    if fromRoute==toRoute: return
    assert len(fromRoute.stops)==len(toRoute.stops), _("Route {0} has the wrong number of stops for provisioning").format(toRoute.RouteName)
    for key in ['TruckType','ShipIntervalDays','ShipLatencyDays','Conditions']:
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
        if (l0,l1) in canonicalRouteDict:
            srcRoute = canonicalRouteDict[(l0,l1)]
            assert srcRoute is not None, _("There is no canonical route matching {0}".format(rt.RouteName))
            _copyRouteProvisions(srcRoute, rt)
        elif (l1,l0) in canonicalRouteDict:
            srcRoute = canonicalRouteDict[(l1,l0)]
            assert srcRoute is not None, _("There is no canonical route matching {0} backwards".format(rt.RouteName))
            _copyRouteProvisions(srcRoute, rt, backwards=True)
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
        for j in xrange(i,len(levelNames)):
            d[(levelNames[i],levelNames[j])] = None

    for rt in model.routes.values():
        assert len(rt.stops)==2, _("Route {0} unexpectedly has more than two stops").format(rt.RouteName)
        l0 = rt.stops[0].store.CATEGORY
        l1 = rt.stops[1].store.CATEGORY
        if (l0,l1) in d:
            if d[(l0,l1)] is None: d[(l0,l1)] = rt
        elif (l1,l0) in d:
            if d[(l1,l0)] is None: d[(l1,l0)] = rt
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
def modelCreatePage(db,uiSession,step="unknown"):
    #paramList = ['%s:%s'%(str(k),str(v)) for k,v in bottle.request.params.items()]
    #_logMessage("Hit model_create; step=%s, params=%s"%(step,paramList))

    formVals = { 'breadcrumbPairs':uiSession.getCrumbs() }
    try:
        crumbTrack = uiSession.getCrumbs()
        stepPairs = [('nlevels',_('Start')),
                     ('levelnames',_('Names')),                 
                     ('countsbylevel',_('Counts')),                 
                     ('interlevel',_('Shipping')),                 
                     ('interleveltimes',_('Times')),                 
                     ('done',_('Adjust')),                 
                     ('people',_('Population')),                 
                     ('vaccines',_('Vaccines')),                 
                     ('fridges',_('Storage')),                 
                     ('trucks',_('Transport')),                 
                     ('setdemand',_('Consumption')),                 
                     ('provision',_('Equipment')),                 
                     ('provisionroutes',_('Logistics')),    
                     ]
        namedStepList = [a for a,b in stepPairs] # @UnusedVariable
        screen = None
        if "subCrumbTrack" in uiSession:
            subCrumbTrack = uiSession['subCrumbTrack']
            if crumbTrack.trail[-1] != subCrumbTrack:
                crumbTrack.push(subCrumbTrack)
        else:
            subCrumbTrack = None
        if 'newModelInfo' not in uiSession:
            uiSession['newModelInfo'] = {}
        if step=="unknown":
            if subCrumbTrack is None:
                subCrumbTrack = crumbtracks.TrackCrumbTrail(bottle.request.path, "Create Model")
                for a,b in stepPairs: subCrumbTrack.append((a,b))
                uiSession['subCrumbTrack'] = subCrumbTrack
                crumbTrack.push(subCrumbTrack)
            step = screen = subCrumbTrack.current()
        elif step=='next':
            screen = subCrumbTrack.next()
            if screen is None:
                # We just finished the track
                del uiSession['subCrumbTrack']
                crumbTrack.pop()
                screen = 'models-top'
        elif step=='back':
            screen = subCrumbTrack.back()
            if screen is None:
                # We just backed off the start of the track
                crumbTrack.pop()
                screen = 'models-top'
        else:
            if not crumbTrack.jump(step):
                raise bottle.BottleException("Invalid step %s in model create"%step)
            screen = crumbTrack.current()
    
        newModelInfo = uiSession['newModelInfo']
        reqParams = bottle.request.params
        _checkDefAndInvalidate(reqParams, newModelInfo, 'name', 'name', 'pottable')
        _intCheckDefAndInvalidate(reqParams, newModelInfo, 'nlevels', 'nlevels', 'pottable')
        _checkAscendingListAndInvalidate(reqParams,newModelInfo,'model_create_levelname_%d','levelnames','pottable')
        _intCheckAscendingListAndInvalidate(reqParams,newModelInfo,'model_create_lcounts_%d','levelcounts','pottable')
        _boolCheckAscendingListAndInvalidate(reqParams,newModelInfo,'model_create_interl_isfetch_%d','shippatterns_isfetch','pottable',2)
        _boolCheckAscendingListAndInvalidate(reqParams,newModelInfo,'model_create_interl_issched_%d','shippatterns_issched','pottable',2)
        _intCheckAscendingListAndInvalidate(reqParams,newModelInfo,'model_create_interl_howoften_%d','shippatterns_howoften','pottable',2)
        _checkAscendingListAndInvalidate(reqParams,newModelInfo,'model_create_interl_ymw_%d','shippatterns_ymw','pottable',2)
        if all([k in newModelInfo for k in ['shippatterns_isfetch','shippatterns_issched','shippatterns_howoften','shippatterns_ymw']]):
            shipPatternList = [()] + zip(newModelInfo['shippatterns_isfetch'],newModelInfo['shippatterns_issched'],
                                         newModelInfo['shippatterns_howoften'],newModelInfo['shippatterns_ymw'])[1:]
            newModelInfo['shippatterns'] = shipPatternList
            for k in ['shippatterns_isfetch','shippatterns_issched','shippatterns_howoften','shippatterns_ymw']:
                del newModelInfo[k]
                
        if 'create' in bottle.request.params and bottle.request.params['create'] == 'true':
                if 'modelId' in newModelInfo:
                    # the user is messing around with the back/next buttons
                    pass
                else:
                    newModelInfo['name'],newModelInfo['modelId'] = _createModel(db,uiSession)
        if 'provision' in bottle.request.params and bottle.request.params['provision'] == 'true':
            if 'modelId' in newModelInfo:
                _provisionModel(db, newModelInfo['modelId'])
            else:
                raise RuntimeError(_("The model is not ready for provisioning"))
        if 'provisionroutes' in bottle.request.params and bottle.request.params['provisionroutes'] == 'true':
            if 'modelId' in newModelInfo:
                _provisionModelRoutes(db, newModelInfo['modelId'])
            else:
                raise RuntimeError(_("The routes are not ready for provisioning"))
                    
        formVals = {"breadcrumbPairs":crumbTrack}
        for k in ['name','nlevels','levelnames','levelcounts','shippatterns','modelId']:
            if k in newModelInfo: formVals[k] = newModelInfo[k]
        
        screenToTpl = {"nlevels":"model_create_begin.tpl",
                       "levelnames":"model_create_levelnames.tpl",
                       "countsbylevel":"model_create_countsbylevel.tpl",
                       "interlevel":"model_create_interlevel.tpl",
                       "interleveltimes":"model_create_interlevel_timings.tpl",
                       "done":"model_create_done.tpl",
                       "provision":"model_create_provision.tpl",
                       "provisionroutes":"model_create_provision_routes.tpl",
                       'people':'people_top.tpl',
                       'vaccines':'vaccine_top.tpl',
                       'fridges':'fridge_top.tpl',
                       'trucks':'truck_top.tpl',
                       'setdemand':'demand_top.tpl'
                       }
        
        screenRequires = {"countsbylevel":["levelnames"],
                          "provision":["modelId"],
                          "provisionroutes":["modelId"],
                          "people":["modelId"],
                          "vaccines":["modelId"],
                          "fridges":["modelId"],
                          "trucks":["modelId"],
                          "setdemand":["modelId"],
                          }
        
        if screen in screenRequires:
            for req in screenRequires[screen]:
                if req not in formVals:
                    raise RuntimeError(_("Expected to know the value of {0} by now").format(req))
                
        if screen=="provision":
            formVals['canonicalStoresDict'] = _findCanonicalStores(shadow_network_db_api.ShdNetworkDB(db, formVals['modelId']))
        elif screen=="provisionroutes":
            formVals['canonicalRoutesDict'] = _findCanonicalRoutes(shadow_network_db_api.ShdNetworkDB(db, formVals['modelId']))
        elif screen in ["people","vaccines","fridges","trucks","setdemand"]:
            uiSession['selectedModelId'] = formVals['modelId']
            formVals.update({'backNextButtons':True,
                             'title_slogan':_("Create A Model"),
                             'topCaption':{'people':_("Select population types to be used in your model."),
                                           'vaccines':_("Select vaccine types to be used in your model."),
                                           'fridges':_("Select cold storage equipment types to be used in your model."),
                                           'trucks':_("Select trucks and other transport equipment types to be used in your model."),
                                           'setdemand':_("What are the vaccine requirements of each population type?")
                                           }[screen]
                             })
        elif screen=="done":
            if 'pottable' not in newModelInfo:
                pot,recDict = _buildPreOrderTree(newModelInfo)
                newModelInfo['pottable'] = pot.table
                newModelInfo['potrecdict'] = recDict
                newModelInfo['maxidcode'] = NumberedNameGenerator.totCount
            
        uiSession['newModelInfo'] = newModelInfo
        uiSession.changed()
            
        if screen in screenToTpl:
            return bottle.template(screenToTpl[screen],formVals)
        elif screen=="models-top":
            if 'subCrumbTrack' not in newModelInfo:
                # we're done, or we never started
                if 'newModelInfo' in uiSession: del uiSession['newModelInfo']
            p = bottle.request.path
            fp = bottle.request.fullpath
            offset = fp.find(p)
            rootPath = fp[:offset+1] # to include slash
            bottle.redirect("%smodels-top"%rootPath)
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
    mList = db.query(shadow_network.ShdNetwork)
    pairs = [(p.modelId,p.name) for p in mList]
    pairs.sort()
    s = ""
    prv = uiSession.getPrivs()
    allowedPairs = []
    for thisId,name in pairs: 
        try:
            prv.mayReadModelId(db, thisId) # Exclude models for which we don't have read access
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
    if 'newModelInfo' not in uiSession or 'levelnames' not in uiSession['newModelInfo'] \
            or 'pottable' not in uiSession['newModelInfo'] or 'potrecdict' not in uiSession['newModelInfo']:
        raise bottle.BottleException("Model creation data table is missing")
    newModelInfo = uiSession['newModelInfo']
    pot = PreOrderTree(newModelInfo['pottable'])
    potRecDict = newModelInfo['potrecdict']
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
                    if lvl < newModelInfo['nlevels']-1:
                        cloneLvl = lvl+1
                        for _ in xrange(newNKids-oldNKids):
                            parentId = idcode
                            for lvl,name,count in zip(xrange(cloneLvl,newModelInfo['nlevels']),
                                                      newModelInfo['levelnames'][cloneLvl:],
                                                      newModelInfo['levelcounts'][cloneLvl:]):
                                newModelInfo['maxidcode'] += 1
                                newIdcode = newModelInfo['maxidcode']
                                pot.add(newIdcode,parentId)
                                newModelInfo['levelcounts'][lvl] += 1
                                name = "%s_%d"%(newModelInfo['levelnames'][lvl],newModelInfo['levelcounts'][lvl])
                                rec = _buildTreeRec(name,1,newModelInfo['shippatterns'][lvl])
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
            newModelInfo['potrecdict'] = potRecDict
            newModelInfo['pottable'] = pot.table
            uiSession['newModelInfo'] = newModelInfo
            uiSession.changed()
            return {'reload':needsReload}
        else:
            raise bottle.BottleException("Bad parameters to %s"%bottle.request.path)
    else:
        raise bottle.BottleException("Bad parameters to %s"%bottle.request.path)
        
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
        newModelInfo = uiSession['newModelInfo']
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
        for k,v in bottle.request.params.items():
            print '%s: %s'%(k,v)
        if 'newModelInfo' not in uiSession:
            raise bottle.BottleException(_("We are not creating a new model right now."))
        newModelInfo = uiSession['newModelInfo']
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
        #print times
        #print units
        newModelInfo['shippatterns_transittimes'] = times
        newModelInfo['shippatterns_transitunits'] = units
        uiSession['newModelInfo'] = newModelInfo
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
    modelId = int(bottle.request.params['id'])
    uiSession['selectedModelId'] = modelId
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)
    result = { 'id':modelId, 'name':m.name }
    return result
        
@bottle.route('/json/manage-models-table')
def jsonManageModelsTable(db, uiSession):
    mList = []
    prv = uiSession.getPrivs()
    for m in db.query(shadow_network.ShdNetwork):
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
    
@bottle.route('/json/adjust-models-table')
def jsonAdjustModelsTable(db,uiSession):
    if 'newModelInfo' not in uiSession or 'levelnames' not in uiSession['newModelInfo'] \
            or 'pottable' not in uiSession['newModelInfo'] or 'potrecdict' not in uiSession['newModelInfo']:
        raise bottle.BottleException("Model creation data table is missing")
    newModelInfo = uiSession['newModelInfo']
    pot = PreOrderTree(newModelInfo['pottable'])
    potRecDict = newModelInfo['potrecdict']
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
                    r = {'levelname':newModelInfo['levelnames'][lvl], 'idcode':idcode, 
                         'level':lvl, 'lft':lkey, 'rgt':rkey, 'isLeaf':(rkey==lkey+1),'expanded':(lvl<2),
                         'kids':pot.nKids(idcode,tpl=(lkey,rkey,lvl))}
                    r.update(potRecDict[idcode])
                    mList.append(r)
    else: # Initial request for root
        lkey, rkey, lvl, idcode = pot.getRoot(returnAll=True)
        r = {'levelname':newModelInfo['levelnames'][lvl], 'idcode':idcode, 
             'level':lvl, 'lft':lkey, 'rgt':rkey, 'isLeaf':(rkey==lkey+1),'expanded':(lvl<2),
             'kids':pot.nKids(idcode,tpl=(lkey,rkey,lvl))}
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
              "rows": [ {"idcode":m['idcode'], "cell":[m['levelname'], m['name'], m['idcode'], m['isfetch'], m['issched'],
                                                   m['howoften'],m['ymw'],m['kids'],
                                                   m['level'],m['lft'],m['rgt'],m['isLeaf']]} 
                       for m in mList ]
              }
    return result
    
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
        #print typeName
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
def jsonRemoveTypeFromModel(db, uiSession):
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

@bottle.route('/json/model-structure-tree-d3')
def jsonModelStructureTreeD3(db,uiSession):
    try:
        import locale
        print locale.getdefaultlocale()[1]
        modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        json = model.getWalkOfClientsDictForJson(model.rootStores()[0].idcode)
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

@bottle.post('/upload-model')
def uploadModel(db,uiSession):
    _logMessage('Model file upload is happening')
    #uiSession['notes'] += ', upload request'
    fileKey = None
    try:
        print "Bottle Request: " +str(bottle.request)
        info = uploadAndStore(bottle.request, uiSession)
        clientData= makeClientFileInfo(info)
        clientData['code']= 0
        clientData['message']= ""
        clientData['files'] = [{
                                "name": info['shortName'],
                                "size": os.path.getsize(info['serverSideName'])
        }]
        print "Client Data = " + str(clientData)
        import HermesInput
        from input import UnifiedInput
        unifiedInput = UnifiedInput()
        userInputList,gblDict = HermesInput.extractInputs(info['serverSideName']) # @UnusedVariable
        userInput = userInputList[0]
        shdTypes = shadow_network.ShdTypes()
        shdTypes.loadShdNetworkTypeManagers(userInput, unifiedInput)
        net = shadow_network.loadShdNetwork(userInput, shdTypes, name=info['shortName'])
        net.attachParms(userInput.definitionFileName)
        db.add(net)
        db.flush()
        db.refresh(net,['modelId'])
        uiSession.getPrivs().registerModelId(db, net.modelId,
                                         uiSession.getDefaultReadGroupID(),uiSession.getDefaultWriteGroupID())
        _logMessage("Database insertion was successful!")
        # We now delete the uploaded file.
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
    
@bottle.route('/download-model')
def downloadModel(db,uiSession):
    modelId = int(bottle.request.params['model'])
    uiSession.getPrivs().mayReadModelId(db, modelId)
    m = shadow_network_db_api.ShdNetworkDB(db, modelId)
    zipFileName = "%s_%d.zip"%(m.name,modelId)
    with uiSession.getLockedState() as state:
        (fileKey, fullZipFileName) = \
            state.fs().makeNewFileInfo(shortName = zipFileName,
                                       fileType = 'application/zip',
                                       deleteIfPresent = True)

    oldHDO = util.redirectOutput(fullZipFileName)
    m.writeCSVRepresentation()
    util.redirectOutput(None,oldHDO)
    
    return bottle.static_file(zipFileName,os.path.dirname(fullZipFileName),
                              mimetype='application/zip',download=zipFileName)


@bottle.route('/json/get-existing-model-names')
def jsonGetExistingModelNames(db,uiSession):
    try:
        mList = []
        #prv = uiSession.getPrivs()
        for m in db.query(shadow_network.ShdNetwork):
            try:
                #prv.mayReadModelId(db, m.name)
                mList.append(m.name)
            except privs.PrivilegeException:
                pass
        result = {'names':mList,'success':True}
        return result
    except bottle.HTTPResponse:
        raise
    except Exception as e:
        result = {'success':False, 'msg':str(e)}
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
