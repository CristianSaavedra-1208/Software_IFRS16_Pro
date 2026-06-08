# Manual de Actualización y Despliegue de Docker - IFRS 16 Pro

Este manual proporciona una guía detallada y técnica de extremo a extremo para el proceso de modificación, empaquetado y actualización del software **IFRS 16 Pro** utilizando contenedores Docker. 

Está dividido en dos partes principales:
1. **Rol de Desarrollador (Tú):** Pasos para modificar el código y generar el archivo de actualización.
2. **Rol de TI del Cliente (Servidor):** Protocolo seguro para aplicar la actualización en el servidor final sin pérdida de datos.

---

## 1. Guía para el Desarrollador (Producir la Actualización)

Sigue estos pasos en tu máquina local cada vez que necesites realizar una modificación en el software (por ejemplo, corregir un reporte, ajustar una cuenta contable o integrar una nueva funcionalidad).

### Paso 1.1: Modificación del Código
* Realiza tus cambios en la raíz del proyecto. Asegúrate de que las modificaciones queden implementadas tanto en la raíz como sincronizadas en la carpeta [software_IFRS16_Docker](file:///c:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/software_IFRS16_Docker) si corresponden a los archivos core del sistema:
  * `app.py`
  * `core.py`
  * `db.py`
  * `reconciliacion.py`
  * `licencia_utils.py`
  * `asistente_ibr.py`
  * `auditoria_ifrs16.py`

### Paso 1.2: Validación de Sintaxis y Compilación
Antes de empaquetar, comprueba que el intérprete de Python no detecte errores en los archivos modificados de la carpeta docker. En tu terminal PowerShell ejecuta:
```powershell
python -m compileall -b software_IFRS16_Docker
```
*Si todo está en orden, se generarán archivos `.pyc` sin arrojar excepciones. Limpia estos archivos de prueba locales ejecutando:*
```powershell
Remove-Item software_IFRS16_Docker\*.pyc -Force
```

### Paso 1.3: Generación del Empaquetado Actualizado
1. Abre la aplicación **Docker Desktop** en tu computador Windows y asegúrate de que el motor esté encendido.
2. Abre una terminal de PowerShell en la raíz del proyecto.
3. Ejecuta el script de empaquetado seguro:
   ```powershell
   .\construir_entregable.ps1
   ```
4. El script automatizado realizará lo siguiente de forma transparente:
   * Compilará la imagen de Docker basada en el `Dockerfile` (que oculta tu código fuente a través del bytecode cifrado y expone el entrypoint wrapper `app.py`).
   * Exportará la imagen cifrada al archivo consolidado `Paquete_Cliente\instalador_ifrs16.tar`.

### Paso 1.4: Qué archivos enviar al Cliente
Para una **actualización de versión**, solo requieres enviarle al cliente el nuevo archivo generado:
* 📦 **`instalador_ifrs16.tar`** (La nueva versión lógica del sistema)

*(No es necesario enviar el archivo `.db` a menos que desees restaurar sus datos a un estado en blanco).*

---

## 2. Guía para el Administrador de TI / Servidor (Aplicar la Actualización)

> [!WARNING]
> **PROTOCOLO DE SEGURIDAD CONTRA PÉRDIDA DE DATOS:**
> Este protocolo asegura que la base de datos de producción (`ifrs16_platinum.db`), que vive físicamente en el disco duro del servidor del cliente, no sufra alteraciones de datos financieros, mantenga todas las licencias de activación vigentes y no sufra tiempos de inactividad prolongados.

Instrucciones paso a paso para ejecutar en el servidor donde está corriendo la plataforma:

### Paso 2.1: Respaldo Preventivo (Backup de Datos)
1. Conéctate al servidor por SSH (si es Linux) o accede a la carpeta de instalación mediante el Explorador de Archivos (si es Windows).
2. Ubica la carpeta base donde está alojada la aplicación (Ej: `/opt/IFRS16_Pro/` o `C:\IFRS16_Pro\`).
3. Localiza el archivo de base de datos **`ifrs16_platinum.db`**.
4. Haz una copia de seguridad física de este archivo y renómbralo con la fecha del día:
   * **Ejemplo:** `ifrs16_platinum_BAK_2026-06-08.db`
   * Almacena esta copia en una ruta de respaldo segura fuera del directorio de instalación.

### Paso 2.2: Detener los Servicios Activos
Detén el contenedor actual para evitar bloqueos de archivos en lectura y escritura:
```bash
docker-compose down
```
*Este comando apagará el contenedor actual de forma segura sin borrar la base de datos, ya que esta se encuentra fuera del contenedor (enlazada mediante un volumen).*

### Paso 2.3: Reemplazar y Cargar la Nueva Imagen del Software
1. Copia el nuevo archivo `instalador_ifrs16.tar` enviado por el proveedor a la carpeta base de instalación en el servidor.
2. Ejecuta el comando de Docker para cargar la nueva imagen:
   ```bash
   docker load -i instalador_ifrs16.tar
   ```
   *Docker detectará la firma `ifrs16_pro_image:latest` y actualizará automáticamente la imagen existente.*

### Paso 2.4: Levantar el Servicio Actualizado
Inicia la plataforma utilizando Docker Compose en modo desatendido (background):
```bash
docker-compose up -d
```
*Docker Compose leerá el archivo `docker-compose.yml` existente, levantará un nuevo contenedor con el código modificado y montará de forma automática el archivo de datos original (`ifrs16_platinum.db`), conservando toda la información histórica e IFRS 16 registrada.*

### Paso 2.5: Verificación de Estado
1. Ingresa a la URL o IP asignada en tu navegador (ejemplo: `http://localhost:8501`).
2. Confirma que la interfaz de inicio cargue correctamente.
3. Dirígete a cualquier sección del sistema para verificar que los contratos y configuraciones del cliente sigan intactos.

### Paso 2.6: Limpieza de Disco (Opcional)
Para liberar espacio de almacenamiento eliminando las versiones lógicas viejas del contenedor que ya no se usan:
```bash
docker image prune -f
```

---
**Fin del Documento**
