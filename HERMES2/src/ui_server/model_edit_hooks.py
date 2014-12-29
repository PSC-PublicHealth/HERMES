import sys,os,os.path,time,json,math,types
import bottle
import ipath
import site_info
import shadow_network_db_api
from sqlalchemy.orm import Session
import privs
from upload import uploadAndStore, makeClientFileInfo
from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace
import session_support_wrapper as session_support
import string
from util import listify
import input
import traceback

import validate_model

import shadow_network as shd

import base64
import random

from ui_utils import b64E, b64D

inlizer=session_support.inlizer
_=session_support.translateString

class METC:  # model edit type constants
    """
    Model Edit Type Constants
    
    These are the prefixes for the various types of nodes and item id's

    they are currently set to non-obvious values so that code using old literals will break
    """
    WAREHOUSE = 'W'
    STORE = WAREHOUSE
    ROUTE = 'R'
    STOP = 'S'
    LITERAL = 'L'

    constantList = set([WAREHOUSE, ROUTE, STOP, LITERAL])

class TREE:
    """
    tree constants so we can specify a given tree
    """
    MAIN = 'A'
    UNATTACHED = 'B'

def javascriptEscape(s):
    """
    escape for including in quoted strings in javascript source code

    This is a first pass and needs to be made complete
    """
    s = unicode(s)

    if s.find('\\'):
        s = string.join(s.split('\\'), '\\\\')
    if s.find('"'):
        s = string.join(s.split('"'), '\\"')
    if s.find("'"):
        s = string.join(s.split("'"), "\\'")
    return s

je = javascriptEscape

def htmlEscape(s):
    """
    escape for including in html
    remove <, >, ', ", and & from strings and replace them with the html escape equivalent
    """
    s = unicode(s)

    # ampersand must be done first
    if s.find('&'):
        s = string.join(s.split('&'), '&amp;')
    if s.find('<'):
        s = string.join(s.split('<'), '&lt;')
    if s.find('>'):
        s = string.join(s.split('>'), '&gt;')
    if s.find("'"):
        s = string.join(s.split("'"), '&#39;')
    if s.find('"'):
        s = string.join(s.split('"'), '&quot;')
    return s

h = htmlEscape

from ui_utils import _safeGetReqParam
def getParm(parm):
    return _safeGetReqParam(bottle.request.params, parm)

def getIntParm(parm):
    return _safeGetReqParam(bottle.request.params, parm, isInt=True)

class InvalidUpdate(Exception):
    def __init__(self, string, inputId=None, setVal=None, updateList=None):
        self.string = string
        self.inputId = inputId
        self.setVal = setVal
        self.updateList = updateList

class InvalidRecursiveUpdate(Exception):
    def __init__(self, string):
        self.string = string
        # use the normal update list

def createLocalUpdateEntry(inputId, value, updateType='value', displayValue=None):
    """
    create a dict that can be passed to the client to define a DOM update

    valid update types include:
    
    value : the value in a single updatable field in an html 'input', 'textarea', or 'select'
            along with the display only 'fixed_' version of this.

    html : set the inner html of a dom object.
    savedValue : update a specific value in the fieldChanges structure (that records local updates)
    focus : set the focus to a specific input element
    node : replace a jstree node with the data in value
    create : create a new jstree node.  value (v) is a dict with 
                v['parent'] being the parent node
                v['location'] is where to create the node based on the parent node.  From the jstree
                   docs: This can be a zero based index to position the element at a specific point 
                   among the current children. You can also pass in one of those strings: "before", 
                   "after", "inside", "first", "last".
                v['node'] is the new node json (children of this node are not allowed to be specified)
              create should not be used when the parent node of the node being created has not been
              populated yet.  If this is the case it is better to create the new node in the database
              and then request that jstree open the node.
    remove : remove a node
    open : open a node
    clearUpdates : clear all updates saved in the fieldChanges structure referring to a given node.
                   Use encodeItemId() to encode the node type.
    changeId : change the node id of a single node.  The client will immediately request
               that the node be resent as well.
    alert : generate a popup text message for the user.
    widget : use the value to create a widget on the client.
    """
    #if updateType == 'value':
    #    displayValue = h(displayValue)
    #    value = h(value)
    if displayValue is not None:
        return { 'updateType' : updateType,
                 'inputId' : inputId,
                 'value' : value ,
                 'displayValue' : displayValue}
        
    return { 'updateType' : updateType,
             'inputId' : inputId,
             'value' : value }

class LocalUpdateList:
    "class to hold a list of DOM updates that can be passed to the client"
    def __init__(self, updateOrInputId=None, value=None, updateType='value', displayValue=None):
        self._updateList = []
        if updateOrInputId is None:
            return
        self.addUpdate(updateOrInputId, value, updateType, displayValue)

    def addUpdate(self, updateOrInputId, value=None, updateType='value', displayValue=None):
        if isinstance(updateOrInputId, dict):
            self._updateList.append(updateOrInputId)
            return
        if not isinstance(updateOrInputId, types.StringTypes):
            raise RuntimeError("invalid updateOrInputId creating LocalUpdateList")
        self._updateList.append(createLocalUpdateEntry(updateOrInputId, value, updateType, 
                                                       displayValue))

    def updateList(self):
        return self._updateList

class ULCM:
    """
    Update List Context Manager

    a singleton update list providing us with a means of creating updates out of band
    """
    ul = None
    def __init__(self):
        ULCM.ul = LocalUpdateList()
        
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        ULCM.ul = None

    @classmethod
    def addUpdate(cls, updateOrInputId, value=None, updateType='value', displayValue=None):
        if ULCM.ul is None:
            raise RuntimeError("Update List Context Manager has not been initialized")
        ULCM.ul.addUpdate(updateOrInputId, value, updateType, displayValue)

    @classmethod
    def updateList(cls):
        return ULCM.ul.updateList()


def getIds(storeOrRoute):
    if isinstance(storeOrRoute, shd.ShdStore):
        modelId = storeOrRoute.modelId
        itemId = METC.WAREHOUSE + unicode(storeOrRoute.idcode)
    elif isinstance(storeOrRoute, shd.ShdRoute):
        modelId = storeOrRoute.modelId
        itemId = METC.ROUTE + storeOrRoute.RouteName
    elif isinstance(storeOrRoute, shd.ShdStop):
        modelId = storeOrRoute.modelId
        itemId = METC.STOP + stopId(storeOrRoute)
    else:
        raise RuntimeError('need a store, route, or stop for this')

    return modelId, itemId

class LiteralItem:
    """
    this class exists so that string literals can be packed into an itemId/inputId
    """
    def __init__(self, stringLiteral):
        self.s = stringLiteral

def getItemId(item):
    if isinstance(item, types.StringTypes):
        if item[0] in METC.constantList:
            return item

    if isinstance(item, LiteralItem):
        return METC.LITERAL + item.s

    modelId, itemId = getIds(item)
    return itemId
    
def resiliantStopId(stop):
    route = stop.route
    count = 0
    for s in route.stops:
        if s.idcode == stop.idcode:
            if s is stop:
                break
            count += 1
    else:
        raise RuntimeError('resiliantStopId: stop somehow not found in route')
    return '%d_%d_%s'%(stop.idcode,
                       count,
                       stop.RouteName)

def getStopFromResiliantStopId(model, i):
    (storeId, count, routeName) = i.split('_', 2)
    storeId = long(storeId)
    count = int(count)
    route = model.getRoute(routeName)
    c = 0
    for stop in route.stops:
        if stop.idcode == storeId:
            if c == count:
                return stop
            c += 1
    print "can't find stop!"
    raise KeyError("no such stop")

def stopId(stop):
    "return a unique id for a given stop"
    # this is excessive but I want things to blow up
    # if someone has changed the route order out from
    # under the editor
    #print 'stop: idcode %s, store %s, RouteOrder %s, RouteName %s'%\
    #    (stop.idcode, stop.store, stop.RouteOrder, stop.RouteName)
    return '%d_%d_%s'%(stop.idcode,
                       stop.RouteOrder,
                       stop.RouteName)

def getStopFromItemId(model, itemId):
    """
    return a ShdStop based on a model and stopId

    validate that the stop hasn't changed which storeId it points to.
    """
    if itemId[0] != METC.STOP:
        raise KeyError('item id is not a valid stop id')
    itemId = itemId[1:]
    (storeId, stopNum, routeName) = itemId.split('_', 2)
    stop = model.getStop(routeName, stopNum)
    if stop.idcode == long(storeId):
        return stop
    raise KeyError("stop doesn't match")

def getStoreFromItemId(model, itemId):
    """
    return a store from an itemId
    """
    if itemId[0] != METC.STORE:
        raise KeyError('item id is not a valid store id')
    itemId = itemId[1:]
    return model.getStore(long(itemId))

def getRouteFromItemId(model, itemId):
    """
    return a route from an itemId
    """
    if itemId[0] != METC.ROUTE:
        raise KeyError('item id is not a valid route id')
    itemId = itemId[1:]
    return model.getRoute(itemId)


# well this is embarrassing...
# I need to know which tree things are on and it's quite ugly trying to figure
# it out.  Similarly it would be ugly to pass the tree up through all the code that
# needs it.  So we'll put it in a global and pretty it up with a context manager
# around it!

currentTree = 'A'
class selectTree:
    def __init__(self, tree):
        global currentTree
        self.lastTree = currentTree
        currentTree = tree
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        global currentTree
        currentTree = self.lastTree


def packInputId(modelId, item, field, secondaryId=None, tree=None):
    """
    use this to create an input id for any updatable fields

    item can be a store, route or stop or a valid itemId

    If the format of this is changed unpackInputId needs updated
    along with doUpdate() in model_edit.js (especially the 'clearUpdates' section)
    """
    if tree is None:
        tree = currentTree

    itemId = getItemId(item)
    
    ret = "%s:%d:%s:%s"%(tree, modelId, field, b64E(itemId))
    if secondaryId is not None:
        ret += ":%s"%b64E(secondaryId)
    return ret

def encodeItemId(itemId):
    """
    encode the itemId section of an inputId for the purpose of negating updates
    to individual fields within a node when the entire node is resent to the client.
    
    (specifically used for the local update type 'clearUpdates')
    """
    return b64E(itemId)


def unpackInputId(inputId):
    (tree, modelId, field, itemId) = inputId.split(':', 3)
    secondaryId = None
    if ':' in itemId:
        (itemId,secondaryId) = itemId.split(':', 1)
        secondaryId = b64D(secondaryId)
    itemId = b64D(itemId)
    itemType = itemId[0]
    itemLabel = itemId[1:]
    
    return {'modelId' : modelId,
            'field' : field,
            'itemId' : itemId,
            'secondaryId' : secondaryId, 
            'tree' : tree,
            'itemType' : itemType,
            'itemLabel' : itemLabel
            }

def inputIdTriple(inputId):
    val = unpackInputId(inputId)
    return val['modelId'], val['itemId'], val['field']

def inputIdQuad(inputId):
    val = unpackInputId(inputId)
    return val['modelId'], val['itemId'], val['field'], val['secondaryId']

def inputIdTree(inputId):
    val = unpackInputId(inputId)
    return val['tree']

def packNodeId(item, optType=None, tree=None):
    """
    use this to create the id for a jstree node.

    optType can be a single character node type identifier
    if you wish to override the default

    by default the current tree will be used but this can 
    can be overridden with tree
    """
    if isinstance(item, shd.ShdStore):
        itemId = item.idcode
        nodeType = METC.WAREHOUSE
    elif isinstance(item, shd.ShdRoute):
        itemId = b64E(item.RouteName)
        nodeType = METC.ROUTE
    elif isinstance(item, shd.ShdStop):
        itemId = resiliantStopId(item)
        nodeType = METC.STOP
    elif isinstance(item, types.StringTypes):
        itemId = item
        nodeType = METC.LITERAL
    else:
        raise RuntimeError("invalid node %s of type %s"%(item, type(item)))

    if optType is not None:
        nodeType = optType

    global currentTree
    if tree is None:
        tree = currentTree

    return '%s%s%s'%(tree, nodeType, itemId)

def unpackNodeId(nodeId):
    "unpack a jstree node id into constituent parts"
    tree = nodeId[0]
    nodeType = nodeId[1]
    nodeId = nodeId[2:]

    if nodeType == METC.ROUTE:
        nodeId = b64D(nodeId)

    return { 'tree' : tree,
             'nodeType' : nodeType,
             'nodeId' : nodeId }
    

def TupleFromNodeId(nodeId):
    "unpack a node id into constituent parts and return them in a convenient tuple"
    d = unpackNodeId(nodeId)
    return (d['tree'], d['nodeType'], d['nodeId'])

def addUpdateClearUpdates(item):
    """
    create a "clearUpdates" update for a store, stop or route node and add it to the update list ul
    """
    itemId = encodeItemId(getItemId(item))
    ULCM.addUpdate(itemId, 'x', 'clearUpdates')


class EditableFieldInfo:
    """
    structure to define an editable element on the page

    default is a standard text field but other types can be defined
    based on fieldType.  Acceptable fieldType values include:
    'pulldown'  : requires pullDownOpts to have a value
    'tuplelist' : may have pullDownOpts for adding to the tuple list
    'widget'    : requires widgetOpts
    'textarea'  :
    'button'    : Currently only partially implemented

    """
    def __init__(self, className, fieldName, value, fieldType='text',
                 pullDownOpts=None, size=None, displayValue=None,
                 cols=None, rows=None, widgetOpts=None):
        self.className = className
        self.fieldName = fieldName
        self.value = value
        self.fieldType = fieldType
        self.pullDownOpts = pullDownOpts
        self.widgetOpts = widgetOpts
        self.size = size
        self.cols = cols
        self.rows = rows
        if displayValue is None:
            self.displayValue = value
        else:
            self.displayValue = displayValue

class EditableTuple:
    def __init__(self, count, item, displayName=None):
        if displayName is None:
            displayName = item
        self.count = count
        self.item = item
        self.displayName = displayName
        
    def __repr__(self):
        return 'EditableTuple(%s, %s, %s)'%(self.count, self.item, self.displayName)

class EditableTupleList:
    def __init__(self, et=None):
        self.etList = []
        if et is not None:
            self.addTuple(et)
    
    def addTuple(self, et):
        self.etList.append(et)

    def getList(self):
        return self.etList

def renderTupleList(modelId, itemId, fieldInfo):
    """
    render a tuple list in a fixed, non-editable form.

    This will display a list of EditableTuple()s (from the value field of fieldInfo). 
    """
    f = fieldInfo

    ret = []
    ret.append('<table border="0">')
    for i,et in enumerate(f.value.getList()):
        ret.append('<tr>')
        if i == 0:
            ret.append('<td>%s:</td>'%h(f.fieldName))
        else:
            ret.append('<td></td>')
        ret.append('<td>%s</td>'%h(et.displayName))
        fixedInputId = 'fixed_' + packInputId(modelId, itemId, f.className, et.item)
        ret.append('<td id="%s">%s</td>'%(fixedInputId, et.count))
        ret.append('</tr>')

    ret.append('</table>')

    return ret


def renderEditableTupleList(modelId, itemId, fieldInfo):
    """
    render a tuple list in editable form.

    This will display a list of EditableTuple()s (from the value field of fieldInfo) 
    along with an add box (if pulldownOpts are set) at the bottom.
    Each count will be updatable and the add box will be a pulldown menu of available
    choices.
    """
    f = fieldInfo
    ret = []
    ret.append('<table border="0">')
    for i,et in enumerate(f.value.getList()):
        ret.append('<tr>')
        if i == 0:
            ret.append('<td>%s:</td>'%f.fieldName)
        else:
            ret.append('<td></td>')
        ret.append('<td>%s</td>'%h(et.displayName))
        inputId = packInputId(modelId, itemId, f.className, et.item)
        ret.append('<td><input id="%s" type="text" value="%s" size="7"'%\
                       (inputId, et.count))
        ret.append('    onblur="changeTupleCount(\'%s\');" /></td>'%inputId)
        ret.append('</tr>')
        ULCM.addUpdate(inputId, "%s"%et.count, 'savedValue')

    if f.pullDownOpts is not None:
        ret.append('<tr><td></td><td>')
        inputId = packInputId(modelId, itemId, f.className)
        addSelInputId = 'addSel_' + inputId
        addCountInputId = 'addCount_' + inputId
        addHideInputId = 'addHide_' + inputId
        ret.append('<select id="%s" onblur="unhideCount(\'%s\', \'%s\', \'%s\');"'%\
                       (addSelInputId, addSelInputId, addHideInputId, addCountInputId))
        ret.append('onmouseup="unhideCount(\'%s\', \'%s\', \'%s\');" >'%\
                       (addSelInputId, addHideInputId, addCountInputId))
        ret.extend(renderPullDownOption(('None', _('new {0} type').format(f.fieldName))))
        for opt in f.pullDownOpts:
            opt = listify(opt)
            ret.extend(renderPullDownOption(opt))

        ret.append('</select>')
        ret.append('</td>')
        ret.append('<td><span id="%s" style="display:none;">'%addHideInputId)
        ret.append('<input id="%s" type="text" size="7" />'%addCountInputId)
        ret.append('<button type="button" onclick="addNewTuple(\'%s\');">'%inputId)
        ret.append(_('add'));
        ret.append('</button>')
        ret.append('</span></td></tr>')

    ret.append('</table>')

    return ret

def renderPullDownOption(opt, selected=False):
    value = opt[0]
    if len(opt) > 1:
        disp = opt[1]
    else:
        disp = value

    if selected:
        selectStr = ' selected'
    else:
        selectStr = ''

    ret = []
    ret.append('<option value="%s"%s>%s</option>'%(h(value), selectStr, h(disp)))
    return ret

def renderPullDown(modelId, itemId, fieldInfo):
    """
    render a pulldown selection.

    fieldInfo defines everything about what might go in the pulldown
    modelId, itemId are identifiers necessary to uniquely define the field.
    """
    f = fieldInfo
    inputId = packInputId(modelId, itemId, f.className)
    ret = []
    ret.append('<select id="%s" onchange="changePullDown(\'%s\');">'%\
                   (inputId, inputId))
    for opt in f.pullDownOpts:
        selected = False
        opt = listify(opt)
        if opt[0] == f.value:
            selected = True
        ret.extend(renderPullDownOption(opt, selected))
    ret.append('</select>')
    return ret
                   
def renderButton(modelId, itemId, fieldInfo):
    f = fieldInfo
    ret = []
    inputId = packInputId(modelId, itemId, f.className)
    ret.append('<button id="%s" class="%s" type="button">%s</button>'%\
                   (inputId, f.className, f.value))
    return ret

def renderEditableString(modelId, itemId, fieldInfo): 
    f = fieldInfo
    ret = []
    inputId = packInputId(modelId, itemId, f.className)
    attrString = ''
    if f.size:
        attrString += ' size="%s"'%f.size
    ret.append('<input id="%s" class="%s", type="text" value="%s" %s onblur="changeString(\'%s\');" />'%\
                   (inputId, f.className, h(f.value), attrString, inputId))
    ULCM.addUpdate(inputId, "%s"%f.value, 'savedValue')
    return ret

def renderWidget(modelId, itemId, fieldInfo):
    f = fieldInfo
    ret = []
    inputId = packInputId(modelId, itemId, f.className)
    attrString = ''
    if f.size:
        attrString += ' size="%s"'%f.size
    ret.append('<div id="%s" class="%s" %s>%s</div>' %
               (inputId, f.className, attrString, h(f.value)))
    ULCM.addUpdate(inputId, f.widgetOpts, 'widget')
    return ret

def renderEditableTextArea(modelId, itemId, fieldInfo):
    f = fieldInfo
    ret = []
    inputId = packInputId(modelId, itemId, f.className)
    attrString = ''
    if f.size:
        attrString += ' maxlength="%s"'%f.size
    if f.cols:
        attrString += ' cols="%s"'%f.cols
    if f.rows:
        attrString += ' rows="%s"'%f.rows
    ret.append('<textarea id="%s" class="%s" %s onblur="changeTextArea(\'%s\');">'%\
                   (inputId, f.className, attrString, inputId))
    ret.append(h(f.value))
    ret.append('</textarea>')
    ULCM.addUpdate(inputId, "%s"%f.value, 'savedValue')
    return ret


def addTupleFieldUpdates(modelId, itemId, fieldInfo):
    f = fieldInfo

    for et in f.value.getList():
        inputId = packInputId(modelId, itemId, f.className, et.item)
        update = createLocalUpdateEntry(inputId, et.count, 'savedValue')
        ULCM.addUpdate(update)

def updateBasicTupleList(storeOrRoute, groupClassName, editableField, updateFocus=True):
    """
    creating the updates for a tuple list largely means recreating
    the entire tuple list html and then adding some extra bookkeeping.

    This function does all of that for you.
    """

    modelId, itemId = getIds(storeOrRoute)
    inputId = packInputId(modelId, itemId, editableField.className)

    # create the editable and fixed versions of the html
    editHtml = string.join(renderEditableTupleList(modelId, itemId, editableField),
                           '\n')
    fixedHtml = string.join(renderTupleList(modelId, itemId, editableField),
                            '\n')

    ULCM.addUpdate(createLocalUpdateEntry('edit_'+inputId,
                                          editHtml,
                                          'html'))
    ULCM.addUpdate(createLocalUpdateEntry('fixed_'+inputId,
                                        fixedHtml,
                                        'html'))

    # those fields may have old updates saved in the client
    # fieldUpdates structure.  Create a whole new set of updates
    # to make sure nothing is stale.
    addTupleFieldUpdates(modelId, itemId, editableField)

    if updateFocus:
        # overwriting the html where the page focus is resets focus.
        # Put the focus back to where the user expects it.
        addSelInputId = 'addSel_' + inputId
        ULCM.addUpdate(createLocalUpdateEntry(addSelInputId, 0, 'focus'))


def renderBasicTupleList(storeOrRoute, groupClassName, EditableField):
    modelId, itemId = getIds(storeOrRoute)

    ret = []
    ret.append('<div class="%s">'%groupClassName)
    inputId = packInputId(modelId, itemId, EditableField.className)
    ret.append('<div class="edit_%s" id="edit_%s">'%(groupClassName, inputId))
    ret.extend(renderEditableTupleList(modelId, itemId, EditableField))
    ret.append('</div>')
    ret.append('<div class="fixed_%s" id="fixed_%s">'%(groupClassName, inputId))
    ret.extend(renderTupleList(modelId, itemId, EditableField))
    ret.append('</div>')
    ret.append('</div>')
    return ret

def renderBasicEditableFields(storeOrRoute, groupClassName, EditableFields):
    modelId, itemId = getIds(storeOrRoute)

    ret = []
    ret.append('<div class="%s" title="this is a tool tip">'%groupClassName)
    EditableFields = listify(EditableFields)
    for f in EditableFields:
        ret.append('<table><tr><td>%s: </td><td><div class="edit_%s">'%(f.fieldName, groupClassName))
        if f.fieldType == 'pulldown':
            ret.extend(renderPullDown(modelId, itemId, f))
        elif f.fieldType == 'textarea':
            ret.extend(renderEditableTextArea(modelId, itemId, f))
        elif f.fieldType == 'button':
            ret.extend(renderButton(modelId, itemId, f))
        elif f.fieldType == 'text':
            ret.extend(renderEditableString(modelId, itemId, f))
        elif f.fieldType == 'widget':
            ret.extend(renderWidget(modelId, itemId, f))
        else:
            raise RuntimeError("invalid fieldType %s"%f.fieldType)
        fixedInputId = 'fixed_' + packInputId(modelId, itemId, f.className)
        ret.append('</div><span class="%s"><b id="%s">%s</b></span></td></tr></table>'%\
                       ('fixed_'+groupClassName, fixedInputId, h(f.displayValue)))
    ret.append('</div>')
    return ret

def renderBasicEditableField(storeOrRoute, className, fieldName, value, 
                             pullDownOpts=None, displayValue=None, widgetOpts=None):
    fieldType = 'text'
    if widgetOpts is not None:
        fieldType = 'widget'
    elif pullDownOpts is not None:
        fieldType = 'pulldown'
    return renderBasicEditableFields(storeOrRoute,
                                     className,
                                     [EditableFieldInfo(className,
                                                        fieldName,
                                                        value,
                                                        fieldType = fieldType,
                                                        pullDownOpts = pullDownOpts,
                                                        displayValue = displayValue,
                                                        widgetOpts = widgetOpts)])


def addStoreMessage(store, msg):
    "add a message to a store along with child messages to the parents recursively"

    inputId = packInputId(store.modelId, store, 'storeMessages')
    ULCM.addUpdate(inputId, msg, 'addMessage')

    name = store.NAME
    msg = _('{0}: {1}').format(name, msg)

    while(True):
        suppliers = store.suppliers()
        if len(suppliers) == 0:
            return
        (store, route) = suppliers[0]

        inputId = packInputId(store.modelId, route, 'routeChildMessages')
        ULCM.addUpdate(inputId, msg, 'addMessage')

        inputId = packInputId(store.modelId, store, 'storeChildMessages')
        ULCM.addUpdate(inputId, msg, 'addMessage')
        
def addRouteMessage(route, msg):
    "add a message to a route along with child messages to the parents recursively"

    inputId = packInputId(route.modelId, route, 'routeMessages')
    ULCM.addUpdate(inputId, msg, 'addMessage')

    name = route.RouteName
    msg = _('route {0}: {1}').format(name, msg)

    store = route.supplier()
    inputId = packInputId(store.modelId, store, 'storeChildMessages')
    ULCM.addUpdate(inputId, msg, 'addMessage')

    while(True):
        suppliers = store.suppliers()
        if len(suppliers) == 0:
            return
        (store, route) = suppliers[0]

        inputId = packInputId(store.modelId, route, 'routeChildMessages')
        ULCM.addUpdate(inputId, msg, 'addMessage')

        inputId = packInputId(store.modelId, store, 'storeChildMessages')
        ULCM.addUpdate(inputId, msg, 'addMessage')


# strings for making things draggable or droppable
dragString = 'draggable="true" ondragstart="emDrag(event)"'
dropString = 'ondrop="emDrop(event)" ondragover="emAllowDrop(event)" ondragenter="emDragEnter(event)" ondragLeave="emDragLeave(event)"'
dndString = dragString + ' ' + dropString

def renderStoreLabelString(store):
    return "<b>%s (%s)</b>"%(h(store.NAME), store.idcode)

def renderStoreLabel(store):
    ret = []
    dispId = packInputId(store.modelId, store, 'storeHeader')
    ret.append('<p id="%s" class="store-edit-label" style="display:inline;" %s>%s</p>'%\
                   (dispId, dndString, renderStoreLabelString(store)))
    editId = packInputId(store.modelId, store, 'storeEditButton')
#    ret.append('<button id="%s" style="display:inline" onclick="meStoreEdit(%d,%d)">edit</button>'%\
#                   (editId, store.modelId, store.idcode))
    ret.append('<button id="%s" class="store-edit-menu" style="display:inline" tabindex="-1">%s</button>'%\
                   (editId, _('edit')))
    return ret
    
def renderStoreName(store):
    return renderBasicEditableField(store, 'storeName', _('Name'), store.NAME)

def updateStoreName(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)
    store = getStoreFromItemId(model, itemId)
    if origStr != unicode(store.NAME):
        raise(InvalidUpdate(_('value previously updated'), inputId, unicode(store.NAME)))

    name = newStr.strip()
    store.NAME = name
    ULCM.addUpdate(inputId, name)
    ULCM.addUpdate(packInputId(store.modelId, store, 'storeHeader'),
                   renderStoreLabelString(store),
                   'html')
    return True


def updateRouteName(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)
    tree = inputIdTree(inputId)
    route = getRouteFromItemId(model, itemId)
    stops = route.stops
    name = newStr.strip()
    net = route.model
    if name in net.routes:
        raise InvalidUpdate(_("Route names must be unique, {0} is already in use.").format(name))

    # do we need any other validations on the route name?
    
    with selectTree(tree):
        currentNodeId = packNodeId(route)
    
        # get nodeIds for all of the old stops
        sd = calcStopDisplayTypes(route)
        
        oldStopIds = []
        for disp, stop in zip(sd, stops):
            if disp == SDC.DISP_STOP:
                oldStopIds.append(packNodeId(stop))
            elif disp == SDC.DISP_STORE:
                oldStopIds.append(packNodeId(stop.store))
            elif disp == SDC.DISP_NOTHING:
                oldStopIds.append(None)
            else:
                raise RuntimeError("Unknown stop display type")

        # we have the old node ids, so lets change the route name on the route and stops
        for stop in stops:
            stop.RouteName = name
        route.RouteName = name

        # now create updates
        ULCM.addUpdate(currentNodeId, 
                       packNodeId(route),
                       "changeId")

        for disp, stop, sId in zip(sd, stops, oldStopIds):
            if disp == SDC.DISP_STOP:
                ULCM.addUpdate(sId,
                               packNodeId(stop),
                               "changeId")
        
    return True

def renderStoreCategory(store):
    userInput = getUserInput(store.model)
    levels = set(categoryLevelList(store.model, userInput))
    centralLevels = set(centralLevelCategories(store.model, userInput))
    
    levels = levels - centralLevels

    if store.CATEGORY in centralLevels:
        opts = list(centralLevels)
    elif store.CATEGORY in levels:
        opts = list(levels)
    else:
        print "store %d in model %d has invalid category %s"%(store.idcode, store.modelId, store.CATEGORY)
        levels.add(store.CATEGORY)
        opts = list(levels)
    
    return renderBasicEditableField(store, 'storeCategory', _('Category'), store.CATEGORY, 
                                    pullDownOpts = opts)

def updateCategory(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)
    store = getStoreFromItemId(model, itemId)
    
    userInput = getUserInput(model)
    levels = set(categoryLevelList(model, userInput))
    centralLevels = set(centralLevelCategories(model, userInput))
    levels = levels - centralLevels

    if origStr in centralLevels:
        if newStr not in centralLevels:
            raise InvalidUpdate(_("Central stores can't change categories."))

    else:
        if newStr not in levels:
            raise InvalidUpdate(_("Attempting to change to an invalid category"))

    store.CATEGORY = newStr.strip()
    return store.CATEGORY


def renderStoreLatLon(store):
    fields = [EditableFieldInfo('storeLatitude', _('Latitude'), store.Latitude, size=10),
              EditableFieldInfo('storeLongitude', _('Longitude'), store.Longitude, size=10)]
    return renderBasicEditableFields(store, 'storeLatLon', fields)


def storeSiteCostCurWidgetOpts(store):
    opts = {'widget': 'currencySelector',
            'label': '',
            'modelId': store.modelId,
            'selected': store.SiteCostCurCode
            }.copy()
    return opts


def renderStoreSiteCost(store):
    fields = [EditableFieldInfo('storeSiteCost', _('Site Cost Per Year'), store.SiteCost, size=10),
              EditableFieldInfo('storeSiteCostCurCode', _('Currency'), store.SiteCostCurCode,
                                size=10, fieldType='widget',
                                widgetOpts=storeSiteCostCurWidgetOpts(store)),
              EditableFieldInfo('storeSiteCostYear', _('Site Cost Base Year'), store.SiteCostYear,
                                size=10),
              ]
    return renderBasicEditableFields(store, 'storeSiteCost', fields)


def updateStoreSiteCostCurCode(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)  # @UnusedVariable
    store = getStoreFromItemId(model, itemId)

    if origStr != '' and origStr != store.SiteCostCurCode:
        ul = LocalUpdateList(inputId,
                             store.SiteCostCurCode,
                             updateType='value')
        raise(InvalidUpdate(_('value previously updated'), updateList=ul))

    if newStr not in [cc.code for cc in model.currencyTable]:
        ul = LocalUpdateList(inputId,
                             store.SiteCostCurCode,
                             updateType='value')
        raise(InvalidUpdate(_('Invalid currency code'), updateList=ul))

    store.SiteCostCurCode = newStr

    ULCM.addUpdate(inputId, newStr, updateType='value')

    return True


def updateStoreSiteCostYear(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)  # @UnusedVariable
    store = getStoreFromItemId(model, itemId)

    curVal = store.SiteCostYear
    curValStr = unicode(curVal)
    if origStr != curValStr:
        raise(InvalidUpdate(_('value of site cost base year previously updated'),
                            inputId, curValStr))
    try:
        newVal = int(newStr.strip())
    except:
        raise(InvalidUpdate(_('invalid site cost base year {0}').format(newStr),
                            inputId, 
                            curValStr))

    store.SiteCostYear = newVal

    ULCM.addUpdate(inputId, newStr, updateType='value')

    return True


def renderStoreUseVials(store):
    fields = [EditableFieldInfo('storeUseVialsInterval', 
                                _('Use Vials Interval'), 
                                store.UseVialsInterval, 
                                size=5),
              EditableFieldInfo('storeUseVialsLatency',
                                _('Latency'),
                                store.UseVialsLatency,
                                size=5)]

    return renderBasicEditableFields(store, 'storeUseVials', fields)

def renderStoreDeviceUtilizationRate(store):
    return renderBasicEditableField(store, 
                                    'storeUtilizationRate', 
                                    _('storage utilization rate'), 
                                    store.utilizationRate)

def id2Store(model, itemId, secondaryId):
    return getStoreFromItemId(model, itemId)

def id2Route(model, itemId, secondaryId):
    return getRouteFromItemId(model, itemId)

def id22Stop(model, itemId, secondaryId):
    "secondary id to stop"
    return getStopFromItemId(model, secondaryId)
    

# go through some gyrations so that "internationalizable" strings are found by the
# search routines but don't actually internationalize anything in this table

def _nopFn(v):
    return v
_tempFn = _
_ = _nopFn

# users of updateFloatFields must internationalize the 3rd element at runtime.
# this can't be done at compile time where this table is created in memory!
updateFloatFields = {
    'storeLatitude': (id2Store, 'Latitude', _('latitude'), -90.0, 90.0),
    'storeLongitude': (id2Store, 'Longitude', _('longitude'), -180.0, 180.0),
    'storeUseVialsInterval': (id2Store, 'UseVialsInterval', _('use vials interval'), 0.0, None),
    'storeUseVialsLatency': (id2Store, 'UseVialsLatency', _('use vials latency'), None, None),
    'storeUtilizationRate' : (id2Store, 'utilizationRate', _('storage utilization rate'), 0.0, None),
    'storeSiteCost' : (id2Store, 'SiteCost', _('yearly site cost'), 0.0, None),
    'routeDistances' : (id22Stop, 'DistanceKM', _('distance (KM)'), 0.0, None),
    'routeTransitHours' : (id22Stop, 'TransitHours', _('transit hours'), 0.0, None),
    'routeOrderAmount' : (id22Stop, 'PullOrderAmountDays', _('order amounts'), 0.0, None),
    'routeInterval' : (id2Route, 'ShipIntervalDays', _('shipping interval'), 0.0, None),
    'routeLatency' : (id2Route, 'ShipLatencyDays', _('shipping latency'), None, None),
    }
_ = _tempFn

def updateFloatErrorString(field, fmin, fmax):
    "generate an error string for an out of bounds float update"
    if fmin is not None and fmax is not None:
        return _('{0} must be a numeric value between {1} and {2}.').format(field, fmin, fmax)
    elif fmin is not None:
        return _('{0} must be a numeric value greater than {1}.').format(field, fmin)
    elif fmax is not None:
        return _('{0} must be a numeric value less than {1}.').format(field, fmax)
    else:
        return _('{0} must be a numeric value.').format(field)

def updateFloat(inputId, model, origStr, newStr):
    "generic updating of a float field based on attributes in updateFloatFields"
    modelId, itemId, field, secondaryId = inputIdQuad(inputId)
    objFn, attr, name, fmin, fmax = updateFloatFields[field]
    name = _(name)
    obj = objFn(model, itemId, secondaryId)
    
    curVal = getattr(obj, attr)
    curValStr = unicode(curVal)
    if origStr != curValStr:
        raise(InvalidUpdate(_('value of {0} previously updated').format(name), inputId, curValStr))
    try:
        newVal = float(newStr.strip())
    except:
        raise(InvalidUpdate(updateFloatErrorString(name, fmin, fmax),
                            inputId, 
                            curValStr))
    if fmax is not None and newVal > fmax:
        raise(InvalidUpdate(updateFloatErrorString(name, fmin, fmax),
                            inputId, 
                            curValStr))
    if fmin is not None and newVal < fmin:
        raise(InvalidUpdate(updateFloatErrorString(name, fmin, fmax),
                            inputId, 
                            curValStr))

    setattr(obj, attr, newVal)
    return unicode(newVal)
    
def getDemandTypeList(model):
    people = model.people.values()
    people.sort(key=lambda p: '%08d%s'%(p.SortOrder, p.Name))
    return people

def storeDemandOpts(store):
    opts = []
    model = store.model

    people = getDemandTypeList(model)

    for p in people:
        value = p.Name
        if 0 != store.countDemand(value):
            continue
        if p.DisplayName is not None and len(p.DisplayName):
            display = p.DisplayName
        else:
            display = value

        opts.append((value, display))

    return opts

def storeDemandEtl(store):
    model = store.model
    demandList = [(d.count, d.invName) for d in store.demand]

    demandList.sort(key = lambda t: '%08d%s'%(model.people[t[1]].SortOrder,model.people[t[1]].Name))

    etl = EditableTupleList()
    
    for d in demandList:
        etl.addTuple(EditableTuple(d[0], d[1]))

    return etl

def renderStoreDemand(store):
    opts = storeDemandOpts(store)
    etl = storeDemandEtl(store)

    return renderBasicTupleList(store, 
                                'storeDemand', 
                                EditableFieldInfo('storeDemand', 
                                                  _('population'), 
                                                  etl,
                                                  fieldType='tuplelist',
                                                  pullDownOpts=opts))

def updateStoreDemandCount(inputId, model, origStr, newStr):
    modelId, itemId, field, peopleType = inputIdQuad(inputId)
    origCnt = int(origStr)
    newCnt = int(newStr)
    store = getStoreFromItemId(model, itemId)
    count = store.countDemand(peopleType)
    if origCnt != count:
        raise(InvalidUpdate(_('value previously updated'), inputId, unicode(count)))
    store.updateDemand(peopleType, newCnt)
    return unicode(newCnt)

    
def addTupleStoreDemand(inputId, model, value, count):
    modelId, itemId, field = inputIdTriple(inputId)
    store = getStoreFromItemId(model, itemId)

    value = value.strip()
    count = int(count.strip())

    store.addDemand(value, count)

    opts = storeDemandOpts(store)

    etl = storeDemandEtl(store)

    efi = EditableFieldInfo('storeDemand',
                            _('population'),
                            etl,
                            fieldType='tuplelist',
                            pullDownOpts=opts)
    return updateBasicTupleList(store, 'storeDemand', efi)
        
def getInvTypeList(model, iType):
    inv = getattr(model, iType).values()
    inv.sort(key=lambda i: i.getDisplayName())
    return inv
_tempFn = _
_ = _nopFn

_storeInvTitles = {
    'fridges' : _('storage'),    #  any user of _storeInvTitles must 
    'trucks' : _('transport'),
    'staff' : _('staff') }  #  internationalize at runtime!
_ = _tempFn

def storeInvOpts(store, iType):
    opts = []
    model = store.model

    inv = getInvTypeList(model, iType)
    for i in inv:
        value = i.Name
        if 0 != store.countInventory(i):
            continue
        display = i.getDisplayName()
        opts.append((value, display))

    return opts
        

def storeInvEtl(store, iType):
    model = store.model
    invList = []
    for inv in store.inventory:
        invType = model.types[inv.invName]
        if invType.shdType == iType:
            invList.append((inv.count, inv.invName, invType.getDisplayName()))
    invList.sort(key = lambda i: i[1])

    etl = EditableTupleList()

    for i in invList:
        etl.addTuple(EditableTuple(i[0], i[1], i[2]))

    return etl

def renderStoreInv(store, iType):
    title = _(_storeInvTitles[iType])
    opts = storeInvOpts(store, iType)
    etl = storeInvEtl(store, iType)

    return renderBasicTupleList(store,
                                'store'+iType,
                                EditableFieldInfo('store'+iType,
                                                  title,
                                                  etl,
                                                  fieldType='tuplelist',
                                                  pullDownOpts=opts))

def updateStoreInvCount(inputId, model, origStr, newStr):
    modelId, itemId, field, whichType = inputIdQuad(inputId)
    origCnt = int(origStr)
    newCnt = int(newStr)
    store = getStoreFromItemId(model, itemId)
    count = store.countInventory(whichType)
    if origCnt != count:
        raise(InvalidUpdate(_('value previously updated'), inputId, unicode(count)))
    store.updateInventory(whichType, newCnt)
    return unicode(newCnt)

    
def addTupleStoreInv(inputId, model, value, count):
    modelId, itemId, field = inputIdTriple(inputId)
    store = getStoreFromItemId(model, itemId)
    iType = field.partition('store')[2]

    value = value.strip()
    count = int(count.strip())

    store.addInventory(value, count)

    opts = storeInvOpts(store, iType)

    etl = storeInvEtl(store, iType)

    efi = EditableFieldInfo('store'+iType,
                            _(_storeInvTitles[iType]),
                            etl,
                            fieldType='tuplelist',
                            pullDownOpts=opts)
    return updateBasicTupleList(store, 'store'+iType, efi)
        
def renderStoreNotes(store):
    fields = [EditableFieldInfo('storeNotes', _('Notes'), store.Notes, 
                                fieldType='textarea', size=4000,
                                rows=5, cols=50)]
    return renderBasicEditableFields(store, 'storeNotes', fields)

def updateStoreNotes(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)
    store = getStoreFromItemId(model, itemId)
    notes = newStr.strip()
    # validation?
    store.Notes = notes
    return store.Notes

def renderStoreMessages(store):
    ret = []
    inputId = packInputId(store.modelId, store, 'storeMessages')
    ret.append('<div id="%s" class="em-message-border pre-emsmb" style="display:none;">'%inputId)
    ret.append('</div>')

    clients = store.clients()

    return ret

def renderStoreChildMessages(store):
    ret = []
    inputId = packInputId(store.modelId, store, 'storeChildMessages')
    ret.append('<div id="%s" class="em-child-message-border pre-emsmb" style="display:none;">'%inputId)
    ret.append('</div>')
    return ret

def renderStoreData(store):
    ret = []

    ret.extend(renderStoreLabel(store))
    ret.extend(renderStoreMessages(store))
    ret.extend(renderStoreChildMessages(store))
    ret.append('<div class="store-edits-border">')
    ret.extend(renderStoreName(store))
    ret.extend(renderStoreCategory(store))
    ret.extend(renderStoreLatLon(store))
    ret.extend(renderStoreUseVials(store))
    ret.extend(renderStoreDeviceUtilizationRate(store))
    ret.extend(renderStoreDemand(store))
    ret.extend(renderStoreInv(store, 'fridges'))
    ret.extend(renderStoreInv(store, 'trucks'))
    ret.extend(renderStoreSiteCost(store))
    ret.extend(renderStoreNotes(store))
    ret.append('</div>')
    return ret

def renderStoreJson(store):
    ret = {}
    retData = {}
    retData['title'] = string.join(renderStoreData(store), '\n')
    retData['attr'] = {'href' : '/testing', 'class' : 'em_replace_me'}
    ret['data'] = retData

    if store.clients():
        ret["state"] = "closed"
    else:
        ret["state"] = "leaf"

    ret["attr"] = { "id" : packNodeId(store) }
    return ret


def renderRouteLabelString(route):
    return "<b>%s</b>"%(_('Route {0}').format(route.RouteName))

def renderRouteLabel(route):
    ret = []
    dispId = packInputId(route.modelId, route, 'routeHeader')
    ret.append('<p id="%s" class="route-edit-label" style="display:inline;" %s>%s</p>'%\
                   (dispId, dndString, renderRouteLabelString(route)))
    editId = packInputId(route.modelId, route, 'routeEditButton')
    ret.append('<button id="%s" class="route-edit-menu" style="display:inline" tabindex="-1">%s</button>'%\
                   (editId, _('edit')))
    return ret

def renderRouteName(route):
    return renderBasicEditableField(route, 'routeName', _('name'), route.RouteName)

def renderRouteType(route):
    opts = shd.ShdRoute.routeTypes.keys()
    return renderBasicEditableField(route, 'routeType', _('type'), route.Type, pullDownOpts = opts)

def routeTruckOpts(route):
    model = route.model

    opts = []
    for truck in model.trucks.values():
        opts.append((truck.Name, truck.getDisplayName()))

    opts.sort(key=lambda t: t[1])

    opts.reverse()
    opts.append(('', 'None'))
    opts.reverse()

    return opts

def renderRouteTruckType(route):
    opts = routeTruckOpts(route)

    displayValue = ''
    if route.TruckType in route.model.trucks:
        displayValue = route.model.trucks[route.TruckType].getDisplayName()

    return renderBasicEditableField(route, 'routeTruckType', _('truck type'), route.TruckType,
                                    pullDownOpts = opts,
                                    displayValue = displayValue)


def updateRouteTruckType(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)
    route = getRouteFromItemId(model, itemId)
    if origStr != route.TruckType:
        ul = LocalUpdateList(inputId, 
                             route.TruckType,
                             updateType='value',
                             displayValue=model.trucks[newStr].getDisplayName())
        raise(InvalidUpdate(_('value previously updated'), updateList=ul))
                            
    if newStr != '' and newStr not in model.trucks:
        ul = LocalUpdateList(inputId, 
                             route.TruckType,
                             updateType='value',
                             displayValue=model.trucks[origStr].getDisplayName())
        raise(InvalidUpdate(_('Invalid truck type'), updateList=ul))
                            
    route.TruckType = newStr

    displayValue = ''
    if route.TruckType in route.model.trucks:
        displayValue = route.model.trucks[route.TruckType].getDisplayName()

    ULCM.addUpdate(inputId, newStr, updateType='value', 
                   displayValue=displayValue)

    return True


def routePerDiemWidgetOpts(route):
    opts = {'widget': 'typeSelector',
            'label': '',
            'invtype': 'perdiems',
            'modelId': route.model.modelId,
            'selected': route.PerDiemType
            }.copy()
    return opts


def renderRoutePerDiemType(route):
    opts = routePerDiemWidgetOpts(route)

    displayValue = ''
    if route.PerDiemType in route.model.perdiems:
        displayValue = route.model.perdiems[route.PerDiemType].getDisplayName()

    return renderBasicEditableField(route, 'routePerDiemType', _('per diem rule'),
                                    route.PerDiemType,
                                    widgetOpts=opts,
                                    displayValue=displayValue)


def updateRoutePerDiemType(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)  # @UnusedVariable
    route = getRouteFromItemId(model, itemId)

    if origStr != '' and origStr != route.PerDiemType:
        ul = LocalUpdateList(inputId,
                             route.PerDiemType,
                             updateType='value',
                             displayValue=model.perdiems[newStr].getDisplayName())
        raise(InvalidUpdate(_('value previously updated'), updateList=ul))

    if newStr not in model.perdiems:
        ul = LocalUpdateList(inputId,
                             route.PerDiemType,
                             updateType='value',
                             displayValue=model.perdiems[origStr].getDisplayName())
        raise(InvalidUpdate(_('Invalid per diem type'), updateList=ul))

    route.PerDiemType = newStr

    displayValue = ''
    if route.PerDiemType in route.model.perdiems:
        displayValue = route.model.perdiems[route.PerDiemType].getDisplayName()

    ULCM.addUpdate(inputId, newStr, updateType='value',
                   displayValue=displayValue)

    return True

def updateDBRouteType(route, newStr):
    routeTypes = shd.ShdRoute.routeTypes

    # save the old route type because we need it below.
    oldType = route.Type
    route.Type = newStr
    newType = newStr # just to make the code clearer
    
    # if the route type changes who the supplier is then we need to reorder
    # the stops (and rerender them)
    # first check if there's enough stops in the route for that to make sense
    highestAffectedStopNum = max(routeTypes[oldType], routeTypes[newType])
    if len(route.stops) <= highestAffectedStopNum:
        return

    # position of supplier
    newPos = routeTypes[newType]
    oldPos = routeTypes[oldType]
    if newPos == oldPos:
        # don't do anything, just return the basic update
        return

    route.unlinkRoute()
    supplierStop = route.stops[oldPos]
    route.stops = route.stops[:oldPos] + route.stops[oldPos+1:]
    route.stops = route.stops[:newPos] + [supplierStop] + route.stops[newPos:]
    route.relabelRouteOrder()
    route.linkRoute()

def updateRouteType(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)
    route = getRouteFromItemId(model, itemId)
    if origStr != unicode(route.Type):
        raise(InvalidUpdate(_('value previously updated'), inputId, unicode(route.Type)))
    
    routeTypes = shd.ShdRoute.routeTypes

    if newStr not in routeTypes.keys():
        raise(InvalidUpdate(_('invalid route type'), inputId, unicode(route.Type)))

    if not shd.ShdRoute.types[newStr].multiClient():
        if len(route.clients()) > 1:
            raise(InvalidUpdate(_('New route type {0} does not support multiple client stores').format(newStr)))

    ULCM.addUpdate(inputId, newStr)

    # to be used in generating update below
    highestAffectedStopNum = max(routeTypes[route.Type], routeTypes[newStr])

    updateDBRouteType( route, newStr )
    
    # now we need to update the client copy of the route type and
    # resend all stops up to highestAffectedStopNum
    # need to follow the same logic as in renderRouteJson() but send things
    # differently
    storesVisited = []
    for i in xrange(highestAffectedStopNum + 1):
        stop = route.stops[i]
        if stop.isSupplier:
            continue
        if stop.idcode in storesVisited:
            ULCM.addUpdate(packNodeId(stop),
                         string.join(renderStopData(stop), '\n'),
                         'node')
        else:
            ULCM.addUpdate(packNodeId(stop.store),
                         string.join(renderStoreData(stop.store), '\n'),
                         'node')
            
    return True

def renderRouteTimings(route):
    fields = [EditableFieldInfo('routeInterval', _('shipping interval(days)'),
                                route.ShipIntervalDays, size=8),
              EditableFieldInfo('routeLatency', _('latency(days)'),
                                route.ShipLatencyDays, size=8)]
    return renderBasicEditableFields(route, 'routeTimings', fields)

def renderRouteConditions(route):
    return renderBasicEditableField(route, 'routeConditions', _('conditions'), route.Conditions)

def updateRouteConditions(inputId, model, origStr, newStr):
    modelId, itemId, field = inputIdTriple(inputId)
    route = getRouteFromItemId(model, itemId)
    if route.Conditions != origStr:
        raise(InvalidUpdate(_('conditions previously updated'), inputId, route.Conditions))
    route.Conditions = newStr
    return newStr

def renderRouteOrderAmount(route):
    etl = EditableTupleList()
    for stop in route.stops:
        name = stop.store.NAME
        etl.addTuple(EditableTuple(stop.PullOrderAmountDays,
                                   getItemId(stop),
                                   _('order amount in days for {0}').format(name)))
    return renderBasicTupleList(route,
                                'routeOrderAmount',
                                EditableFieldInfo('routeOrderAmount',
                                                  _('order amounts'),
                                                  etl,
                                                  fieldType='tuplelist'))

    

def renderRouteDistances(route):
    etl = EditableTupleList()
    for stop in route.stops:
        nextName = stop.nextStop(loopOk=True).store.NAME
        etl.addTuple(EditableTuple(stop.DistanceKM,
                                   getItemId(stop),
                                   _('distance to %s(km)').format(nextName)))
    return renderBasicTupleList(route,
                                'routeDistances',
                                EditableFieldInfo('routeDistances',
                                                  _('distances'),
                                                  etl,
                                                  fieldType='tuplelist'))


def renderRouteTransitHours(route):
    etl = EditableTupleList()
    for stop in route.stops:
        nextName = stop.nextStop(loopOk=True).store.NAME
        etl.addTuple(EditableTuple(stop.TransitHours,
                                   getItemId(stop),
                                   _('time to {0}(hours)').format(nextName)))
    return renderBasicTupleList(route,
                                'routeTransitHours',
                                EditableFieldInfo('routeTransitHours',
                                                  _('transit hours'),
                                                  etl,
                                                  fieldType='tuplelist'))
    

def renderStopLabelString(stop):
    s = _("{0}({1}) (stop {2})").format(stop.store.NAME, stop.idcode, stop.RouteOrder)
    return '<b>%s</b>'%s
        

def renderStopLabel(stop):
    ret = []
    dispId = packInputId(stop.modelId, stop, 'stopHeader')
    ret.append('<p id="%s" style="display:inline;" %s>%s</p>'%\
                   (dispId, dndString, renderStopLabelString(stop)))
    return ret

def renderStopData(stop):
    ret = []
    ret.extend(renderStopLabel(stop))
    ret.append('<div class="stop-edits-border">')
    ret.append('</div>')
    return ret

def renderStopJson(stop):
    ret = {}
    retData = {}
    retData['title'] = string.join(renderStopData(stop), '\n')
    retData['attr'] = {'href':'/testing', 'class':'em_replace_me'}
    ret['data'] = retData
    
    # stops are now only leafs, if not it would be a store
    ret["state"] = "leaf"

    ret["attr"] = { "id" : packNodeId(stop) }

    return ret

def renderRouteMessages(route):
    ret = []
    inputId = packInputId(route.modelId, route, 'routeMessages')
    ret.append('<div id="%s" class="em-message-border pre-emsmb" style="display:none;">'%inputId)
    ret.append('</div>')

    return ret

def renderRouteChildMessages(route):
    ret = []
    inputId = packInputId(route.modelId, route, 'routeChildMessages')
    ret.append('<div id="%s" class="em-child-message-border pre-emsmb" style="display:none;">'%inputId)
    ret.append('</div>')
    return ret

def renderRouteData(route):
    ret = []
    ret.extend(renderRouteLabel(route))
    ret.extend(renderRouteMessages(route))
    ret.extend(renderRouteChildMessages(route))
    ret.append('<div class="route-edits-border">')
    ret.extend(renderRouteName(route))
    ret.extend(renderRouteType(route))
    ret.extend(renderRouteTruckType(route))
    ret.extend(renderRouteTimings(route))
    ret.extend(renderRouteTransitHours(route))
    ret.extend(renderRouteDistances(route))
    ret.extend(renderRouteOrderAmount(route))
    ret.extend(renderRouteConditions(route))
    ret.extend(renderRoutePerDiemType(route))
    ret.append('</div>')
    return ret

class SDC:
    "stop display constants, ie what to display for a given stop in a route"
    DISP_NOTHING = 1
    DISP_STORE = 2
    DISP_STOP = 3

def calcStopDisplayTypes(route):
    "returns a list corresponding to how each stop should be displayed on a route"
    ret = []
    storesVisited = []
    for stop in route.stops:
        if stop.isSupplier:
            ret.append(SDC.DISP_NOTHING)
            continue
        if stop.idcode in storesVisited:
            ret.append(SDC.DISP_STOP)
        else:
            ret.append(SDC.DISP_STORE)
            storesVisited.append(stop.idcode)

    return ret

def renderRouteJson(route):
    ret = {}
    retData = {}
    retData['title'] = string.join(renderRouteData(route), '\n')
    retData['attr'] = {'href':'/testing', 'class':'em_replace_me'}
    ret['data'] = retData
    if route.stops:
        ret["state"] = "open"
        stops = route.stops
        ret["children"] = []

        sd = calcStopDisplayTypes(route)
        for i, stop in enumerate(stops):
            if sd[i] == SDC.DISP_NOTHING:
                continue
            if sd[i] == SDC.DISP_STOP:
                ret["children"].append(renderStopJson(stop))
            if sd[i] == SDC.DISP_STORE:
                ret["children"].append(renderStoreJson(stop.store))

    else:
        ret["state"] = "leaf"
    ret["attr"] = { "id" : packNodeId(route) }
    return ret



def renderStoreRouteData(store):
    ret = []
    ret.extend(renderStoreLabel(store))
    return ret

def renderStoreRoutesJson(store):
    ret = {}
    retData = {}
    retData['title'] = string.join(renderStoreRouteData(store), '\n')
    retData['attr'] = {'href' : '/testing', 'class' : 'em_replace_me'}
    ret['data'] = retData
    if store.clients():
        ret["state"] = "open"
        routes = store.clientRoutes()
        routes.sort(key = lambda r: r.RouteName)
        ret["children"] = []
        for route in routes:
            ret["children"].append(renderRouteJson(route))
    else:
        ret["state"] = "leaf"
    ret["attr"] = { "id" : packNodeId(store, optType='T') }
    return ret


def renderUnattachedJson(modelId, stores):
    ret = {}
    retData = {}
    dispId = packInputId(modelId, LiteralItem('U'), 'unattachedHeader')
    s = _('Unattached')
    retData['title'] = '<h3 id="%s" style="display:inline;" %s>%s</h3>'%\
        (dispId, dropString, s)
    retData['attr'] = {'href' : '/testing', 'class' : 'em_replace_me'}
    ret['data'] = retData
    if len(stores):
        ret["state"] = "open"
        ret["children"] = []
        for store in stores:
            ret["children"].append(renderStoreJson(store))
    else:
        ret["state"] = "leaf"
    ret["attr"] = { "id" : packNodeId('Unattached') }
    return ret
    
def getUserInput(model):
    dbSession = Session.object_session(model)
    modelId = model.modelId
    return input.UserInput(modelId, True, dbSession)

def categoryLevelList(model, userInput=None):
    if userInput is None:
        userInput = getUserInput(model)
    return userInput['levellist']

def centralLevelCategories(model, userInput=None):
    if userInput is None:
        userInput = getUserInput(model)
    return userInput['centrallevellist']


@bottle.route('/json/modelRoutes/<modelId>')
def jsonModelRoutes(db, uiSession, modelId):
    """
    provide updates to the model structure tree when nodes are opened
    """
    nodeId = getParm('id')

    (tree, nodeType, nodeId) = TupleFromNodeId(nodeId)

    with selectTree(tree):
        with ULCM():
            modelId = int(modelId)
            uiSession.getPrivs().mayReadModelId(db, modelId)
            model = shadow_network_db_api.ShdNetworkDB(db, modelId)

            ret = []
            if nodeType == '-':
                clc = centralLevelCategories(model)
                rootStores = model.rootStores()
                stores = []
                for store in rootStores:
                    if nodeId == '1' and store.CATEGORY in clc:
                        stores.append(store)
                    if nodeId == '2' and store.CATEGORY not in clc:
                        stores.append(store)
                if nodeId == '1':
                    for store in stores:
                        ret.append(renderStoreJson(store))
                else:
                    ret.append(renderUnattachedJson(modelId, stores))

            elif nodeType == METC.STORE:
                parentStore = model.getStore(long(nodeId))
                routes = parentStore.clientRoutes()
                routes.sort(key=lambda r: r.RouteName)
                for route in routes:
                    ret.append(renderRouteJson(route))

            elif nodeType == METC.STOP:  # this shouldn't happen
                raise RuntimeError(_("invalid code path.  Trying to expand stop"))
                try:
                    stop = getStopFromResiliantStopId(model, nodeId[1:])
                except:
                    jsonRet = { 'success' : False,
                                'errorString' : _('The structure of this model has been changed.  Please reload this page.'),
                                'successString' : 'False' }
                    return jsonRet

                store = stop.store
                routes = store.clientRoutes()
                for route in routes:
                    ret.append(renderRouteJson(route))
            else:
                raise RuntimeError(_('invalid node type {0}').format(nodeId[0]))

            updates = ULCM.updateList()

            jsonRet = { 'success' : True, 
                        'successString' : 'True', 
                        'data' : ret,
                        'updates' : updates }
            #print jsonRet
            return jsonRet




    

# these functions should either return True if they've just updated the update list
# or return the new value to set to be added to an update list.
# (or throw an invalid update exception)
updateFn = {
    'storeCategory' : updateCategory,
    'storeLatitude' : updateFloat,
    'storeLongitude' : updateFloat,
    'storeUseVialsInterval' : updateFloat,
    'storeUseVialsLatency' : updateFloat,
    'storeUtilizationRate' : updateFloat,
    'storeName' : updateStoreName,
    'storeDemand' : updateStoreDemandCount,
    'storefridges' : updateStoreInvCount,
    'storetrucks' : updateStoreInvCount,
    'storeNotes' : updateStoreNotes,
    'storeSiteCost' : updateFloat,
    'storeSiteCostCurCode' : updateStoreSiteCostCurCode,
    'storeSiteCostYear' : updateStoreSiteCostYear,
    'routeName' : updateRouteName,
    'routeType' : updateRouteType,
    'routeTransitHours' : updateFloat,
    'routeDistances' : updateFloat,
    'routeOrderAmount' : updateFloat,
    'routeTruckType' : updateRouteTruckType,
    'routeInterval' : updateFloat,
    'routeLatency' : updateFloat,
    'routeConditions' : updateRouteConditions,
    'routePerDiemType' : updateRoutePerDiemType
    }


@bottle.route('/json/modelUpdate', method='POST')
@bottle.route('/json/modelUpdate')
def jsonModelUpdate(db, uiSession):
    """
    handle simple field updates.  Pass the update off to a function based on
    the field part of the inputId (as referenced in updateFn
    """
    # print 'parms: %s' % {k:v for k,v in bottle.request.params.items()}
    try:
        inputId = getParm('inputId')
        inputs = unpackInputId(inputId)
        origStr = getParm('origStr')
        newStr = string.strip(getParm('newStr'))

        modelId = inputs['modelId']
        itemId = inputs['itemId']
        field = inputs['field']
        secondaryId = inputs['secondaryId']
        tree = inputs['tree']

        uiSession.getPrivs().mayModifyModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)

        with selectTree(tree):
            with ULCM():
                val = updateFn[field](inputId, model, origStr, newStr)

                if val is not True:
                    ULCM.addUpdate(inputId, val)

                ret =  { 'success': True, 'updateList' : ULCM.updateList() }
            #    print ret
                return ret

    except InvalidUpdate as e:
        ret = { 'success' : False }
        if e.updateList is not None:
            ul = e.updateList
        elif e.setVal is not None and e.inputId is not None:
            ul = LocalUpdateList(e.inputId, e.setVal)
        else:
            # for lack of anything better, reset the client to the original value
            ul = LocalUpdateList(inputId, origStr)

        ret['updateList'] = ul.updateList()
        ret['errorString'] = e.string
        # print ret
        return ret

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()
        # for lack of anything better, reset the client to the original value
        ul = LocalUpdateList(inputId, origStr)
        return { 'success' : False, 'errorString' : _('unknown error'), 'updateList': ul.updateList() }
    
    # for lack of anything better, reset the client to the original value
    ul = LocalUpdateList(inputId, origStr)
    return { 'success' : False, 'errorString' : _('unreachable error'), 'updateList': ul.updateList() }



addTupleFn = {
    'storeDemand' : addTupleStoreDemand,
    'storefridges' : addTupleStoreInv,
    'storetrucks' : addTupleStoreInv
}

@bottle.route('/json/modelUpdateAddTuple')
def jsonModelUpdateAddTuple(db, uiSession):
    """
    handle adding a tuple to a tuple list by the client

    Hand the update to an add tuple function based on the field part of the inputId
    (referenced in addTupleFn)
    """
    try:
        inputId = getParm('inputId')
        inputs = unpackInputId(inputId)
        value = getParm('value')
        count = getParm('count')

        modelId = inputs['modelId']
        itemId = inputs['itemId']
        field = inputs['field']
        secondaryId = inputs['secondaryId']
        tree = inputs['tree']

        uiSession.getPrivs().mayModifyModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)

        with selectTree(tree):
            with ULCM():
                addTupleFn[field](inputId, model, value, count)
                return  { 'success': True, 'updateList' : ULCM.updateList() }


    except InvalidUpdate as e:
        ret = { 'success' : False }
        ret['errorString'] = e.string
        return ret

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()
        return { 'success' : False, 'errorString' : _('unknown error') }

    return { 'success' : False, 'errorString' : _('unreachable error') }


def createCopyName(model, name):
    a = 1
    while True:
        try:
            model.getStoreByName('%s(%d)'%(name, a))
        except:
            break
        a += 1
    return '%s(%d)'%(name, a)


def createCopyRouteName(model, name):
    a = 1
    while True:
        try:
            model.getRoute('%s_%d'%(name, a))
        except:
            break
        a += 1
    return '%s_%d'%(name, a)

def createCopyId(model, idcode):
    idcode = int(idcode) + 1
    while True:
        try:
            model.getStore(long(idcode))
        except:
            break
        idcode = idcode * 2 + random.randint(1,10)
    return idcode

def copyStoreToUnlinked(model, store):
    # first make the copy
    rec = store.createRecord()
    rec['NAME'] = createCopyName(model, rec['NAME'])
    rec['idcode'] = createCopyId(model, rec['idcode'])
    newStore = model.addStore(rec)
    
    # since we're doing this before the commit adds this field, we'll do it manually
    newStore.modelId = store.modelId

    # make the new store visible
    # unlinked area is already open so that's one less worry
    with selectTree(TREE.UNATTACHED):
        storeJson = renderStoreJson(newStore)
        
        val = { 'parent' : packNodeId('Unattached'),
                'location' : 'last',
                'node' : storeJson }
    ULCM.addUpdate(storeJson['attr']['id'], val, 'create')


@bottle.route('/json/RequestBasicEdit')
def jsonRequestBasicEdit(db, uiSession):
    try:
        modelId = getParm('modelId')
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)

        packedId = getParm('packedId')
        iId = unpackInputId(packedId)
        itemId = iId['itemId']
        secondaryId = iId['secondaryId']
        tree = iId['tree']
        itemType = iId['itemType']

        context = getParm('context')
        
        request = getParm('request')

        nyi = False
        with ULCM():
            if itemType == METC.STORE:
                store = getStoreFromItemId(model, itemId)
                if request == 'copy':
                    copyStoreToUnlinked(model, store)
                elif request == 'cut':
                    moveStoreToUnlinked(store, tree)
                elif request == 'delete':
                    deleteStore(store, tree)
                else:
                    nyi = True
            elif itemType == METC.ROUTE:
                route = getRouteFromItemId(model, itemId)
                if request == 'delete':
                    deleteRoute(route, tree)
                else:
                    nyi = True
            else:
                nyi = True

            if nyi:
                raise InvalidUpdate(_('Not yet implemented (itemType {0}, request {1})').format(itemType, request))
            return {'success' : True, 'updateList' : ULCM.updateList() }

    except InvalidUpdate as e:
        ret = { 'success' : False }
        ret['errorString'] = e.string
        return ret

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()

        return { 'success' : False, 'errorString' : _('unknown error') }

            
        

class DetachStore:
    """
    class for detaching a store and generating updates to both the model and display
    """
    def __init__(self):
        self.store = None         # the store in question
        self.deleteStore = False  # do we delete the store in question
        self.supplierRoute = None # the supplier route or none if non-existant
        # whether to delete supplier route (and orphan sibblings) or
        # just modify it (and resend route data)
        self.deleteSupplierRoute = False
        self.routesToDelete = []  # client routes that will need deleted
        self.clientStoresToDetach = []  # client stores that will become orphaned
        self.sibblingStores = [] # sibbling stores


    def prep(self, store, 
             detachClients=False, 
             deleteStore=False,
             forceDeleteParentRoute=False):
        """
        calculates what needs to happen to detach a store either for deletion or moving

        options:
            detachClients : breaks the links between the store and clients stores in
                    addition to the store and its parent stores.
            deleteStore : after detaching the store, delete it (implies detachClients)
            forceDeleteParentRoute : by default the parent route is only deleted if it
                    is rendered non-functional.  This will cause the parent route to be
                    deleted regardless.
        """
        self.store = store

        if deleteStore:
            self.deleteStore = True
            detachClients = True

        if detachClients:
            clients = store.clients()
            for s,r in clients:
                if s not in self.clientStoresToDetach:
                    self.clientStoresToDetach.append(s)
                if r not in self.routesToDelete:
                    self.routesToDelete.append(r)

        suppliers = store.suppliers()
        if len(suppliers) == 0:
            return
        if len(suppliers) > 1:
            raise RuntimeError("store id %d of model %d has multiple suppliers"%\
                                   (store.idcode, store.modelId))

        (sStore, sRoute) = suppliers[0]
        self.supplierRoute = sRoute
        
        t = sRoute.Type
        ss = shd.ShdRoute.types[t].ss()

        # find the sibblings that share the route of the store to be removed
        for stop in sRoute.stops:
            sid = stop.idcode
            if sid == sStore.idcode:
                continue
            if sid == store.idcode:
                continue
            if sid in self.sibblingStores:
                continue
            self.sibblingStores.append(sid)
        
        # if the store to be removed is stop number zero (ie supplies the truck)
        # then the route needs to be removed.
        # similarly if the store is the only client of the route then the route
        # needs removed.
        if (sRoute.stops[0].idcode == store.idcode) \
                or (len(self.sibblingStores) == 0) \
                or forceDeleteParentRoute:
            self.deleteSupplierRoute = True
        

                    
    def generateUpdatesAndModifyDb(self, tree, addToUnattached=True):
        "generate updates and append them to the update list"
        # we know that the tree is open at least to the store to be detached
        # we also know that the unattached tree is open
        
        net = self.store.net
        session = Session.object_session(net)


        # we don't need to remove the client stores.  We do need to remove the routes
        with selectTree(tree):
            for route in self.routesToDelete:
                ULCM.addUpdate(packNodeId(route), 'X', 'remove')
                net.removeRoute(route)

            if self.deleteSupplierRoute:
                ULCM.addUpdate(packNodeId(self.supplierRoute), 'X', 'remove')
                net.removeRoute(self.supplierRoute)
                # move any sibblings to unattached
                with selectTree(TREE.UNATTACHED):
                    for store in self.sibblingStores:
                        storeJson = renderStoreJson(store)
                        val = { 'parent' : packNodeId('Unattached'),
                                'location' : 'last',
                                'node' : storeJson }
                        ULCM.addUpdate(storeJson['attr']['id'], val, 'create')
                
            else:
                if self.supplierRoute is not None:
                    self.supplierRoute.removeStop(self.store)
                # need to delete store node
                ULCM.addUpdate(packNodeId(self.store, tree=tree), 'X', 'remove')
                # need to resend route node
                if self.supplierRoute is not None:
                    updateResendNodeFromItem(self.supplierRoute, tree)
                    # need to resend any child stop (not store) nodes
                    sd = calcStopDisplayTypes(self.supplierRoute)
                    for i,stop in enumerate(self.supplierRoute.stops):
                        if not sd[i] == SDC.DISP_STOP:
                            continue
                        updateResendNodeFromItem(stop, tree)

                    addUpdateClearUpdates(self.supplierRoute)

            # delete store if necessary
            if self.deleteStore:
                # we've already made all the interface updates for this
                # just kill it.
                net.removeStore(self.store)
            # otherwise move it to detached
            else:
                if addToUnattached:
                    with selectTree(TREE.UNATTACHED):
                        storeJson = renderStoreJson(self.store)
                        val = { 'parent' : packNodeId('Unattached'),
                                'location' : 'last',
                                'node' : storeJson }
                        ULCM.addUpdate(storeJson['attr']['id'], val, 'create')
                

            # deal with the now detached client stores
            with selectTree(TREE.UNATTACHED):
                for store in self.clientStoresToDetach:
                    storeJson = renderStoreJson(store)
                    val = { 'parent' : packNodeId('Unattached'),
                            'location' : 'last',
                            'node' : storeJson }
                    ULCM.addUpdate(storeJson['attr']['id'], val, 'create')
                
    
def addStoreAsClient(store, supStore, hintRoute=None):
    if hintRoute is not None:
        if isinstance(hintRoute, shd.ShdRoute):
            recs = hintRoute.createRecords()
        else:
            recs = hintRoute
        if len(recs) < 2:
            raise RuntimeError('hintRoute is invalid')
        recs = recs[0:2]
    else:
        recs = [{'RouteName' : 'new_route',
                 'Type' : 'varpush',
                 # can we get a truck type from store and supStore and rType?
                 'TruckType' : '', 
                 'ShipIntervalDays' : 28},
                {'Type' : 'varpush',
                 'TruckType' : '',
                 'ShipIntervalDays' : 28}]

    rType = recs[0]['Type']
    
    # fill in some details
    ss = shd.ShdRoute.types[rType].supplierStop()
    fc = shd.ShdRoute.types[rType].firstClientStop()
    
    routeName = createCopyRouteName(store.net, recs[0]['RouteName'])
    recs[ss]['RouteName'] = routeName
    recs[ss]['idcode'] = supStore.idcode
    recs[ss]['LocName'] = supStore.NAME
    # if I had locations and general speeds I could try and fill in things like 
    # distance and transit hours, but right now I'm not even going to try.

    recs[fc]['RouteName'] = routeName
    recs[fc]['idcode'] = store.idcode
    recs[ss]['LocName'] = store.NAME

    net = supStore.net
    return net.addRoute(recs)

def findHintRoute(storeAndRouteList):
    for item in storeAndRouteList:
        if isinstance(item, shd.ShdRoute):
            return item
        if not isinstance(item, shd.ShdStore):
            continue
        store = item
        for route in store.clientRoutes():
            return route
        
    return None
    

def moveStoreToRoute(store, route, srcTree, dstTree, dstParentNode, dstStatus):
    # can't move store to a child route
    dstSupplier = route.supplier()
    dstSuppliers = dstSupplier.recursiveSuppliers()
    dstSuppliers.append((dstSupplier, None))
    for supStore, xxxRoute in dstSuppliers:
        if store is supStore:
            raise InvalidUpdate(_("It is not allowed to move a store to one of its clients"))

    if store.supplierRoute() is route:
        return reorderStops(store, None, srcTree, dstTree, dstParentNode, dstStatus)

    # verify that the route type will support multiple clients
    if not shd.ShdRoute.types[route.Type].multiClient():
        raise InvalidUpdate(_("Destination route type only supports one client store"))

    # at this point we wish to detach the store
    ds = DetachStore()
    ds.prep(store)
    ds.generateUpdatesAndModifyDb(srcTree, addToUnattached=False)

    # now let's make it the last store within that route
    lastClientRec = None
    recs = route.createRecords()
    for stop,rec in zip(route.stops, recs):
        if stop.isSupplier:
            continue
        lastClientRec = rec

    rec = lastClientRec
    rec['LocName'] = store.NAME
    rec['idcode'] = store.idcode


    net = store.model
    route.addStop(rec, net.stores, relink=True)
    
    # the route should be populated.  If not then we're not handling it correctly
    if dstStatus == 'unpopulated':
        # if this ever becomes valid, addUpdate(dstParentNode, 'X', 'open') should work
        raise RuntimeError("destination route display in unexpected state")

    with selectTree(dstTree):
        storeJson = renderStoreJson(store)
        
        val = { 'parent' : packNodeId(route),
                'location' : 'last',
                'node' : storeJson }
        ULCM.addUpdate(storeJson['attr']['id'], val, 'create')

def reorderStops(store, dstStore, srcTree, dstTree, dstParentNode, dstStatus):
    """
    move store to just after dstStore in the stop order list
    if dstStore is None move store to the first spot
    """
    route = store.supplierRoute()

    #
    #BUG we do not support interface interactions with visiting the same store twice
    # on a route
    #

    with selectTree(dstTree):
        ULCM.addUpdate(packNodeId(store), 'X', 'remove')

    route.unlinkRoute()

    # remove the parent stop from this
    parentIndex = route.routeTypes[route.Type]
    parentStop = route.stops[parentIndex]
    route.stops = route.stops[:parentIndex] + route.stops[parentIndex+1:]

    # remove the source stop
    srcIndex = None
    for i, stop in enumerate(route.stops):
        if stop.idcode == store.idcode:
            srcIndex = i
            srcStop = stop
            break

    route.stops = route.stops[:srcIndex] + route.stops[srcIndex + 1:]

    # put it in place immediately after the dest stop
    if dstStore is None:
        dstIndex = -1
    else:
        dstIndex = None
        for i, stop in enumerate(route.stops):
            if stop.idcode == dstStore.idcode:
                dstIndex = i
                break

    route.stops = route.stops[:dstIndex+1] + [srcStop] + route.stops[dstIndex+1:]

    # put the parent stop back in
    route.stops = route.stops[:parentIndex] + [parentStop] + route.stops[parentIndex:]

    # do some cleanup
    route.relabelRouteOrder()
    route.linkRoute()

    updateResendNodeFromItem(store.supplierRoute(), dstTree)
    with selectTree(dstTree):
        storeJson = renderStoreJson(store)
        val = { 'parent' : packNodeId(store.supplierRoute()),
                'location' : dstIndex + 1 ,
                'node' : storeJson }
        ULCM.addUpdate(storeJson['attr']['id'], val, 'create')


def moveStoreToStore(store, dstStore, srcTree, dstTree, dstParentNode, dstStatus, routeTemplate):
    "move a store so that it's becomes a client of dstStore"

    # if we're dropping a store onto itself, do nothing
    if store is dstStore:
        return

    net = store.net

    #
    # check if this move is valid
    #
    suppliers = dstStore.recursiveSuppliers()
    for supStore, supRoute in suppliers:
        if supStore.idcode == store.idcode:
            raise InvalidUpdate(_("It is not allowed to move a store to one of its clients"))

    # see which type of move this is.  
    # if src and dst share the same parent route then we're just reordering the route
    if store.supplierRoute() is dstStore.supplierRoute():
        #print "suppliers are same"
        return reorderStops(store, dstStore, srcTree, dstTree, dstParentNode, dstStatus)

    #
    # next actually make the move
    #
    if routeTemplate is not None:
        hintRoute = routeTemplate
    else:
        hintRoute = findHintRoute([dstStore])
    ds = DetachStore()
    ds.prep(store)
    ds.generateUpdatesAndModifyDb(srcTree, addToUnattached=False)
    
    newRoute = addStoreAsClient(store, dstStore, hintRoute)
    # add the modelId to newRoute otherwise display stuff breaks.  Alternately
    # we could cause the commit to happen, but that's not such a good plan either.
    newRoute.modelId = store.modelId 

    #
    # finish synchronizing the display
    #


    # make the new route appear
    # make the new store appear under the new route
    return updateDisplayNewRoute(newRoute, dstTree, dstParentNode, dstStatus)


def moveStoreToUnlinked(store, srcTree):
    "move store to the unattached pile, return an update list"
    ds = DetachStore()
    ds.prep(store, detachClients=False, deleteStore=False)
    ds.generateUpdatesAndModifyDb(srcTree)


def deleteStore(store, srcTree):
    "delete store, return an update list"
    ds = DetachStore()
    ds.prep(store, detachClients=True, deleteStore=True)
    ds.generateUpdatesAndModifyDb(srcTree)


def deleteRoute(route, srcTree):
    """
    delete a route and generate updates.

    We're going to cheat by using detachStore on a client with some special
    options since that already did virtually everything we needed anyways.
    """
    store = route.clients()[0]
    ds = DetachStore()
    ds.prep(store, forceDeleteParentRoute = True)
    ds.generateUpdatesAndModifyDb(srcTree)
    

def updateDisplayNewRoute(route, dstTree, dstParentNode, dstStatus):
    "return an update list to make a newly created route show up in the UI"
    if dstStatus == 'unpopulated':
        # the target node's children has never been populated 
        # so it's better just to tell it to open and get the new content
        # since that's already been updated.
        ULCM.addUpdate(dstParentNode, 'X', 'open')
        return

    # else the target node is either a leaf-node or has previously been populated.
    with selectTree(dstTree):
        routeJson = renderRouteJson(route)
        # unfortunately child nodes aren't 'create'd so let's pull them out
        # and add them as separate create updates.
    childNodes = []
    if 'children' in routeJson:
        childNodes = routeJson['children']
        del routeJson['children']

    val = { 'parent' : dstParentNode,
            'location' : 'last',
            'node' : routeJson }
    ULCM.addUpdate(routeJson['attr']['id'], val, 'create')
    for node in childNodes:
        val = { 'parent' : routeJson['attr']['id'],
                'location' : 'last',
                'node' : node }
        ULCM.addUpdate(node['attr']['id'], val, 'create')



def moveRoute(route, store, srcTree, dstTree, dstParentNode, dstStatus):

    # it is illegal/nonsensical to move a route to one of its children
    # (this would create a circular route)
    suppliers = store.recursiveSuppliers()
    for supStore, supRoute in suppliers:
        if supRoute.RouteName == route.RouteName:
            raise InvalidUpdate(_("It is not allowed to move a route to one of its clients"))

    
    # perform the move

    # before anything can be done with the stops in a route
    route.unlinkRoute()

    # get the supplier stop
    stop = route.stops[shd.ShdRoute.routeTypes[route.Type]]
    
    stop.store = store
    stop.idcode = store.idcode  # does sqlalchemy do this for me?
    

    route.relabelRouteOrder()
    route.linkRoute()

    # move has been made, figure out how to display the move on the client side
    # mark the moved route to be removed from the client display
    ULCM.addUpdate(packNodeId(route, tree=srcTree), 'X', 'remove')
    
    updateDisplayNewRoute(route, dstTree, dstParentNode, dstStatus)



@bottle.route('/json/modelUpdateDND', method='POST')
def jsonModelUpdateDND(db, uiSession):
    """
    handle a drag and drop event from the client
    """
    
    try:
        # draggable object that was picked up
        srcId = getParm('srcId')
        (modelId, srcItemId, srcField) = inputIdTriple(srcId)
        srcTree = inputIdTree(srcId)

        # object that was dropped on
        dstId = getParm('dstId')
        (modelId, dstItemId, dstField) = inputIdTriple(dstId)
        dstTree = inputIdTree(dstId)

        # any extra client context we should care about?
        context = json.loads(getParm('context'))
        

        # has the dstNode had its children fetched?
        # value should be one of 'leaf', 'populated', 'unpopulated' or 'other'
        dstStatus = getParm('dstStatus')

        uiSession.getPrivs().mayModifyModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)

        with ULCM():

            if srcField == 'stopHeader' or dstField == 'stopHeader':
                raise InvalidUpdate('Drag and drop for dropandcollect route types are not yet implemented')

            if srcField == 'routeHeader':
                # only acceptable place to move a route is onto a store
                # this should be a 'storeHeader'
                if dstField == 'storeHeader':
                    store = getStoreFromItemId(model, dstItemId)
                    route = getRouteFromItemId(model, srcItemId)
                    moveRoute(route,
                              store,
                              srcTree, 
                              dstTree, 
                              packNodeId(store, tree=dstTree),
                              dstStatus)
                else:
                    raise InvalidUpdate(_('Routes may only be moved on to locations'))

            if srcField == 'storeHeader':
                store = getStoreFromItemId(model, srcItemId)

                if dstField == 'routeHeader':
                    route = getRouteFromItemId(model, dstItemId)
                    moveStoreToRoute(store,
                                     route,
                                     srcTree,
                                     dstTree,
                                     packNodeId(route, tree=dstTree),
                                     dstStatus)
                elif dstField == 'storeHeader':
                    dstStore = getStoreFromItemId(model, dstItemId)
                    routeTemplate = None
                    if context['routeTemplate'] is not None:
                        try:
                            routeTemplate = model.getRoute(context['routeTemplate'])
                        except:
                            pass
                    moveStoreToStore(store, 
                                     dstStore, 
                                     srcTree, 
                                     dstTree, 
                                     packNodeId(dstStore, tree=dstTree),
                                     dstStatus,
                                     routeTemplate)
                elif dstField == 'unattachedHeader':
                    moveStoreToUnlinked(store, srcTree)
                else:
                    raise InvalidUpdate(_('Not yet implemented (dstField: {0})').format(dstField))


            return {'success' : True, 'updateList' : ULCM.updateList() }



    except InvalidUpdate as e:
        ret = { 'success' : False }
        ret['errorString'] = e.string
        return ret

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()

        return { 'success' : False, 'errorString' : _('unknown error') }


    
def updateResendNodeFromItem(item, tree):
    nodeId = packNodeId(item, tree=tree)
    # hmm, I need the node type that packNodeId used.  May as well get it 
    # from the nodeId.
    (x,nodeType,y) = TupleFromNodeId(nodeId)

    with selectTree(tree):
        if nodeType == METC.STORE:
            store = item
            #addUpdateClearUpdates(store)
            ULCM.addUpdate(packNodeId(store),
                           string.join(renderStoreData(store), '\n'),
                           'node')

        if nodeType == METC.ROUTE:
            route = item
            #addUpdateClearUpdates(route)
            ULCM.addUpdate(packNodeId(route),
                           string.join(renderRouteData(route), '\n'),
                           'node')

        if nodeType == METC.STOP:
            stop = item
            #addUpdateClearUpdates(stop)
            ULCM.addUpdate(packNodeId(stop),
                           string.join(renderStopData(stop), '\n'),
                           'node')


def updateResendNodeFromNodeId(nodeId, model):
    (tree, nodeType, nodeId) = TupleFromNodeId(nodeId)

    with selectTree(tree):
        if nodeType == METC.STORE:
            store = model.getStore(long(nodeId))
            #addUpdateClearUpdates(store)
            ULCM.addUpdate(packNodeId(store),
                           string.join(renderStoreData(store), '\n'),
                           'node')

        if nodeType == METC.ROUTE:
            route = model.getRoute(nodeId)
            #addUpdateClearUpdates(route)
            ULCM.addUpdate(packNodeId(route),
                           string.join(renderRouteData(route), '\n'),
                           'node')

        if nodeType == METC.STOP:
            stop = getStopFromResiliantStopId(model, nodeId)
            #addUpdateClearUpdates(stop)
            ULCM.addUpdate(packNodeId(stop),
                           string.join(renderStopData(stop), '\n'),
                           'node')


@bottle.route('/json/ModelResendNode')
def jsonModelResendNode(db, uiSession):
    """
    resend a node to the client
    """
    try:
        modelId = getParm('modelId')
        uiSession.getPrivs().mayReadModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)

        nodeId = getParm('id')
        
        with ULCM():
            updateResendNodeFromNodeId(nodeId, model)
            return { 'success' : True, 'updateList' : ULCM.updateList() }

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()

        return { 'success' : False, 'errorString' : _('unknown error') }


def rseRenderAffectedCategories(unique, store, clients):
    global currentTree
    categories = {}
    for cStore, cRoute in clients:
        cat = cStore.CATEGORY
        if cat in categories:
            categories[cat] += 1
        else:
            categories[cat] = 1

    ret = []
    ret.append('<select class="rse_category_select" id="rse_category_%d" onchange="updateRSEDialog(%d,%d,\'%s\');">'%\
                   (unique, unique, store.idcode, currentTree))
    for cat,count in categories.items():
        ret.append('<option value="%s">%s (%d)</option>'%\
                       (cat, cat, count))
    ret.append('</select>')

    return ret
    

def rseDispNone(store, field, category, unique):
    divId = 'rse_content_%s'%unique
    
    ULCM.addUpdate(divId, '<p></p>', 'html')

def rseUpdateNone(store, field, category, unique, action, value):
    # this should be unreachable!
    pass

def rseDispUtilization(store, field, category, unique):
    global currentTree
    divId = 'rse_content_%s'%unique
    ret = []
    ret.append('<p>' + _('Set utilization rate:'))
    ret.append('<input type="text" class="rse_utilization_set_input" id="rseInput_set_%s" />'%unique)
    ret.append('<button type="button" class="rse_utilization_set_button" onclick="updateRSEValue(%s,%s,\'%s\',\'set\');">%s</button>'%(unique, store.idcode, currentTree, _('Ok')))
    ret.append('</p>')
    ret.append('<p>' + _('Mutliply rate by a factor:'))
    ret.append('<input type="text" class="rse_utilization_mult_input" id="rseInput_mult_%s" />'%unique)
    ret.append('<button type="button" class="rse_utilization_mult_button" onclick="updateRSEValue(%s,%s,\'%s\',\'mult\');">%s</button>'%(unique, store.idcode, currentTree, _('Ok')))
    ret.append('</p>')
    ret = string.join(ret, '\n')
    ULCM.addUpdate(divId, ret, 'html')

def rseUpdateUtilization(store, field, category, unique, action, value, secondary, tertiary):
    try:
        value = value.strip()
        value = float(value)
    except:
        raise InvalidRecursiveUpdate(_('Utilization rate must be 0.0 or greater'))

    if action not in ['set', 'mult']:
        raise InvalidRecursiveUpdate(_('invalid action {0}').format(action))

    clients = store.recursiveClients()
    for client, cRoute in clients:
        if client.CATEGORY != category:
            continue
        
        if action == 'set':
            client.utilizationRate = value
        if action == 'mult':
            client.utilizationRate *= value
        inputId = packInputId(store.modelId, client, 'storeUtilizationRate')
        ULCM.addUpdate(inputId, unicode(client.utilizationRate))

def rseDispCosts(store, field, category, unique):
    global currentTree
    divId = 'rse_content_%s'%unique
    ret = []
    ret.append('<p>' + _('Set cost information:'))
    ret.append('<div class="rse_cost_set_input" id="rseInput_set_%s">'%unique)
    ret.append('<input type="text" class="rse_cost1_set_input" id="rseInput_set_cost_%s" />'%unique)
    ret.append('<div id="rseInput_set_costcur_%s" class="hrm_widget_become_currencySelector"></div>' % unique)
    ret.append('<input type="text" class="rse_cost3_set_input" id="rseInput_set_costyear_%s" />'%unique)
    ret.append('</div>\n')
    ret.append('<button type="button" class="rse_cost_set_button" onclick="updateRSECostValue(%s,%s,\'%s\',\'set\');">%s</button>'%(unique, store.idcode, currentTree, _('Ok')))
    ret.append('</p>')
    ret = string.join(ret, '\n')
    ULCM.addUpdate(divId, ret, 'html')

def rseDispPerDiem(store, field, category, unique):
    global currentTree
    divId = 'rse_content_%s'%unique
    ret = []
    ret.append('<p>' + _('Set route per diem information:'))
    ret.append('<div class="rse_cost_set_input" id="rseInput_set_%s">'%unique)
    ret.append('<div id="rseInput_set_perdiem_%s" class="hrm_widget_become_perDiemSelector"></div>' % unique)
    ret.append('</div>\n')
    ret.append('<button type="button" class="rse_cost_set_button" onclick="updateRSERoutePerDiemValue(%s,%s,\'%s\',\'set\');">%s</button>'%(unique, store.idcode, currentTree, _('Ok')))
    ret.append('</p>')
    ret = string.join(ret, '\n')
    ULCM.addUpdate(divId, ret, 'html')

def rseUpdateCosts(store, field, category, unique, action, value, secondary, tertiary):
    try:
        cost = value.strip()
        cost = float(cost)
        assert cost >= 0.0
    except:
        raise InvalidRecursiveUpdate(_('Site cost must be a number greater than or equal to zero'))
    try:
        costcur = secondary.strip()
    except:
        raise InvalidRecursiveUpdate(_('Site cost currency is an invalid code'))
    try:
        costyear = tertiary.strip()
        costyear = int(costyear)
    except:
        raise InvalidRecursiveUpdate(_('Site cost base year must be an integer'))

    if action not in ['set']:
        raise InvalidRecursiveUpdate(_('invalid action {0}').format(action))

    clients = store.recursiveClients()
    for client, cRoute in clients:
        if client.CATEGORY != category:
            continue

        if action == 'set':
            client.SiteCost = cost
            client.SiteCostCurCode = costcur
            client.SiteCostYear = costyear
        inputId = packInputId(store.modelId, client, 'storeSiteCost')
        ULCM.addUpdate(inputId, unicode(client.SiteCost))
        inputId = packInputId(store.modelId, client, 'storeSiteCostCurCode')
        ULCM.addUpdate(inputId, unicode(client.SiteCostCurCode))
        inputId = packInputId(store.modelId, client, 'storeSiteCostYear')
        ULCM.addUpdate(inputId, unicode(client.SiteCostYear))

def rseUpdatePerDiem(store, field, category, unique, action, value, secondary, tertiary):
    # print 'rseUpdatePerDiem parms: store=%s field=%s category=%s unique=%s action=%s value=%s secondary=%s tertiary=%s' % \
    #     (store, field, category, unique, action, value, secondary, tertiary)
    try:
        pdType = store.model.perdiems[value]
    except:
        raise InvalidRecursiveUpdate(_('Invalid per diem type {0}').format(value))

    if action not in ['set']:
        raise InvalidRecursiveUpdate(_('invalid action {0}').format(action))

    clients = store.recursiveClients()
    doneSet = set()
    for client, cRoute in clients:
        if client.CATEGORY != category:
            continue
        if cRoute in doneSet:
            continue
        doneSet.add(cRoute)
        if action == 'set':
            cRoute.PerDiemType = pdType.Name
            inputId = packInputId(store.modelId, cRoute, 'routePerDiemType')
            ULCM.addUpdate(inputId, unicode(pdType.DisplayName))

def rseDispStorage(store, field, category, unique):
    rseDispInventory('fridges', store, field, category, unique)

def rseDispTransport(store, field, category, unique):
    rseDispInventory('trucks', store, field, category, unique)

def rseDispDemand(store, field, category, unique):
    rseDispInventory('demand', store, field, category, unique)

def rseDispStaff(store, field, category, unique):
    rseDispInventory('staff', store, field, category, unique)

def rseDispInventory(iType, store, field, category, unique):
    global currentTree
    divId = 'rse_content_%s'%unique
    if iType == 'demand':
        inv = getDemandTypeList(store.model)
    else:
        inv = getInvTypeList(store.model, iType)

    ret = []
    ret.append('<table id="rse_input_table_%s">'%unique)
    ret.append('  <tr>')
    ret.append('    <td class="rse_%s_action_header">%s</td>'%(iType, _('action')))
    ret.append('    <td class="rse_%s_count_header">%s</td>'%(iType, _('count')))
    ret.append('    <td class="rse_%s_type_header">%s</td>'%(iType, _('type')))
    ret.append('    <td style="display:none" class="rse_%s_repl_header">%s</td>'%(iType, _('replace with')))
    ret.append('    <td></td>')
    ret.append('  </tr>')
    ret.append('  <tr>')
    ret.append('    <td>')
    aeoString = 'onchange="autohideColumns({'
    aeoString += "'selectorId' : 'rse_input_action_%s', "%unique
    aeoString += "'tableId' : 'rse_input_table_%s', "%unique
    aeoString += "'defShow' : [1,2], "
    aeoString += "'defHide' : [3], "
    aeoString += "'conditionals' : {'clear' : [1,2], 'repl' : [1,3]}"
    aeoString += '});"'
    ret.append('      <select class="rse_%s_action_select" id="rse_input_action_%s"'%(iType,unique))
    ret.append('        %s>'%aeoString)
    ret.append('        <option value="add">%s</option>'%_('Add'))
    ret.append('        <option value="set">%s</option>'%_('Set'))
    ret.append('        <option value="scaleUp">%s</option>'%_('Scale (round up)'))
    ret.append('        <option value="scaleDn">%s</option>'%_('Scale (round dn)'))
    ret.append('        <option value="repl">%s</option>'%_('Replace with'))
    ret.append('        <option value="clear">%s</opton>'%_('Clear all'))
    ret.append('      </select>')
    ret.append('    </td><td>')
    ret.append('      <input class="rse_%s_count_input" id="rse_input_value_%s" type="text" size="7" />'%(iType, unique))
    ret.append('    </td><td>')
    ret.append('      <select class="rse_%s_type_select" id="rse_input_type_%s">'%(iType,unique))
    for i in inv:
        ret.append('    <option value="%s">%s</option>'%(i.Name,i.getDisplayName()))
    ret.append('      </select>')
    ret.append('    </td><td style="display:none">')
    ret.append('      <select class="rse_%s_repl_select" id="rse_input_repl_%s">'%(iType,unique))
    for i in inv:
        ret.append('    <option value="%s">%s</option>'%(i.Name,i.getDisplayName()))
    ret.append('      </select>')
    ret.append('    </td><td>')
    ret.append('      <button class="rse_%s_update_button" type="button" onclick="updateRSETypeValue(%s,%s,\'%s\');">%s</button>'%(iType, unique, store.idcode, currentTree, _('Ok')))
    ret.append('    </td>')
    ret.append('  </tr>')
    ret.append('<table>')

    ret = string.join(ret, '\n')
    ULCM.addUpdate(divId, ret, 'html')

def rseUpdateStorage(store, field, category, unique, action, value, secondary, tertiary):
    rseUpdateInventory('fridges', store, field, category, unique, action, value, secondary, tertiary)

def rseUpdateTransport(store, field, category, unique, action, value, secondary, tertiary):
    rseUpdateInventory('trucks', store, field, category, unique, action, value, secondary, tertiary)

def rseUpdateDemand(store, field, category, unique, action, value, secondary, tertiary):
    rseUpdateInventory('demand', store, field, category, unique, action, value, secondary, tertiary)

def rseUpdateStaff(store, field, category, unique, action, value, secondary, tertiary):
    rseUpdateInventory('staff', store, field, category, unique, action, value, secondary, tertiary)

def rseUpdateInventory(iType, store, field, category, unique, action, value, secondary, tertiary):
    if action not in ['set', 'add', 'clear', 'repl', 'scaleUp', 'scaleDn']:
        raise InvalidRecursiveUpdate('invalid action %s'%action)

    if action in ['set', 'add']:
        try:
            count = value.strip()
            count = int(count)
        except:
            raise InvalidRecursiveUpdate(_('invalid count for update'))

    if action in ['scaleUp', 'scaleDn']:
        try:
            factor = value.strip()
            factor = float(factor)
            if factor < 0.0:
                raise InvalidRecursiveUpdate(_('scaling factor must be a non-negative number'))
        except:
            raise InvalidRecursiveUpdate(_('scaling factor must be a non-negative number'))

    if action in ['set', 'add', 'repl', 'scaleUp', 'scaleDn']:
        try:
            invName = secondary
            if iType == 'demand':
                invType = store.net.people[invName]
            else:
                invType = store.net.types[invName]
        except:
            raise InvalidRecursiveUpdate(_('invalid type name for update'))

    if action in ['repl']:
        try:
            replName = tertiary
            if iType == 'demand':
                replType = store.net.people[invName]
            else:
                replType = store.net.types[invName]
        except:
            raise InvalidRecursiveUpdate(_('invalid type name for update'))


    clients = store.recursiveClients()
    for client, cRoute in clients:
        if client.CATEGORY != category:
            continue
        
    belowZeroMsg = False
    clients = store.recursiveClients()
    for client, cRoute in clients:
        if client.CATEGORY != category:
            continue

        # make sure that any case where the client is updated that we reach
        # the end of this loop clause so that the updates can be sent to the
        # interface

        # handle 'clear'
        if action == 'clear':
            if iType == 'demand':
                invList = client.demand[:]
            else:
                invList = client.inventory[:]
            for i in invList:
                if iType == 'demand':
                    client.updateDemand(0)
                else:
                    name = i.invName
                    if name in getattr(store.net, iType):
                        client.updateInventory(name, 0)

        # handle 'scaleUp', 'scaleDn', 'repl'
        elif action in ['scaleUp', 'scaleDn', 'repl']:
            if iType == 'demand':
                count = client.countDemand(invName)
            else:
                count = client.countInventory(invName)

            if count == 0:
                continue

            if action == 'scaleUp':
                count = int(math.ceil(float(count) * factor))
            elif action == 'scaleDn':
                count = int(float(count) * factor)

            if action in ['scaleUp', 'scaleDn']:
                if iType == 'demand':
                    client.updateDemand(invName, count)
                else:
                    client.updateInventory(invName, count)
            else:
                if iType == 'demand':
                    client.updateDemand(invName, 0)
                    client.updateDemand(replName, count)
                else:
                    client.updateInventory(invName, 0)
                    client.updateInventory(replName, count)


        # handle 'set', 'add'
        elif action in ['set', 'add']:
            if action == 'set':
                if iType == 'demand':
                    client.updateDemand(invName, count)
                else:
                    client.updateInventory(invName, count)
            elif action == 'add':
                if iType == 'demand':
                    client.addDemand(invName, count)
                else:
                    client.addInventory(invName, count)
            
            if iType == 'demand':
                if client.countDemand(invName) < 0:
                    client.updateDemand(invName, 0)
                    if not belowZeroMsg:
                        ULCM.addUpdate('X', _('This update caused one or more populations to be set negative.  Those have been reset to 0'), 'alert')
                        belowZeroMsg = True
            else:
                if client.countInventory(invName) < 0:
                    client.updateInventory(invName, 0)
                    if not belowZeroMsg:
                        ULCM.addUpdate('X', _('This update caused one or more inventory items to be set negative.  Those have been reset to 0'), 'alert')
                        belowZeroMsg = True

        # now perform the updates for the changed inventory
        if iType == 'demand':
            opts = storeDemandOpts(client)
            etl = storeDemandEtl(client)
            efi = EditableFieldInfo('storeDemand',
                                    _('population'),
                                    etl,
                                    fieldType='tuplelist',
                                    pullDownOpts=opts)
            updateBasicTupleList(client, 'storeDemand', efi, updateFocus=False)
        else:
            opts = storeInvOpts(client, iType)
            etl = storeInvEtl(client, iType)
            efi = EditableFieldInfo('store'+iType,
                                    _(_storeInvTitles[iType]),
                                    etl,
                                    fieldType='tuplelist',
                                    pullDownOpts=opts)
            updateBasicTupleList(client, 'store'+iType, efi, updateFocus=False)
                                


    

rseFields = {
    'None' : ['choose a field', rseDispNone, rseUpdateNone, 0],
    'utilizationRate' : ['utilizationRate', rseDispUtilization, rseUpdateUtilization, 1],
    'storage' : ['storage', rseDispStorage, rseUpdateStorage, 2],
    'transport' : ['transport', rseDispTransport, rseUpdateTransport, 3],
    'population' : ['population', rseDispDemand, rseUpdateDemand, 4],
    'staff' : ['staff', rseDispStaff, rseUpdateStaff, 5],
    'costs' : ['costs', rseDispCosts, rseUpdateCosts, 6],
    'perdiems' : ['route perdiems', rseDispPerDiem, rseUpdatePerDiem, 7]
    }
    
def rseRenderAvailableFields(unique, store):
    ret = []
    global currentTree
    ret.append('<select class="rse_field_select" id="rse_field_%d" onchange="updateRSEDialog(%d,%d,\'%s\');">'%\
                   (unique, unique, store.idcode, currentTree))
    sortMe = []
    for field, fDef in rseFields.items():
        sortMe.append((fDef[-1], field, fDef))
    sortMe.sort()
    for field, fDef in [(b,c) for a,b,c in sortMe]:
        ret.append('<option value="%s">%s</option>'%(field, fDef[0]))
    ret.append('</select>')
                   
    return ret

def jsonRecursiveStoreEditCreate(db, uiSession):
    try:
        modelId = getParm('modelId')
        uiSession.getPrivs().mayReadModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)
        idcode = getParm('idcode')
        store = model.getStore(long(idcode))
        tree = getParm('tree')
        
        if 'storeEditorUniqueId' not in uiSession:
            uiSession['storeEditorUniqueId'] = 1
        unique = uiSession['storeEditorUniqueId']
        uiSession['storeEditorUniqueId'] += 1

        clients = store.recursiveClients()
        
        with selectTree(tree):

            ret = []

            ret.append('<div id="store_edit_wgt_%s">')
            ret.append('<p>%s</p>'%_('Modify Stores Supplied by {0}').format(store.NAME))
            ret.extend(rseRenderAffectedCategories(unique, store, clients))
            ret.extend(rseRenderAvailableFields(unique, store))
            ret.append('<div id="rse_content_%d"></div>'%unique)
            ret.append('</div>')

            return { 'success' : True,
                     'htmlstring' : string.join(ret, '\n')}

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()
        return { 'success' : False,
                 'msg' : 'screwed up somewhere' }

@bottle.route('/json/meUpdateRSEDialog')
def jsonUpdateRSEDialog(db, uiSession):
    try:
        modelId = getParm('modelId')
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)
    
        idcode = getParm('idcode')
        store = model.getStore(long(idcode))

        tree = getParm('tree')

        category = getParm('category')
        field = getParm('field')
        unique = getParm('unique')
        


        title, dispFn, updateFn, order = rseFields[field]
        with selectTree(tree):
            with ULCM():
                dispFn(store, field, category, unique)

                return { 'success' : True,
                         'updateList' : ULCM.updateList() }

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()
        
        return { 'success' : False, 'errorString' : _('unknown error') }


@bottle.route('/json/meUpdateRSEValue')
def jsonUpdateRSEValue(db, uiSession):
    try:
        modelId = getParm('modelId')
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)
    
        idcode = getParm('idcode')
        store = model.getStore(long(idcode))

        tree = getParm('tree')

        category = getParm('category')
        field = getParm('field')
        unique = getParm('unique')
        action = getParm('action')
        value = getParm('value')
        value = value.strip()
        secondary = getParm('secondary')
        tertiary = getParm('tertiary')

        title, dispFn, updateFn, order = rseFields[field]
        with ULCM():
            with selectTree(tree):
                success = True
                errorString = None
                try:
                    updateFn(store, field, category, unique, action, value, secondary, tertiary)

                except InvalidRecursiveUpdate as e:
                    success = False
                    errorString = e.string
                except Exception as e:
                    print 'Exception: %s'%e
                    traceback.print_exc()
                    success = False
                    errorString = _('unknown error updating records')

                # as long as we're mostly ok, we still want to print this
                dispFn(store, field, category, unique)

                ret = { 'success' : success,
                        'updateList' : ULCM.updateList() }
                if errorString is not None:
                    ret['errorString'] = errorString

                return ret

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()
        
        return { 'success' : False, 'errorString' : _('unknown error') }




@bottle.route('/json/meValidateModel')
def jsonValidateModel(db, uiSession):
    """
    Validate a model
    """
    try:
        modelId = getParm('modelId')
        uiSession.getPrivs().mayReadModelId(db, modelId)
        model = shadow_network_db_api.ShdNetworkDB(db, modelId)

        stores = model.stores
        routes = model.routes
        vmc = validate_model.VMC

        v = validate_model.Validator(model)
        v.registerTest("all")
        v.runAvailableTests()
        
        # tree selection needs to be fixed
        with selectTree(TREE.MAIN):
            with ULCM():
                for (nType, nId, nText, test, msg) in v.warnings + v.fatals:
                    if nType == vmc.STORE:
                        addStoreMessage(stores[nId], msg)
                    if nType == vmc.ROUTE:
                        addRouteMessage(routes[nId], msg)

                if len(v.warnings + v.fatals) == 0:
                    # need to do something here
                    pass
                return { 'success' : True, 'updateList' : ULCM.updateList() }

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()

        return { 'success' : False, 'errorString' : _('unknown error') }

