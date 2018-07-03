!/usr/bin/env python


####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id: routehooks.py 2262 2015-02-09 14:38:25Z stbrown $"

fieldMap = [
    {'label':_('Data Base ID'),'key':'RouteName','id':'name','info':False,'edit':False,'type':'dbKey','req':True,'default':None},
    {'label':_('Route Type'),'key':'Type','id':'routetype','info':True,'edit':True,'type':'select',
        'options':[('varpush','desc of varpush'), ('pull':_('desc of pull'))],'default':'varpush'},
    {'label':_('Frequency of Shipment','key':'ShipFrequency','id':'shipfreq','info':True,'edit':True.'type':'time','req':True,
               'recMap':['shipfreq'.'shipfreqUnits'],'default':'1:M'}
            ]
