_hermes_svn_id_="$Id$"

from pyjamas.JSONService import JSONProxy

class TopLevelService(JSONProxy):
    def __init__(self):
        JSONProxy.__init__(self,"/bottle_hermes/TopLevel",
                           ["test","getSessionKey","getServerState",
                            "getUploadHandle","getClientStateUpdate",
                            "getFilesOfType","copyServerSideFile","getFileInfo",
                            "renameServerSideFile","getDownloadHandle","buildSharedState",
                            "getNetworkGraph","getNetworkDotGraph"])

