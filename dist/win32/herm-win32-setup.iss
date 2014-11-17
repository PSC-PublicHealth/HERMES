; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "HERMES"
#define MyAppVersion "0.9.1"
#define MyAppPublisher "HERMES Team"
#define MyAppURL "http://hermes.psc.edu"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{D4EF6D37-5303-45CD-A978-DD25E7FCB75E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=C:\HermesInnoOut
OutputBaseFilename=hermes-setup-win32
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
AppMutex=HERMES: Highly Extensible Resource for Modeling Event-driven Supply chains; {{D82029AE-9A89-4A58-AD00-3E5C5CE68400},Global\HERMES: Highly Extensible Resource for Modeling Event-driven Supply chains; {{D82029AE-9A89-4A58-AD00-3E5C5CE68400}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
;de-fang old faulty {pf}-deleting uninstaller
Type: files; Name: "{app}\unins*.dat"
Type: files; Name: "{app}\unins*.exe"

[Files]
Source: "..\..\HERMES2\*"; Excludes: "*.pyc,*.pyo,..\..\HERMES2\src\ui_www\jquery-ui-1.10.2\demos\*,..\..\HERMES2\src\ui_www\jquery-ui-1.10.2\tests\*,..\..\HERMES2\master_data\*\regression-output\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "requirements\*"; Excludes: "*.pyc,*.pyo"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "misc\hermes-tray.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "misc\log_install_hermes.bat"; DestDir: "{app}\src\tools"; Flags: ignoreversion

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\hermes-tray.exe"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\hermes-tray.exe"; Tasks: desktopicon


[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: "-m compileall ""{app}"""; StatusMsg: "Compiling Python libraries"
Filename: "{cmd}"; Parameters: "/C ""{app}\src\tools\log_install_hermes.bat"""; StatusMsg: "Installing HERMES database"; Flags: runhidden
Filename: "{app}\hermes-tray.exe"; Description: "Run HERMES"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{%appdata}\HERMES\standalone.log"
Type: dirifempty; Name: "{%appdata}\HERMES"
Type: filesandordirs; Name: "{app}"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var mRes : integer;
begin
  case CurUninstallStep of
    usUninstall:
      begin
        mRes := MsgBox('Do you want to remove the HERMES database? This contains models you have created or modified while using HERMES.', mbConfirmation, MB_YESNO or MB_DEFBUTTON2)
        if mRes = IDYES then
          begin
             DeleteFile(ExpandConstant('{%appdata}\HERMES\hermes.db'));
          end;
      end;
  end;
end;