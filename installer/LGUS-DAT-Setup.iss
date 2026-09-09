#define AppVersion "1.0.2"
#define AppName "LGUS-DAT"
#define AppPublisher "Jake Hellsing"
#define AppURL ""

[Setup]
AppId=72D4E2B4-7F6A-4B7E-9C1D-3E8A5F2B1C6D
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=LGUS-DAT-Setup-V{#AppVersion}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
WizardStyle=modern
UninstallDisplayIcon={app}\lgus-dat-desktop-V{#AppVersion}.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\desktop\lgus-dat-desktop-V{#AppVersion}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\lgus-dat-desktop-V{#AppVersion}.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\lgus-dat-desktop-V{#AppVersion}.exe"; Tasks: desktopicon
