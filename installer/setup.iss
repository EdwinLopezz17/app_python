#define NombreApp "Certificacion"
#define NombreVisible "Certificación"
#define Ejecutable "Certificacion.exe"

#ifndef VersionApp
  #define VersionApp "1.0.0"
#endif

[Setup]
AppId={{8F3C1A72-5D94-4B60-9E2A-7C4B1F0D6E35}
AppName={#NombreVisible}
AppVersion={#VersionApp}
AppVerName={#NombreVisible} {#VersionApp}
VersionInfoVersion={#VersionApp}
DefaultDirName={localappdata}\Programs\{#NombreApp}
PrivilegesRequired=lowest
DefaultGroupName={#NombreVisible}
DisableProgramGroupPage=yes
DisableWelcomePage=no
UninstallDisplayName={#NombreVisible}
UninstallDisplayIcon={app}\{#Ejecutable}
OutputDir=Output
OutputBaseFilename={#NombreApp}-Setup-{#VersionApp}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=no
RestartApplications=no
SetupIconFile=..\app\ui\assets\logo.ico

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\{#NombreApp}\*"
[Icons]
Name: "{group}\{#NombreVisible}"; Filename: "{app}\{#Ejecutable}"
Name: "{group}\Desinstalar {#NombreVisible}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#NombreVisible}"; Filename: "{app}\{#Ejecutable}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#Ejecutable}"; Description: "Iniciar {#NombreVisible}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\.env"

[Code]
var
  PaginaDatos: TInputDirWizardPage;
  RutaDatosPrevia: String;
  DeteccionHecha: Boolean;

function RutaEnvExistente(): String;
var
  Contenido: TArrayOfString;
  i: Integer;
  Linea: String;
  ArchivoEnv: String;
begin
  Result := '';
  ArchivoEnv := AddBackslash(WizardDirValue) + '.env';
  if not FileExists(ArchivoEnv) then
    Exit;
  if not LoadStringsFromFile(ArchivoEnv, Contenido) then
    Exit;
  for i := 0 to GetArrayLength(Contenido) - 1 do
  begin
    Linea := Trim(Contenido[i]);
    if Pos('DATA_PATH=', Uppercase(Linea)) = 1 then
    begin
      Result := Trim(Copy(Linea, 11, Length(Linea)));
      Exit;
    end;
  end;
end;

procedure InitializeWizard();
begin
  RutaDatosPrevia := '';
  DeteccionHecha := False;

  PaginaDatos := CreateInputDirPage(
    wpSelectDir,
    'Carpeta de datos',
    'Elegí dónde se guardará la información de las certificaciones.',
    'Los archivos Excel que cargues y los reportes generados se guardarán en' + #13#10 +
    'esta carpeta. Si no existe, el instalador la creará junto con su estructura' + #13#10 +
    'interna de subcarpetas.',
    False,
    'Carpeta de datos'
  );
  PaginaDatos.Add('');
  PaginaDatos.Values[0] := '';
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID <> PaginaDatos.ID then
    Exit;
  if DeteccionHecha then
    Exit;

  DeteccionHecha := True;
  RutaDatosPrevia := RutaEnvExistente();

  if RutaDatosPrevia <> '' then
    PaginaDatos.Values[0] := RutaDatosPrevia
  else
    PaginaDatos.Values[0] := ExpandConstant('{userdocs}\Certificacion\Datos');
end;

function CarpetaEsEscribible(Ruta: String): Boolean;
var
  Prueba: String;
begin
  Result := False;
  if not DirExists(Ruta) then
  begin
    if not ForceDirectories(Ruta) then
      Exit;
  end;
  Prueba := AddBackslash(Ruta) + 'permiso.tmp';
  if SaveStringToFile(Prueba, 'x', False) then
  begin
    DeleteFile(Prueba);
    Result := True;
  end;
end;

function NextButtonClick(PageId: Integer): Boolean;
var
  Ruta: String;
begin
  Result := True;
  if PageId <> PaginaDatos.ID then
    Exit;

  Ruta := Trim(PaginaDatos.Values[0]);

  if Ruta = '' then
  begin
    MsgBox('Indicá una carpeta de datos para continuar.', mbError, MB_OK);
    Result := False;
    Exit;
  end;

  if Length(Ruta) < 3 then
  begin
    MsgBox('La ruta indicada no es válida.', mbError, MB_OK);
    Result := False;
    Exit;
  end;

  if not CarpetaEsEscribible(Ruta) then
  begin
    MsgBox(
      'No se puede escribir en esa carpeta.' + #13#10#13#10 +
      'Elegí otra ubicación donde tengas permiso de escritura, ' +
      'por ejemplo dentro de Documentos.',
      mbError, MB_OK
    );
    Result := False;
    Exit;
  end;
end;

procedure CrearEstructura(Base: String);
begin
  ForceDirectories(Base);
  ForceDirectories(AddBackslash(Base) + 'usuarios');
  ForceDirectories(AddBackslash(Base) + 'base_datos');
  ForceDirectories(AddBackslash(Base) + 'generales');
  ForceDirectories(AddBackslash(Base) + '_backups');
end;

procedure EscribirEnv(Base: String);
var
  Contenido: TArrayOfString;
begin
  SetArrayLength(Contenido, 1);
  Contenido[0] := 'DATA_PATH=' + RemoveBackslash(Base);
  SaveStringsToFile(ExpandConstant('{app}\.env'), Contenido, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Base: String;
begin
  if CurStep <> ssPostInstall then
    Exit;

  Base := Trim(PaginaDatos.Values[0]);
  if Base = '' then
    Exit;

  CrearEstructura(Base);
  EscribirEnv(Base);
end;
