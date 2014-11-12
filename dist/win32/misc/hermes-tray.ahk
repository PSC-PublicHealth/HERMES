;HERMES tray icon and launcher

#Persistent
#SingleInstance off

url = http://localhost:8080/bottle_hermes/top
seconds_to_attempt = 30
mutex = HERMES: Highly Extensible Resource for Modeling Event-driven Supply chains; {D82029AE-9A89-4A58-AD00-3E5C5CE68400}
logfile = %USERPROFILE%\standalone.log
bugemail = hermes-devel@psc.edu
bugsubject = HERMES bug report
bugsubject := uriEncode(bugsubject)

hMutex := DllCall("OpenMutex", "UInt", 0x00100000, "Int", null, "Str", "Global\" mutex) ; SYNCHRONIZE = 0x00100000L
DllCall("CreateMutex", "uint", 0, "int", false, "Str", mutex)
DllCall("CreateMutex", "uint", 0, "int", false, "Str", "Global\" mutex)
if hMutex <> 0
{
    Gosub, Launch
    ExitApp
}

Menu, Tray, NoStandard
Menu, Tray, Tip, Starting HERMES...
TrayTip, HERMES, Starting HERMES..., 30

IsFirstRun := false
IfNotExist, %logfile%
    IsFirstRun := true

;EnvSet, PATH, %A_ScriptDir%\python\,%A_ScriptDir%\python\Scripts\,%PATH%
SetWorkingDir %A_ScriptDir%\src\ui_server
Run, %A_ScriptDir%\python\pythonw.exe standalone_server.py, , , StandaloneServerPid

FoundServer := false
Loop, %seconds_to_attempt% {
    Sleep, 1000
    response := HttpQueryInfo(url)
    if InStr(response, "200 OK")
    {
        FoundServer := true
        break
    }
}

if not (FoundServer) {
    MsgBox, Error: Cannot start HERMES server.
    Gosub, Quit
}
Gosub, Launch
Menu, Tray, Add, Launch, Launch
Menu, Tray, Default, Launch
Menu, Tray, Add, Send a Bug Report, Bug
Menu, Tray, Add ; separator
Menu, Tray, Add, Quit, Quit
Menu, Tray, Tip, HERMES

MsgBox, %IsFirstRun%
if (IsFirstRun)
{
    TrayTip, HERMES, First time running HERMES? Launch or quit it from here., 30
}
Goto End

Launch:
Run, %url%
return

Bug:
IfExist, %logfile%
{
    logtail := SubStr(uriEncode(TF_Tail(logfile, 200)),-2000)
    Run, mailto:%bugemail%?subject=%bugsubject%&body=%logtail%
}
return

Quit:
Process, Close, %StandaloneServerPid%
Sleep, 1000
ExitApp
return

;TF_Tail from:
;   https://github.com/hi5/TF

TF_Tail(Text, Lines = 1, RemoveTrailing = 0, ReturnEmpty = 1)
{
TF_GetData(OW, Text, FileName)
Neg = 0
If (Lines < 0)
{
Neg=1
Lines:= Lines * -1
}
If (ReturnEmpty = 0) ; remove blank lines first so we can't return any blank lines anyway
{
Loop, Parse, Text, `n, `r
OutPut .= (RegExMatch(A_LoopField,"[\S]+?\r?\n?")) ? A_LoopField "`n" :
StringTrimRight, OutPut, OutPut, 1 ; remove trailing `n added by loop above
Text:=OutPut
OutPut=
}
If (Neg = 1) ; get only one line!
{
Lines++
Output:=Text
StringGetPos, Pos, Output, `n, R%Lines% ; These next two Lines by Tuncay see
StringTrimLeft, Output, Output, % ++Pos ; http://www.autoHotkey.com/forum/viewtopic.php?p=262375#262375
StringGetPos, Pos, Output, `n
StringLeft, Output, Output, % Pos
Output .= "`n"
}
Else
{
Output:=Text
StringGetPos, Pos, Output, `n, R%Lines% ; These next two Lines by Tuncay see
StringTrimLeft, Output, Output, % ++Pos ; http://www.autoHotkey.com/forum/viewtopic.php?p=262375#262375
Output .= "`n"
}
OW = 2 ; make sure we return variable not process file
Return TF_ReturnOutPut(OW, OutPut, FileName, RemoveTrailing)
}

TF_GetData(byref OW, byref Text, byref FileName)
{
OW=0 ; default setting: asume it is a file and create file_copy
IfNotInString, Text, `n ; it can be a file as the Text doesn't contact a newline character
{
If (SubStr(Text,1,1)="!") ; first we check for "overwrite"
{
Text:=SubStr(Text,2)
OW=1 ; overwrite file (if it is a file)
}
IfNotExist, %Text% ; now we can check if the file exists, it doesn't so it is a var
{
If (OW=1) ; the variable started with a ! so we need to put it back because it is variable/text not a file
Text:= "!" . Text
OW=2 ; no file, so it is a var or Text passed on directly to TF
}
}
Else ; there is a newline character in Text so it has to be a variable
{
OW=2
}
If (OW = 0) or (OW = 1) ; it is a file, so we have to read into var Text
{
Text := (SubStr(Text,1,1)="!") ? (SubStr(Text,2)) : Text
FileName=%Text% ; Store FileName
FileRead, Text, %Text% ; Read file and return as var Text
If (ErrorLevel > 0)
{
MsgBox, 48, TF Lib Error, % "Can not read " FileName
ExitApp
}
}
Return
}

TF_ReturnOutPut(OW, Text, FileName, TrimTrailing = 1, CreateNewFile = 0) {
If (OW = 0) ; input was file, file_copy will be created, if it already exist file_copy will be overwritten
{
IfNotExist, % FileName ; check if file Exist, if not return otherwise it would create an empty file. Thanks for the idea Murp|e
{
If (CreateNewFile = 1) ; CreateNewFile used for TF_SplitFileBy* and others
{
OW = 1
Goto CreateNewFile
}
Else
Return
}
If (TrimTrailing = 1)
StringTrimRight, Text, Text, 1 ; remove trailing `n
SplitPath, FileName,, Dir, Ext, Name
If (Dir = "") ; if Dir is empty Text & script are in same directory
Dir := A_WorkingDir
IfExist, % Dir "\backup" ; if there is a backup dir, copy original file there
FileCopy, % Dir "\" Name "_copy." Ext, % Dir "\backup\" Name "_copy.bak", 1
FileDelete, % Dir "\" Name "_copy." Ext
FileAppend, %Text%, % Dir "\" Name "_copy." Ext
Return Errorlevel ? False : True
}
CreateNewFile:
If (OW = 1) ; input was file, will be overwritten by output
{
IfNotExist, % FileName ; check if file Exist, if not return otherwise it would create an empty file. Thanks for the idea Murp|e
{
If (CreateNewFile = 0) ; CreateNewFile used for TF_SplitFileBy* and others
Return
}
If (TrimTrailing = 1)
StringTrimRight, Text, Text, 1 ; remove trailing `n
SplitPath, FileName,, Dir, Ext, Name
If (Dir = "") ; if Dir is empty Text & script are in same directory
Dir := A_WorkingDir
IfExist, % Dir "\backup" ; if there is a backup dir, copy original file there
FileCopy, % Dir "\" Name "." Ext, % Dir "\backup\" Name ".bak", 1
FileDelete, % Dir "\" Name "." Ext
FileAppend, %Text%, % Dir "\" Name "." Ext
Return Errorlevel ? False : True
}
If (OW = 2) ; input was var, return variable
{
If (TrimTrailing = 1)
StringTrimRight, Text, Text, 1 ; remove trailing `n
Return Text
}
}


uriEncode(str)
{
	; Replace characters with uri encoded version except for letters, numbers,
	; and the following: /.~:&=-

	f = %A_FormatInteger%
	SetFormat, Integer, Hex
	pos = 1
	Loop
		If pos := RegExMatch(str, "i)[^\/\w\.~`:%&=-]", char, pos++)
			StringReplace, str, str, %char%, % "%" . Asc(char), All
		Else Break
	SetFormat, Integer, %f%
	StringReplace, str, str, 0x, , All
	Return, str
}


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; HttpQueryInfo ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
;	http://www.autohotkey.com/forum/post-74345.html#74345

HttpQueryInfo(URL, QueryInfoFlag=21, Proxy="", ProxyBypass="") { 
hModule := DllCall("LoadLibrary", "str", "wininet.dll") 

If (Proxy != "") 
AccessType=3 
Else 
AccessType=1 

io_hInternet := DllCall("wininet\InternetOpenA" 
, "str", "" ;lpszAgent 
, "uint", AccessType 
, "str", Proxy 
, "str", ProxyBypass 
, "uint", 0) ;dwFlags 
If (ErrorLevel != 0 or io_hInternet = 0) { 
DllCall("FreeLibrary", "uint", hModule) 
return, -1 
} 

iou_hInternet := DllCall("wininet\InternetOpenUrlA" 
, "uint", io_hInternet 
, "str", url 
, "str", "" ;lpszHeaders 
, "uint", 0 ;dwHeadersLength 
, "uint", 0x80208000 ;dwFlags: INTERNET_FLAG_RELOAD = 0x80000000 // retrieve the original item 
, "uint", 0) ;dwContext 
If (ErrorLevel != 0 or iou_hInternet = 0) { 
DllCall("FreeLibrary", "uint", hModule) 
return, -1 
} 

VarSetCapacity(buffer, 1024, 0) 
VarSetCapacity(buffer_len, 4, 0) 

Loop, 5 
{ 
  hqi := DllCall("wininet\HttpQueryInfoA" 
  , "uint", iou_hInternet 
  , "uint", QueryInfoFlag ;dwInfoLevel 
  , "uint", &buffer 
  , "uint", &buffer_len 
  , "uint", 0) ;lpdwIndex 
  If (hqi = 1) { 
    hqi=success 
    break 
  } 
} 

IfNotEqual, hqi, success, SetEnv, res, timeout 

If (hqi = "success") { 
p := &buffer 
Loop 
{ 
  l := DllCall("lstrlen", "UInt", p) 
  VarSetCapacity(tmp_var, l+1, 0) 
  DllCall("lstrcpy", "Str", tmp_var, "UInt", p) 
  p += l + 1  
  res := res  . "`n" . tmp_var 
  If (*p = 0) 
  Break 
} 
StringTrimLeft, res, res, 1 
} 

DllCall("wininet\InternetCloseHandle",  "uint", iou_hInternet) 
DllCall("wininet\InternetCloseHandle",  "uint", io_hInternet) 
DllCall("FreeLibrary", "uint", hModule) 

return, res 
}

End: