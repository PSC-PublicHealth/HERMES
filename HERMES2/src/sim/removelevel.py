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


__doc__="""
Code that will remove a 'level' from the simple hermes network representation
"""


import network
import copy


class RemoveLevel:
    """
    Remove a level (based on CATEGORY) from a network and patch the routes tables with
    routes based on routeTemplate (effectively a route record line as a dict)

    if any entry in the routeTemplate is a function, that function will be called as needed
    with the following arguments:
        supplier:   NetStore instance for the supplier
        client:     NetStore instance for the client
        order:      Which stop is currently being worked on or -1 if for the route as a whole
        template:   A link back to your route template.
    

    issues: 
       do we remove trucks from stores involved in old routes
       do we add trucks to stores involved in new routes
       fetch "loops" (ie with multiple clients) likely won't be processed correctly.
       if only some stops are removed from a route, the TransitHours should be updated
           but this code doesn't provide a means to do this.
       if only some stops from a route are removed then the timings for the rest of the 
           route would likely not be valid but these are not updated.

    """
    def __init__(self, net, category, routeTemplate):
        self.net = net
        self.category = category
        self.rt = routeTemplate

        for code,s in net.stores.items():
            if s.CATEGORY == category:
                self.removeStore(code)
        
        

    def removeStore(self, code):
        """ 
        unlink a store and connect all of this store's suppliers to all of his clients
        """
        st = self.net.stores[code]
        for supplier in st.suppliers:
            for client in st.clients:
                self.link(supplier[0], client[0])

        # remove all routes for which this is the supplier
        while(len(st.clients)):
            client = st.clients[0]
            (clStore,clRoute) = client
            self.net.removeRoute(clRoute)

        # remove all stops for which this is a client
        # if this makes the route have only one stop then remove the full route as well

        # BUG: This code is not guaranteed to work with fetch routes with multiple clients
        while(len(st.suppliers)):
            supplier = st.suppliers[0]
            (suStore, suRoute) = supplier
            suRoute.unlinkRoute()
            suRoute.removeStop(st)
            if len(suRoute.stops) < 2:
                self.net.removeRoute(suRoute, unlinked=True)
            else:
                suRoute.linkRoute()

        # remove the store itself
        self.net.removeStore(st)


    def link(self, supplier, client):
        template = copy.copy(self.rt)
        for attr in network.NetRoute.routeAttrs:
            a = network._parseAttr(attr)
            n = a['name']
            if n in template:
                if callable(template[n]):
                    template[n] = template[n](supplier, client, -1, self.rt)
            
        r = self.net.addRoute(template, True)
        
        for i in (0,1):
            templateCopy = copy.copy(template)
            for n in templateCopy.keys():
                if callable(templateCopy[n]):
                    templateCopy[n] = templateCopy[n](supplier, client, i, self.rt)
            r.addStop(templateCopy, self.net.stores)

def _genRouteName(supplier, client, order, template):
    return "r%d_%d"%(supplier.idcode, client.idcode)

def _genLocName(supplier, client, order, template):
    if network.NetRoute.routeTypes[template['Type']] == order:
        return supplier.NAME
    else:
        return client.NAME

def _genidcode(supplier, client, order, template):
    if network.NetRoute.routeTypes[template['Type']] == order:
        return supplier.idcode
    else:
        return client.idcode

def _genRouteOrder(supplier, client, order, template):
    return order
    


def removeLevelWithDefaults(net, category, routeTemplate):
    """
    this removes a level but handles RouteName, LocName, idcode, and RouteOrder in the 
    routeTemplate for you.  This depends on a valid route Type being used.
    """
    rt = routeTemplate
    rt['RouteName'] = _genRouteName
    rt['LocName'] = _genLocName
    rt['idcode'] = _genidcode
    rt['RouteOrder'] = _genRouteOrder

    RemoveLevel(net, category, routeTemplate)
