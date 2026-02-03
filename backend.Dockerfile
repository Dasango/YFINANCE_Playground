# Usamos una imagen ligera de Python
FROM python:3.10-slim

# Directorio de trabajo en el contenedor
WORKDIR /app

# Copiamos los requisitos primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalamos dependencias
# --no-cache-dir reduce el tamaño de la imagen
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código del backend y los assets necesarios
COPY backend/ ./backend
COPY assets/ ./assets

# Exponemos el puerto (aunque Railway lo gestiona, es buena práctica)
EXPOSE 8000

# Comando de arranque
# Usamos la variable de entorno PORT que Railway inyecta
CMD ["sh", "-c", "uvicorn backend.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
