$ErrorActionPreference = "Stop"

Write-Host "Iniciando la creacion del paquete seguro para el cliente..." -ForegroundColor Cyan

# 1. Crear directorio del paquete
$OutputDir = "Paquete_Cliente"
if (Test-Path $OutputDir) {
    Remove-Item -Recurse -Force $OutputDir
}
New-Item -ItemType Directory -Path $OutputDir | Out-Null

# 2. Construir la imagen Docker desde la carpeta software_IFRS16_Docker
Write-Host "Construyendo imagen Docker (esto puede tardar unos minutos)..." -ForegroundColor Yellow
cd software_IFRS16_Docker
docker build -t ifrs16_pro_image:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error al construir la imagen Docker." -ForegroundColor Red
    exit 1
}
cd ..

# 3. Exportar la imagen a .tar
Write-Host "Exportando imagen Docker a archivo .tar (encriptando codigo fuente)..." -ForegroundColor Yellow
docker save -o "$OutputDir\instalador_ifrs16.tar" ifrs16_pro_image:latest

# 4. Copiar archivos necesarios para el cliente
Write-Host "Copiando docker-compose y manual..." -ForegroundColor Yellow
Copy-Item "docker-compose-cliente.yml" -Destination "$OutputDir\docker-compose.yml"
Copy-Item "Manual_IT_Instalacion_y_Mantenimiento.md" -Destination "$OutputDir\"

# 5. Copiar base de datos inicial
Copy-Item "ifrs16_platinum.db" -Destination "$OutputDir\"

Write-Host "=====================================================" -ForegroundColor Green
Write-Host "¡PAQUETE CREADO EXITOSAMENTE EN LA CARPETA 'Paquete_Cliente'!" -ForegroundColor Green
Write-Host "Estos son los UNICOS archivos que debes enviar:"
Write-Host "1. instalador_ifrs16.tar (Imagen del sistema)"
Write-Host "2. docker-compose.yml (Configuracion)"
Write-Host "3. ifrs16_platinum.db (Base de datos)"
Write-Host "4. Manual_IT_Instalacion_y_Mantenimiento.md (Instrucciones)"
Write-Host "=====================================================" -ForegroundColor Green
