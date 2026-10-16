#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
[Setup]
AppId={{D75F765B-4424-4C77-B57B-E5B0C574E19D}
AppName=Moldura
AppVersion={#AppVersion}
AppPublisher=RedLab
AppPublisherURL=https://github.com/redlab-coder/moldura
AppSupportURL=https://github.com/redlab-coder/moldura/issues
AppUpdatesURL=https://github.com/redlab-coder/moldura/releases
DefaultDirName={localappdata}\Programs\Moldura
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
WizardStyle=modern
SetupIconFile=..\assets\moldura-v4.ico
UninstallDisplayIcon={app}\Moldura.exe
OutputDir=..\dist
OutputBaseFilename=Moldura-Setup-{#AppVersion}
Compression=lzma2/fast
SolidCompression=yes
MinVersion=10.0.17763
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
AppMutex=Local\Moldura.Installed.Running
SetupMutex=Local\Moldura.Setup.Running
CloseApplications=no
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; Flags: unchecked

[Files]
Source: "..\dist\Moldura-v8.exe"; DestDir: "{app}"; DestName: "Moldura.exe"; Flags: ignoreversion
Source: "..\assets\installed.marker"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\Moldura"; Filename: "{app}\Moldura.exe"
Name: "{userdesktop}\Moldura"; Filename: "{app}\Moldura.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Moldura.exe"; Description: "Abrir o Moldura"; Flags: nowait postinstall skipifsilent

[Code]
function OpenProcess(Access: LongWord; InheritHandle: Boolean; ProcessId: LongWord): THandle;
external 'OpenProcess@kernel32.dll stdcall';
function WaitForSingleObject(Handle: THandle; Milliseconds: LongWord): LongWord;
external 'WaitForSingleObject@kernel32.dll stdcall';
function CloseHandle(Handle: THandle): Boolean;
external 'CloseHandle@kernel32.dll stdcall';

function InitializeSetup(): Boolean;
var
  ProcessId: Integer;
  Handle: THandle;
begin
  Result := True;
  ProcessId := StrToIntDef(ExpandConstant('{param:WAITPID|0}'), 0);
  if ProcessId > 0 then
  begin
    Handle := OpenProcess($00100000, False, ProcessId);
    if Handle <> 0 then
    begin
      Result := WaitForSingleObject(Handle, 120000) = 0;
      CloseHandle(Handle);
      Sleep(1000);
    end;
  end;
end;
