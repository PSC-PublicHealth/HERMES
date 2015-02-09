#! /usr/bin/env python

###################################################################################
# Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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

_hermes_svn_id_ = "$Id$"

import sys
import types
from StringIO import StringIO
import ipath
import serverconfig
from HermesServiceException import HermesServiceException
from ui_utils import _logStacktrace, _logMessage


class CrumbTrail(object):

    def __init__(self, rootPath, changeListener=None):
        self.rootPath = rootPath[:]
        self.trail = []
        self.owner = None
        if changeListener is not None:
            self.changeListener = changeListener
        else:
            self.changeListener = lambda: None  # @IgnorePep8

    def change(self):
        if self.owner is not None:
            self.owner.change()
        else:
            self.changeListener()

    def setChangeListener(self, changeListener):
        if self.owner:
            raise HermesServiceException("It is almost certainly an error to set the"
                                         " changeListener of a child crumbTrail")
        self.changeListener = changeListener

    def _innerRender(self, sio, crumbTrail, folded):
        raise HermesServiceException("Base class CrumbTrail._innerRender was called.")

    def clear(self):
        raise HermesServiceException("Base class CrumbTrail.clear was called.")

    def _dump(self, indent=0):
        print "%sDUMP %s %s" % (indent*" ", type(self).__name__, self.rootPath)
        for thing, argDict in self.trail:
            if isinstance(thing, CrumbTrail):
                kid = thing
                print "%s  CHILD ( %s %s )" % (indent*" ", str(kid), argDict)
                kid._dump(indent+2)
            else:
                assert len(thing) == 2, "internal error: tuple %s should have 2 components" % thing
                print "%s  %s %s" % (indent*" ", str(thing), argDict)

    def render(self):
        sio = StringIO()
        sio.write('<ul>\n<li>')
        self._innerRender(sio, folded=False)
        sio.write('</li></ul>\n')
        return sio.getvalue()

    def _buildPath(self, tailPath, offset=0, argDict=None):
        if tailPath and tailPath[0] == '/':
            basePath = tailPath
        else:
            basePath = "%s/%s" % (self.rootPath, tailPath)
        if self.owner is None:
            result = self._addArgs(serverconfig.rootPath + basePath.strip('/'),
                                   argDict)
        else:
            result = self.owner._buildPath(basePath, argDict=argDict)
        return result

    def _addArgs(self, thePath, argDict):
        if not argDict:
            return thePath
        else:
            return "%s?%s" % (thePath,
                              '&'.join([("%s=%s" % (k, v)) for k, v in argDict.items()]))

    def _removeArgs(self, rawPath):
        """
        Given a raw path of the form foo/baz?blrfl=znorg&other=7 ,
        returns ('foo/baz', {'blrfl':'znorg','other':'7'}
        """
        off1 = rawPath.find('?')
        if off1 >= 0:
            prefix = rawPath[:off1]
            rest = rawPath[off1+1:]
            while rest and rest[0] == '?':
                rest = rest[1:]  # fix a common problem
            argDict = {}
            if len(rest) > 0:
                pairs = rest.split('&')
                for p in pairs:
                    if len(p) == 0:
                        continue
                    words = p.split('=')
                    if len(words) == 1 and len(words[0]) > 0:
                        argDict[words[0]] = True
                    else:
                        argDict[words[0]] = words[1]
            return (prefix, argDict)
        else:
            return rawPath, {}

    def __getstate__(self):
        """
        The changeListener callback cannot be pickled, so we use this hook to eliminate it.
        It will get put back by the session manager during session_support.getCrumbs()
        """
        d = self.__dict__.copy()
        d['changeListener'] = None
        return d

    def _toJSON(self):
        """
        Make a JSON-safe representation. The 'owner' field points to our parent, creating a loop,
        so elide it.
        """
        try:
            d = self.__dict__.copy()
            d['changeListener'] = None
            del d['owner']
            newTrail = []
            for thing, argDict in d['trail']:
                if isinstance(thing, CrumbTrail):
                    newTrail.append((thing._toJSON(), argDict))
                elif isinstance(thing, types.TupleType):
                    assert len(thing) == 2, \
                        "internal error: tuple %s should have 2 components" % thing
                    newTrail.append(thing)
            d['trail'] = newTrail
            return d
        except Exception, e:
            _logMessage('Exception in CrumbTrail._toJSON: %s' % str(e))
            _logStacktrace()
            raise

    def jump(self, goal, goalArgs=None):
        raise HermesServiceException("Base class CrumbTrail.jump was called.")

    def next(self):
        raise HermesServiceException("Base class CrumbTrail.next was called.")

    def back(self):
        raise HermesServiceException("Base class CrumbTrail.back was called.")

    def current(self):
        raise HermesServiceException("Base class CrumbTrail.current was called.")

    def currentPath(self):
        raise HermesServiceException("Base class CrumbTrail.currentPath was called.")

    def showBackNext(self):
        if self.trail and isinstance(self.trail[-1][0], CrumbTrail):
            return self.trail[-1][0].showBackNext()
        else:
            return False

    def showDone(self):
        if self.trail and isinstance(self.trail[-1][0], CrumbTrail):
            return self.trail[-1][0].showDone()
        else:
            return False

    def getDoneURL(self):
        raise HermesServiceException("Base class CrumbTrail.getDoneURL was called.")

    def getNextURL(self):
        raise HermesServiceException("Base class CrumbTrail.getNextURL was called.")

    def getBackURL(self):
        raise HermesServiceException("Base class CrumbTrail.getBackURL was called.")

#     def genericDoneJS(self):
#         result = """
# $(function(){{
#     $(document).hrmWidget({{widget:'stdDoneButton', doneURL:'{0}' }});
# }});""".format(self.getDoneURL())
#         return result

#     def genericVerifySaveJS(self):
#         result = ("""
#             (function(argDict) { $('#done_button').button({ label:{0} }).click(
#                 function() {
#                 }
#             )})
#         """
#         )
#         return result


class StackCrumbTrail(CrumbTrail):
    def __init__(self, rootPath, changeListener=None):
        CrumbTrail.__init__(self, rootPath, changeListener)

    def push(self, thing, argDict=None):
        assert (isinstance(thing, CrumbTrail) or (isinstance(thing, types.TupleType)
                                                  and len(thing) == 2)), \
            "Tried to push a %s onto the CrumbTrail" % (type(thing).__name__)
        if isinstance(thing, CrumbTrail):
            if len(self.trail) == 0 or not self.jump(thing, argDict):
                self.trail.append((thing, argDict))
                thing.owner = self
        else:
            path, newArgs = self._removeArgs(thing[0])
            if argDict is not None:
                newArgs.update(argDict)
            if len(self.trail) == 0 or not self.jump((path, thing[1]), newArgs):
                self.trail.append(((path, thing[1]), newArgs))
        self.change()
        return self  # for chaining

    def pop(self):
        self.trail.pop()
        self.change()
        return self  # for chaining

    def clear(self):
        if len(self.trail) > 1:
            self.trail = self.trail[:1]
            self.change()
        return self  # for chaining

    def _innerRender(self, sio, folded=False):
        if not self.trail:
            return
        for idx, tpl in enumerate(self.trail[:-1]):
            thing, argDict = tpl
            if isinstance(thing, types.TupleType):
                urlTail, label = thing
                if idx == 0 and self.owner is None and urlTail != '/':
                    urlTail = '/'+urlTail
                lclPath = self._buildPath(urlTail, offset=idx, argDict=argDict)
                sio.write('<a href="%s">%s</a><span class="divider"></span>></li>\n<li>'
                          % (lclPath, label))
            else:
                thing._innerRender(sio, folded=True)
        thing, argDict = self.trail[-1]
        idx = len(self.trail)-1
        if isinstance(thing, types.TupleType):
            urlTail, label = thing
            if idx == 0 and self.owner is None and urlTail != '/':
                urlTail = '/'+urlTail
            lclPath = self._buildPath(urlTail, offset=idx, argDict=argDict)
            sio.write('<a href="%s">%s</a>\n' % (lclPath, label))
        else:
            thing._innerRender(sio, folded=False)

    def jump(self, goal, goalArgs=None):
        """
        StackCrumbTrail does a jump just by scanning through its stack, finding the first track
        that contains the target.  If not found, return False.
        """
        nPop = None
        for ind, tpl in enumerate(self.trail):
            thing, argDict = tpl
            if isinstance(thing, TrackCrumbTrail):
                if thing.jump(goal, goalArgs):
                    nPop = len(self.trail) - (ind + 1)
                    break
            elif (isinstance(goal, types.TupleType)  # we already know thing is a tuple
                  and thing[0] == goal[0]
                  and (goalArgs is None or argDict == goalArgs)):
                nPop = len(self.trail) - (ind + 1)
                break
        if nPop is not None:
            for a in xrange(nPop):  # @UnusedVariable
                self.pop()
            return True
        return False

    def _buildPath(self, tailPath, offset=0, argDict=None):
        if len(self.trail) == 0 or tailPath[0] == '/':
            pass
        else:
            subT = self.trail[:offset-1]
            subT.reverse()
            for thing, thingArgs in subT:  # @UnusedVariable
                if isinstance(thing, CrumbTrail):
                    tailPath = thing.current()
                    if tailPath and tailPath[0] != '/':
                        tailPath = "%s/%s" % (thing.rootPath, tailPath)
                else:
                    tailPath = "%s/%s" % (thing[0], tailPath)
                if tailPath[0] == '/':
                    break
        if tailPath and tailPath[0] == '/':
            basePath = tailPath
        else:
            basePath = "%s/%s" % (self.rootPath, tailPath)
        if self.owner is None:
            result = self._addArgs(serverconfig.rootPath+basePath.strip('/'), argDict)
        else:
            result = self.owner._buildPath(basePath, argDict=argDict)
        return result

    def current(self):
        """
        Return the current tag or CrumbTrail, or None if the is no such element
        """
        if self.trail == []:
            return None
        else:
            thing = self.trail[-1][0]
            if isinstance(thing, CrumbTrail):
                return thing.current()
            else:
                return thing[0]

    def currentLabel(self):
        """
        Return the current label, or None if the is no such element
        """
        if self.trail == []:
            return None
        else:
            thing = self.trail[-1][0]
            if isinstance(thing, CrumbTrail):
                return thing.currentLabel()
            else:
                return thing[1]

    def currentArgs(self):
        """
        Return the current URL options, or None if there is no such element,
        or {} if there is a current URL but it has no options.
        """
        if self.trail == []:
            return None
        else:
            thing = self.trail[-1][0]
            if isinstance(thing, CrumbTrail):
                return thing.currentArgs()
            else:
                return self.trail[-1][1]

    def currentPath(self):
        # self._dump()
        return self._buildPath(self.current(), argDict=self.currentArgs())

    def showBackNext(self):
        if self.trail and isinstance(self.trail[-1][0], CrumbTrail):
            return self.trail[-1][0].showBackNext()
        else:
            return False

    def showDone(self):
        if self.trail and isinstance(self.trail[-1][0], CrumbTrail):
            return self.trail[-1][0].showDone()
        else:
            return True

    def getDoneURL(self):
        if len(self.trail) < 2:
            result = self.currentPath()  # already at the top
        else:
            thing, thingArgs = self.trail[-2]
            if isinstance(thing, CrumbTrail):
                rawPath, rawArgs = self._removeArgs(thing.currentPath())
                if thingArgs is not None:
                    rawArgs.update(thingArgs)
                result = self._addArgs(rawPath, rawArgs)
            else:
                result = self._buildPath(thing[0], argDict=thingArgs)
        return result

    def getBackURL(self):
        if self.trail and isinstance(self.trail[-1][0], CrumbTrail):
            return self.trail[-1][0].getBackURL()
        else:
            raise HermesServiceException("StackCrumbTrail.getBackURL should not have been"
                                         " called for last element.")

    def getNextURL(self):
        if self.trail and isinstance(self.trail[-1][0], CrumbTrail):
            return self.trail[-1][0].getNextURL()
        else:
            raise HermesServiceException("StackCrumbTrail.getNextURL should not have been"
                                         " called for last element.")


class TrackCrumbTrail(CrumbTrail):

    def __init__(self, basePath, foldedName, changeListener=None):
        CrumbTrail.__init__(self, basePath, changeListener)
        self.foldedName = foldedName
        self.currentOffset = 0
        self.available = {}

    def append(self, thing, argDict=None):
        assert (isinstance(thing, CrumbTrail) or (isinstance(thing, types.TupleType)
                                                  and len(thing) == 2)), \
            "Tried to append a %s to the TrackCrumbTrail" % (type(thing).__name__)
        if isinstance(thing, CrumbTrail):
            thing.owner = self
            self.trail.append((thing, argDict))
        else:
            self.available[thing[0]] = (len(self.trail) == 0)  # first element starts out available
            path, newArgs = self._removeArgs(thing[0])
            if argDict is not None:
                newArgs.update(argDict)
            self.trail.append(((path, thing[1]), newArgs))
        self.change()
        return self  # for chaining

    def _innerRender(self, sio, folded):
        if not self.trail:
            return
        if folded:
            thing, thingArgs = self.trail[self.currentOffset]
            if isinstance(thing, CrumbTrail):
                lclPath = thing.currentPath()
                sio.write('<a href="%s">%s</a><span class="divider"></span>></li>\n<li>'
                          % (lclPath, self.foldedName))
            else:
                lclPath = self._buildPath(thing[0], argDict=thingArgs)
                sio.write('<a href="%s">%s</a><span class="divider"></span>></li>\n<li>'
                          % (lclPath, self.foldedName))
        else:
            for ind, tpl in enumerate(self.trail[:-1]):
                thing, thingArgs = tpl
                if isinstance(thing, CrumbTrail):
                    thing._innerRender(sio, folded=True)
                else:
                    tag, name = thing
                    if self.available[tag]:
                        if ind == self.currentOffset:
                            lclPath = self._buildPath(tag, argDict=thingArgs)
                            sio.write(('<a href="%s"><b>%s</b></a><span class="divider">'
                                      % (lclPath, name))
                                      + '</span></li>\n<li>')
                        else:
                            lclPath = self._buildPath(tag, argDict=thingArgs)
                            sio.write(('<a href="%s" style="font-size:smaller;">'
                                       % lclPath)
                                      + '%s</a><span class="divider"></span></li>\n<li>' % name)
                    else:
                        if ind == self.currentOffset:
                            sio.write('<a class="noclick"><b>'
                                      '%s</b></a><span class="divider"></span></li>\n<li>' % name)
                        else:
                            sio.write('<a class="noclick" style="font-size:smaller;">'
                                      '%s</a><span class="divider"></span></li>\n<li>' % name)
            thing, thingArgs = self.trail[-1]
            ind = len(self.trail) - 1
            if isinstance(thing, CrumbTrail):
                thing._innerRender(sio, folded=False)
            else:
                tag, name = thing
                if ind == self.currentOffset:
                    if self.available[tag]:
                        lclPath = self._buildPath(tag, argDict=thingArgs)
                        sio.write('<a href="%s"><b>%s</b></a>\n' %
                                  (lclPath, name))
                    else:
                        sio.write('<a class="noclick"><b>%s</b></a>\n' % name)
                else:
                    if self.available[tag]:
                        lclPath = self._buildPath(tag)
                        sio.write('<a href="%s" style="font-size:smaller;">%s</a>\n'
                                  % (lclPath, name))
                    else:
                        sio.write('<a class="noclick" style="font-size:smaller;">%s</a>\n' % name)

    def clear(self):
        self.trail = []
        self.change()
        return self  # for chaining

    def jump(self, goal, goalArgs=None):
        """
        TrackCrumbTrail does a jump by resetting itself to make the entry containing the goal be
        the current entry, if present.  If found, return True.  If not found, return False.
        """
        if goal == self:
            return True
        else:
            for ind, tpl in enumerate(self.trail):
                thing, thingArgs = tpl
                if isinstance(thing, CrumbTrail):
                    if thing.jump(goal):
                        return True
                else:
                    tag, name = thing  # @UnusedVariable
                    if (tag == goal and self.available[tag]
                            and (goalArgs is None or thingArgs == goalArgs)):
                        self.currentOffset = ind
                        self.change()
                        return True
        return False

    def next(self):
        """
        Go to the next element of the trail, making it clickable.  If there is a next element that
        tag or CrumbTrail is returned; otherwise return None
        """
        if self.currentOffset >= len(self.trail) - 1:
            return None
        else:
            self.currentOffset += 1
            thing, thingArgs = self.trail[self.currentOffset]  # @UnusedVariable
            if isinstance(thing, CrumbTrail):
                return thing
            else:
                tag, name = thing  # @UnusedVariable
                self.available[tag] = True
                return tag

    def back(self):
        """
        Go to the previous element of the trail.  If there is a previous element, return that tag
        or CrumbTrail. Otherwise, return None.
        """
        if self.currentOffset <= 0 or len(self.trail) == 0:
            return None
        else:
            self.currentOffset -= 1
            thing, thingArgs = self.trail[self.currentOffset]  # @UnusedVariable
            if isinstance(thing, CrumbTrail):
                return thing
            else:
                tag, name = thing  # @UnusedVariable
                return tag

    def current(self):
        """
        Return the current tag or CrumbTrail, or None if the is no such element
        """
        if self.currentOffset < 0 or self.currentOffset > len(self.trail) - 1:
            return None
        else:
            thing = self.trail[self.currentOffset][0]
            if isinstance(thing, CrumbTrail):
                return thing
            else:
                tag, name = thing  # @UnusedVariable
                return tag

    def currentLabel(self):
        """
        Return the current label, or None if the is no such element
        """
        if self.currentOffset < 0 or self.currentOffset > len(self.trail) - 1:
            return None
        else:
            thing = self.trail[self.currentOffset][0]
            if isinstance(thing, CrumbTrail):
                return thing
            else:
                tag, name = thing  # @UnusedVariable
                return name

    def currentArgs(self):
        """
        Return the current URL options, or None if there is no such element,
        or {} if there is a current URL but it has no options.
        """
        if self.currentOffset < 0 or self.currentOffset > len(self.trail) - 1:
            return None
        else:
            thing, thingArgs = self.trail[self.currentOffset]
            if isinstance(thing, CrumbTrail):
                return thing.currentArgs()
            else:
                return thingArgs

    def currentPath(self):
        lclPath = self._buildPath(self.rootPath + '/' + self.current(), argDict=self.currentArgs())
        return lclPath

    def _dump(self, indent=0):
        print "%sDUMP %s %s" % (indent*" ", type(self).__name__, self.rootPath)
        for ind, tpl in enumerate(self.trail):
            thing, thingArgs = tpl
            if ind == self.currentOffset:
                if isinstance(thing, CrumbTrail):
                    kid = thing
                    print "%s**CHILD ( %s %s )" % (indent*" ", str(kid), thingArgs)
                    kid._dump(indent+2)
                else:
                    print "%s**%s" % (indent*" ", str(thing))
            else:
                if isinstance(thing, CrumbTrail):
                    kid = thing
                    print "%s  CHILD ( %s %s )" % (indent*" ", str(kid), thingArgs)
                    kid._dump(indent+2)
                else:
                    print "%s  %s" % (indent*" ", str(thing))

    def showBackNext(self):
        if self.trail and isinstance(self.trail[-1], CrumbTrail):
            return self.trail[-1].showBackNext()
        else:
            return True

    def showDone(self):
        if self.trail and isinstance(self.trail[-1], CrumbTrail):
            return self.trail[-1].showDone()
        else:
            return False

    def getNextURL(self):
        if self.currentOffset < 0 or self.currentOffset > len(self.trail) - 1:
            raise HermesServiceException('TrackCrumbTrail offset is out of range')
        else:
            result = self._buildPath('next', self.currentArgs())
        return result

    def getBackURL(self):
        if self.currentOffset < 0 or self.currentOffset > len(self.trail) - 1:
            raise HermesServiceException('TrackCrumbTrail offset is out of range')
        else:
            result = self._buildPath('back', self.currentArgs())
        return result


def main(myargv=None):
    "Provides a few test routines"

    if myargv is None:
        myargv = sys.argv

    def _(s):
        """In liu of translateString"""
        return s

    t = TrackCrumbTrail('/model-create', 'Create Model')
    tPairs = [('nlevels', _('Levels')),
              ('levelnames', _('Level Names')),
              ('countsbylevel', _('How Many')),
              ('interlevel', _('Shipment Types')),
              ('interleveltimes', _('Shipment Times')),
              ('done', _('Adjustments')),
              ('people', _('Population Types')),
              ('vaccines', _('Vaccine Types')),
              ('fridges', _('Storage Types')),
              ('trucks', _('Transport Types')),
              ('setdemand', _('Demand')),
              ('provision', _('Provision Locations')),
              ('provisionroutes', _('Provision Routes'))
              ]
    for p in tPairs:
        t.append(p)
    t2 = StackCrumbTrail("whatever")
    t2.push(('welcome', _('Welcome')))
    t2.push(('models-top', _('Models')), {'modelId': 7, 'expert': 'false'})

    print t.render()
    print "\n\n\n"

    print t2.render()
    print "\n\n\n"

    t2.push(t)
    print t2.render()

    print "\n\n\n"

    t2.push(('finish', _('Finish')))
    print t2.render()

    print "\n\n\n"
    t2._dump()
    print "\n\n\n"

    t2.pop()
    print t2.render()
    print "\n\n\n"

    t2.push(('models-top', _('Models')))
    print t2.render()
    print "\n\n\n"

    t2.clear()
    print t2.render()
    print "\n\n\n"

############
# Main hook
############

if __name__ == "__main__":
    main()
