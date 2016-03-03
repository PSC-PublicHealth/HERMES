# -*- coding: utf-8 -*-
import requests,cgi,sysconfig,sys
from datetime import date
import pprint

pp = pprint.PrettyPrinter(indent=1, width=40)
def main():
    
    ### URL API information
    beginUrl = "http://www.openexchangerates.org/api"
    app_id = "928f1e29f43f42bdacb1e5dcfaf14d18"
    
    ### Get List of currencies
    r = requests.get('{0}/currencies.json'.format(beginUrl))
    if r.status_code != requests.codes.ok:
        raise RuntimeError("There was a problem accessing the currency json")
    
    currencies = r.json()
    print currencies
    conversionDict = {x:{} for x in currencies}
    print conversionDict
    for year in range(2008,date.today().year):
        print year
        url = "{0}/historical/{1}-06-01.json?app_id={2}".format(beginUrl,year,app_id)
        try:
            r = requests.get(url) 
        except requests.exceptions.RequestException as e:    
            print "Problem: {0}".format(e)
            #sys.exit(1) 
#         if r.status_code != requests.codes.ok:
#             raise RuntimeError("There was a problem getting the currencies")
          
        jsonDict = r.json() 
        
        baseCurrency = jsonDict['base']
        for code1 in conversionDict.keys():
            if jsonDict['rates'].has_key(code1):
                for code2 in currencies.keys():
                    if not conversionDict[code1].has_key(code2):
                        conversionDict[code1][code2]={}
                    if jsonDict['rates'].has_key(code2):
                        rate1 = jsonDict['rates'][code1]
                        rate2 = jsonDict['rates'][code2]
                        rate = rate2/rate1
                        conversionDict[code1][code2][year] = rate
                    else:
                        conversionDict[code1][code2][year] = -1.0
                
    #pp.pprint(conversionDict)
    
    for currency,converts in conversionDict.items():
        curInfo = currencies[currency]
        print curInfo   
        

if __name__ == '__main__':
    main()      