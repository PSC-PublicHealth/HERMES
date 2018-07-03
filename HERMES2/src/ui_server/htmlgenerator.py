from views import obsolete
7#!/usr/bin/env python

__doc__ = """htmlgenerator
This module provides routines to gene html from database 
information on the server side, for example model description 
information.

Several functions in this module take fieldMap parameters. See
the documentation for _buildEditFieldTable for details.
"""
_hermes_svn_id_="$Id: htmlgenerator.py 2330 2015-10-07 20:54:08Z stbrown $"

import sys,os,types
from StringIO import StringIO
import ipath
import shadow_network_db_api
import input
from HermesServiceException import HermesServiceException

from ui_utils import _logMessage, _logStacktrace
from session_support_wrapper import inlizer, translateString
import shadow_network
import privs
import typehelper
import minionrunner
from htmlHelper import *
from reporthooks import *

_=translateString

def getModelInfoHTML(db,uiSession,modelId):
    
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    modelJSON = createModelSummaryWSCall(db,uiSession)
    
    titleStr = _("Model {0}").format(modelJSON['name'])
    table = HTMLTable(name_="Model Summary",title_= _("Model Summary Statistics"),width='100%',height='100%', 
                      border='1px solid black')
    table.addRow([_("Facility Statistics")],["m",3])
    table.addRow([_("Level"),_("Total"),_("Vaccinating")],["n",1,1,1])
    levels = modelJSON['orderedLevelList']
    levelCount = modelJSON['fixedLocationCount']
    vaccLevelCount = modelJSON['vaccinationLocationCount']
    for level in levels:
        if level in levelCount.keys():
            tableList = [level,levelCount[level]]
            if level in vaccLevelCount.keys():
                tableList.append(vaccLevelCount[level])
            else:
                tableList.append(0)
            table.addRow(tableList,['c',1,1,1])
    table.addRow([_('All Levels'),levelCount['Total'],vaccLevelCount['Total']],
                 ['n',1,1,1])   
    return table.htmlString(),titleStr

def XgetModelInfoHTML(db,uiSession,modelId):
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)

    titleStr = _("Model {0}").format(model.name)
    
    sio = StringIO()
    sio.write("<h3>\n")
    sio.write("{0}\n".format(model.name))
    sio.write("</h3>\n")
    sio.write("<table>\n")
    sio.write('<tr><td>')
    sio.write(_("Stores"))
    sio.write('</td><td>%d</td></tr>'%len(model.stores))
    sio.write('<tr><td>')
    sio.write(_("Routes"))
    sio.write('</td><td>%d</td></tr>'%len(model.routes))

    for title,attr in [(_("People Types"),model.people),
                       (_("Vaccines"),model.vaccines),          
                       (_("Storage"),model.fridges),
                       (_("Transport"),model.trucks),
                       (_("Packaging"),model.packaging),          
                       (_("Ice"),model.ice),          
                       ]:
        sio.write('<tr><td>')
        sio.write(title)
        sio.write('</td><td>')
        start = True
        for t in attr.keys():
            if start: start=False
            else: sio.write(", ")
            sio.write("%s"%t)
        sio.write('</td></tr>\n')
    
    sio.write("</table>\n")
    
    return sio.getvalue(), titleStr

def getModelStoreInfoHTML(db, uiSession, modelId, storeId):
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    store = model.getStore(storeId)

    titleStr = _("Status of {0} in model {1}").format(store.NAME,model.name)

    sio = StringIO()
    sio.write("<h3>\n")
    sio.write("{0}\n".format(store.NAME))
    sio.write("</h3>\n")
    sio.write("<table>\n")
    attrRec = {}
    shadow_network._copyAttrsToRec(attrRec,store)
    for k,v in attrRec.items(): sio.write('<tr><td>%s</td><td>%s</td>\n'%(k,v))
    sio.write("</table>\n")
    sio.write(_("Inventory\n"))
    sio.write("<table>\n")
    for shdInventory in store.inventory: sio.write('<tr><td>%s</td><td>%s</td>\n'%\
                                                   (shdInventory.invName,shdInventory.count))
    sio.write("</table>\n")
    sio.write(_("Population\n"))
    sio.write("<table>\n")
    for shdInventory in store.demand: sio.write('<tr><td>%s</td><td>%s</td>\n'%\
                                                (shdInventory.invName,shdInventory.count))
    sio.write("</table>\n")
    
    
    return sio.getvalue(), titleStr

def getModelRouteInfoHTML(db, uiSession, modelId, routeName):
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    route = model.getRoute(routeName)
    
    titleStr = _("Status of {0} in model {1}").format(route.RouteName,model.name)
    sio = StringIO()
    sio.write("<h3>\n")
    sio.write(_('Route '))
    sio.write("{0}\n".format(route.RouteName))
    sio.write("</h3>\n")
    sio.write("<table>\n")
    supplierStore = route.supplier()
    clientStoreList = route.clients()
    if supplierStore is None:
        sio.write('<tr><td>%s</td><td>%s</td></tr>' % (_('Supplier'),
                                                       _('None')))
    else:
        sio.write('<tr><td>%s</td><td>%s (%d)</td></tr>' % (_('Supplier'),
                                                            supplierStore.NAME,
                                                            supplierStore.idcode))
    if clientStoreList is None or len(clientStoreList) == 0:
        sio.write('<tr><td>%s</td><td>%s</td></tr>' % (_('Clients'),
                                                       _('None')))
    else:
        start = True
        for clientStore in clientStoreList:
            if start:
                sio.write('<tr><td>%s</td><td>%s (%d)</td></tr>' % (_('Clients'),
                                                                    clientStore.NAME,
                                                                    clientStore.idcode))
                start = False
            else:
                sio.write('<tr><td></td><td>%s (%d)</td></tr>' % (clientStore.NAME,
                                                                  clientStore.idcode))

    attrRec = {}
    shadow_network._copyAttrsToRec(attrRec, route)
    for k, v in attrRec.items():
        if k != 'RouteName':  # because that's obvious
            sio.write('<tr><td>%s</td><td>%s</td>\n' % (k, v))
    sio.write("</table>\n")

    return sio.getvalue(), titleStr

def getPeopleInfoHTML(db,uiSession, modelId, typeName, simple=False):
    from peoplehooks import fieldMap

    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)

    if canWrite:
        titleStr = _("Population Type '{0}' in '{1}'").format(typeName,model.name)
    else:
        titleStr = _("Population Type '{0}'").format(typeName)
    
    if simple:
        htmlStr,titleStr = _buildTypeInfoPopUp(fieldMap, typeInstance, "Population"),None
    else:
        htmlStr,titleStr = _buildTypeInfoBox(fieldMap, typeInstance, "Population"),titleStr
    return htmlStr,titleStr
#_buildTypeInfoBox(fieldMap, typeInstance, "Population"),titleStr

def getStaffInfoHTML(db,uiSession, modelId, typeName,simple=False):
    from staffhooks import fieldMap
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
           
    if canWrite:
        titleStr = _("Staff Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Staff Type {0}").format(typeName)
        
    if simple:
        htmlStr,titleStr = _buildTypeInfoPopUp(fieldMap,typeInstance,"Staff"),None
    else:
        htmlStr,titleStr = _buildTypeInfoBox(fieldMap,typeInstance,"Staff"),titleStr
        
    return htmlStr,titleStr
                             
def getPerDiemInfoHTML(db,uiSession, modelId, typeName,simple=False):
    from perdiemhooks import fieldMap
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    
    if canWrite:
        titleStr = _("PerDiem Type '{0}' in '{1}'").format(typeName,model.name)
    else:
        titleStr = _("PerDiem Type '{0}'").format(typeName)
    
    if simple:
        htmlStr,titleStr = _buildTypeInfoPopUp(fieldMap, typeInstance, _("Per Deim")),None
    else:
        htmlStr,titleStr = _buildTypeInfoBox(fieldMap, typeInstance, _("Per Deim")),titleStr
        
    return htmlStr,titleStr
            
def getVaccineInfoHTML(db, uiSession, modelId, typeName,simple=False):
    from vaccinehooks import fieldMap
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    
    if canWrite:
        titleStr = _("Vaccine Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Vaccine Type {0}").format(typeName)
    
    if simple:
        htmlStr,titleStr = _buildTypeInfoPopUp(fieldMap, typeInstance, "Vaccine"),None
    else:
        htmlStr,titleStr = _buildTypeInfoBox(fieldMap, typeInstance, "Vaccine"),titleStr
    return htmlStr,titleStr

def getFridgeInfoHTML(db, uiSession, modelId, typeName, simple=False):
    from fridgehooks import fieldMap
    canWrite,typeInstance = typehelper.getTypeWithFallback(db, modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db, modelId)

    if canWrite:
        titleStr = _("Storage Device Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Storage Device Type {0}").format(typeName)
    
    
    if simple:
        htmlStr,titleStr = _buildTypeInfoPopUp(fieldMap,typeInstance,"Store Device"),None
    else:
        htmlStr,titleStr = _buildTypeInfoBox(fieldMap,typeInstance,"Storage Device"),titleStr
    
    return htmlStr,titleStr

#_buildTypeInfoBox(fieldMap,typeInstance,"Storage Device"),titleStr

def getIceInfoHTML(db, uiSession, modelId, typeName):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db, modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db, modelId)

    if canWrite:
        titleStr = _("Ice Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Ice Type {0}").format(typeName)
    sio = StringIO()
    sio.write("<h3>\n")
    sio.write("{0}\n".format(typeName))
    sio.write("</h3>\n")
    sio.write("<table>\n")
    attrRec = {}
    shadow_network._copyAttrsToRec(attrRec,typeInstance)
    for k,v in attrRec.items(): 
        sio.write('<tr><td>%s</td><td>%s</td>\n'%(k,v))
    sio.write("</table>\n")
    
    return sio.getvalue(), titleStr

def getPackagingInfoHTML(db, uiSession, modelId, typeName):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db, modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db, modelId)

    if canWrite:
        titleStr = _("Packaging Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Packaging Type {0}").format(typeName)
    sio = StringIO()
    sio.write("<h3>\n")
    sio.write("{0}\n".format(typeName))
    sio.write("</h3>\n")
    sio.write("<table>\n")
    attrRec = {}
    shadow_network._copyAttrsToRec(attrRec,typeInstance)
    for k,v in attrRec.items(): 
        sio.write('<tr><td>%s</td><td>%s</td>\n'%(k,v))
    sio.write("</table>\n")
    
    return sio.getvalue(), titleStr

def getTruckInfoHTML(db, uiSession, modelId, typeName, simple=False):
    from truckhooks import fieldMap
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    
    if canWrite:
        titleStr = _("Transport Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Transport Type {0}").format(typeName)
    
    if simple:
        htmlStr,titleStr = _buildTypeInfoPopUp(fieldMap, typeInstance, _("Transport"),model=model),None
    else:
        htmlStr,titleStr = _buildTypeInfoBox(fieldMap, typeInstance, _("Transport"),model=model),titleStr
        
    return htmlStr,titleStr
#_buildTypeInfoBox(fieldMap, typeInstance, _("Transport"),model=model),titleStr

def getGenericTypeInfoHTML(db, uiSession, modelId, typeName,simple=False):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    category = typeInstance.shdType
    if category=='people': return getPeopleInfoHTML(db, uiSession, modelId, typeName,simple)
    elif category=='trucks': return getTruckInfoHTML(db, uiSession, modelId, typeName,simple)
    elif category=='fridges': return getFridgeInfoHTML(db, uiSession, modelId, typeName,simple)
    elif category=='vaccines': return getVaccineInfoHTML(db, uiSession, modelId, typeName,simple)
    elif category=='ice': return getIceInfoHTML(db, uiSession, modelId, typeName)
    elif category=='packaging': return getPackagingInfoHTML(db, uiSession, modelId, typeName)
    elif category=='staff': return getStaffInfoHTML(db, uiSession, modelId, typeName,simple)
    elif category=='perdiems': return getPerDiemInfoHTML(db, uiSession, modelId, typeName,simple)

def getRunInfoHTML(db, uiSession, tickInfo):
    runName = tickInfo.runName
    

    titleStr = _("Run Information: {0}").format(tickInfo.runDisplayName)
    
    table = HTMLTable(name_='Run Information',title_= _('Run Information'),width='100%',height='100%')
    table.addRow([_('Name'),tickInfo.runDisplayName],['c',1,1])
    table.addRow([_('Model Name'),tickInfo.modelName],['c',1,1])
    table.addRow([_('Starting Time of Run'),tickInfo.starttime],['c',1,1])
    table.addRow([_('Running on the Machine Named'),tickInfo.hostName],['c',1,1])
    table.addRow([_('Under the Proccess Number'),tickInfo.processId],['c',1,1])
    table.addRow([_('Current Run Status'),tickInfo.status],['c',1,1])
    
    return table.htmlString(),titleStr

#     sio = StringIO()
#     sio.write("<h3>\n")
#     sio.write("{0}\n".format(runName))
#     sio.write("</h3>\n")
#     sio.write("<table>\n")
#     for a in tickInfo.attrs:
#         k = a[0]
#         v = getattr(tickInfo, k)
#         sio.write('<tr><td>%s</td><td>%s</td>\n'%(k,v))
#     sio.write("</table>\n")
    
    #return sio.getvalue(), titleStr

def getGeneralStorageInfoHTML(db,uiSession,modelId,locId):
    
    ### Check permissions
    uiSession.getPrivs().mayReadModelId(db,modelId)
    
    ### get the Storage location
    result = db.query(shadow_network.ShdStore).filter(shadow_network.ShdStore.modelId==modelId).one()
    store = result.ShdStore
    model = store.model
    
    print str(result)
    print str(store)
    print str(model)
    
    
def getResultsInfoHTML(db, uiSession, resultsId):
    
    hR = db.query(shadow_network.HermesResults).filter(shadow_network.HermesResults.resultsId==resultsId).one()
    hRG = hR.resultsGroup
    uiSession.getPrivs().mayReadModelId(db, hRG.modelId)
    model = hRG.model

    titleStr = _("Results Set Info")

    sio = StringIO()
#    sio.write("<h3>\n")
#    sio.write(_("Results Set Info")+'\n')
#    sio.write("</h3>\n")
    sio.write("<table>\n")
    sio.write('<tr><td>%s</td><td>%s</td>\n'%(_('Model Name'),model.name))
    sio.write('<tr><td>%s</td><td>%s</td>\n'%(_('Model ID'),hRG.modelId))
    sio.write('<tr><td>%s</td><td>%s</td>\n'%(_('Run Name'),hRG.name))
    sio.write('<tr><td>%s</td><td>%s</td>\n'%(_('Sub-Run'),hR.runNumber))
    sio.write('<tr><td>%s</td><td>%s</td>\n'%(_('Result Type'),hR.resultsType))
    sio.write('<tr><td>%s</td><td>%s</td>\n'%(_('Results ID'),hR.resultsId))
    sio.write("</table>\n")
    
    return sio.getvalue(), titleStr

def _buildRunParmEditFieldTableNew(fieldMap):
    htmlDoc = HTMLDocument("inputfieldmap",_("HERMES Input Parameters"),standAlone_=False)
    htmlForm = HTMLForm("run_parms_edit_form",None,width=800)
    
    ## run through the fields and create the form
    #print fieldMap
    for fME in fieldMap:
        if fME['type'] == 'select':
            pass
        elif fME['type'] in ['int','float','string']:
            htmlForm.addElement(HTMLFormInputBox(fME['key'],fME['label'],fME['value'],fME['type'],True))
        elif fME['type'] == 'bool':
            htmlForm.addElement(HTMLFormSelectBox(fME['key'],fME['label'],
                                                  [('true',True),('false',False)],
                                                  fME['value']))
            #htmlForm.addElement(HTMLFormCheckBox(fME['key'],fME['label'],fME['value'],True))
    htmlDoc.addConstruct(htmlForm)    
    htmlString = htmlDoc.htmlString()
    
    return htmlString

def _buildNameLevelsForm(prefix="",numberOfLevels=4,currentLevelNames=None):
    
    htmlDoc = HTMLDocument("levalnameform",None,standAlone_=False)
    htmlForm = HTMLForm("Level_Names")
    
    print "Number of Levels = " + str(numberOfLevels)
    fillTableNames = []
    if currentLevelNames:
        if len(currentLevelNames) != numberOfLevels:
            return '<p> There was a problem creating the Levels Form</p>'
    
        fillTableNames = currentLevelNames
    else:
#         if numberOfLevels == 3:
#             fillTableNames = [_("Central"),_("District"),_("Health Post")]
#         elif numberOfLevels == 4:
#             fillTableNames = [_("Central"),_("Region"),_("District"),_("Health Post")]
#         elif numberOfLevels == 5:
#             fillTableNames = [_("Central"),_("Province"),_("Region"),_("District"),_("Health Post")]
#         else:
        fillTableNames = [_("Level {0}".format(x+1)) for x in range(0,numberOfLevels)]
    
    for i in range(0,numberOfLevels):
        htmlForm.addElement(HTMLFormInputBox('model_create_levelname_{0}'.format(i+1),
                                             u'Name for Level {0}'.format(i+1),
                                             fillTableNames[i],
                                             'string',
                                             True))
                            
    htmlDoc.addConstruct(htmlForm)
    htmlString = htmlDoc.htmlString()
    
    return htmlString

def _buildNameLevelsFormFromSession(prefix="",levelInfo={},numberOfLevels_=4):
    
    numberOfLevels = numberOfLevels_;
    if levelInfo.has_key('nlevels'):
        numberOfLevels = levelInfo['nlevels']
    
    levelNames = [_("Level {0}".format(x+1)) for x in range(0,numberOfLevels)]
    if levelInfo.has_key('levelnames'):
        levelNames = levelInfo['levelnames']
            
    htmlDoc = HTMLDocument("levalnameform",None,standAlone_=False)
    htmlForm = HTMLForm("Level_Names")
    
    print "Number of Levels = " + str(numberOfLevels)
    
    for i in range(0,numberOfLevels):
        htmlForm.addElement(HTMLFormInputBox('model_create_levelname_{0}'.format(i+1),
                                             _('Name for Level') + u'<span class="levelnames-em"> {0} </span>'.format(i+1),
                                             levelNames[i],
                                             'string',
                                             True))
                            
    htmlDoc.addConstruct(htmlForm)
    htmlString = htmlDoc.htmlString()
    
    return htmlString

### Deprecated
# def _buildNumberPlacesPerLevelsForm(prefix="",levelNames=[],currentLevelNumbers=None):
#     
#     htmlDoc = HTMLDocument("levalplacenumbersform",None,standAlone_=False)
#     htmlForm = HTMLForm("Level_Place_Numbers")
#     
#     fillTableNums = []
#     numberOfLevels = len(levelNames)
#     if currentLevelNumbers:
#         if len(currentLevelNumbers) != numberOfLevels:
#             return '<p> There was a problem creating the Levels Form</p>'
#     
#         fillTableNums = currentLevelNumbers
#     else:
#         fillTableNums = [1 for x in range(0,numberOfLevels)]
#     
#     for i in range(0,numberOfLevels):
#         htmlForm.addElement(HTMLFormInputBox('model_create_lcounts_{0}'.format(i+1),
#                                              'Number of Locations in {0} level'.format(levelNames[i]),
#                                              fillTableNums[i],
#                                              'int',
#                                              True))
#                             
#     htmlDoc.addConstruct(htmlForm)
#     htmlString = htmlDoc.htmlString()
#     
#     return htmlString 

def _buildNumberPlacesPerLevelsFormFromSession(prefix="",levelInfo={},levelNames_=None):
    ### check if I have some prerequisites
    levelNames = []
    if (not levelInfo.has_key('levelnames')):
        if levelNames_ is None:
            return "<p> Building Number of Places Model Create Form: The prerequisites of levelnames and levelcounts are not in the current session.</p>"
        else:
            levelNames = levelNames_
    else:
        levelNames = levelInfo['levelnames']
    
    ### Default is one
    levelCounts = [1 for x in levelNames]
    
    ### if there is info in the info, put it in
    if levelInfo.has_key('levelcounts'):
        levelCounts = [x for x in levelInfo['levelcounts']]
    
    htmlDoc = HTMLDocument("levalplacenumbersform",None,standAlone_=False)
    htmlForm = HTMLForm("Level_Place_Numbers")
    
    for i in range(0,len(levelNames)):
        activated = True
        if i == 0:
            activated = False
        #print "IS THIS ACTIVE: {0}".format(activated)
        htmlForm.addElement(HTMLFormInputBox('model_create_lcounts_{0}'.format(i+1),
                                             _('Number of Locations in')+u'<span class="levelcount-em"> {0} </span> '.format(levelNames[i]) + _('level'),
                                             levelCounts[i],
                                             'int',
                                             activated_=activated,
                                             pretty_=True))
                            
    htmlDoc.addConstruct(htmlForm)
    htmlString = htmlDoc.htmlString()
    
    return htmlString 

def _buildInterLevelInfoFormFromSession(prefix="",levelInfo={}):
    ### check if I have some prerequisites
    if (not levelInfo.has_key('levelnames')) or (not levelInfo.has_key('levelcounts')):
        return "<p> Building Interlevel Model Create Form: The prerequisites of levelnames and levelcounts are not in the current session.</p>"
    
    levelNames = levelInfo['levelnames']
    
    for l in levelNames:
        print type(l)
    
    htmlDoc = HTMLDocument("interlevelinfoform",None,standAlone_=False)
    htmlForm = HTMLForm("Iter_Level_Info_Form",cssclass='interleveltable')

    numberEntries = len(levelNames)-1
    amtEntries = [(_("based on demand"),"false"),(_("the same each shipment"),"true")]
    fetchEntries = [(_("delivered by the supplier"),"false"),(_("picked up by the receiver"),"true")]
    schedEntries = [(_('at a fixed interval'),"true"),(_('when products are needed'),"false")]
    timeEntries = [(_('year'),'year'),(_('month'),'month'),(_('week'),'week')]
    
    sio = StringIO()
    for i in range(0,numberEntries):
        defaultsList = ["false","false","true",12.0,"year"]
        ### lets see if there is existing data in the levelInfo
        if levelInfo.has_key('shippatterns'):
            defaultsList = levelInfo['shippatterns'][i]

        thisString = u'<span class="interleveltablehead">'+_("For routes from the ") + u"<span class='interleveltableem'>" + u'{0}'.format(levelNames[i])\
                    + u"</span> "+ _("to") + u" <span class='interleveltableem'>" + u'{0}'.format(levelNames[i+1]) + u"</span> " + _("levels") + u": <br><br class='smallbr'>"
        htmlForm.addRow([thisString],['N',2])
        htmlForm.addElement(HTMLFormSelectBox(u'model_create_interl_isfetch_{0}'.format(i+1),
                                              _('Products are'),
                                              fetchEntries, str(defaultsList[1]).lower(),
                                              cssclass=u"interleveltable"))
        htmlForm.addElement(HTMLFormSelectBox('model_create_interl_isfixedam_{0}'.format(i+1),
                                              _('for an amount that is'),
                                              amtEntries,str(defaultsList[0]).lower(),
                                              cssclass="interleveltable"))
        htmlForm.addElement(HTMLFormSelectBox('model_create_interl_issched_{0}'.format(i+1),
                                              _('on a schedule that occurs'),
                                              schedEntries,str(defaultsList[2]).lower(),
                                              cssclass="interleveltable"))
        if defaultsList[2]:
            thisHead = _("at a frequency of")
        else:
            thisHead = _("up to a frequency of")
        htmlForm.addElement(HTMLFormInputBox('model_create_interl_howoften_{0}'.format(i+1),
                                              thisHead,
                                              defaultsList[3],
                                              'float'
                                              ,cssclass="interleveltable"))
        htmlForm.addElement(HTMLFormSelectBox('model_create_interl_ymw_{0}'.format(i+1),
                                              _('time(s) per'),
                                              timeEntries, defaultsList[4],
                                              cssclass="interleveltable"))
        htmlForm.addRow([u"<hr>"] ,['N',2])
    htmlDoc.addConstruct(htmlForm)
    sio.write(u'{0}'.format(htmlDoc.htmlString()))
    return sio.getvalue()

def _buildInterLevelTimingFormFromSession(prefix="",levelInfo={}):
    if (not levelInfo.has_key('levelnames')) or (not levelInfo.has_key('levelcounts')):
        return u"<p> Building Interlevel Model Create Form: The prerequisites of levelnames and levelcounts are not in the current session.</p>"
    
    levelNames = levelInfo['levelnames']
    
    
    htmlDoc = HTMLDocument("interltimingform",None,standAlone_=False)
    htmlForm = HTMLForm(u"Iter_Level_Timing_Form",cssclass='interltimingtable')
    
    numberEntries = len(levelNames) - 1
    timeEntries = [(_("year(s)"),'year'),(_("month(s)"),'month'),(_("week(s)"),'week'),
                   (_("day(s)"),'day'),(_("hour(s)"),'hour')]
    
    sio = StringIO()
    for i in range(0,numberEntries):
        defaultList = [1.0,'hour',5.0]
        if levelInfo.has_key('shiptransittimes'):
            defaultList[0] = levelInfo['shiptransittimes'][i]
        if levelInfo.has_key('shiptransitunits'):
            defaultList[1] = levelInfo['shiptransitunits'][i]
        if levelInfo.has_key('shiptransitdist'):
            defaultList[2] = levelInfo['shiptransitdist'][i] 
        
        thisString = u'<span class="interleveltablehead">' \
                         +_("For routes from the ") + u"<span class='interleveltableem'> {0} </span>".format(levelNames[i]) \
                         + _("to") + u"<span class='interleveltableem'> {0} </span>".format(levelNames[i+1])+ _("levels") + u":<br><br>" \
                         + u"</span>"
        htmlForm.addRow([thisString],['N',3])
        
        htmlForm.addRow([_('Trips take on average'),
                        HTMLFormInputBox('model_create_timing_time_{0}'.format(i+1),
                                          '',
                                          defaultList[0],
                                        'float',
                                        cssclass="interleveltable").htmlString(),
                         HTMLFormSelectBox('model_create_timing_units_{0}'.format(i+1),
                                              '',
                                              timeEntries,defaultList[1],
                                              cssclass="interleveltable").htmlString()],
                        ['N',1,1,1]) 
        htmlForm.addRow([_('and have a one way distance of'),
                         HTMLFormInputBox('model_create_timing_distance_{0}'.format(i+1),
                                        '',
                                        defaultList[2],
                                        'float',
                                        cssclass="interleveltable").htmlString(),
                        _('Kilometers')],
                        ['N',1,1,1])  
        htmlForm.addRow([u"<hr>"] ,['N',3])
    
    htmlDoc.addConstruct(htmlForm)
    thisString = htmlDoc.htmlString()
    sio.write(u'{0}'.format(thisString))
    
    return sio.getvalue()

def _buildTypeInfoPopUp(fieldMap,typeInstance,typeName="Type",model=None):
    infoTable = HTMLTable(name="Type Info",
                          title_=None,
                          minwidth='200px',maxwidth='500px',
                          border='0px')
    
    
    #print fieldMap
    for rec in fieldMap:
        ### Do we show this field in the info table
        if rec.has_key('info'):
            if rec['info'] is False:
                continue
    
        recType = rec['type']
        ### Map to HERMES DB for this type (i.e. what it is called in the database
        if rec.has_key('recMap'):
            recKey = rec['recMap']
        else:
            recKey = rec['key']
      
        if recType in ['string','int','float','stringbox']:
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'],getattr(typeInstance,recKey)],['c',1,1])
        if recType in ['scaledfloat']:
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'],float(getattr(typeInstance,recKey))*float(rec['scale'])],['c',1,1])
        elif recType == "select":
            if getattr(typeInstance,recKey):
                ## find the option data
                selOpt = ('None','',[],[])
                for option in rec['options']:
                    if getattr(typeInstance,recKey) == option[0]:
                        selOpt = option
                infoTable.addRow([rec['label'],selOpt[1]],['c',1,1])
        elif recType == 'cost':
            if len(recKey) != 3:
                _logMessage("Unsupported dbKey in cost type in creating info page for {0}: ignoring".format(typeName))
                continue
            if getattr(typeInstance,recKey[0]):
                    if getattr(typeInstance,recKey[1]) and getattr(typeInstance,recKey[2]):
                        costString = "{0} in {2} {1}".format(getattr(typeInstance,recKey[0]), getattr(typeInstance,recKey[1]), getattr(typeInstance,recKey[2]))
                    else:
                        costString = "{0}".format(getattr(typeInstance,recKey[0]))  
                    infoTable.addRow([rec['label'],costString],['c',1,1])
        elif recType == "bool":
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'],'True'],['c',1,1])
            else:
                infoTable.addRow([rec['label'],'False'],['c',1,1])
        elif recType == 'time':
            if getattr(typeInstance, recKey[0]):
                print "Getting recKey[0]: {0}".format(recKey[0])
                timeValue = getattr(typeInstance,recKey[0])
                print "Value = {0}".format(timeValue)
                unitStr = "Months"
                if timeValue < 0.1:
                    timeValue = "No Lifetime"
                else:
                    if getattr(typeInstance, "{0}".format(recKey[1])):
                        if  getattr(typeInstance, "{0}".format(recKey[1])) == "D":
                            unitStr = "Days"
                        timeValue = "{0} {1}".format(timeValue, unitStr)
            else:
                timeValue = "No Lifetime"
            infoTable.addRow([rec['label'], timeValue], ['c', 1, 1])
        elif recType == 'dynamicunit':
            if getattr(typeInstance, recKey[0]):
                Value = "{0}".format(getattr(typeInstance,recKey[0]))
                if getattr(typeInstance,recKey[1]):
                    Value += " {0}".format(getattr(typeInstance,recKey[1]))
                infoTable.addRow([rec['label'], Value], ['c', 1, 1])
        elif recType == 'energy':
            from fridgetypes import energyTranslationDict
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'],energyTranslationDict[getattr(typeInstance,recKey)][1]],['c',1,1])
        elif recType == 'fuel':
            #from trucktypes import fuelTranslationDict
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'] + _(" Type"),rec['fuelDict'][getattr(typeInstance,recKey)][1]],['c',1,1])
        elif recType == 'custtruckstoresum':
            from shadow_network import ShdTruckType
            if not isinstance(typeInstance,ShdTruckType):
                _logMessage("Cannot use custtruckstoresum as a field type for anything other than transport: Ignoring")
                continue
            if model is None:
                _logMessage("Cannot use custtruckstoresum as a field type without specifying a model in the _build call: Ignoring")
                continue
            ### This is a custom type that only works for transport types
            volSum = 0.0
            if getattr(typeInstance,'CoolVolumeCC') != '':
                volSum+= getattr(typeInstance,'CoolVolumeCC')/1000.0
             
            if getattr(typeInstance,'Storage')!='':
                storageList = typeInstance.getStorageDeviceList(model)
                for count,dev in storageList:
                    volSum += count*dev.cooler
             
            infoTable.addRow([rec['label'],"{0}".format(volSum)],['c',1,1])
        
        elif recType == 'custtruckstoragetable':
            from shadow_network import ShdTruckType
            if not isinstance(typeInstance,ShdTruckType):
                _logMessage("Cannot use custtruckstoragetable  as a field type for anything other than transport: Ignoring")
                continue
            if model is None:
                _logMessage("Cannot use custtruckstoragetable as a field type without specifying a model in the _build call: Ignoring")
                continue
            if getattr(typeInstance,"Storage") != '':
                storageList = typeInstance.getStorageDeviceList(model)
                print "###### StorageList for {1} =  {0}".format(storageList,typeInstance.Name)
                firstRow = True
                for count,dev in storageList:
                    '''
                    STB - Need to make flexible for all storage types
                    '''
                    if firstRow:
                        infoTable.addRow(['Storage Devices',"{0} {1}".format("{0}".format(count),dev.DisplayName)],['c',1,1])            
                        firstRow = False
                    else:
                        infoTable.addRow(['',"{0} {1}".format("{0}".format(count),dev.DisplayName)],['c',1,1])
        else:
            _logMessage("Unsupported Field Type, will be ignored in creating info page for {0}".format(typeName))
            
    return infoTable.htmlString()
def _buildTypeInfoBox(fieldMap,typeInstance,typeName="Type",model=None):
    infoTable = HTMLTable(name="Type Info",
                          title_=_("{0} Type Information".format(typeName)),
                          minwidth='500px',maxwidth='700px',
                          border='1px solid black')
    
    
    #print fieldMap
    for rec in fieldMap:
        ### Do we show this field in the info table
        if rec.has_key('info'):
            if rec['info'] is False:
                continue
    
        recType = rec['type']
        ### Map to HERMES DB for this type (i.e. what it is called in the database
        if rec.has_key('recMap'):
            recKey = rec['recMap']
        else:
            recKey = rec['key']
      
        if recType in ['string','int','float','stringbox']:
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'],getattr(typeInstance,recKey)],['c',1,1])
        if recType in ['scaledfloat']:
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'],float(getattr(typeInstance,recKey))*float(rec['scale'])],['c',1,1])
        elif recType == "select":
            if getattr(typeInstance,recKey):
                ## find the option data
                selOpt = ('None','',[],[])
                for option in rec['options']:
                    if getattr(typeInstance,recKey) == option[0]:
                        selOpt = option
                infoTable.addRow([rec['label'],selOpt[1]],['c',1,1])
        elif recType == 'cost':
            if len(recKey) != 3:
                _logMessage("Unsupported dbKey in cost type in creating info page for {0}: ignoring".format(typeName))
                continue
            if getattr(typeInstance,recKey[0]):
                    if getattr(typeInstance,recKey[1]) and getattr(typeInstance,recKey[2]):
                        costString = "{0} in {2} {1}".format(getattr(typeInstance,recKey[0]), getattr(typeInstance,recKey[1]), getattr(typeInstance,recKey[2]))
                    else:
                        costString = "{0}".format(getattr(typeInstance,recKey[0]))  
                    infoTable.addRow([rec['label'],costString],['c',1,1])
        elif recType == "bool":
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'],'True'],['c',1,1])
            else:
                infoTable.addRow([rec['label'],'False'],['c',1,1])
        elif recType == 'time':
            if getattr(typeInstance, recKey[0]):
                print "Getting recKey[0]: {0}".format(recKey[0])
                timeValue = getattr(typeInstance,recKey[0])
                print "Value = {0}".format(timeValue)
                unitStr = "Months"
                if timeValue < 0.1:
                    timeValue = "No Lifetime"
                else:
                    if getattr(typeInstance, "{0}".format(recKey[1])):
                        if  getattr(typeInstance, "{0}".format(recKey[1])) == "D":
                            unitStr = "Days"
                        timeValue = "{0} {1}".format(timeValue, unitStr)
            else:
                timeValue = "No Lifetime"
            infoTable.addRow([rec['label'], timeValue], ['c', 1, 1])
        elif recType == 'dynamicunit':
            if getattr(typeInstance, recKey[0]):
                Value = "{0}".format(getattr(typeInstance,recKey[0]))
                if getattr(typeInstance,recKey[1]):
                    Value += " {0}".format(getattr(typeInstance,recKey[1]))
                infoTable.addRow([rec['label'], Value], ['c', 1, 1])
        elif recType == 'energy':
            from fridgetypes import energyTranslationDict
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'],energyTranslationDict[getattr(typeInstance,recKey)][1]],['c',1,1])
        elif recType == 'fuel':
            #from trucktypes import fuelTranslationDict
            if getattr(typeInstance,recKey):
                infoTable.addRow([rec['label'] + _(" Type"),rec['fuelDict'][getattr(typeInstance,recKey)][1]],['c',1,1])
        elif recType == 'custtruckstoresum':
            from shadow_network import ShdTruckType
            if not isinstance(typeInstance,ShdTruckType):
                _logMessage("Cannot use custtruckstoresum as a field type for anything other than transport: Ignoring")
                continue
            if model is None:
                _logMessage("Cannot use custtruckstoresum as a field type without specifying a model in the _build call: Ignoring")
                continue
            ### This is a custom type that only works for transport types
            volSum = 0.0
            if getattr(typeInstance,'CoolVolumeCC') != '':
                volSum+= getattr(typeInstance,'CoolVolumeCC')/1000.0
             
            if getattr(typeInstance,'Storage')!='':
                storageList = typeInstance.getStorageDeviceList(model)
                for count,dev in storageList:
                    volSum += count*dev.cooler
             
            infoTable.addRow([rec['label'],"{0}".format(volSum)],['c',1,1])
        
        elif recType == 'custtruckstoragetable':
            from shadow_network import ShdTruckType
            if not isinstance(typeInstance,ShdTruckType):
                _logMessage("Cannot use custtruckstoragetable  as a field type for anything other than transport: Ignoring")
                continue
            if model is None:
                _logMessage("Cannot use custtruckstoragetable as a field type without specifying a model in the _build call: Ignoring")
                continue
            if getattr(typeInstance,"Storage") != '':
                storageList = typeInstance.getStorageDeviceList(model)
                firstRow = True
                for count,dev in storageList:
                    '''
                    STB - Need to make flexible for all storage types
                    '''
                    if firstRow:
                        infoTable.addRow(['Storage Devices',"{0} {1}".format("{0}".format(count),dev.DisplayName)],['c',1,1])            
                        firstRow = False
                    else:
                        infoTable.addRow(['',"{0} {1}".format("{0}".format(count),dev.DisplayName)],['c',1,1])
        else:
            _logMessage("Unsupported Field Type, will be ignored in creating info page for {0}".format(typeName))
            
    return infoTable.htmlString()
def _buildEditFieldTableNew(fieldMap,typeInstance=None,model=None,newName=None):
    """
     fieldMap defines the layout of form fields on a page.  It is a 
    list of elements, each of which is a dict.  The following dict 
    elements are recognized:
    
       'row':   a 1-based integer indicating which row on the page 
                hould include the field.  Within a row, fields are 
                displayed in list order.
                
       'label': the label string to be used for the field
       
       'key':   a string used to index fields, and to associate values 
                with this field in JSON transactions
       
       'id':    this string becomes the html id of the field on the 
                field on the client side
       
       'type':  one of ['string','float','int','bool','lifetime','hide',
                'select', 'energy', 'fuel', 'price', 'currency']
       
       'default': default value
       
       'options': if 'type' is 'select', this provides a list of entries 
                  for the select box. Each element of the list is a tuple 
                  of the form:
                  
                      (value,label,enableList,disableList)
                      
                  enableList and disableList are lists of the key strings 
                  of other dicts in the fieldMap that will be enabled or 
                  disabled by setting the select to this particular option.  
                  This provides a mechanism to have form entries appear 
                  and disappear in response to select box settings.
      """
    # Pre-scan to find anything which starts out disabled
    disabledItems = set()
    htmlDoc = HTMLDocument(name_='typeForm',title_='TypeForm')
    editTable = HTMLForm("edit_table", title_=None)
    
    ### if typeInstance is none, then we should create a new type instance for this model
    ## STB do later
    
    for rec in fieldMap:
        ### Do we show this field or not in the edit table
        rowStyleString = "c"
        if rec.has_key('edit'):
            if rec['edit'] is False:
                rowStyleString = "h"
        
        ## Which hrmwidget to use
        
        recType = rec['type']
        formKey = None
        #which database key does this belong to... if this is a complex type, there will be a recmap
        if rec.has_key('recMap'):
            recKey = rec['recMap']
            formKey = rec['key']
        else:
            recKey = rec['key']
        
        label = rec['label'] 
        reqFlag = False
        zeroFlag = False
        if rec['req']:
            requiredString = "<span style='color:red;font-weight:bold;'>*</span>" 
            reqFlag = True
            if rec.has_key('canzero'):
                if rec['canzero']:zeroFlag = True
        else:
            requiredString = "";
        
        defaultVal = None
        if rec.has_key("default"):
            defaultVal = rec['default']
        
        if recType in ['int','float','string','dbkey']:
            if recType == 'dbkey':
                if newName:
                    defaultVal = newName
            default = None
            if defaultVal is None:
                if recType in ['int','float']:
                    default = 0
                else:
                    default = ""
            else:
                default = defaultVal
            if typeInstance is not None:
                default = getattr(typeInstance,recKey)
                if recType == 'string' and default is not None and len(default)>2:
                    print default
                    if default[0] == '"':
                        default = default[1:]
                    if default[-1] =='"':
                        default = default[:-1]
            
            recclass ='notrequired'
            if rec['req']: recclass = 'required_{0}_input'.format(recType)
            if rec.has_key('canzero'):
                if rec['canzero']:recclass += ' canzero'
            
            print recclass
            formElement = HTMLFormInputBox(name_=recKey,
                                           title_="",
                                           default_=default,
                                           type_=recType,
                                           width='350px',
                                           cssclass=recclass
                                           )
                                                                                      
            editTable.addRow([label,formElement.htmlString(),requiredString],[rowStyleString,1,1,1])
        elif recType =='select':
            defaultValue = rec['default']
            if typeInstance is not None and getattr(typeInstance,recKey): defaultValue = getattr(typeInstance,recKey)
            formOptions = [(x[1],x[0]) for x in rec['options']]
            if rec.has_key('none'):
                if rec['none']:
                    formOptions.append(('No Selection','none'))
            formElement = HTMLFormSelectBox(name_=recKey,
                                            title_="",
                                            options_=formOptions,
                                            default_=defaultValue,
                                            width='350px')
            editTable.addRow([label,formElement.htmlString(),requiredString],[rowStyleString,1,1,1])
            
        elif recType == 'bool':
            defaultValue = False
            if typeInstance is not None and getattr(typeInstance,recKey): defaultValue=getattr(typeInstance,recKey)
            
            formElement = HTMLFormCheckBox(name_=recKey,
                                           title_="",
                                           default_=defaultValue)
            editTable.addRow([label,formElement.htmlString(),requiredString],[rowStyleString,1,1,1])
            
        elif recType == 'stringbox':
            defaultValue = ""
            if typeInstance is not None and getattr(typeInstance,recKey): defaultValue = getattr(typeInstance,recKey)
            formElement = HTMLFormTextArea(name_=recKey,
                                                                   title_="",
                                                                   rows_=4,cols_=52,
                                                                   default_=defaultValue)
            
            editTable.addRow([label,formElement.htmlString(),requiredString],[rowStyleString,1,1,1])
            
        elif recType == 'cost':
            defaultValue = "0.0:USD:2011"
            defaults = []
            for key in recKey:
                if typeInstance is not None and getattr(typeInstance,key): defaults.append(getattr(typeInstance,key))
                else: break
            
            #print "Default here = '{0}'".format(defaults[0])
            if len(defaults) == 1:
                defaultValue = "{0}:USD:2011".format(defaults[0])
            elif len(defaults) == 3:
                defaultValue = "{0}:{1}:{2}".format(defaults[0],defaults[1],defaults[2])
             
            dataDict= {'price':recKey[0],'currency':recKey[1],'year':recKey[2],'required':reqFlag,'canzero':zeroFlag}
            divString = "<div class='hrm_costforminput' id='{0}' data-fieldMap='{1}'>{2}</div>".format(formKey,json.dumps(dataDict),defaultValue)   
            
            editTable.addRow([label,divString,requiredString],[rowStyleString,1,1,1])
        elif recType == 'scaledfloat':
            defaultValue = 0.0
            if typeInstance is not None and getattr(typeInstance,recKey): defaultValue = float(getattr(typeInstance,recKey))
            dataDict = {'value':defaultValue,'scalefactor':float(rec['scale']),'required':reqFlag,'canzero':zeroFlag}
            divString = "<div class='hrm_scalefloatinput' id='{0}' data-fieldMap='{1}'></div>".format(recKey,json.dumps(dataDict))
            
            editTable.addRow([label,divString,requiredString],[rowStyleString,1,1,1])
        elif recType == 'time':
            defaultValue = '0:D'
            if defaultVal is not None:
                defaultValue = defaultVal
            
            defaults = []
            for key in recKey:
                if typeInstance is not None and getattr(typeInstance,key):defaults.append(getattr(typeInstance,key))
                else: break
                
            if len(defaults) == 1:
                defaultValue = "{0}:days".format(defaults[0])
            elif len(defaults) == 2:
                defaultValue = "{0}:{1}".format(defaults[0],defaults[1])
                
            dataDict = {'time':recKey[0],'unit':recKey[1],'required':reqFlag,'canzero':zeroFlag}
            divString = "<div class='hrm_timeforminput' id='{0}' data-fieldmap='{1}'>{2}</div>".format(formKey,json.dumps(dataDict),defaultValue)
            editTable.addRow([label,divString,requiredString],[rowStyleString,1,1,1])
        
        elif recType == 'dynamicunit':
            defaultValue = '0:Unknown'
            # # will write a validator for the field maps sepaly
            defaults = []
            for key in recKey:
                if typeInstance is not None and getattr(typeInstance,key):defaults.append(getattr(typeInstance,key))
                else: break
                
            if len(defaults) == 1:
                defaultValue = "{0}:None".format(defaults[0])
            elif len(defaults) == 2:
                defaultValue = "{0}:{1}".format(defaults[0], defaults[1])
            
            dataDict = {'value':recKey[0], 'unit':recKey[1], 'lookup':None, 'lookupdict':None,'required':reqFlag,'canzero':zeroFlag}
            
            if rec.has_key('lookup'):
                dataDict['lookup'] = rec['lookup']
                dataDict['lookupdict'] = rec['lookupDict']
                   
            divString = "<div class='hrm_dynamicunitforminput' id = '{0}' data-fieldmap = '{1}'>{2}</div>".format(formKey,json.dumps(dataDict),defaultValue)
            editTable.addRow([label,divString,requiredString],[rowStyleString,1,1,1])
        
        elif recType == "custtruckstoragetable":
            ## Note, there is no default value for this type
            tName = 'new'
            if typeInstance is not None and getattr(typeInstance,'Name'):
                tName = typeInstance.Name
            dataDict = {'key':recKey,'modelId':model.modelId,'typename':tName,'required':reqFlag}
            divString = "<div class='hrm_truckinventorygrid' id = '{0}' data-fieldmap = '{1}'></div>".format(recKey,json.dumps(dataDict))
            editTable.addRow([label,divString,requiredString],[rowStyleString,1,1,1])
    
    reqstr = '<span style="color:red;font-weight:bold">*</span>' + _(' indicates a required field')      
    editTable.addRow([reqstr],['c',3])                                                                                    
    htmlDoc.addConstruct(editTable)
    return htmlDoc.htmlString()
    


def getTypeEditHTML(db,uiSession,wireType,modelId,protoname,fieldMap,newName=None):
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    if(protoname != "new_type"):
        canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, protoname)
    else:
        typeInstance = None
    
    titleStr = _("This will go in model {0}").format(model.name)
    
    return _buildEditFieldTableNew(fieldMap,typeInstance,model=model,newName=newName), titleStr

    
    
def getRouteDialogHTML(db,uiSession,name="model_route_dialog",genInfo=True,util=True,tripMan=True):
    tabCount =1
    sio=StringIO()
    
    sio.write("<div id='{0}_dialog' class = '{1}_dialog' title='This should get replaced'>".format(name,name))
    sio.write("<div id = '{0}_content'>".format(name))
    sio.write("<ul>")
    if genInfo:
        sio.write(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Route Information')))
        tabCount += 1
    if util:
        sio.write(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Vehicle Utilization')))
        tabCount += 1
    if tripMan:
        sio.write(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Trips')))
        tabCount += 1
        
    sio.write("</ul>")
    tabCount = 1
    if genInfo:
        sio.write("<div id='tab-{0}'><table id='{1}_RGenInfo'></table></div>".format(tabCount,name))
        tabCount += 1
    if util:
        sio.write("<div id='tab-{0}'><table id='{1}_RUtilInfo'></table></div>".format(tabCount,name))
        tabCount += 1
    if tripMan:
        sio.write("<div id='tab-{0}'><table id='{1}_RTripMan'></table><div id='trippager'></div></div>".format(tabCount,name))
        tabCount += 1  
        
    sio.write("</div>")
    sio.write("</div>")
    ### Now add the javascript to load the dialog box
    sio.write("<script>")
    sio.write("$('#{0}_dialog').dialog({{".format(name))
    sio.write("autoOpen:false,") 
    sio.write("height:'auto',")
    sio.write("width:'auto',")
    sio.write("close: function() {")
    sio.write("$('#{0}_content').tabs();".format(name))
    sio.write("    $('#{0}_content').tabs('destroy');".format(name))
    sio.write("    $('#{0}_content').innerHtml = '';".format(name))
    if genInfo:
        sio.write("    $('#{0}_RGenInfo').jqGrid('GridUnload');".format(name))
    if util:
        sio.write("    $('#{0}_RUtilInfo').jqGrid('GridUnload');".format(name))
    if tripMan:
        sio.write("   $('#{0}_RTripMan').jqGrid('GridUnload');".format(name))
    sio.write("$(this).remove();")
    sio.write("var script = document.getElementById('{0}_script');".format(name))
    sio.write("script.parentElement.removeChild(script);")
    sio.write("}")
    sio.write("});")
    
    sio.write("var {0}_meta = new Object();".format(name))
    sio.write("{0}_meta['getResult'] = false;".format(name))
    if genInfo: sio.write("{0}_meta['genInfo'] = true;".format(name))
    if util: sio.write("{0}_meta['utilInfo'] = true; {1}_meta['getResults'] = true;".format(name,name))
    if tripMan: sio.write("{0}_meta['tripMan'] = true;{1}_meta['getResults'] = true;".format(name,name))
    sio.write("</script>")
  
    print type(sio.getvalue())
    return sio.getvalue()
    
        
def getStoreDialogHTML(db,uiSession,name="model_store_dialog",buttonName=None,genInfo=True,util=True,
                       popInfo=True,storeDev=True,
                       transDev=True,invent=True,fillRatio=True,vaccAvail=True,
                       availPlot=True):
    tabCount = 1
    stringList = []
    stringList.append("<div id='%s_dialog' class = '%s_dialog' title='This should get replaced'>"%(name,name))
    stringList.append("<div id = '%s_content'>"%(name))
    stringList.append("<ul>")
    if genInfo:
        stringList.append(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('General Info')))
        tabCount += 1
    if popInfo:
        stringList.append(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Population Information')))
        tabCount += 1
    if util:
        stringList.append(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Utilization')))
        tabCount += 1
    if storeDev:
        stringList.append(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Storage Devices')))
        tabCount += 1
    if transDev:
        stringList.append(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Transport Devices')))
        tabCount += 1
    if invent:
        stringList.append(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Inventory')))
        tabCount += 1
    if fillRatio:
        stringList.append(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Fill Ratio')))
        tabCount += 1
    if vaccAvail:
        stringList.append(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Vaccine Administration')))
        tabCount += 1
    if availPlot:
        stringList.append(u"<li style='font-size:small'><a href='#tab-{0}'>{1}</a></li>".format(tabCount,_('Availability Plot')))
        tabCount += 1
    stringList.append("</ul>")
    tabCount = 1
    if genInfo:
        stringList.append("<div id='tab-%d'><table id='%s_GenInfo'></table></div>"%(tabCount,name))
        tabCount += 1
    if popInfo:
        stringList.append("<div id='tab-%d'><table id='%s_PopInfo'></table></div>"%(tabCount,name))
        tabCount += 1
    if util:
        stringList.append("<div id='tab-%d'><table id='%s_Utilization'></table></div>"%(tabCount,name))
        tabCount += 1
    if storeDev:
        stringList.append("<div id='tab-%d'><table id='%s_StoreDevInfo'></table></div>"%(tabCount,name))
        tabCount += 1
    if transDev:
        stringList.append("<div id='tab-%d'><table id='%s_TransDevInfo'></table></div>"%(tabCount,name))
        tabCount += 1
    if invent:
        stringList.append("<div id='tab-%d'><div id='%s_VialsPlot' style='position:relative;'></div><p align='right'>%s<br>%s</p></div>"%(tabCount,
                                                                                                                                          name,
                                                                                                                                          _('Click on the check mark to add vaccine to Chart'),
                                                                                                                                          _('Click on Name of Vaccine show only it on the Chart.')))
        tabCount += 1  
    if fillRatio:
        stringList.append("<div id='tab-%d'><div id='%s_FillPlot' style='position:relative;'></div><p align='right'>%s<br>%s</p></div>"%(tabCount,
                                                                                                                                               name,
                                                                                                                                          _('Click on the check mark to add storage type to Chart'),
                                                                                                                                          _('Click on Name of storage type show only it on the Chart.')))
        tabCount += 1
    if vaccAvail:
        stringList.append("<div id='tab-%d'><table id='%s_Availability'></table></div>"%(tabCount,name))
        tabCount += 1
    if availPlot:
        stringList.append("<div id='tab-%d'><div id='%s_AvailPlot' style='position:relative;'></div></div>"%(tabCount,name))
        tabCount += 1
    stringList.append("</div>")
    stringList.append("</div>")
    ### Now add the javascript to load the dialog box
    stringList.append("<script id='{0}_script'>".format(name))
    stringList.append("$('#%s_dialog').dialog({"%name)
    stringList.append("autoOpen:false,") 
    stringList.append("height:'auto',")
    stringList.append("width:'auto',")
    stringList.append("close: function() {")
    stringList.append("$('#ajax_busy_image').hide();")
    stringList.append("$('#%s_content').tabs();"%name)
    stringList.append("    $('#%s_content').tabs('destroy');"%name)
    stringList.append("    $('#%s_content').innerHtml = '';"%name)
    if genInfo:
        stringList.append("    $('#%s_GenInfo').jqGrid('GridUnload');"%name)
    if popInfo:
        stringList.append("    $('#%s_PopInfo').jqGrid('GridUnload');"%name)
    if util:
        stringList.append("   $('#%s_Utilization').jqGrid('GridUnload');"%name)
    if storeDev:
        stringList.append("   $('#%s_StoreDevInfo').jqGrid('GridUnload');"%name)
    if transDev:
        stringList.append("   $('#%s_TransDevInfo').jqGrid('GridUnload');"%name)
    if vaccAvail:
        stringList.append("   $('#%s_Availability').jqGrid('GridUnload');"%name)
    stringList.append("$(this).remove();")
    stringList.append("var script = document.getElementById('{0}_script');".format(name))
    stringList.append("script.parentElement.removeChild(script);")
    stringList.append("}")
    stringList.append("});")
    
    stringList.append("var %s_meta = new Object();"%name)
    stringList.append("%s_meta['getResult'] = false;"%name)
    if genInfo: stringList.append("%s_meta['genInfo'] = true;"%name)
    if util: stringList.append("%s_meta['utilInfo'] = true; %s_meta['getResults'] = true;"%(name,name))
    if popInfo: stringList.append("%s_meta['popInfo'] = true;"%name)
    if storeDev: stringList.append("%s_meta['storeDev'] = true;"%name)
    if transDev: stringList.append("%s_meta['transDev'] = true;"%name)
    if vaccAvail: stringList.append("%s_meta['vaccAvail'] = true;%s_meta['getResults'] = true;"%(name,name))
    if fillRatio: stringList.append("%s_meta['fillRatio'] = true;%s_meta['getResults'] = true;"%(name,name))
    if invent: stringList.append("%s_meta['invent'] = true;"%name)
    if availPlot: stringList.append("%s_meta['availPlot'] = true;%s_meta['getResults'] = true;"%(name,name))
    stringList.append("</script>")
    return "".join(stringList)


''''
obsolete
def _buildEditFieldTable(fieldMap):
    """
    fieldMap defines the layout of form fields on a page.  It is a 
    list of elements, each of which is a dict.  The following dict 
    elements are recognized:
    
       'row':   a 1-based integer indicating which row on the page 
                should include the field.  Within a row, fields are 
                displayed in list order.
                
       'label': the label string to be used for the field
       
       'key':   a string used to index fields, and to associate values 
                with this field in JSON transactions
       
       'id':    this string becomes the html id of the field on the 
                field on the client side
       
       'type':  one of ['string','float','int','bool','lifetime','hide',
                'select', 'energy', 'fuel', 'price', 'currency']
       
       'default': default value
       
       'options': if 'type' is 'select', this provides a list of entries 
                  for the select box. Each element of the list is a tuple 
                  of the form:
                  
                      (value,label,enableList,disableList)
                      
                  enableList and disableList are lists of the key strings 
                  of other dicts in the fieldMap that will be enabled or 
                  disabled by setting the select to this particular option.  
                  This provides a mechanism to have form entries appear 
                  and disappear in response to select box settings.
      """
    
    # Pre-scan to find anything which starts out disabled
    disabledItems = set()
    for d in fieldMap:
        if d['type'] == 'select':
            if 'value' in d:
                for val,txt,enabledList,disabledList in d['options']:      # @UnusedVariable
                    if val==d['value']: disabledItems.update(disabledList)
            elif 'default' in d:
                for val,txt,enabledList,disabledList in d['options']:      # @UnusedVariable
                    if val==d['default']: disabledItems.update(disabledList)
            elif len(d['options'])>0:
                val,txt,enabledList,disabledList = d['options'][0] # first entry selected by default @UnusedVariable
                disabledItems.update(disabledList)
        
    maxRow = max([d['row'] for d in fieldMap])
    sio = StringIO()
    sio.write("<table class='hrm_edittype'>\n")
    for row in xrange(1,maxRow+1):
        subSlots = [d for d in fieldMap if d['row']==row and d['type']!='hide']
        sio.write("<tr>\n")
        for d in subSlots: sio.write("  <th>%s</th>\n"%d['label'])
        sio.write("</tr>\n")
        sio.write("<tr>\n")
        for d in subSlots:
            if d['id'] in disabledItems: hideStr = 'style="display:none"'
            else: hideStr = ""
            if 'value' in d and d['value'] is not None and d['value']!="": oldVal = d['value']
            elif 'default' in d: oldVal = d['default']
            else: oldVal = None
            
            if d['type'] == 'int':
                if oldVal is not None:
                    sio.write('  <td><input type=number value="%s" id="%s" %s></td>\n'%(oldVal,d['id'],hideStr))
                else:
                    sio.write('  <td><input type=number value="0" id="%s" %s></td>\n'%(d['id'],hideStr))
                    
            elif d['type'] == 'string':
                if oldVal is not None:
                    if isinstance(oldVal,types.ListType) :
                        s = ",".join([str(v).replace('"','&quot;') for v in oldVal])
                        escapedStr= str(s)
                    else:
                        #print 'oldVal: %s <%s>'%(type(oldVal),oldVal)
                        escapedStr = oldVal.replace('"','&quot;')
                    sio.write('  <td><input type=text value="%s" id="%s" %s></td>\n'%(escapedStr,d['id'],hideStr))
                else:
                    sio.write('  <td><input type=text id="%s" %s></td>\n'%(d['id'],hideStr))
                    
            elif d['type'] == 'float':
                if oldVal is not None:
                    sio.write('  <td><input type=text value="%s" id="%s" onkeypress="validateFloat(event)" %s></td>\n'%\
                              (oldVal,d['id'],hideStr))
                else:
                    sio.write('  <td><input type=text value="0.0" id="%s" onkeypress="validateFloat(event)" %s></td>\n'%(d['id'],hideStr))
                    
            elif d['type'] == 'price':
                if oldVal is not None:
                    sio.write(' <td><div class="hrm_costforminput" id="%s" %s>0.5:USD:2001</div></td>\n'%(d['id'],hideStr))
                   # sio.write('  <td><input class="hrm_price" type=text value="%s" id="%s" onkeypress="validateFloat(event)" %s></td>\n'%(oldVal,d['id'],hideStr))
                else:
                    sio.write(' <td><div class="hrm_costforminput" id="%s" %s>0.5:USD:2001</td>\n'%(d['id'],hideStr))
                   # sio.write('  <td><input class="hrm_price" type=text value="0.0" id="%s" onkeypress="validateFloat(event)" %s></td>\n'%(d['id'],hideStr))
                    
            elif d['type'] == 'bool':
                if oldVal: # True
                    sio.write('  <td><input type=checkbox checked id="%s" %s></td>\n'%(d['id'],hideStr))
                else: # False, or default
                    sio.write('  <td><input type=checkbox id="%s" %s></td>\n'%(d['id'],hideStr))
                    
            elif d['type'] == 'select':
                sio.write('<td><select id="%s" %s>\n'%(d['id'],hideStr))
                for val,txt,enableList,disableList in d['options']:
                    if oldVal==val:
                        sio.write('  <option value="%s" selected data-enable="%s" data-disable="%s">%s</option>\n'%\
                                  (val, ','.join(enableList), ','.join(disableList), txt))
                    else:
                        sio.write('  <option value="%s" data-enable="%s" data-disable="%s">%s</option>\n'%\
                                  (val, ','.join(enableList), ','.join(disableList), txt))
                sio.write('</select></td>\n')
            elif d['type'] == 'lifetime':
                if oldVal is not None:
                    val,units = oldVal
                    sio.write('  <td><div class="hrm_lifetime" %s><input type=text value="%s" id="%s" onkeypress="validateFloat(event)" >\n'%\
                              (hideStr,val,d['id']))
                    if units=='D':
                        sio.write('  <select id="%s_units"><option value="D" selected>%s</option><option value="W">%s</option><option value="M">%s</option></select></div></td>\n'%\
                                  (d['id'],_("Days"),_("Weeks"),_("Months")))
                    elif units=='W':
                        sio.write('  <select id="%s_units"><option value="D">%s</option><option value="W" selected>%s</option><option value="M">%s</option></select></div></td>\n'%\
                                  (d['id'],_("Days"),_("Weeks"),_("Months")))
                    elif units=='M':
                        sio.write('  <select id="%s_units"><option value="D">%s</option><option value="W">%s</option><option value="M" selected>%s</option></select></div></td>\n'%\
                                  (d['id'],_("Days"),_("Weeks"),_("Months")))
                    else:
                        raise RuntimeError("Nonsense lifetime units code %s"+units)
                else:
                    sio.write('  <td><div %s class="hrm_lifetime"><input type=text id="%s" onkeypress="validateFloat(event)" %s>\n'%\
                              (hideStr,d['id'],hideStr))
                    sio.write('  <select id="%s_units"><option value="D">%s</option><option value="W">%s</option><option value="M">%s</option></select></div></td>\n'%\
                              (d['id'],_("Days"),_("Weeks"),_("Months")))
            elif d['type'] == 'currency':
                if oldVal is None:
                    sio.write('  <td><div class="hrm_costforminput" id="%s" %s> %s </td>\n'%(d['id'],hideStr,''))
                   # sio.write('  <td><div class="hrm_costformInput" id="%s" %s> 1.0:USD:2003 </td>\n'%(d['id'],hideStr,''))

                else:
                    #print 'oldVal: %s <%s>'%(type(oldVal),oldVal)
                    #sio.write(' <td><div class="hrm_costforminput" id="%s" %s>0.5:USD:2001</td>\n'%(d['id'],hideStr))
                    sio.write('  <td><div class="hrm_currency" id="%s" %s>%s</td>\n'%(d['id'],hideStr,oldVal))
                if 'price' in d and 'year' in d:
                    # We have enough info to make a cost editing triple
                    pass
            elif d['type'] == 'energy':
                if oldVal is None:
                    sio.write('  <td><div class="hrm_energy" id="%s" %s> %s </td>\n'%(d['id'],hideStr,''))

                else:
                    #print 'oldVal: %s <%s>'%(type(oldVal),oldVal)
                    sio.write('  <td><div class="hrm_energy" id="%s" %s>%s</td>\n'%(d['id'],hideStr,oldVal))
            elif d['type'] == 'fuel':
                if oldVal is None:
                    sio.write('  <td><div class="hrm_fuel" id="%s" %s> %s </td>\n'%(d['id'],hideStr,''))

                else:
                    #print 'oldVal: %s <%s>'%(type(oldVal),oldVal)
                    sio.write('  <td><div class="hrm_fuel" id="%s" %s>%s</td>\n'%(d['id'],hideStr,oldVal))
            else:
                raise HermesServiceException(_("Unknown type {0} in fieldmap entry for {1}".format(d['type'],d['key'])))
            
        sio.write("</tr>\n")
    sio.write("</table>\n")
    # print sio.getvalue()
    return sio.getvalue()
    '''
