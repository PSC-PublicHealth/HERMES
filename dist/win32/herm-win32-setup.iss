﻿; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "HERMES"
#define MyAppPublisher "HERMES Team"
#define MyAppURL "http://hermes.psc.edu"
#define BaseVersion "0.9.1"
#define BaseFilename "hermes-setup"

#ifdef SvnRevision
#	define MyAppVersion BaseVersion + "." + SvnRevision
#	define MySetupName BaseFilename + "-r" + StringChange(SvnRevision, ":", "-")
#else
#	define MyAppVersion BaseVersion
#	define MySetupName BaseFilename
#endif

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{D4EF6D37-5303-45CD-A978-DD25E7FCB75E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=build
OutputBaseFilename={#MySetupName}
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=poweruser
AppMutex=HERMES: Highly Extensible Resource for Modeling Event-driven Supply chains; {{D82029AE-9A89-4A58-AD00-3E5C5CE68400},Global\HERMES: Highly Extensible Resource for Modeling Event-driven Supply chains; {{D82029AE-9A89-4A58-AD00-3E5C5CE68400}
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\hermes-tray.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"
Name: "corsican"; MessagesFile: "compiler:Languages\Corsican.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "greek"; MessagesFile: "compiler:Languages\Greek.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "hungarian"; MessagesFile: "compiler:Languages\Hungarian.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "nepali"; MessagesFile: "compiler:Languages\Nepali.islu"
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "scottishgaelic"; MessagesFile: "compiler:Languages\ScottishGaelic.isl"
Name: "serbiancyrillic"; MessagesFile: "compiler:Languages\SerbianCyrillic.isl"
Name: "serbianlatin"; MessagesFile: "compiler:Languages\SerbianLatin.isl"
Name: "slovenian"; MessagesFile: "compiler:Languages\Slovenian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[CustomMessages]
InstallingDB={code:GetFinishingStatusMsg}
english.AskDelDB=Do you want to remove the {#MyAppName} database? This contains models you have created or modified while using {#MyAppName}.
spanish.AskDelDB=¿Quiere eliminar la base de datos de {#MyAppName}? Este contiene los modelos que ha creado o modificado durante el uso de {#MyAppName}.
russian.AskDelDB=Вы хотите удалить базу данных {#MyAppName}? Здесь находятся модели которые вы создали или модифицировали.
english.InstallingDB=Installing {#MyAppName} database
spanish.InstallingDB=Instalando de la base de datos de {#MyAppName}
russian.InstallingDB=Установка базы данных {#MyAppName}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
;de-fang old faulty {pf}-deleting uninstaller
Type: files; Name: "{app}\unins*.dat"
Type: files; Name: "{app}\unins*.exe"

[Files]
Source: "..\..\HERMES2\*"; Excludes: "*.pyc,*.pyo,alembic.ini,install_hermes.log,..\..\HERMES2\src\ui_www\jquery-ui-1.10.2\demos\*,..\..\HERMES2\src\ui_www\jquery-ui-1.10.2\tests\*,..\..\HERMES2\master_data\*\regression-output\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
;Source: "requirements\*"; Excludes: "*.pyc,*.pyo"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "misc\hermes-tray.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "misc\log_install_hermes.bat"; DestDir: "{app}\src\tools"; Flags: ignoreversion
Source: "reqall\*"; Excludes: "*.pyc,*.pyo"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "req32\*"; Excludes: "*.pyc,*.pyo"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: not Is64BitInstallMode
Source: "req64\*"; Excludes: "*.pyc,*.pyo"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: Is64BitInstallMode

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\hermes-tray.exe"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\hermes-tray.exe"; Tasks: desktopicon


[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: "-m compileall ""{app}"""
Filename: "{cmd}"; Parameters: "/C ""{app}\src\tools\log_install_hermes.bat"""; StatusMsg: "{cm:InstallingDB}"; Flags: runhidden
Filename: "{app}\hermes-tray.exe"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{%appdata}\HERMES\standalone.log"
Type: dirifempty; Name: "{%appdata}\HERMES"
Type: filesandordirs; Name: "{app}"

[Code]
function GetFinishingStatusMsg(Value: string): string;
begin
  Result := SetupMessage(msgStatusRunProgram);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var mRes : integer;
begin
  case CurUninstallStep of
    usUninstall:
      begin
        mRes := MsgBox(ExpandConstant('{cm:AskDelDB}'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2)
        if mRes = IDYES then
          begin
             DeleteFile(ExpandConstant('{%appdata}\HERMES\hermes.db'));
          end;
      end;
  end;
end;