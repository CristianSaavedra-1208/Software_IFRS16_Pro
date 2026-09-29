@echo off
echo Solicitando permisos de administrador...
powershell -Command "Start-Process cmd -ArgumentList '/k tzutil /s \"\"\"Pacific SA Standard Time\"\"\" & w32tm /resync & echo. & echo ====================================================== & echo LISTO: Zona horaria cambiada a Santiago de Chile (UTC-04:00) & echo ====================================================== & pause & exit' -Verb RunAs"
exit
