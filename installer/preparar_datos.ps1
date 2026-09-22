<#
    preparar_datos.ps1

    Equivalente de CrearEstructura() + EscribirEnv() del setup.iss.
    Lo invoca la custom action PrepararDatos del MSI despues de copiar
    los archivos.

    Dos responsabilidades:
      1. Crear la carpeta de datos y sus subcarpetas
      2. Escribir <INSTALLFOLDER>\.env con DATA_PATH en UTF-8 SIN BOM

    El "sin BOM" no es cosmetico: app/config.py lee el .env y un BOM al
    inicio corrompe la primera clave. Por eso se usa UTF8Encoding($false)
    y no Out-File -Encoding utf8, que en PowerShell 5.1 SI escribe BOM.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $DataPath,
    [Parameter(Mandatory = $true)] [string] $InstallDir
)

$ErrorActionPreference = 'Stop'

function Escribir-Log {
    param([string] $Mensaje)
    $carpeta = Join-Path $env:LOCALAPPDATA 'Certificacion\logs'
    if (-not (Test-Path $carpeta)) {
        New-Item -ItemType Directory -Path $carpeta -Force | Out-Null
    }
    $linea = "{0} [instalador] {1}" -f (Get-Date -Format 'o'), $Mensaje
    Add-Content -Path (Join-Path $carpeta 'instalacion.log') -Value $linea -Encoding UTF8
}

try {
    # --- Normalizacion de la ruta ------------------------------------
    # MSI entrega las rutas de directorio con backslash final.
    $DataPath   = $DataPath.Trim().TrimEnd('\')
    $InstallDir = $InstallDir.Trim().TrimEnd('\')

    if ([string]::IsNullOrWhiteSpace($DataPath)) {
        throw 'DATA_PATH llego vacio.'
    }

    # --- Estructura de carpetas --------------------------------------
    $subcarpetas = @('', 'usuarios', 'base_datos', 'generales', '_backups')
    foreach ($sub in $subcarpetas) {
        $destino = if ($sub) { Join-Path $DataPath $sub } else { $DataPath }
        if (-not (Test-Path $destino)) {
            New-Item -ItemType Directory -Path $destino -Force | Out-Null
        }
    }
    Escribir-Log "Estructura creada en: $DataPath"

    # --- Verificacion de escritura -----------------------------------
    $prueba = Join-Path $DataPath 'permiso.tmp'
    try {
        Set-Content -Path $prueba -Value 'x' -NoNewline
        Remove-Item $prueba -Force
    }
    catch {
        Escribir-Log "ADVERTENCIA: sin permiso de escritura en $DataPath"
    }

    # --- .env en UTF-8 SIN BOM ---------------------------------------
    $rutaEnv = Join-Path $InstallDir '.env'
    $linea   = "DATA_PATH=$DataPath"
    $sinBom  = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($rutaEnv, $linea, $sinBom)

    Escribir-Log "Archivo .env escrito: $rutaEnv"
    exit 0
}
catch {
    Escribir-Log "ERROR: $($_.Exception.Message)"
    # Return="ignore" en la CA: no abortamos la instalacion. La app tiene
    # reparar_env() en precheck.py como red de seguridad.
    exit 0
}
