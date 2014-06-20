#! /usr/bin/env python

_hermes_svn_id_="$Id$"

import sys,os,os.path,types
from cStringIO import StringIO
import ipath
import serverconfig
import session_support_wrapper as session_support
from HermesServiceException import HermesServiceException

class CrumbTrail(object):
    
    def __init__(self, rootPath, changeListener=None):
        self.rootPath = rootPath[:]
        self.trail = []
        self.owner = None
        if changeListener is not None: self.changeListener = changeListener
        else: self.changeListener = lambda : None

    def change(self):
        if self.owner is not None: self.owner.change()
        else: self.changeListener()

    def setChangeListener(self, changeListener):
        if self.owner: 
            raise HermesServiceException("It is almost certainly an error to set the changeListener of a child crumbTrail")
        self.changeListener = changeListener

    def _innerRender(self, sio, crumbTrail, folded):
        raise HermesServiceException("Base class CrumbTrail._innerRender was called.")
    
    def clear(self):
        raise HermesServiceException("Base class CrumbTrail.clear was called.")

    def _dump(self, indent=0):
        print "%sDUMP %s %s"%(indent*" ",type(self).__name__,self.rootPath)
        for ind,thing in enumerate(self.trail):
            if isinstance(thing,CrumbTrail) or isinstance(thing[0],CrumbTrail):
                if isinstance(thing,CrumbTrail): kid = thing
                else: kid=thing[0]
                print "%s  CHILD %s"%(indent*" ",str(kid))
                kid._dump(indent+2)
            else:
                if len(thing) == 2:
                    a,b = thing
                    thing = a,b
                elif len(thing) == 3:
                    a,b,c = thing
                    thing = a,b,c
                print "%s  %s"%(indent*" ",str(thing))
        
    def render(self):
        #self._dump()
        sio = StringIO()
        sio.write('<ul>\n<li>')
        self._innerRender(sio, folded=False)
        sio.write('</li></ul>\n')
        return sio.getvalue()
    
    def _buildPath(self, tailPath):
        if tailPath[0] == '/': basePath = tailPath
        else: basePath = "%s/%s"%(self.rootPath, tailPath)
        if self.owner is None:
            return serverconfig.rootPath+basePath.strip('/')
        else: 
            return self.owner._buildPath(basePath)
    
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
        d = self.__dict__.copy()
        d['changeListener'] = None        
        del d['owner']
        newTrail = []
        for thing in d['trail']:
            if isinstance(thing, CrumbTrail): 
                newTrail.append(thing._toJSON())
            elif isinstance(thing, types.TupleType):
                if isinstance(thing[0], CrumbTrail):
                    l = list(thing)
                    l[0] = l[0]._toJSON()
                    newTrail.append(tuple(l))
                else:
                    newTrail.append(thing)
        d['trail'] = newTrail
        return d
    
    def jump(self, goal):
        raise HermesServiceException("Base class CrumbTrail.jump was called.")
        
    def next(self):
        raise HermesServiceException("Base class CrumbTrail.next was called.")
        
    def back(self):
        raise HermesServiceException("Base class CrumbTrail.back was called.")
        
    def current(self):
        raise HermesServiceException("Base class CrumbTrail.current was called.")

    def currentPath(self):
        raise HermesServiceException("Base class CrumbTrail.currentPath was called.")
        
class StackCrumbTrail(CrumbTrail):
    def __init__(self, rootPath, changeListener=None):
        CrumbTrail.__init__(self, rootPath, changeListener)

    def push(self, thing):
        assert isinstance(thing, CrumbTrail) or (isinstance(thing, types.TupleType) and len(thing)==2), \
            "Tried to push a %s onto the CrumbTrail"%(type(thing).__name__)
        if len(self.trail)==0 or not self.jump(thing):
            self.trail.append(thing)
        if isinstance(thing, CrumbTrail): thing.owner = self
        self.change()
        return self # for chaining

    def pop(self):
        self.trail.pop()
        self.change()
        return self # for chaining

    def clear(self):
        if len(self.trail) >1:
            self.trail = self.trail[:1]
            self.change()
        return self # for chaining
    
    def _innerRender(self, sio, folded=False):
        if not self.trail: return
        for thing in self.trail[:-1]:
            if isinstance(thing,types.TupleType):
                sio.write('<a href="%s">%s</a><span class="divider"></span>></li>\n<li>'%(self._buildPath(thing[0]),thing[1]))
            else:
                thing._innerRender(sio, folded=True)
        thing =self.trail[-1]
        if isinstance(thing,types.TupleType):
            sio.write('<a href="%s">%s</a>\n'%(self._buildPath(thing[0]),thing[1]))
        else:
            thing._innerRender(sio, folded=False)

    def jump(self, goal):
        """
        StackCrumbTrail does a jump just by scanning through its stack, finding the first track that 
        contains the target.  If not found, return False.
        """
        nPop = None
        for ind,thing in enumerate(self.trail):
            if isinstance(thing, TrackCrumbTrail):
                if thing.jump(goal): return True
            elif thing == goal:
                nPop = len(self.trail) - (ind + 1)
                break
        if nPop is not None: 
            for _ in xrange(nPop): self.pop()
            return True
        return False

    def _buildPath(self, tailPath):
        if len(self.trail) == 0 or tailPath[0] == '/':
            pass
        else:
            subT = self.trail[:]
            subT.reverse()
            for thing in subT:
                if isinstance(thing, CrumbTrail): 
                    tailPath = thing.current()
                    if tailPath[0] != '/': tailPath = "%s/%s"%(thing.rootPath,tailPath)
                else: tailPath = "%s/%s"%(thing[0],tailPath)
                if tailPath[0] == '/': break
        if tailPath[0] == '/': basePath = tailPath
        else: basePath = "%s/%s"%(self.rootPath, tailPath)
        if self.owner is None:
            return serverconfig.rootPath+basePath.strip('/')
        else: 
            return self.owner._buildPath(basePath)

    def current(self):
        """
        Return the current tag or CrumbTrail, or None if the is no such element
        """
        if self.trail == []: return None
        else: 
            thing = self.trail[-1]
            if isinstance(thing, CrumbTrail): return thing.current()
            else: return thing[0]

    def currentPath(self):
        #self._dump()
        return self._buildPath(self.current())
                
class TrackCrumbTrail(CrumbTrail):
    
    def __init__(self, basePath, foldedName, changeListener=None):
        CrumbTrail.__init__(self, basePath, changeListener)
        self.foldedName = foldedName
        self.currentOffset = 0

    def append(self, thing):
        assert isinstance(thing, CrumbTrail) or (isinstance(thing, types.TupleType) and len(thing)==2), \
            "Tried to append a %s to the TrackCrumbTrail"%(type(thing).__name__)
        if isinstance(thing,CrumbTrail):
            thing.owner = self
            if len(self.trail) == 0: self.trail.append((thing,True))
            else: self.trail.append((thing,False))
        else:
            if len(self.trail) == 0: self.trail.append((thing[0],thing[1],True))
            else: self.trail.append((thing[0],thing[1],False))
        self.change()
        return self # for chaining

    def _innerRender(self, sio, folded):
        if not self.trail: return
        if folded:
            tag = self.trail[self.currentOffset][0]
            sio.write('<a href="%s">%s</a><span class="divider"></span>></li>\n<li>'%(self._buildPath(tag),self.foldedName))
        else:                    
            for ind,thing in enumerate(self.trail[:-1]):
                if isinstance(thing[0], CrumbTrail):
                    thing[0]._innerRender(sio, folded=True)
                else:
                    tag,name,flag = thing
                    if flag:
                        if ind==self.currentOffset:
                            sio.write('<a href="%s"><b>%s</b></a><span class="divider"></span></li>\n<li>'%(self._buildPath(tag),name))
                        else:
                            sio.write('<a href="%s" style="font-size:smaller;">%s</a><span class="divider"></span></li>\n<li>'%(self._buildPath(tag),name))
                    else:
                        if ind==self.currentOffset:
                            sio.write('<a class="noclick"><b>%s</b></a><span class="divider"></span></li>\n<li>'%name)
                        else:
                            sio.write('<a class="noclick" style="font-size:smaller;">%s</a><span class="divider"></span></li>\n<li>'%name)
            thing =self.trail[-1]
            ind = len(self.trail) - 1
            if isinstance(thing[0],CrumbTrail):
                cT, flag = thing
                cT._innerRender(sio, folded=False)
            else:
                tag,name,flag = thing
                if ind==self.currentOffset:
                    if flag:
                        sio.write('<a href="%s"><b>%s</b></a>\n'%(self._buildPath(tag),name))
                    else:
                        sio.write('<a class="noclick"><b>%s</b></a>\n'%name)
                else:
                    if flag:
                        sio.write('<a href="%s" style="font-size:smaller;">%s</a>\n'%(self._buildPath(tag),name))
                    else:
                        sio.write('<a class="noclick" style="font-size:smaller;">%s</a>\n'%name)

    def clear(self):
        self.trail = []
        self.change()
        return self # for chaining

    def jump(self, goal):
        """
        TrackCrumbTrail does a jump by resetting itself to make the entry containing the goal be the 
        current entry, if present.  If found, return True.  If not found, return False.
        """
        for ind,thing in enumerate(self.trail):
            if isinstance(thing[0], CrumbTrail):
                if thing.jump(goal): return True
            else:
                tag, name, flag = thing
                if tag == goal and flag:
                    self.currentOffset = ind
                    self.change()
                    return True
        return False
    
    def next(self):
        """
        Go to the next element of the trail, making it clickable.  If there is a next element that tag or
        CrumbTrail is returned; otherwise return None
        """
        if self.currentOffset >= len(self.trail) - 1: 
            return None
        else:
            self.currentOffset += 1
            thing = self.trail[self.currentOffset]
            if isinstance(thing[0],CrumbTrail):
                cT,flag = thing
                self.trail[self.currentOffset] = (cT, True)
                return cT
            else:
                tag,name,flag = thing
                self.trail[self.currentOffset] = (tag, name, True)
                return tag
                
        
    def back(self):
        """
        Go to the previous element of the trail.  If there is a previous element, return that tag or CrumbTrail.
        Otherwise, return None.
        """
        if self.currentOffset <= 0 or len(self.trail) == 0: 
            return None
        else:
            self.currentOffset -= 1
            thing = self.trail[self.currentOffset]
            if isinstance(thing[0],CrumbTrail):
                cT,flag = thing
                return cT
            else:
                tag,name,flag = thing
                return tag
                
    def current(self):
        """
        Return the current tag or CrumbTrail, or None if the is no such element
        """
        if self.currentOffset < 0 or self.currentOffset > len(self.trail) - 1:
            return None
        else:
            return self.trail[self.currentOffset][0]

    def currentPath(self):
        #self._dump()
        return self._buildPath(self.current())

    def _dump(self, indent=0):
        print "%sDUMP %s %s"%(indent*" ",type(self).__name__,self.rootPath)
        for ind,thing in enumerate(self.trail):
            if ind==self.currentOffset:
                if isinstance(thing,CrumbTrail) or isinstance(thing[0],CrumbTrail):
                    if isinstance(thing,CrumbTrail): kid = thing
                    else: kid=thing[0]
                    print "%s**CHILD %s"%(indent*" ",str(kid))
                    kid._dump(indent+2)
                else:
                    if len(thing) == 2:
                        a,b = thing
                        #a = a.strip('/')
                        thing = a,b
                        #self.trail[ind] = thing
                    elif len(thing) == 3:
                        a,b,c = thing
                        #a = a.strip('/')
                        thing = a,b,c
                        #self.trail[ind] = thing
                    print "%s**%s"%(indent*" ",str(thing))
            else:
                if isinstance(thing,CrumbTrail) or isinstance(thing[0],CrumbTrail):
                    if isinstance(thing,CrumbTrail): kid = thing
                    else: kid=thing[0]
                    print "%s  CHILD %s"%(indent*" ",str(kid))
                    kid._dump(indent+2)
                else:
                    if len(thing) == 2:
                        a,b = thing
                        #a = a.strip('/')
                        thing = a,b
                        #self.trail[ind] = thing
                    elif len(thing) == 3:
                        a,b,c = thing
                        #a = a.strip('/')
                        thing = a,b,c
                        #self.trail[ind] = thing
                    print "%s  %s"%(indent*" ",str(thing))
        
def main(myargv = None):
    "Provides a few test routines"
    
    if myargv is None: 
        myargv = sys.argv

    t = TrackCrumbTrail('/model-create','Create Model')
    tPairs = [('nlevels',_('Levels')),
              ('levelnames',_('Level Names')),
              ('countsbylevel',_('How Many')),
              ('interlevel',_('Shipment Types')),
              ('interleveltimes',_('Shipment Times')),
              ('done',_('Adjustments')),
              ('people',_('Population Types')),
              ('vaccines',_('Vaccine Types')),
              ('fridges',_('Storage Types')),
              ('trucks',_('Transport Types')),
              ('setdemand',_('Demand')),
              ('provision',_('Provision Locations')),
              ('provisionroutes',_('Provision Routes'))
               ]
    for p in tPairs: t.append(p)
    t2 = StackCrumbTrail("whatever")
    t2.push(('welcome',_('Welcome')))
    t2.push(('models-top',_('Models')))
    
    print t.render()
    print "\n\n\n"
    
    print t2.render()
    print "\n\n\n"
    
    t2.push(t)
    print t2.render()
    
    print "\n\n\n"
    
    t2.push(('finish',_('Finish')))
    print t2.render()
    
    print "\n\n\n"
    t2._dump()
    print "\n\n\n"    
    
    t2.pop()
    print t2.render()
    print "\n\n\n"
    
    t2.push(('models-top',_('Models')))
    print t2.render()
    print "\n\n\n"
    
    t2.clear()
    print t2.render()
    print "\n\n\n"

############
# Main hook
############

if __name__=="__main__":
    main()

