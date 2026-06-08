# Manual de Instalación y Mantenimiento - IFRS 16 Pro (Versión Docker)

Este documento está redactado de manera extremadamente detallada para guiar al personal técnico o de infraestructura (TI) en la instalación inicial y el mantenimiento de la plataforma **IFRS 16 Pro**. 

Siga las instrucciones paso a paso para garantizar un despliegue exitoso y sin pérdida de datos contables.

---

## Estructura del Documento
1. [Requisitos Previos del Servidor](#1-requisitos-previos-del-servidor)
2. [Estructura de la Carpeta de Instalación](#2-estructura-de-la-carpeta-de-instalación)
3. [Guía de Instalación Inicial (Día 1)](#3-guía-de-instalación-inicial-día-1)
4. [Cómo Acceder a la Aplicación](#4-cómo-acceder-a-la-aplicación)
5. [Protocolo de Actualización de Versión (Mantenimiento)](#5-protocolo-de-actualización-de-versión-mantenimiento)
6. [Resolución de Problemas Comunes (Troubleshooting)](#6-resolución-de-problemas-comunes-troubleshooting)

---

## 1. Requisitos Previos del Servidor

Antes de iniciar la instalación, asegúrese de que el servidor (ya sea Linux Ubuntu/Debian, RedHat o Windows Server con WSL2) cumpla con los siguientes requisitos:

1. **Docker Engine:** Versión 20.10 o superior instalada y activa.
   * *Para verificarlo, ejecute en la consola:* `docker --version`
2. **Docker Compose:** Versión 2.0 o superior instalada.
   * *Para verificarlo, ejecute en la consola:* `docker compose version`
3. **Puerto de Red Libre:** El puerto **8501** del servidor debe estar libre y no ser utilizado por ningún otro servicio contable o web.
4. **Firewall:** El firewall del servidor debe permitir el tráfico de red de entrada en el puerto **8501** para que los usuarios puedan acceder desde la red interna.

---

## 2. Estructura de la Carpeta de Instalación

El paquete de entrega proporcionado por el desarrollador contiene **4 archivos esenciales**. Debe colocarlos todos en la misma carpeta física en el servidor (por ejemplo, `/opt/ifrs16_pro/` en Linux, o `C:\IFRS16_Pro\` en Windows).

La carpeta debe lucir exactamente así antes de iniciar cualquier comando:

```text
📁 C:\IFRS16_Pro\  (o /opt/ifrs16_pro/)
 ├── 📄 instalador_ifrs16.tar                 <-- La imagen del software (Cifrada)
 ├── 📄 docker-compose.yml                    <-- Configuración de inicio de Docker
 ├── 💾 ifrs16_platinum.db                    <-- Base de datos real del negocio
 └── 📑 Manual_IT_Instalacion_y_Mantenimiento.md  <-- Este manual de instrucciones
```

> [!IMPORTANT]
> **ADVERTENCIA CRÍTICA SOBRE LA BASE DE DATOS:**
> El archivo `ifrs16_platinum.db` **DEBE estar físicamente en la carpeta antes** de iniciar los contenedores. Si intentas ejecutar Docker y este archivo no existe, Docker asumirá por error que es una carpeta y creará un directorio vacío llamado `ifrs16_platinum.db`, lo cual dañará el arranque del sistema.

---

## 3. Guía de Instalación Inicial (Día 1)

Siga este orden estricto de pasos en la consola de comandos del servidor (Terminal en Linux, o PowerShell/CMD en Windows):

### Paso 3.1: Navegar a la carpeta del proyecto
Abra la terminal del sistema y desplácese a la carpeta de instalación creada:
* **En Windows (PowerShell):**
  ```powershell
  cd C:\IFRS16_Pro\
  ```
* **En Linux:**
  ```bash
  cd /opt/ifrs16_pro/
  ```

### Paso 3.2: Cargar la Imagen del Software en Docker
Importe la imagen del sistema desde el archivo `.tar` ejecutando el siguiente comando:
```bash
docker load -i instalador_ifrs16.tar
```
*Espere a que la barra de carga finalice. Al terminar, la consola mostrará un mensaje de éxito similar a:* `Loaded image: ifrs16_pro_image:latest`.

### Paso 3.3: Iniciar la Aplicación
Inicie el contenedor en segundo plano (modo desatendido/daemon) ejecutando:
```bash
docker-compose up -d
```
*(O `docker compose up -d` dependiendo de la versión de Docker de su servidor).*

### Paso 3.4: Verificar que el Contenedor está Activo
Para asegurarse de que el contenedor está funcionando correctamente, ejecute:
```bash
docker ps
```
Debería ver una línea con los siguientes detalles:
* **Names:** `ifrs16_pro_app`
* **Status:** `Up X seconds` o `Up X minutes`
* **Ports:** `0.0.0.0:8501->8501/tcp`

---

## 4. Cómo Acceder a la Aplicación

Una vez levantado el contenedor:
* **Desde el mismo servidor:** Abra un navegador web e ingrese a `http://localhost:8501` o `http://127.0.0.1:8501`.
* **Desde computadores de la red local:** Los usuarios deben ingresar a la IP fija del servidor en el puerto 8501.
  * **Ejemplo:** `http://192.168.1.50:8501`

---

## 5. Protocolo de Actualización de Versión (Mantenimiento)

Cuando el proveedor envíe una nueva versión, usted recibirá un nuevo archivo `.tar`. Siga este procedimiento para actualizar la plataforma **sin riesgo de borrar contratos históricos ni invalidar la licencia contable activa**:

### Paso 5.1: Crear una Copia de Seguridad (Backup)
Antes de tocar el servicio, copie el archivo `ifrs16_platinum.db` a una carpeta externa y segura.
* **Comando en Linux:**
  ```bash
  cp ifrs16_platinum.db /ruta/segura/backups/ifrs16_platinum_backup_$(date +%F).db
  ```
* **En Windows:** Simplemente copie y pegue el archivo `ifrs16_platinum.db` en otra carpeta con un nombre descriptivo.

### Paso 5.2: Apagar el Contenedor Actual
```bash
docker-compose down
```
*Este comando apagará y removerá de forma segura el contenedor de la versión antigua. Los datos en el archivo `.db` se mantendrán intactos en el servidor.*

### Paso 5.3: Cargar la Nueva Imagen
Reemplace el archivo `instalador_ifrs16.tar` antiguo en la carpeta por el nuevo archivo `.tar` recibido y ejecute:
```bash
docker load -i instalador_ifrs16.tar
```

### Paso 5.4: Levantar la Nueva Versión
Inicie el contenedor nuevamente:
```bash
docker-compose up -d
```
*El sistema se iniciará usando el nuevo código cargado, montando automáticamente la base de datos con los datos reales previos.*

### Paso 5.5: Limpieza de Disco (Opcional)
Para liberar espacio de almacenamiento eliminando imágenes obsoletas del sistema:
```bash
docker image prune -f
```

---

## 6. Resolución de Problemas Comunes (Troubleshooting)

### Problema A: El comando `docker-compose up -d` falla porque el puerto 8501 está ocupado
* **Causa:** Otro programa en el servidor ya está utilizando el puerto 8501.
* **Solución:** Cambie el puerto de acceso externo en el archivo `docker-compose.yml`.
  1. Abra el archivo `docker-compose.yml` con un editor de texto (Notepad, nano, etc.).
  2. Modifique la línea de puertos (ports) de:
     ```yaml
     ports:
       - "8501:8501"
     ```
     a un puerto libre en su servidor (por ejemplo, el 9000):
     ```yaml
     ports:
       - "9000:8501"
     ```
     *(El lado izquierdo es el puerto público en el servidor; el derecho es el puerto interno del contenedor y NUNCA debe cambiarse).*
  3. Guarde el archivo y ejecute: `docker-compose up -d`
  4. Los usuarios ahora accederán a través de: `http://<IP-SERVIDOR>:9000`.

### Problema B: Docker creó una carpeta llamada `ifrs16_platinum.db` y la aplicación falla
* **Causa:** Levantó Docker antes de colocar el archivo de base de datos en la carpeta del servidor.
* **Solución:**
  1. Detenga el servicio: `docker-compose down`
  2. Elimine la carpeta vacía errónea `ifrs16_platinum.db`.
  3. Copie el archivo real `ifrs16_platinum.db` provisto por el desarrollador dentro del directorio.
  4. Inicie el servicio de nuevo: `docker-compose up -d`

### Problema C: La aplicación web se cae o muestra un error en pantalla
* **Solución:** Revise las bitácoras (logs) del contenedor para diagnosticar la falla. Ejecute en la consola:
  ```bash
  docker logs ifrs16_pro_app
  ```
  Esto mostrará las líneas del terminal interno del sistema y el mensaje de error exacto para enviarlo al equipo de desarrollo si es necesario.
