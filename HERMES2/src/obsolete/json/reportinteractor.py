##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

from somethinginteractor import SomethingInteractor

class ReportInteractor(SomethingInteractor):
    def __init__(self, owner, name="reportInteractor"):
        SomethingInteractor.__init__(self,owner,thingName="Reports", name=name)
