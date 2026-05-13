# Usamos una imagen oficial de Python liviana y segura
FROM python:3.11-slim

# Configuramos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias básicas del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero las dependencias para aprovechar la caché
COPY requirements.txt .

# Instalamos las librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código fuente (lo que no esté bloqueado por .dockerignore)
COPY . .

# --- PROTECCIÓN DE PROPIEDAD INTELECTUAL ---
# Compilamos todos los archivos .py a archivos binarios ilegibles (.pyc)
RUN python -m compileall -b . 

# Eliminamos los archivos de texto legibles (.py) para que nadie pueda ver ni editar el código fuente
RUN find . -name "*.py" -type f -delete

# Exponemos el puerto de Streamlit
EXPOSE 8501

# Comando de arranque usando el archivo compilado principal
CMD ["streamlit", "run", "app.pyc", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.fileWatcherType=none"]
