; IDE Launcher — Inno Setup 6 (v2.0.1)
; Compiled by:  python build.py  (from project root) or ISCC.exe build\installer.iss
; Paths: relative to this file (build/); ..\ = project root

#define MyAppName "IDE Launcher by Adam Natad"
#define MyAppShortName "IDELauncher"
#define MyAppPublisher "Adam Natad"
#define MyAppSupportURL "https://github.com/AdamNatad/IDELauncher/issues"
#define MyAppHelpURL "https://github.com/AdamNatad/IDELauncher"
#define MyAppExeName "IDELauncher.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion=2.0.1
AppVerName={#MyAppName} (v2.0.1)
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppHelpURL}
AppSupportURL={#MyAppSupportURL}
DefaultDirName={autopf}\{#MyAppShortName}
DefaultGroupName={#MyAppShortName}
DisableProgramGroupPage=yes
SetupIconFile=..\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=..\output
OutputBaseFilename=IDELauncher-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppShortName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppShortName}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
    Exec('icacls', ExpandConstant('"{app}"') + ' /grant Users:(OI)(CI)M /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
