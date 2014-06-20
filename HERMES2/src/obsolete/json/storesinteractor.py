##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

from somethinginteractor import SomethingInteractor

class StoresInteractor(SomethingInteractor):
    def __init__(self, owner, name="storesInteractor"):
        SomethingInteractor.__init__(self,owner,thingName="Stores", name=name)
