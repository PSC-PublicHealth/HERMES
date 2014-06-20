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
from cStringIO import StringIO
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

_=translateString

def getModelInfoHTML(db,uiSession,modelId):
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
    attrRec = {}
    shadow_network._copyAttrsToRec(attrRec,route)
    for k,v in attrRec.items(): 
        if k != 'RouteName': # because that's obvious
            sio.write('<tr><td>%s</td><td>%s</td>\n'%(k,v))
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
    for fME in fieldMap:
        if fME['type'] == 'select':
            pass
        elif fME['type'] in ['int','float','string']:
            htmlForm.addElement(HTMLFormInputBox(fME['key'],fME['label'],fME['value'],fME['type'],True))
        elif fME['type'] == 'bool':
            htmlForm.addElement(HTMLFormCheckBox(fME['key'],fME['label'],fME['value'],True))
    htmlDoc.addConstruct(htmlForm)    
    htmlString = htmlDoc.htmlString()
    
    return htmlString

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
                'select']
       
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
                        raise RuntimeError("Nonsense lifetype units code %s"+units)
                else:
                    sio.write('  <td><div %s class="hrm_lifetime"><input type=text id="%s" onkeypress="validateFloat(event)" %s>\n'%\
                              (hideStr,d['id']))
                    sio.write('  <select id="%s_units"><option value="D">%s</option><option value="W">%s</option><option value="M">%s</option></select></div></td>\n'%\
                              (d['id'],_("Days"),_("Weeks"),_("Months")))
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

   