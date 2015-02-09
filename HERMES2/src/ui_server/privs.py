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

import sys, os.path, time, types

from HermesServiceException import HermesServiceException

from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import ipath
from ui_utils import _logMessage
from shadow_network import ShdNetwork
from shadow_network_db_api import ShdNetworkDB
import db_routines
from dbinterface import getDBSession

from i18n import i18n

_ = i18n('locale').translateString

userGroupTable = Table('prvusergroupassociation', db_routines.Base.metadata,
                       Column('user_id', Integer, ForeignKey('prvusers.userId')),
                       Column('group_id', Integer, ForeignKey('prvgroups.groupId')))

class PrvUser(db_routines.Base):
    __tablename__ = 'prvusers'
    userId = Column(Integer, primary_key=True)
    userName = Column(String(32))
    
    def __init__(self, userId, userName):
        self.userId = userId
        self.userName = userName

class PrvGroup(db_routines.Base):
    __tablename__ = 'prvgroups'
    groupId = Column(Integer, primary_key=True)
    groupName = Column(String(32))
    users = relationship("PrvUser", secondary=userGroupTable, 
                         backref='groups')
    def __init__(self, groupId, groupName):
        self.groupId = groupId
        self.groupName = groupName
    
class PrvModelAccessRights(db_routines.Base):
    __tablename__ = 'prvmodelaccessrights'
    primKey = Column(Integer, primary_key=True)
    modelId = Column(Integer, ForeignKey('models.modelId'))
    ownerId = Column(Integer, ForeignKey('prvusers.userId'))
    readGroupId = Column(Integer, ForeignKey('prvgroups.groupId'))
    writeGroupId = Column(Integer, ForeignKey('prvgroups.groupId'))
    model = relationship("ShdNetwork",backref=backref('prvmodelaccessrights', uselist=False,
                                                      cascade='all, delete-orphan'))
    
    def __init__(self, modelId, ownerId, readGroupId, writeGroupId):
        self.modelId = modelId
        self.ownerId = ownerId
        self.readGroupId = readGroupId
        self.writeGroupId = writeGroupId

class PrivilegeException(Exception):
    pass

class MayModifyPrivilegeException(PrivilegeException):
    pass

class Privileges:
    """
    A simple privilege framework, to restrict access to the model and results database
    """
    def __init__(self,uid):
        self.uid = uid
    
    def mayReadModelId(self, sn, modelId, msg=_("The current user does not have permission to read this model")):
        """
        This should raise a PrivilegeException (with the given message) if permission is not available.
        Simply returning implies that the privilege is granted.
        """
        try:
            try:
                mAR = sn.query(PrvModelAccessRights).filter(PrvModelAccessRights.modelId==modelId).one()
            except NoResultFound:
                raise PrivilegeException(msg+': No such modelId %s'%modelId)
            except MultipleResultsFound:
                raise PrivilegeException(msg+': modelId %d is not unique'%modelId)
            if mAR.ownerId==self.uid: return
            try:
                group = sn.query(PrvGroup).filter(PrvGroup.groupId==mAR.readGroupId).one()
            except NoResultFound:
                raise PrivilegeException(msg+': not owner and read group is invalid')
            if not self.uid in [u.userId for u in group.users]:
                raise PrivilegeException(msg+': not owner and not in read group')
        except PrivilegeException,e:
            _logMessage('Privilege violation uid=%d'%self.uid + str(e))
            raise e

    def mayWriteModelId(self, sn, modelId, msg=_("The current user does not have permission to write this model")):
        """
        This should raise a PrivilegeException (with the given message) if permission is not available.
        Simply returning implies that the privilege is granted.
        """
        try:
            try:
                mAR = sn.query(PrvModelAccessRights).filter(PrvModelAccessRights.modelId==modelId).one()
            except NoResultFound:
                raise PrivilegeException(msg+': No privileges set for modelId %d'%modelId)
            except MultipleResultsFound:
                raise PrivilegeException(msg+': modelId %d is not unique'%modelId)
            if mAR.ownerId==self.uid: return
            try:
                group = sn.query(PrvGroup).filter(PrvGroup.groupId==mAR.writeGroupId).one()
            except NoResultFound:
                raise PrivilegeException(msg+': not owner and write group is invalid')
            if not self.uid in [u.userId for u in group.users]:
                raise PrivilegeException(msg+': not owner and not in write group')
        except PrivilegeException,e:
            _logMessage('Privilege violation uid=%d'%self.uid + str(e))
            raise e
        
    def mayModifyModelId(self, sn, modelId, msg=_("This model has results which will become invalid if the model is changed.  Either delete the results or work on a new copy of the model.")):
        self.mayWriteModelId(sn, modelId) # Check write permissions first
        m = ShdNetworkDB(sn, modelId)
        if len(m.resultsGroups)>0: raise MayModifyPrivilegeException(msg)
            
    def registerModelId(self, sn, modelId, readGroupId, writeGroupId):
        """
        When a new model is created, this call should be used to associate read and write privileges 
        with the modelId.
        """
        try:
#            # Is the model ID valid?
#            try:
#                sn.query(ShdNetwork).filter(ShdNetwork.modelId==modelId).one()
#            except NoResultFound:
#                raise PrivilegeException('No such modelId %d'%modelId)
#            except MultipleResultsFound:
#                raise PrivilegeException('modelId %d is not unique'%modelId)
            # Does it already exist?  If so we return silently.
            n = sn.query(PrvModelAccessRights).filter(PrvModelAccessRights.modelId==modelId).count()
            if n==0:
                sn.add(PrvModelAccessRights(modelId, self.uid, readGroupId, writeGroupId))
                sn.commit()
            elif n==1: 
                pass # it's already registered
            else:
                raise PrivilegeException("The modelId %d appears multiple times in the privilege table"%modelId)
        except PrivilegeException,e:
            _logMessage('Privilege violation uid=%d'%self.uid + str(e))
            raise e
    
def main():
    uidList = [1,2]
    privsList = [Privileges(u) for u in uidList]
    for model in getDBSession().query(ShdNetwork):
        modelId = model.modelId
        for (uid,privs) in zip(uidList,privsList):
            try:
                privs.mayReadModelId(getDBSession(), modelId)
                print 'privs for uid %d can read %d'%(uid,modelId)
            except Exception,e:
                print 'Exception on read: %s'%e
            try:
                privs.mayModifyModelId(getDBSession(), modelId)
                print 'privs for uid %d can write %d'%(uid,modelId)
            except Exception,e:
                print 'Exception on write: %s'%e

############
# Main hook
############

if __name__=="__main__":
    main()
