#define MyAppName "Keyword Contact Crawler"
#define MyAppVersion GetEnv("GITHUB_RUN_NUMBER")
#define MyAppPublisher "AutoBuild"
#define MyAppExeName "crawler.exe"

[Setup]
AppId={{8F8A3E28-8D7F-4E3F-9E8C-9AE6D2C2A0A1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=KeywordContactCrawlerSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"; LicenseFile: "README-run.txt"

[Files]
Source: "dist\crawler.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "start.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "README-run.txt"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\\data"; Flags: uninsneveruninstall
Name: "{app}\\export"; Flags: uninsneveruninstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "其他:"; Flags: unchecked

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
