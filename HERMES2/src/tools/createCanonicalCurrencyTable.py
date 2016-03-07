# -*- coding: utf-8 -*-
import requests,cgi,sysconfig,sys
from datetime import date
import pprint
import codecs

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
    sortedKeys = sorted(currencies.keys())
    
    conversionDict = {x:{} for x in currencies}
    
    for year in range(2000,date.today().year):
        url = "{0}/historical/{1}-06-01.json?app_id={2}".format(beginUrl,year,app_id)
        try:
            r = requests.get(url) 
        except requests.exceptions.RequestException as e:    
            print "Problem: {0}".format(e)
          
        jsonDict = r.json() 
        
        baseCurrency = jsonDict['base']
        for code1 in conversionDict.keys():
            if jsonDict['rates'].has_key(code1):
                conversionDict[code1][year] = jsonDict['rates'][code1]
            else:
                conversionDict[code1][year] = -1.0
                
    #pp.pprint(conversionDict)
    with codecs.open("../../master_data/unified/CurrencyConversionTable.csv",'wb',encoding='utf8') as f:
        f.write(u"Country Name, Currency Name, Currency Code")
        for year in range(2000,date.today().year):
            f.write(u",{0}".format(year))
        f.write(u"\n")
        #for currency,converts in conversionDict.items():
        for code in sortedKeys:
            curInfo = currencies[code]
            f.write(u",{0},{1}".format(curInfo,code))
            for year in range(2000,date.today().year):
                f.write(u",{0}".format(conversionDict[code][year]))
            f.write(u"\n")

if __name__ == '__main__':
    main()      