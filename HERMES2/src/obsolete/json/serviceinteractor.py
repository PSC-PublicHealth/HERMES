
_hermes_svn_id_="$Id$"

import pyjd # dummy in pyjs

from pyjamas import Window
from pyjamas.JSONService import JSONProxy
from pyjamas.ui.SimplePanel import SimplePanel

class ServiceInteractor(SimplePanel):
    def __init__(self, owner, name="ServiceInteractor", jSONRPCService= None):
        SimplePanel.__init__(self)
        self.owner= owner
        self.name= name
        self.remoteService = jSONRPCService
        self.inFlight= {}
        self.state= {}
        
    def lateBuild(self):
        pass

    def debugMsg(self,txt):
        self.owner.debugMsg(txt)
        
    def applyState(self,state):
        self.state= state.copy()
        
    def saveState(self):
        self.owner.setChildState(self,self.state)

    def doActionCall(self, sender):
        return None,None

    def onClick(self, sender):
        try:
            self.owner.setStatus("%s: Waiting for response..."%self.name)
            id,info= self.doActionCall(sender)
            if id is None: 
                # The derived class's call didn't know what to do
                self.owner.setStatus("Internal error; %s can't tell what clicked"%self.name)
            else:
                if info is None:
                    # Derived class sent no JSONRPC message, so nothing to track
                    self.owner.setStatus("%s: done"%self.name)
                else:
                    self.inFlight[id]= info
            self.saveState()

        except Exception,e:
            self.owner.debugMsg("%s: Problem invoking the service: %s"%(self.name,str(e)))
            self.owner.setStatus('%s: Problem invoking the service'%self.name)
            self.saveState()
            
    def noteRemoteCall(self,idInfoTuple):
        id,info= idInfoTuple
        if id is None: 
            # The derived class's call didn't know what to do
            self.owner.setStatus("Internal error; %s claims to have made a request but got no ID"%self.name)
        else:
            if info is None:
                # Derived class sent no JSONRPC message, so nothing to track
                pass
            else:
                self.inFlight[id]= info
        self.saveState()
        

    def doActionResponse(self, callInfo, response, request_info):
        return True

    def onRemoteResponse(self, response, request_info):
#        try:
#            #Window.alert('Got something; id is '+request_info.id)
#            #Window.alert('ServiceInteractor point 1: %s'%str(self.inFlight))
#            if self.inFlight.has_key(request_info.id):
#                info= self.inFlight[request_info.id]
#                if self.doActionResponse(info, response, request_info):
#                    self.owner.setStatus("%s: responded"%self.name)
#                else:
#                    self.owner.debugMsg("Error: %s got unknown response for %s"%(self.name,str(info)))
#                    self.owner.setStatus("Fumbled a <%s> message"%str(info))
#                del self.inFight[request_info.id]
#            else:
#                self.owner.debugMsg("Error: %s missing inFlight info for json message %s"%(self.name,request_info.id))
#                self.owner.setStatus('Fumbled a message')
#            self.saveState()
#        except Exception,e:
#            self.owner.debugMsg("%s: No request info: %s"%(self.name,str(e)))
#            self.owner.setStatus('%s: No request info'%self.name)
#            self.saveState()
#        Window.alert('Got something; id is '+request_info.id)
#        Window.alert('ServiceInteractor point 1 for %s: %s'%(self.name,str(self.inFlight)))
        if self.inFlight.has_key(request_info.id):
            info= self.inFlight[request_info.id]
            if self.doActionResponse(info, response, request_info):
                self.owner.setStatus("%s: responded"%self.name)
            else:
                self.owner.debugMsg("Error: %s got unknown response for %s"%(self.name,str(info)))
                self.owner.setStatus("Fumbled a <%s> message"%str(info))
#            del self.inFight[request_info.id]
        else:
            self.owner.debugMsg("Error: %s missing inFlight info for json message %s"%(self.name,request_info.id))
            self.owner.setStatus('Fumbled a message')
        self.saveState()

    def onRemoteError(self, code, errobj, request_info):
        # onRemoteError gets the HTTP error code or 0 and
        # errobj is an jsonrpc 2.0 error dict:
        #     {
        #       'code': jsonrpc-error-code (integer) ,
        #       'message': jsonrpc-error-message (string) ,
        #       'data' : extra-error-data
        #     }
        Window.alert('Got an error!')
        message = errobj['message']
        if code != 0:
            self.owner.setStatus("%s: HTTP error %d: %s" % 
                                 (self.name,code, message))
        else:
            code = errobj['code']
            self.owner.setStatus("%s: JSONRPC Error %s: %s" %
                                 (self.name, code, message))
        del self.inFlight[request_info.id]
        self.saveState()

