# -*- mode: python -*-
import os,glob

baseDir = 'C:\Users\Shawn\Workspaces\Eclipse 3.6 Classic\HERMES_p2'
unifiedDir = baseDir + "\master_data\unified"
unifiedFiles = glob.glob(unifiedDir+"\*.csv")

model_files = glob.glob(baseDir+"\model_*.py")
modelFileNames = []
modelNames= []
for mf in model_files:
    fname = os.path.basename(mf)
    name = fname[:-3]
    modelFileNames.append(fname)
    modelNames.append(name)
    

a = Analysis(['main.py']+modelFileNames,
             pathex=['C:\\Users\\Shawn\\Workspaces\\Eclipse 3.6 Classic\\HERMES_p2'],
             hiddenimports=modelNames,
             hookspath=None)

a.datas += [('input_default.csv',baseDir+'/input_default.csv','DATA')]
for uFile in unifiedFiles:
    a.datas += [(os.path.basename(uFile),uFile,'DATA')]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts + [('O','','OPTION')],
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'main.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=True )
