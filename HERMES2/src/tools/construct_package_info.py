#! /usr/bin/env python


import sys
import csv_tools

with open('UnifiedVaccineTypeInfo.csv','rU') as f:
    inKeys, inRecs = csv_tools.parseCSV(f)

#print inKeys

if len(sys.argv) == 2:
    if  sys.argv[1] == '--splitdiluents':
        dilKey = 'Packed vol/dose(cc) of diluent'
        outKeys = inKeys[:]
        outKeys.remove(dilKey)
        outKeys = outKeys[:8]+['Requires']+outKeys[8:]
        print outKeys
        
        outRecs = []
        for rec in inRecs:
            vacRec = {}
            dilRec = {}
            for k,v in rec.items():
                if k in outKeys:
                    vacRec[k] = v
                    dilRec[k] = v
            dilRec['Name'] = vacRec['Name'] + '_Diluent'
            if 'DisplayName' in vacRec:
                dilRec['DisplayName'] = vacRec['DisplayName'] + '_D'
            dilRec['Abbreviation'] = vacRec['Abbreviation'] + '_D'
            dilRec['Packed vol/dose(cc) of vaccine'] = rec['Packed vol/dose(cc) of diluent']
            dilRec['Requires'] = ''
            dilRec['Vaccine price/vial'] = dilRec['Vaccine price/dose'] = 0.0
            dilRec['LifetimeFreezerDays'] = 0.1
            dilRec['LifetimeCoolerDays'] = 0.2
            dilRec['LifetimeRoomTempDays'] = 1000.0
            if rec['Packed vol/dose(cc) of diluent'] == '':
                rec['Packed vol/dose(cc) of diluent'] = 0.0
            if rec['Packed vol/dose(cc) of diluent'] > 0.0:
                vacRec['Requires'] = dilRec['Name']
                outRecs.append(vacRec)
                outRecs.append(dilRec)
                print '********'
                print vacRec
                print dilRec
            else:
                vacRec['Requires'] = ''
                outRecs.append(vacRec)
                print '********'
                print vacRec
                
        with open('NewUnifiedVaccineTypeInfo.csv','w') as f:
            csv_tools.writeCSV(f,outKeys,outRecs)
    else:
        sys.exit('Nonsense parameter '+sys.argv[1])
else:
    outKeys = inKeys
    outRecs = inRecs

pkgKeys = ['Name', 'Contains', 'Count', 'Category', 'Volume(CC)', 'SortOrder', 'Notes']
pkgRecs = []
for n,rec in enumerate(outRecs):
    print rec['Name']
    print rec['Packed vol/dose(cc) of vaccine']
    print rec['Doses per vial']
    sngRec = { 'Name':rec['Name']+'_Single', 'Contains':rec['Name'], 'Count':1,
               'Category':'single',
               'Volume(CC)':1.0*rec['Packed vol/dose(cc) of vaccine']*rec['Doses per vial'],
               'SortOrder':100*n+0, 'Notes':'' }
    boxRec = { 'Name':rec['Name']+'_Box', 'Contains':rec['Name'],
               'Count':25*sngRec['Count'],
               'Category':'box',
               'Volume(CC)':1.1*25*sngRec['Volume(CC)'],
               'SortOrder':100*n+1, 'Notes':'' }
    cartonRec = { 'Name':rec['Name']+'_Carton', 'Contains':rec['Name'],
                  'Category':'carton',
                  'Count':40*boxRec['Count'],
                  'Volume(CC)':1.1*40*boxRec['Volume(CC)'],
                  'SortOrder':100*n+2, 'Notes':'' }
    print 'done with '+rec['Name']
    pkgRecs.append(sngRec)
    pkgRecs.append(boxRec)
    pkgRecs.append(cartonRec)
with open('UnifiedPackageTypeInfo.csv','w') as f:
    csv_tools.writeCSV(f,pkgKeys,pkgRecs)



           
        
