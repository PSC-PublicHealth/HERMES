#!/usr/bin/env python
__doc__ = """htmlgenerator
This module provides routines to generate html from database 
information on the server side, for example model description 
information.

Several functions in this module take fieldMap parameters. See
the documentation for _buildEditFieldTable for details.
"""
_hermes_svn_id_="$Id$"

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

def getPeopleInfoHTML(db,uiSession, modelId, typeName):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)

    if canWrite:
        titleStr = _("Population Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Population Type {0}").format(typeName)
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

def getStaffInfoHTML(db,uiSession, modelId, typeName):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)

    if canWrite:
        titleStr = _("Staff Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Staff Type {0}").format(typeName)
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

def getPerDiemInfoHTML(db,uiSession, modelId, typeName):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)

    if canWrite:
        titleStr = _("PerDiem Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("PerDiem Type {0}").format(typeName)
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

def getVaccineInfoHTML(db, uiSession, modelId, typeName):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)

    if canWrite:
        titleStr = _("Vaccine Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Vaccine Type {0}").format(typeName)
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

def getFridgeInfoHTML(db, uiSession, modelId, typeName):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db, modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db, modelId)

    if canWrite:
        titleStr = _("Cold Storage Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Cold Storage Type {0}").format(typeName)
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

def getTruckInfoHTML(db, uiSession, modelId, typeName):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)

    if canWrite:
        titleStr = _("Transport Type {0} in {1}").format(typeName,model.name)
    else:
        titleStr = _("Transport Type {0}").format(typeName)
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

def getGenericTypeInfoHTML(db, uiSession, modelId, typeName):
    canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, typeName)
    category = typeInstance.shdType
    if category=='people': return getPeopleInfoHTML(db, uiSession, modelId, typeName)
    elif category=='trucks': return getTruckInfoHTML(db, uiSession, modelId, typeName)
    elif category=='fridges': return getFridgeInfoHTML(db, uiSession, modelId, typeName)
    elif category=='vaccines': return getVaccineInfoHTML(db, uiSession, modelId, typeName)
    elif category=='ice': return getIceInfoHTML(db, uiSession, modelId, typeName)
    elif category=='packaging': return getPackagingInfoHTML(db, uiSession, modelId, typeName)
    elif category=='staff': return getStaffInfoHTML(db, uiSession, modelId, typeName)
    elif category=='perdiems': return getPerDiemInfoHTML(db, uiSession, modelId, typeName)

def getRunInfoHTML(db, uiSession, runId, minionFactory):
    minionInfo,sp = minionFactory.liveRuns[runId]
    runName = minionInfo['runName']

    titleStr = _("Run {0}").format(runName)

    sio = StringIO()
    sio.write("<h3>\n")
    sio.write("{0}\n".format(runName))
    sio.write("</h3>\n")
    sio.write("<table>\n")
    for k,v in minionInfo.items():
        sio.write('<tr><td>%s</td><td>%s</td>\n'%(k,v))
    sio.write("</table>\n")
    
    return sio.getvalue(), titleStr

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
                                             'Name for Level {0}'.format(i+1),
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
                                             'Name for Level <span class="levelnames-em">{0}</span>'.format(i+1),
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
        htmlForm.addElement(HTMLFormInputBox('model_create_lcounts_{0}'.format(i+1),
                                             'Number of Locations in <span class="levelcount-em">{0}</span> level'.format(levelNames[i]),
                                             levelCounts[i],
                                             'int',
                                             True))
                            
    htmlDoc.addConstruct(htmlForm)
    htmlString = htmlDoc.htmlString()
    
    return htmlString 

def _buildInterLevelInfoFormFromSession(prefix="",levelInfo={}):
    ### check if I have some prerequisites
    if (not levelInfo.has_key('levelnames')) or (not levelInfo.has_key('levelcounts')):
        return "<p> Building Interlevel Model Create Form: The prerequisites of levelnames and levelcounts are not in the current session.</p>"
    
    levelNames = levelInfo['levelnames']
    
    
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
        print "------ I = %d---------"%i
        ### lets see if there is existing data in the levelInfo
        if levelInfo.has_key('shippatterns'):
            defaultsList = levelInfo['shippatterns'][i]
        
        htmlForm.addRow(['<span class="interleveltablehead">' \
                         +_("For routes from the <span class='interleveltableem'>{0}</span> to <span class='interleveltableem'>{1}</span> levels:<br><br class='smallbr'>".format(levelNames[i],levelNames[i+1])) \
                         + "</span>"],['N',2])
        htmlForm.addElement(HTMLFormSelectBox('model_create_interl_isfetch_{0}'.format(i+1),
                                              _('Products are'),
                                              fetchEntries, str(defaultsList[1]).lower(),
                                              cssclass="interleveltable"))
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
        htmlForm.addRow(["<hr>"] ,['N',2])
        
    htmlDoc.addConstruct(htmlForm)
    sio.write('{0}'.format(htmlDoc.htmlString()))
    
    return sio.getvalue()

def _buildInterLevelTimingFormFromSession(prefix="",levelInfo={}):
    if (not levelInfo.has_key('levelnames')) or (not levelInfo.has_key('levelcounts')):
        return "<p> Building Interlevel Model Create Form: The prerequisites of levelnames and levelcounts are not in the current session.</p>"
    
    levelNames = levelInfo['levelnames']
    
    
    htmlDoc = HTMLDocument("interltimingform",None,standAlone_=False)
    htmlForm = HTMLForm("Iter_Level_Timing_Form",cssclass='interltimingtable')
    
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
        
        htmlForm.addRow(['<span class="interleveltablehead">' \
                         +_("For routes from the <span class='interleveltableem'>{0}</span> to <span class='interleveltableem'>{1}</span> levels:<br><br>".format(levelNames[i],levelNames[i+1])) \
                         + "</span>"],['N',3])
        
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
        htmlForm.addRow(["<hr>"] ,['N',3])
    
    htmlDoc.addConstruct(htmlForm)
    sio.write('{0}'.format(htmlDoc.htmlString()))
    
    return sio.getvalue()
def _buildEditFieldTable(fieldMap):
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
                    sio.write('  <td><input class="hrm_price" type=text value="%s" id="%s" onkeypress="validateFloat(event)" %s></td>\n'%(oldVal,d['id'],hideStr))
                else:
                    sio.write('  <td><input class="hrm_price" type=text value="0.0" id="%s" onkeypress="validateFloat(event)" %s></td>\n'%(d['id'],hideStr))
                    
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
                    sio.write('  <td><div class="hrm_currency" id="%s" %s> %s </td>\n'%(d['id'],hideStr,''))

                else:
                    #print 'oldVal: %s <%s>'%(type(oldVal),oldVal)
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

def getTypeEditHTML(db,uiSession,wireType,modelId,protoname,fieldMap):
    model = shadow_network_db_api.ShdNetworkDB(db,modelId)
    
    titleStr = _("This will go in model {0}").format(model.name)
    
    return _buildEditFieldTable(fieldMap), titleStr

def getRouteDialogHTML(db,uiSession,name="model_route_dialog",genInfo=True,util=True,tripMan=True):
    tabCount =1
    sio=StringIO()
    
    sio.write("<div id='%s_dialog' class = '%s_dialog' title='This should get replaced'>"%(name,name))
    sio.write("<div id = '%s_content'>"%(name))
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
        sio.write("<div id='tab-%d'><table id='%s_RGenInfo'></table></div>"%(tabCount,name))
        tabCount += 1
    if util:
        sio.write("<div id='tab-%d'><table id='%s_RUtilInfo'></table></div>"%(tabCount,name))
        tabCount += 1
    if tripMan:
        sio.write("<div id='tab-%d'><table id='%s_RTripMan'></table></div>"%(tabCount,name))
        tabCount += 1  
        
    sio.write("</div>")
    sio.write("</div>")
    ### Now add the javascript to load the dialog box
    sio.write("<script>")
    sio.write("$('#%s_dialog').dialog({"%name)
    sio.write("autoOpen:false,") 
    sio.write("height:'auto',")
    sio.write("width:'auto',")
    sio.write("close: function() {")
    sio.write("$('#%s_content').tabs();"%name)
    sio.write("    $('#%s_content').tabs('destroy');"%name)
    sio.write("    $('#%s_content').innerHtml = '';"%name)
    if genInfo:
        sio.write("    $('#%s_RGenInfo').jqGrid('GridUnload');"%name)
    if util:
        sio.write("    $('#%s_RUtilInfo').jqGrid('GridUnload');"%name)
    if tripMan:
        sio.write("   $('#%s_RTripMan').jqGrid('GridUnload');"%name)
    sio.write("$(this).remove();")
    sio.write("var script = document.getElementById('{0}_script');".format(name))
    sio.write("script.parentElement.removeChild(script);")
    sio.write("}")
    sio.write("});")
    
    sio.write("var %s_meta = new Object();"%name)
    sio.write("%s_meta['getResult'] = false;"%name)
    if genInfo: sio.write("%s_meta['genInfo'] = true;"%name)
    if util: sio.write("%s_meta['utilInfo'] = true; %s_meta['getResults'] = true;"%(name,name))
    if tripMan: sio.write("%s_meta['tripMan'] = true;%s_meta['getResults'] = true;"%(name,name))
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
        stringList.append("<div id='tab-%d'><table id='%s_VialsPlot'></table><p align='right'>%s</p></div>"%(tabCount,name,_('Click on Name of Vaccine to Hide/Show it on the Chart.')))
        tabCount += 1  
    if fillRatio:
        stringList.append("<div id='tab-%d'><table id='%s_FillPlot'></table></div>"%(tabCount,name))
        tabCount += 1
    if vaccAvail:
        stringList.append("<div id='tab-%d'><table id='%s_Availability'></table></div>"%(tabCount,name))
        tabCount += 1
    if availPlot:
        stringList.append("<div id='tab-%d'><table id='%s_AvailPlot'></table></div>"%(tabCount,name))
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
