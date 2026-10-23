#define MyAppName "Cordón de Oro — Sistema de Gestión Empresarial"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#define MyAppPublisher "Cordón de Oro E.I.R.L."
#define MyAppExeName "CordonDeOro.exe"

[Setup]
AppId={{D90DF6F2-121A-492A-A8F4-CC0351CA9D25}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Cordon de Oro
DefaultGroupName=Cordón de Oro
OutputDir=..\output
OutputBaseFilename=CordonDeOro-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\dist\CordonDeOro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env.example"; Flags: ignoreversion
Source: "..\.env"; DestDir: "{app}"; DestName: ".env"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\Cordón de Oro"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Cordón de Oro"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar Cordón de Oro"; Flags: nowait postinstall skipifsilent

