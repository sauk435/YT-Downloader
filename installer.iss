[Setup]
AppName=YouTube Downloader
AppVersion=1.0
DefaultDirName={pf}\YouTube Downloader
DefaultGroupName=YouTube Downloader
UninstallDisplayIcon={app}\icon.ico
SetupIconFile=icon.ico
Compression=lzma2
SolidCompression=yes
OutputDir=Release
OutputBaseFilename=YT Downloader Instalador

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "TempSource\YT Downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\YouTube Downloader"; Filename: "{app}\YT Downloader.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\YouTube Downloader"; Filename: "{app}\YT Downloader.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\YT Downloader.exe"; Description: "Ejecutar YouTube Downloader ahora"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM ""YT Downloader.exe"""; Flags: runhidden skipifdoesntexist

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
