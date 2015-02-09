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


__doc__=""" db_routines.py
abstract some of the low level database routines.
"""
_hermes_svn_id_="$Id$"

import site_info

try:
    # anything gotten from sqlalchemy should have an equivalent noop below
    # ie someone without sqlalchemy should be able to include this so long
    # as nothing is called.

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy.sql import text

    # 'Base' is the superclass from which our db schema is derived.
    # Any classes  that will be a part of the db schema needs to inherit Base
    # All classes that inherit base should be loaded before making or dropping tables
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()
except:
    class EmptyClass():
        def __init__(self, *args, **kwargs):
            pass

    Base = EmptyClass

    def EmptyFunc(*args, **kwargs):
        pass
    text = EmptyFunc

class DbInterface:
    def __init__(self, 
                 dbType = None, 
                 name = 'hermes', 
                 user = 'hermes', 
                 password = 'hermes_pass', 
                 host = '127.0.0.1',
                 echo = False,
                 dbLoc = None):
        sI = site_info.SiteInfo()
        if dbType is None: 
            dbType = sI.dbType()
        if dbLoc is None: 
            dbLoc = sI.dbLoc()

        self.dbType = dbType

        if dbType == 'mysql':
            uri = 'mysql+mysqldb://'
            uri += user
            if password is not None:
                uri += ':' + password
            uri += '@'
            uri += host
            uri += '/'
            uri += name
            uri += '?charset=utf8&use_unicode=1'
            
            engine = create_engine(uri, echo = echo, pool_recycle=3600)
        elif dbType == 'sqlite':
            uri = 'sqlite:///%s'%(dbLoc)
            engine = create_engine(uri, echo = echo, encoding = 'utf-8')
            engine.raw_connection().connection.text_factory=str
        else:
            raise RuntimeError("invalid dbType")
        self.uri = uri
        self.Base = Base
        self.engine = engine
        self.SessionMaker = scoped_session(sessionmaker(bind=engine))

    def getURI(self):
        return self.uri
    
    def Session(self):
        "This creates sessions and hides a link to this interface within"
        s = self.SessionMaker()
        s._hermes_iface = self
        return s
    
    def createTables(self):
        """create the db tables.  

        This should only be called once the definitions for every table have been included.
        """
        #session = self.Session()
        self.Base.metadata.create_all(self.engine)

    def dropTables(self, **kwargs):
        """
        drop all the db tables.

        This should only be called once the definitions for every table has been included.

        Note that you're forced to specify that you really want to do this in the parameters.
        """
        if kwargs['IReallyWantToDoThis'] is True:
            #session = self.Session()
            self.Base.metadata.drop_all(self.engine)

    def advisoryLock(self, key, expiration=30):
        "set an advisory lock.  A dictionary 'handle' is returned.  pass this to unlock."
        ret = {'key':key}
        if self.dbType == 'mysql':
            conn = self.engine.connect()
            g = text("select get_lock(:key,:exp);")
            val = conn.execute(g, key=key, exp=expiration).fetchall()
            #print val
            if not val[0][0] == 1:
                raise RuntimeError("Attempt to get advisory lock %s failed"%key)
            ret['conn'] = conn
        elif self.dbType == 'sqlite':
            # we've agreed that this can be a noop for our use case
            pass
        else:
            raise RuntimeError("DB not supported for advisory locks!")

        return ret

    def advisoryUnlock(self, handle):
        if self.dbType == 'mysql':
            conn = handle['conn']
            key = handle['key']
            r = text("select release_lock(:key);")
            val = conn.execute(r, key=key).fetchall()
            #print val
            conn.close()
        elif self.dbType == 'sqlite':
            # we've agreed that this can be a noop for our use case
            pass
        else:
            raise RuntimeError("DB not supported for advisory locks!")


    
