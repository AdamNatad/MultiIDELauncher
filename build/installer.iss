; Multi-IDE Launcher — Inno Setup 6 (v2.0.0)
; Compiled by:  python build.py  (from project root) or ISCC.exe build\installer.iss
; Paths: relative to this file (build/); ..\ = project root

#define MyAppName "Multi-IDE Launcher"
#define MyAppShortName "MultiIDELauncher"
#define MyAppPublisher "Multi-IDE Launcher"
#define MyAppSupportURL "https://github.com/AdamNatad/MultiIDELauncher/issues"
#define MyAppHelpURL "https://github.com/AdamNatad/MultiIDELauncher"
#define MyAppExeName "MultiIDELauncher.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion=2.0.0
AppVerName={#MyAppName} (v2.0.0)
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppHelpURL}
AppSupportURL={#MyAppSupportURL}
DefaultDirName={autopf}\{#MyAppShortName}
DefaultGroupName={#MyAppShortName}
DisableProgramGroupPage=yes
SetupIconFile=..\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=..\output
OutputBaseFilename=MultiIDELauncher-Setup
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
