#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id$"

import sys,os,os.path,time,json,math,types
import bottle
import ipath

def orderPage(pList, fieldMap, bottleRequest, defaultSortIndex=None):
    sortIndex = bottleRequest.params['sidx']
    sortOrder = bottleRequest.params['sord']
    if len(pList)==0:
        return (0,pList) # no need to sort
    else:
        if sortIndex is None or sortIndex=='':
            sortIndex = defaultSortIndex
        sortFieldList = []
        #print sortIndex
        for field in sortIndex.split(','):
            #print 'field: '+str(field)
            subFields = field.split()
            #print 'subFields: '+str(subFields)
            if len(subFields)>0:
                realField = subFields[0].strip()
                sortFieldList.append(realField)
        #print 'sortFieldList: '+str(sortFieldList)
        #print 'fieldmap: '+str(fieldMap)
        if all([f in fieldMap for f in sortFieldList]):
            sortList = []
            for p in pList:
                if isinstance(p, types.DictType):
                    l = [p[fieldMap[f]] for f in sortFieldList]
                else:
                    l = [getattr(p,fieldMap[f]) for f in sortFieldList]
                l.append(p)
                sortList.append(tuple(l))
            if sortOrder == 'asc':
                sortList.sort()
            else:
                sortList.sort(reverse=True)
            pList = [t[-1] for t in sortList]
            totRecs = len(pList)
            return (totRecs,pList) # no need to sort
        else:
            raise bottle.BottleException("Sort index %s not in field map"%sortIndex)

def orderAndChopPage(pList,fieldMap,bottleRequest,defaultSortIndex=None):
    thisPageNum = int(bottleRequest.params['page'])
    rowsPerPage = int(bottleRequest.params['rows'])
    totRecs,pList = orderPage(pList, fieldMap, bottleRequest, defaultSortIndex)
    nPages = int(math.ceil(float(len(pList))/(rowsPerPage-1)))
    if thisPageNum == nPages:
        eR = totRecs
        sR = max(eR - rowsPerPage, 0)
    else:
        sR = (thisPageNum-1)*(rowsPerPage-1)
        eR = sR + rowsPerPage
    pList = pList[sR:eR]
    return (nPages,thisPageNum,totRecs,pList) # no need to sort
