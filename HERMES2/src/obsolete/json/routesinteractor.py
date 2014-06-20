##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

from somethinginteractor import SomethingInteractor

class RoutesInteractor(SomethingInteractor):
    def __init__(self, owner, name="routesInteractor"):
        SomethingInteractor.__init__(self,owner,thingName="Routes", name=name)
