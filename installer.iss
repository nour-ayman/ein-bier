[Setup]
AppId={{D9A4C62B-8E41-48C7-B8FA-32A1C0F7B812}
AppName=ein Bier
AppVersion=1.1
AppPublisher=Wenz
DefaultDirName={localappdata}\Programs\ein Bier
DefaultGroupName=ein Bier
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=ein_Bier_Setup_v1.1
SetupIconFile=static\img\wenz.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\ein Bier\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ein Bier"; Filename: "{app}\ein Bier.exe"; IconFilename: "{app}\ein Bier.exe"
Name: "{autodesktop}\ein Bier"; Filename: "{app}\ein Bier.exe"; IconFilename: "{app}\ein Bier.exe"; Tasks: desktopicon

[Run]
Description: "{cm:LaunchProgram,ein Bier}"; Filename: "{app}\ein Bier.exe"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\app_debug.log"