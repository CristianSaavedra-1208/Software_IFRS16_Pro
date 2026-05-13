# Manual de Instalación y Mantenimiento - IFRS 16 Pro (Versión Docker)

Este documento contiene las instrucciones exclusivas para el equipo de Infraestructura / TI encargados del servidor que aloja la plataforma **IFRS 16 Pro**. 

Su objetivo es guiar el proceso de instalación inicial y despliegue de actualizaciones del software **sin riesgo de pérdida de datos financieros** ni afectación a la licencia vigente.

---

## 0. Requisitos del Servidor
Para que el software funcione correctamente, el servidor (Linux o Windows) debe cumplir con:
1. **Docker Engine** instalado y en ejecución.
2. **Docker Compose** instalado.
3. Puertos de red: El puerto **8501** debe estar libre y expuesto en el firewall para el tráfico web.

---

## 1. Instalación Inicial (Día 1)

El proveedor le ha entregado un paquete que contiene **3 elementos esenciales**:
- `instalador_ifrs16.tar`: La imagen sellada del sistema (binarios compilados).
- `docker-compose.yml`: Archivo de orquestación.
- `ifrs16_platinum.db`: Base de datos inicial.

### Pasos de Instalación:
1. Cree una carpeta en su servidor dedicada a la aplicación (Ej: `/opt/IFRS16_Pro/` o `C:\IFRS16_Pro\`).
2. Mueva los 3 archivos entregados dentro de esta nueva carpeta.
3. Abra una terminal/consola en esa carpeta.
4. Cargue la imagen del sistema en Docker ejecutando:
   ```bash
   docker load -i instalador_ifrs16.tar
   ```
   *(Este proceso puede tardar unos minutos dependiendo de la velocidad del disco).*
5. Levante el servicio ejecutando:
   ```bash
   docker-compose up -d
   ```
6. El sistema estará disponible en `http://<IP-DEL-SERVIDOR>:8501`.

---

## 2. Protocolo de Actualización de Versión

Cuando el proveedor envíe una nueva versión, usted recibirá un nuevo archivo `.tar`. **Siga rigurosamente estos pasos para no perder la base de datos ni la licencia actual:**

### Paso 1: Respaldo Preventivo (Backup)
1. Ingrese a la carpeta base del proyecto en su servidor.
2. Copie el archivo `ifrs16_platinum.db` a una ruta segura (Ej: `/backups/ifrs16_platinum_FECHA.db`).
*(Nota: Solo requiere respaldar este archivo, ya que contiene todos los contratos, usuarios y vigencia de la licencia).*

### Paso 2: Detener el Servicio Actual
```bash
docker-compose down
```

### Paso 3: Cargar la Nueva Imagen
Mueva el nuevo archivo `.tar` entregado por el proveedor a la carpeta y ejecute:
```bash
docker load -i nombre_del_nuevo_archivo.tar
```

### Paso 4: Levantar el Servicio Actualizado
```bash
docker-compose up -d
```

### Paso 5: Limpieza de Imágenes Huérfanas (Opcional)
Para liberar espacio en el disco duro de imágenes Docker antiguas:
```bash
docker image prune -f
```

---

## 3. Validación y Licenciamiento
Ingrese a la URL o IP asignada a la plataforma a través de su navegador web (puerto `8501`). 
1. El sistema debe mostrar la pantalla de inicio normal.
2. Si el sistema muestra una pantalla de "Candado Rojo" exigiendo licencia, contacte al proveedor para obtener una nueva llave criptográfica. **No intente modificar la base de datos**.

---
**Fin del Documento**
