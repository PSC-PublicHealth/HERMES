import ipath
import csv_tools
import argparse
from xlwt.Workbook import *
from xlwt.Style import *
import xlwt
ezxf = xlwt.easyxf

LevelOrder = ["Central","Division","District","PHC","OutreachClinic"]
costPerOutreach = 82.0

vaccineList = ['I_DTP','I_HepB','I_HepB_birth','I_JE','I_Measles',
               'I_Oral_Polio','I_Tetanus_Toxoid','I_Tuberculosis','I_DTP_HepB_Hib',
               'I_Rotavac','X_IPV10','X_IPV25','X_IPV5','X_IPV55','X_PCV']
vaccineMonDict = {'I_DTP':'DTP','I_HepB':'HepB','I_HepB_birth':'HepB Birth Dose','I_JE':'JE','I_Measles':'Measles',
               'I_Oral_Polio':'OPV','I_Tetanus_Toxoid':'TT','I_Tuberculosis':'BCG','I_DTP_HepB_Hib':'Penta',
               'I_Rotavac':'Rotavac','X_IPV10':'IPV10','X_IPV25':'IPV10(50)','X_IPV5':'IPV5','X_IPV55':'IVP5(25)',
               'X_PCV':'PCV'}
vaccineDoseDict = {'I_DTP':5,'I_HepB':3,'I_HepB_birth':1,'I_Measles':2,
               'I_Oral_Polio':5,'I_Tetanus_Toxoid':4,'I_Tuberculosis':1,'I_DTP_HepB_Hib':3,
               'I_Rotavac':3,'X_IPV10':1,'X_IPV25':2,'X_IPV5':1,'X_IPV55':2,'X_PCV':3}

baseDir = 'C:\Users\stbrown\Box Sync\Shared HERMES\Project\IPV Partial Doses'
directories = [
               {'Title':'UIP','dir':baseDir+"\Kerala",'outPre':'output'},
               {'Title':'IPV 10 Dose','dir':baseDir+"\Kerala-10Dose",'outPre':'output'},
               {'Title':'IPV 10 Dose (50 Partial Doses)','dir':baseDir+"\Kerala-25Dose",'outPre':'output'},
               {'Title':'IPV 5 Dose','dir':baseDir+"\Kerala-5Dose",'outPre':'output'},
               {'Title':'IPV 5 Dose (25 Partial Doses)','dir':baseDir+"\Kerala-55Dose",'outPre':'output'},
               {'Title':'IPV 10 Dose NoMDVP','dir':baseDir+"\NoMDVP\Kerala-10Dose",'outPre':'output'},
               {'Title':'IPV 10 Dose (50 Partial Doses) NoMDVP','dir':baseDir+"\NoMDVP\Kerala-25Dose",'outPre':'output'},
               {'Title':'IPV 5 Dose NoMDVP','dir':baseDir+"\NoMDVP\Kerala-5Dose",'outPre':'output'},
               {'Title':'IPV 5 Dose (25 Partial Doses) NoMDVP','dir':baseDir+"\NoMDVP\Kerala-55Dose",'outPre':'output'},
#               {'Title':'Penta Introduction','dir':baseDir + "Penta", 'outPre':'output'},
#	       {'Title':'Rotavac Introduction','dir':baseDir+"Rotavac",'outPre':'output'},
#	       {'Title':'IPV Introduction','dir':baseDir+"IPV-Birth",'outPre':'output'},
#	       {'Title':'PCV Introduction','dir':baseDir+"PCV",'outPre':'output'},
	       #{'Title':'Per Policy','dir':baseDir+'Bihar Policy','outPre':'output'},
#	       {'Title':'Penta + Rotavac Introduction','dir':baseDir+'Penta-Rotavac','outPre':'output'},
#	       {'Title':'Penta + Rotavac + IPV Introduction','dir':baseDir+'Penta-Rotavac-IPV1','outPre':'output'},
#	       {'Title':'Penta + Rotavac + IPV + PCV Introduction','dir':baseDir+'Penta-Rotavac-IPV1-PCV','outPre':'output'}
	       ]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--debug",action="store_true",default=False,help="Turn on Debugging Output")
    #parser.add_argument("costfile",default="output.ave.costs.csv",help="The Costs Output")
    #parser.add_argument("rawfile",default="output.ave.csv",help="raw HERMES output file")
    #parser.add_argument("summaryfile",default="output.ave_summary.csv")
              
    #parser.add_argument("outfile",default=None,help="output file")
    
    args = parser.parse_args()

    results = []

    for expt in directories:
        
        with open(expt['dir']+"/"+expt['outPre']+".ave_cost.csv","rb") as f:
            costKeys,costRecs = csv_tools.parseCSV(f)

        with open(expt['dir']+"/"+expt['outPre']+".ave.csv","rb") as f:
            resultKeys, resultRecs = csv_tools.parseCSV(f)

        with open(expt['dir']+"/"+expt['outPre']+".ave_summary.csv","rb") as f:
            summaryKeys,summaryRecs = csv_tools.parseCSV(f)
    
        dosesPerVial = {}
        for rec in summaryRecs:
            if rec["DosesPerVial"] > 0:
                dosesPerVial[rec["Name"]] = float(rec["DosesPerVial"])

        resultDict = {'Avail':{},'OverAllVA':0.0,'Wastage':{},'FIC':0.0,'Doses':0.0,'StorageCost':{},
                      'DosesByAntigen':{},'VialsUsed':{},
                      'Maintanence':{'Central':0.0,'Division':0.0,'District':75000,'PHC':263250,'OutreachClinic':0.0},
                      'CB':{'Central':0.0,'Division':0,'District':71219,'PHC':506815,'OutreachClinic':0.0},
                      'LaborCost':{},'BuildingCost':{},'TransportCost':{},
                      'TC':0.0,'TS':0.0,'TSL':{},'TT':0.0,'TTL':{},'TL':0.0,'TLL':{},'TB':0.0,'TBL':{}}

    ### Get Vaccine Avails
    
        vaccine_keys = [x[:-13] for x in resultKeys if x[-12:-4] == "patients"]
    
        availDict = {x:[0.0,0.0] for x in vaccine_keys}
        dosesDict = {x:[0.0] for x in vaccine_keys}
        vialUsedDict = {x:0.0 for x in vaccine_keys}
        
        for rec in resultRecs:
            for key in vaccine_keys:
                if rec['function'] != 'Surrogate':
                    availDict[key][0] += float(rec[key+"_treated_ave"])
                    vialUsedDict[key] += float(rec[key+"_vials_ave"])
                    availDict[key][1] += float(rec[key+"_patients_ave"])


        tot_treated = 0.0
        tot_patients = 0.0

        for vacc,valList in availDict.items():
            tot_treated += valList[0]
            tot_patients += valList[1]
            resultDict['Avail'][vacc] = valList[0]/valList[1]
            resultDict['DosesByAntigen'][vacc] = valList[0]

        for vacc,val in vialUsedDict.items():
            resultDict['VialsUsed'][vacc] = val
        
        resultDict['OverAllVA'] = (tot_treated/tot_patients)
        resultDict['Doses'] = tot_treated

    ### Determine the FIC
        if 'I_DTP_HepB_Hib' in availDict.keys():
            vaccineDoseDict['I_DTP'] = 2

        dpK = []
        for vacc,valList in availDict.items():
            if vacc in vaccineDoseDict.keys():
                dpK.append(valList[0]/vaccineDoseDict[vacc])
            
        resultDict['FIC'] = min(dpK)
        
        
    ### Wastage
        wastageDict = {x:[0.0,0.0] for x in vaccine_keys}
        for rec in resultRecs:
            for key in vaccine_keys:
                if rec['function'] != 'Surrogate':
                    wastageDict[key][0] += float(rec[key+"_treated_ave"])
                    wastageDict[key][1] += float(rec[key+"_vials_ave"])
    
        for vacc,valList in wastageDict.items():
            wast = 1.0 - (wastageDict[vacc][0]/(wastageDict[vacc][1]*dosesPerVial[vacc]))
            if wast < 0.0:
                wast = 0.0
            resultDict['Wastage'][vacc] = wast
    
        
        ### Storage Costs
        for rec in costRecs:
            if rec["ReportingLevel"] == "all":
                cost = rec['StorageCost_ave']
                if cost == "NA":
                    cost = 0.0
                else:
                    cost = float(cost)
                resultDict['StorageCost'][rec['ReportingBranch']] = cost
                resultDict['TSL'][rec['ReportingBranch']] = cost + resultDict['CB'][rec['ReportingBranch']] + resultDict['Maintanence'][rec['ReportingBranch']]
                resultDict['TS'] += cost + resultDict['CB'][rec['ReportingBranch']] + resultDict['Maintanence'][rec['ReportingBranch']]

        ### Labor Costs
        for rec in costRecs:
            if rec["ReportingLevel"] == "all":
                cost = rec['LaborCost_ave']
                if cost == "NA":
                    cost = 0.0
                else:
                    cost = float(cost)
                resultDict['LaborCost'][rec['ReportingBranch']] = cost
                resultDict['TLL'][rec['ReportingBranch']] = cost
                resultDict['TL'] += cost

        ### Buildin Costs
        for rec in costRecs:
            if rec["ReportingLevel"] == "all":
                cost = rec['BuildingCost_ave']
                if cost == "NA":
                    cost = 0.0
                else:
                    cost = float(cost)
                resultDict['BuildingCost'][rec['ReportingBranch']] = cost
                resultDict['TBL'][rec['ReportingBranch']] = cost
                resultDict['TB'] += cost

                
        ### Transport Costs
        for rec in costRecs:
            if rec["ReportingLevel"] == "all":
                cost = rec['PerTripCost_ave']
                if cost == "NA":
                    cost = 0.0
                else:
                    cost = float(cost)
                resultDict['TransportCost'][rec['ReportingBranch']] = cost
                resultDict['TTL'][rec['ReportingBranch']] = cost
                resultDict['TT'] += cost

        ### Have to add Outreach to this item
        outCosts = 0.0
        for rec in costRecs:
            if rec['ReportingBranch'] == 'OutreachClinic':
                outCosts += costPerOutreach*rec['CostingTreatmentDays_ave']

        resultDict['TransportCost']['OutreachClinic'] = outCosts
        resultDict['TTL']['OutreachClinic'] = outCosts
        resultDict['TT'] += outCosts
        results.append((expt['Title'],resultDict))

        print resultDict
    ### OK, now output the columns
        
    style = XFStyle()
    wb = Workbook()
    ws0 = wb.add_sheet('Summary')
    
    row = 0
    col = 1
    heading_xf = ezxf('font: bold on, height 240; align: wrap on, horiz centre, vert top; borders: bottom thin')
    divider_1_xf = ezxf('font: bold on, height 222, colour white; align: horiz left; pattern: pattern solid, fore-color dark_red; borders: bottom thin')
    total_label_xf = ezxf('font: bold on, height 222; align: horiz left; pattern: pattern solid, fore-color grey25',num_format_str='0%')
    total_percent_xf =  ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color grey25',num_format_str='0%')
    total_xf =  ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color grey25',num_format_str='#,##0')
    plain_xf = ezxf('font: bold off, height 222; align: horiz right',num_format_str="#,##0")
    plain_label_xf = ezxf('font: bold off, height 222; align: horiz left')
    plain_percent_xf =  ezxf('font: bold off, height 222; align: horiz right',num_format_str='0%')
    doses_label_xf = ezxf('font: bold on, height 222; align: horiz left; pattern: pattern solid, fore-color olive_ega',num_format_str="#,##0")
    doses_xf = ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color olive_ega',num_format_str="#,##0")
    final_label_xf = ezxf('font: bold on, height 222; align: horiz left; pattern: pattern solid, fore-color light_green',num_format_str="#,##0")
    final_xf = ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color light_green',num_format_str="#,##0.00")
    ws0.row(0).height = 2500
    ws0.col(0).width = 6000
    ws0.write(0,0,'Scenario',heading_xf)
    for expt in results:
        ws0.col(col).width = 6000
        ws0.write(row,col,expt[0],heading_xf)
        col+=1

    #Writing the frame of the sheet
    ws0.write_merge(1,1,0,len(results),'Vaccine Availablity',divider_1_xf)

    row = 2
    for vacc in vaccineList:
        col=0
        ws0.write(row,col,vaccineMonDict[vacc],plain_label_xf)
        col+=1
        for expt in results:
            if vacc in expt[1]['Avail'].keys():
                ws0.write(row,col,expt[1]['Avail'][vacc],plain_percent_xf)
            
            col+=1
        row+=1

    col= 0
    ws0.write(row,col,"Total",total_label_xf)
    col += 1
    for expt in results:
        ws0.write(row,col,expt[1]['OverAllVA'],total_percent_xf)
        col+=1

    row+=1
    col=0
    ws0.write_merge(row,row,0,len(results),'Vaccine Wastage',divider_1_xf)
    row+=1

    for vacc in vaccineList:
        col=0
        ws0.write(row,col,vaccineMonDict[vacc],plain_label_xf)
        col+=1
        for expt in results:
            if vacc in expt[1]['Wastage'].keys():
                ws0.write(row,col,(expt[1]['Wastage'][vacc]),plain_percent_xf)            
            col+=1
        row+=1

    row+=1
    col=0
    ws0.write_merge(row,row,0,len(results),'Doses Administered By Antigen',divider_1_xf)
    row+=1

    for vacc in vaccineList:
        col=0
        ws0.write(row,col,vaccineMonDict[vacc],plain_label_xf)
        col+=1
        for expt in results:
            if vacc in expt[1]['DosesByAntigen'].keys():
                ws0.write(row,col,(expt[1]['DosesByAntigen'][vacc]),plain_xf)            
            col+=1
        row+=1

    row+=1
    col=0
    ws0.write_merge(row,row,0,len(results),'Vials Used By Antigen',divider_1_xf)
    row+=1

    for vacc in vaccineList:
        col=0
        ws0.write(row,col,vaccineMonDict[vacc],plain_label_xf)
        col+=1
        for expt in results:
            if vacc in expt[1]['VialsUsed'].keys():
                ws0.write(row,col,(expt[1]['VialsUsed'][vacc]),plain_xf)            
            col+=1
        row+=1
    col=0
    ws0.write(row,col,'Doses Administered',doses_label_xf)
    col+=1
    for expt in results:
        ws0.write(row,col,expt[1]['Doses'],doses_xf)
        col+=1
    row+=1

    
    col=0
    ws0.write_merge(row,row,0,len(results),'Storage Costs',divider_1_xf)
    row+=1
    total = [0.0 for x in range(0,len(results))]
    for level in LevelOrder:
        col=0
        ws0.write(row,col,level,plain_label_xf)
        col+=1
        for expt in results:
            ws0.write(row,col,expt[1]['StorageCost'][level],plain_xf)
            col+=1
            total[results.index(expt)] += expt[1]['StorageCost'][level]
        row+=1
        
    col=0
    ws0.write(row,col,'Total',total_label_xf)
    col+=1
    for expt in results:
        ws0.write(row,col,total[results.index(expt)],total_xf)
        col+=1
    row+=1
    
    col=0
    ws0.write_merge(row,row,0,len(results),'Maintanence',divider_1_xf)
    row+=1
    total = [0.0 for x in range(0,len(results))]
    for level in LevelOrder:
        col=0
        ws0.write(row,col,level,plain_label_xf)
        col+=1
        for expt in results:
            ws0.write(row,col,expt[1]['Maintanence'][level],plain_xf)
            col+=1
            total[results.index(expt)] += expt[1]['Maintanence'][level]
        row+=1
        
    col=0
    ws0.write(row,col,'Total',total_label_xf)
    col+=1
    for expt in results:
        ws0.write(row,col,total[results.index(expt)],total_xf)
        col+=1
    row+=1

    col=0
    ws0.write_merge(row,row,0,len(results),'Recurring Transport Costs',divider_1_xf)
    row+=1
    total = [0.0 for x in range(0,len(results))]
    for level in LevelOrder:
        col=0
        ws0.write(row,col,level,plain_label_xf)
        col+=1
        for expt in results:
            ws0.write(row,col,expt[1]['TransportCost'][level],plain_xf)
            col+=1
            total[results.index(expt)] += expt[1]['TransportCost'][level]
        row+=1
        
    col=0
    ws0.write(row,col,'Total',total_label_xf)
    col+=1
    for expt in results:
        ws0.write(row,col,total[results.index(expt)],total_xf)
        col+=1
    row+=1

    col=0
    ws0.write_merge(row,row,0,len(results),'CB and VC Costs',divider_1_xf)
    row+=1
    total = [0.0 for x in range(0,len(results))]
    for level in LevelOrder:
        col=0
        ws0.write(row,col,level,plain_label_xf)
        col+=1
        for expt in results:
            ws0.write(row,col,expt[1]['CB'][level],plain_xf)
            col+=1
            total[results.index(expt)] += expt[1]['CB'][level]
        row+=1
        
    col=0
    ws0.write(row,col,'Total',total_label_xf)
    col+=1
    for expt in results:
        ws0.write(row,col,total[results.index(expt)],total_xf)
        col+=1
    row+=1

    col=0
    ws0.write_merge(row,row,0,len(results),'Total Storage Costs',divider_1_xf)
    row+=1
    total = [0.0 for x in range(0,len(results))]
    for level in LevelOrder:
        col=0
        ws0.write(row,col,level,plain_label_xf)
        col+=1
        for expt in results:
            ws0.write(row,col,expt[1]['TSL'][level],plain_xf)
            col+=1
            total[results.index(expt)] += expt[1]['TSL'][level]
        row+=1
        
    col=0
    ws0.write(row,col,'Total',total_label_xf)
    col+=1
    for expt in results:
        ws0.write(row,col,total[results.index(expt)],total_xf)
        col+=1
    row+=1

    col=0
    ws0.write_merge(row,row,0,len(results),'Total Transport Costs',divider_1_xf)
    row+=1
    total = [0.0 for x in range(0,len(results))]
    for level in LevelOrder:
        col=0
        ws0.write(row,col,level,plain_label_xf)
        col+=1
        for expt in results:
            ws0.write(row,col,expt[1]['TTL'][level],plain_xf)
            col+=1
            total[results.index(expt)] += expt[1]['TTL'][level]
        row+=1
        
    col=0
    ws0.write(row,col,'Total',total_label_xf)
    col+=1
    for expt in results:
        ws0.write(row,col,total[results.index(expt)],total_xf)
        col+=1
    row+=1

    col=0
    ws0.write_merge(row,row,0,len(results),'Total Labor Costs',divider_1_xf)
    row+=1
    total = [0.0 for x in range(0,len(results))]
    for level in LevelOrder:
        col=0
        ws0.write(row,col,level,plain_label_xf)
        col+=1
        for expt in results:
            ws0.write(row,col,expt[1]['TLL'][level],plain_xf)
            col+=1
            total[results.index(expt)] += expt[1]['TLL'][level]
        row+=1
        
    col=0
    ws0.write(row,col,'Total',total_label_xf)
    col+=1
    for expt in results:
        ws0.write(row,col,total[results.index(expt)],total_xf)
        col+=1
    row+=1

    col=0
    ws0.write_merge(row,row,0,len(results),'Total Building Costs',divider_1_xf)
    row+=1
    total = [0.0 for x in range(0,len(results))]
    for level in LevelOrder:
        col=0
        ws0.write(row,col,level,plain_label_xf)
        col+=1
        for expt in results:
            ws0.write(row,col,expt[1]['TBL'][level],plain_xf)
            col+=1
            total[results.index(expt)] += expt[1]['TBL'][level]
        row+=1
        
    col=0
    ws0.write(row,col,'Total',total_label_xf)
    col+=1
    for expt in results:
        ws0.write(row,col,total[results.index(expt)],total_xf)
        col+=1
    row+=1  

    col=0
    ws0.write(row,col,'Total Logistics Cost',total_label_xf)
    col += 1
    for expt in results:
        total = expt[1]['TS'] + expt[1]['TT'] + expt[1]['TL'] + expt[1]['TB']
        ws0.write(row,col,total,total_xf)
        col += 1

    row += 2

    col = 0
    ws0.write(row,col,'Per Dose Administered',final_label_xf)
    col +=1
    for expt in results:
        total = expt[1]['TS'] + expt[1]['TT'] + expt[1]['TL'] + expt[1]['TB']
        ws0.write(row,col,total/expt[1]['Doses'],final_xf)
        col+=1
    row += 1

    col = 0
    ws0.write(row,col,'Per FIC',final_label_xf)
    col +=1
    for expt in results:
        total = expt[1]['TS'] + expt[1]['TT'] + expt[1]['TL'] + expt[1]['TB']
        ws0.write(row,col,total/expt[1]['FIC'],final_xf)
        col+=1

    
    wb.save('Kerala_Summary.xls')
'''
    resultStringList = []
    
    for vacc in vaccineList:
        if resultDict['Avail'].has_key(vacc):
            resultStringList.append("%s,%10.0f"%(vaccineMonDict[vacc],resultDict['Avail'][vacc]))
        else:
            resultStringList.append("%s,"%(vaccineMonDict[vacc]))
    
    resultStringList.append("Overall,%10.0f"%(overAllVA))
    resultStringList.append(",")
    
    for vacc in vaccineList:
        if resultDict['Wastage'].has_key(vacc):
            resultStringList.append("%s,%10.0f"%(vaccineMonDict[vacc],resultDict['Wastage'][vacc]))
        else:
            resultStringList.append("%s,"%(vaccineMonDict[vacc]))

    resultStringList.append("Doses Administered,%10.0f"%resultDict['Doses'])
    
    ### Storage

    for cost in ['StorageCost','Maintanence','TransportCost','CB']:
        resultStringList.append(",")
        total = 0.0
        print cost
        for level in LevelOrder:
            resultStringList.append("%s,%10.0f"%(level,resultDict[cost][level]))
            total+= resultDict[cost][level]

        resultStringList.append("Total,%10.0f"%total)
    

    totalCost = 0.0
    ## total Storage
    resultStringList.append(",")
    total = 0.0
    for level in LevelOrder:
        costValue = resultDict['StorageCost'][level] + resultDict['Maintanence'][level] + resultDict['CB'][level]
        resultStringList.append("%s,%10.0f"%(level,costValue))
        total += costValue

    totalCost += total
    resultStringList.append("Total,%10.0f"%total)

    # Total Transport
    resultStringList.append(",")
    total = 0.0
    for level in LevelOrder:
        costValue = resultDict['TransportCost'][level]
        resultStringList.append("%s,%10.0f"%(level,costValue))
        total += costValue

    totalCost += total
    resultStringList.append("Total,%10.0f"%total)

    # Total Labor
    resultStringList.append(",")
    total = 0.0
    for level in LevelOrder:
        costValue = resultDict['LaborCost'][level]
        resultStringList.append("%s,%10.0f"%(level,costValue))
        total += costValue

    totalCost += total
    resultStringList.append("Total,%10.0f"%total)

    # Total Building
    resultStringList.append(",")
    total = 0.0
    for level in LevelOrder:
        costValue = resultDict['BuildingCost'][level]
        resultStringList.append("%s,%10.0f"%(level,costValue))
        total += costValue

    totalCost += total
    resultStringList.append("Total,%10.0f"%total)

    resultStringList.append("Total Logistics Cost,%10.0f"%totalCost)
    resultStringList.append("Cost per Dose Administered,%10.2f"%(totalCost/resultDict['Doses']))
    resultStringList.append("Cost per FIC,%10.2f"%(totalCost/resultDict['FIC']))
    resultString = "\n".join(resultStringList)
'''
    #print resultString
if __name__== '__main__':
    main()
